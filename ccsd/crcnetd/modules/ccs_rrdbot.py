# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# This handles the rrdbot service.
#
# Author:       Chris Browning <ckb6@cs.waikato.ac.nz>
# Version:      $Id$
#
# crcnetd is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# crcnetd is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# crcnetd; if not, write to the Free Software Foundation, Inc., 
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC
from crcnetd._utils.ccsd_service import ccsd_service, ccs_service_error, \
        registerService, getServiceInstance
from crcnetd._utils.ccsd_cfengine import ccs_revision
from crcnetd._utils.ccsd_ca import *
import os.path
import time
import shutil

ccs_mod_type = CCSD_SERVER

class rrdbot_error(ccs_service_error):
    pass
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def snmp_found(session_id, hostname, classname, number, data=''):
    '''Callback from rrdbot-script reporting a class instance'''

    session = getSessionE(session_id)
    sql = "SELECT a.host_id, b.class_id FROM host a , rrdbot_class b WHERE a.host_name=%s and b.class_name=%s"
    res = session.query(sql, (hostname,classname)) 
    host_id = res[0]["host_id"]
    class_id = res[0]["class_id"]
    link_id = 0;

    # Ensure number is a string, as new postgres cares
    number = str(number)

    #Attempt tp assciate the data to a link
    if data != '':
        sql = "SELECT link_id FROM interface WHERE ip_address=%s"
        res = session.query(sql, (data))
        if res:
            link_id = res[0]["link_id"]

    #Check to see if this class has been found before
    sql = "SELECT num FROM snmp_discovery WHERE host_id=%s AND class_id=%s AND num=%s"
    res = session.query(sql, (host_id, class_id, number))
    #If the class exists update it else add it
    if len(res) > 0:
        sql = "UPDATE snmp_discovery SET ip_address=%s, link_id=%s, timestamp=current_timestamp \
            WHERE host_id=%s AND class_id=%s AND num=%s"
        session.execute(sql, (data, link_id, host_id, class_id, number))
    else:    
        sql = "INSERT INTO snmp_discovery VALUES(%s, %s, %s, %s, %s, current_timestamp)"        
        session.execute(sql, (host_id, class_id, number, data, link_id))
    return 1

@catchEvent("interfaceAdded")
def interfaceAdded(eventName, host_id, session_id, **params):
    addSnmpInstruction(session_id, host_id, 3, None, None, None)

@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def addSnmpInstruction(session_id, host_id, instr, param1=None, param2=None, param3=None):
    '''Adds an instruction that rrdbot-script will deal with'''

    session = getSessionE(session_id)
    sql = "INSERT INTO snmp_instructions VALUES(%s, %s, %s, %s, %s)"        
    session.execute(sql, (host_id, instr, param1, param2, param3))
    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def getSnmpInstructions(session_id):
    '''Get all all snmp instructions'''
    instrs = {1:"Probe for Timed out class", 2:"Probe for Timed out class instance", 3:"Re-probe host"}
    session = getSessionE(session_id)
    sql = "SELECT DISTINCT a.host_id, a.instr, a.param1, a.param2, a.param3, \
        b.host_name FROM snmp_instructions a , host b WHERE b.host_id=a.host_id;"
    res = session.query(sql, ())
    for r in res:
        if r["instr"] in instrs.keys():
            r["instr_name"] = instrs[r["instr"]]
        else:
            r["instr_name"] = "Unknowen"
    return res
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def setSnmpState(session_id, hostname, pid, state):
    global state_lock, state_lock_pid, state_lock_hostname, state_lock_count, state_lock_time
    '''Set the current state of rrdbot-script'''
    session = getSessionE(session_id)
    #Check if it is locked
    if state_lock != 0:

        #If it is locked by the requesting process allow any change
        if state_lock_pid == pid and state_lock_hostname == hostname:
            #When unlocking clear old instructions
            if state == 0 and state_lock == 1:
                state_lock_hostname = None
                state_lock_pid = 0
                if state_lock_time:
                    sql = "DELETE FROM snmp_instructions WHERE timestamp<=%s"
                    session.execute(sql, state_lock_time)
                    state_lock_time = None

            #When a dead scripts lock is relesed by another instance
            #new instructions from the dead script are removed
            if state == -1:
                state = 0
                state_lock_hostname = None
                state_lock_pid = 0
                if state_lock_time:
                    sql = "DELETE FROM snmp_instructions WHERE timestamp>=%s"
                    session.execute(sql, state_lock_time)
                    state_lock_time = None
            
            state_lock = state
            state_lock_count = 0
            return pid

        #If it is the right host but not the right process
        elif hostname == state_lock_hostname:
            #If we are locking for a nightly run and it is locked for a
            #nightly run then deny otherwise assume it will kill it and
            #take over the lock otherwise Deny
            tpid = state_lock_pid
            if state == 2:
                state_lock = state
                state_lock_pid = pid
                state_lock_hostname = hostname
                state_lock_count = 0
                state_lock_time = None
            else:
                state_lock_count += 1
                #Check if failsafe has been breached
                if state_lock_count == 5:
                    log_error("SNMP state_lock failsafe initiated: Forced unlock")
                    state_lock_hostname = None
                    state_lock_pid = 0
                    state_lock_count = 0
                    state_lock = 0
                    state_lock_time = None

            return tpid
        else:
            #Locked by another host so deny
            state_lock_count += 1

            #Check if failsafe has been breached
            if state_lock_count == 5:
                log_error("SNMP state_lock failsafe initiated: Forced unlock")
                state_lock_hostname = None
                state_lock_pid = 0
                state_lock_count = 0
                state_lock = 0    
                state_lock_time = None
            return 0
    else:
        #Not locked so take over the lock
        state_lock = state
        state_lock_pid = pid
        state_lock_hostname = hostname
        state_lock_count = 0
        sql = "SELECT current_timestamp"
        state_lock_time = session.query(sql, ())[0][0]
        return state_lock_pid
    
        
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getSnmpState(session_id):
    '''Get the current state of rrdbot-script'''
    countdown = 0
    if state_lock == 0:
        countdown = round(300-(time.time()%300))
    return state_lock, countdown

@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def flushSnmpInstructions(session_id):
    '''Clear all snmp instructions'''

    session = getSessionE(session_id)
    sql = "DELETE FROM snmp_instructions"
    session.execute(sql, ())
    return 1    
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def addClass(session_id, clas):
    """Adds a new class to the database"""
    session = getSessionE(session_id)
    
    # Build query
    props = ["class_name", "poll", "interval", \
            "cf", "archive", "depends", "upper_bound", "lower_bound"]
   
    nulls= []

    if "lower_bound" in clas and clas["lower_bound"] == '':
        nulls.append("lower_bound")
    if "upper_bound" in clas and clas["upper_bound"] == '':
        nulls.append("upper_bound")            
    (sql, values) = buildInsertFromDict("rrdbot_class", props, clas, False, nulls)
    
    # Run query
    session.execute(sql, values)

    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def addClassPart(session_id, part):
    """Adds a new class part to the database"""
    session = getSessionE(session_id)
    
    # Build query
    props = ["class_id", "name", "poll", "type", \
        "min", "max"]
        
    nulls= []

    if "min" in part and part["min"] == '':
        nulls.append("min")
    if "max" in part and part["max"] == '':
        nulls.append("max")

    (sql, values) = buildInsertFromDict("rrdbot_class_parts", props, part, False, nulls)
    
    # Run query
    session.execute(sql, values)

    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def removeClass(session_id, class_id):
    """Removes class from the database."""
    session = getSessionE(session_id)
    
    #First remove any dependants
    sql = "SELECT * FROM rrdbot_class WHERE depends=%s"

    res = session.query(sql, (class_id))
    for clas in res:
        sql = "UPDATE rrdbot_class SET depends=0, poll=\'%s%s\' WHERE class_id=%%s" % (clas["poll"], ":exist")
        res2 = session.execute(sql, (clas["class_id"]))
    
    # Delete the class and its class parts
    sql = "DELETE FROM rrdbot_class WHERE class_id=%s"
    res = session.execute(sql, (class_id))
    sql = "DELETE FROM rrdbot_class_parts WHERE class_id=%s"
    res = session.execute(sql, (class_id))
    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def updateClassDetails(session_id, class_id, newDetails):
    """Updates the details of the Class.

    newDetails should be a dictionary containing only these class paramters
    that have changed and need to be updated in the database.
    """
    session = getSessionE(session_id)
        
    # Build SQL
    props = ["class_id", "class_name", "poll", "interval", \
        "cf", "archive", "depends", "upper_bound", "lower_bound"]


    nulls= []

    if "lower_bound" in newDetails and newDetails["lower_bound"] == '':
        nulls.append("lower_bound")
    if "upper_bound" in newDetails and newDetails["upper_bound"] == '':
        nulls.append("upper_bound")            
    (sql, values) = buildUpdateFromDict("rrdbot_class", props, newDetails, \
            "class_id", class_id, False, nulls)
        
    if values == None:
        # No changes made... ?
        return 1
    
    # Run the query
    session.execute(sql, values)
   
    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def updateClassPartDetails(session_id, part_id, newDetails):
    """Updates the details of the Class part.

    newDetails should be a dictionary containing only these class paramters
    that have changed and need to be updated in the database.
    """
    session = getSessionE(session_id)
        
    # Build SQL
    props = ["part_id", "class_id", "name", "poll", "type", \
        "min", "max"]
    nulls= []

    if "min" in newDetails and newDetails["min"] == '':
        nulls.append("min")
    if "max" in newDetails and newDetails["max"] == '':
        nulls.append("max")

    (sql, values) = buildUpdateFromDict("rrdbot_class_parts", props, newDetails, \
            "part_id", part_id,False,nulls)
        
    if values == None:
        # No changes made... ?
        return 1
    
    # Run the query
    session.execute(sql, values)

    return 1 
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def listClasses(session_id):
    """Returns a list of classes"""
    session = getSessionE(session_id)
        
    # Build SQL
    sql = "SELECT * FROM rrdbot_class"    
    
    # Run the query
    res = session.query(sql, ())
    return res
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getClass(session_id,class_id):
    """Returns a class"""
    session = getSessionE(session_id)
        
    # Build SQL
    sql = "SELECT * FROM rrdbot_class WHERE class_id=%s"    
    
    # Run the query
    res = session.query(sql, (class_id))
    return res
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getClassDepends(session_id,class_id):
    """Returns a list of classes this class could be set to depend on"""
    session = getSessionE(session_id)    
    #If new class flag is set do a custom query
    if class_id == -1:
         # Build SQL
        sql = "SELECT * FROM rrdbot_class WHERE depends=0"    
    
        # Run the query
        res = session.query(sql, ())

        return res

    # Build SQL
    sql = "SELECT * FROM rrdbot_class WHERE depends=%s"    
    
    # Run the query
    res = session.query(sql, (class_id))

    #If class is depended on it can depend on somthing else
    if len(res) > 0:
        return []

    # Build SQL
    sql = "SELECT * FROM rrdbot_class WHERE class_id!=%s AND depends=0"    
    
    # Run the query
    res = session.query(sql, (class_id))

    return res  
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getClassParts(session_id,class_id):
    """Returns a list of Class parts"""
    session = getSessionE(session_id)
    
    # Build SQL
    sql = "SELECT * FROM rrdbot_class_parts WHERE class_id=%s"    
    
    # Run the query
    res = session.query(sql, (class_id))
    return res
    
@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR)
def getClassPart(session_id, part_id):
    """Returns a class part"""
    session = getSessionE(session_id)
    
    # Build SQL
    sql = "SELECT * FROM rrdbot_class_parts WHERE part_id=%s"    
    
    # Run the query
    res = session.query(sql, (part_id))
    return res

@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def removeClassPart(session_id, part_id):
    """Removes class part from the database."""
    session = getSessionE(session_id)
    
    # Delete the class part
    sql = "DELETE FROM rrdbot_class_parts WHERE part_id=%s"
    res = session.execute(sql, (part_id))
    return 1
    

@catchEvent("revisionPrepared")
def handleRevisionPrepEvent(eventName, host_id, session_id, outputDir):
    """Receives callbacks to add extra information to the config revisions"""
    
    # Get a list of hosts running the rrdbot service
    rrdbot = getServiceInstance(session_id, ccs_rrdbot.serviceName)

    ca = ccs_ca()

    try:
        certsdir = "%s/services/rrdbot/certs" % (outputDir)
        ensureDirExists(certsdir)
        if not os.path.exists("%s/key.pem" % certsdir):
            key = ca.getFile("ca/rrdbot-key.pem")
            fp = open("%s/key.pem" % certsdir, "w")
            fp.write(key)
            fp.close()
        if not os.path.exists("%s/cert.pem" % certsdir):
            cert = ca.getFile("ca/rrdbot-cert.pem")
            fp = open("%s/cert.pem" % certsdir, "w")
            fp.write(cert)
            fp.close()
    except:
        log_error("Could not setup rrdbot certificates for %s" % host, \
                sys.exc_info())
    
class ccs_rrdbot(ccsd_service):

    serviceName = "rrdbot"
    networkService = True

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    def getNetworkTemplateVariables(self):
        """Returns a dictionary containing template variables.

        WARNING: The returned dictionary could be very large!
        """
        variables = ccsd_service.getNetworkTemplateVariables(self)
        session = getSessionE(ADMIN_SESSION_ID)
        res = session.query("SELECT * FROM rrdbot_class",())
        classes = {};
        for clas in res:
            clas["variables"] = session.query("SELECT * FROM \
                rrdbot_class_parts WHERE class_id=%s",(clas["class_id"]))
            if clas["depends"] != 0:
                if clas["depends"] in classes:
                    classes[clas["depends"]]["subs"].append(clas)
                else:
                    classes[clas["depends"]] = {}
                    classes[clas["depends"]]["subs"] = []
                    classes[clas["depends"]]["subs"].append(clas)
            else:
                classes[clas["class_id"]] = clas
                classes[clas["class_id"]]["subs"] = []

        variables['classes'] = classes
        variables["graphport"] = config_get("graphs", "port", "80")
        return variables

            
            
    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising rrdbot service")        
        try:
            

            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (ccs_rrdbot.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS server_id", ())
                    
            # Read in schema and dump into database
            fp = open("%s/ccs_graphs.schema" % \
                    config_get("ccsd", "service_data_dir", \
                    DEFAULT_SERVICE_DATA_DIR))
            schema = fp.readlines()
            fp.close()
            session.execute("\n".join(schema), ())

            # Commit the changeset
            session.commit()
            
            log_info("Created rrdbot service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise rrdbot database entries!", \
                    sys.exc_info())
            raise rrdbot_error("Failed to setup database tables!")

        return service_id

        
def ccs_init():
    from crcnetd._utils.ccsd_session import SYSTEM_TABLES
    global state_lock, state_lock_pid, state_lock_hostname
    registerService(ccs_rrdbot)
    #Ensure Certificates exist
    ca = ccs_ca()
    ca.ensureCertificateExists("rrdbot")
    SYSTEM_TABLES.append("snmp_discovery")
    SYSTEM_TABLES.append("snmp_instructions")
    #Ensure state is set to 0
    state_lock = 0
    state_lock_pid = 0
    state_lock_hostname = None
    state_lock_count = 0
    state_lock_time = None
