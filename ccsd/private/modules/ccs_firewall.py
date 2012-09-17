# Copyright (C) 2006  The University of Waikato
#
# Firewall Service Module for the CRCnet Configuration System
# Configures a basic firewall when requested on a host
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# No usage or redistribution rights are granted for this file unless
# otherwise confirmed in writing by the copyright holder.
#
import re
import svn.client as client

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC
from crcnetd._utils.ccsd_service import ccsd_service, ccs_service_error, \
        registerService
from crcnetd.modules.ccs_interface import INTERFACE_TYPE_ALIAS

ccs_mod_type = CCSD_SERVER

# The default class that is applied to any interface without a specific 
# class configured
DEFAULT_CLASS_PROPERTY = "default_class"

class firewall_error(ccs_service_error):
    pass

class firewall_service(ccsd_service):
    """Configures the firewall service on a host"""
    
    serviceName = "firewall"
    allowNewProperties = True
    networkService = True

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def createFirewallClass(self, details):
        """Creates a new firewall class"""
        session = getSessionE(self._session_id)
        
        # Validate the classname
        if not re.match("^[\w]*$", details["firewall_class_name"]):
            raise firewall_error("Invalid firewall class name")

        try:
            session.begin("Creating firewall class: %s'" % \
                    details["firewall_class_name"])

            # Save the file
            outputDir = session.revision.getConfigBase()
            path = "services/firewall/%s" % details["firewall_class_name"]
            fp = open("%s/%s" % (outputDir, path), "w")
            fp.write(details["contents"].replace("\r\n", "\n"))
            fp.close()

            # Create the database record
            session.execute("INSERT INTO firewall_class " \
                    "(firewall_class_name, description, file_path) " \
                    "VALUES (%s,%s, %s)", (details["firewall_class_name"], \
                    details["description"], path))

            # Commit
            session.commit()
        except:
            # Rollback 
            session.rollback()
            # Error
            (etype, value, tb) = sys.exc_info()
            log_error("Could not create firewall class: %s" % value,
                    (etype, value, tb))
            raise firewall_error(value)

        return True

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def updateFirewallClass(self, details):
        """Updates a firewall class"""
        session = getSessionE(self._session_id)
        
        # Validate the classname
        if not re.match("^[\w]*$", details["firewall_class_name"]):
            raise firewall_error("Invalid firewall class name")
        if "firewall_class_id" not in details.keys():
            raise firewall_error("firewall class ID must be specified")

        try:
            session.begin("Updating firewall class: %s'" % \
                    details["firewall_class_name"])
            outputDir = session.revision.getConfigBase()

            # Retrieve the current record
            res = session.query("SELECT * FROM firewall_class WHERE " \
                    "firewall_class_id=%s", (details["firewall_class_id"]))
            fclass = res[0]

            classname = fclass["firewall_class_name"]
            if "firewall_class_name" in details.keys():
                if details["firewall_class_name"] != classname:
                    # Class name has changed
                    oldfilename = "%s/services/firewall/%s" % \
                            (outputDir, classname)
                    client.svn_client_delete([oldfilename], True, 
                            session.revision.ctx, session.revision.pool)
                    classname = details["firewall_class_name"]

            # Save the file, replacing any CFLF sequences with LF 
            outputDir = session.revision.getConfigBase()
            path = "services/firewall/%s" % classname
            fp = open("%s/%s" % (outputDir, path), "w")
            fp.write(details["contents"].replace("\r\n", "\n"))
            fp.close()
            details["file_path"] = path

            # Update the database record
            props = ["firewall_class_name", "description", "file_path"]
            sql, values = buildUpdateFromDict("firewall_class", props, details, 
                    "firewall_class_id", details["firewall_class_id"])
            session.execute(sql, values)

            # Commit
            session.commit()
        except:
            # Rollback 
            session.rollback()
            # Error
            (etype, value, tb) = sys.exc_info()
            log_error("Could not update firewall class: %s" % value,
                    (etype, value, tb))
            raise firewall_error(value)

        return True

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def removeFirewallClass(self, firewall_class_id):
        """Removes a firewall class"""
        session = getSessionE(self._session_id)
        
        try:
            # Retrieve the current record
            res = session.query("SELECT * FROM firewall_class WHERE " \
                    "firewall_class_id=%s", (firewall_class_id))
            fclass = res[0]

            session.begin("Remove firewall class: %s'" % \
                    fclass["firewall_class_name"])
            outputDir = session.revision.getConfigBase()
            path = "services/firewall/%s" % fclass["firewall_class_name"]
 
            # Remove the file
            client.svn_client_delete(["%s/%s" % (outputDir, path)], True, 
                session.revision.ctx, session.revision.pool)

            # Update the database record
            session.execute("DELETE FROM firewall_class WHERE " \
                    "firewall_class_id=%s", (firewall_class_id))

            # Commit
            session.commit()
        except:
            # Rollback 
            session.rollback()
            # Error
            (etype, value, tb) = sys.exc_info()
            log_error("Could not remove firewall class: %s" % value,
                    (etype, value, tb))
            raise firewall_error(value)

        return True

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def getFirewallClass(self, firewall_class_id):
        """Retrieves a firewall class"""
        session = getSessionE(self._session_id)
        

        # Retrieve the class
        res = session.query("SELECT * FROM firewall_class WHERE " \
                "firewall_class_id=%s", (firewall_class_id))
        if len(res) != 1:
            raise ccs_firewall_error("Unknown firewall class ID")
        fclass = filter_keys(res[0])

        classname = fclass["firewall_class_name"]
        session.begin("get revision")
        outputDir = session.revision.getConfigBase()
        filename = "%s/services/firewall/%s" % (outputDir, classname)
        fp = open(filename, "r")
        fclass["contents"] = fp.read()
        fp.close()
        session.rollback()

        return fclass
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True)
    def getFirewallClasses(self):
        session = getSessionE(self._session_id)

        res = session.query("SELECT * FROM firewall_class", ())
        return map(filter_keys,res)

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getHostFirewallDetails")
    def getHostDetails(self, host_id):
        """Returns data relating to the firewall on a host"""
        session = getSessionE(self._session_id)

        service = ccsd_service.getHostDetails(self, host_id)
        service["interfaces"] = self.getInterfaces(host_id)

        return service

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getFirewallInterfaces")
    def getInterfaces(self, host_id):
        """Returns firewall details for the interfaces for the host"""
        session = getSessionE(self._session_id)

        # Get the interface details
        res = session.query("SELECT i.*, fi.firewall_class_id FROM " \
                "interface i LEFT JOIN firewall_interface fi ON " \
                "i.interface_id=fi.interface_id WHERE i.host_id=%s AND " \
                "i.interface_type!=%s", (host_id, INTERFACE_TYPE_ALIAS))

        # Substitute in the no class set sentinel if nothing is set
        for iface in res:
            if iface["firewall_class_id"] == "":
                iface["firewall_class_id"] = -1

        return res
    
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def updateFirewallInterface(self, host_id, interface_id, firewall_class_id):
        """Updates the firewall class assigned to an interface"""
        session = getSessionE(self._session_id)
                       
        if int(firewall_class_id)==-1:
            session.execute("DELETE FROM firewall_interface WHERE " \
                    "host_id=%s AND interface_id=%s", (host_id, interface_id))
        else:
            try:
                session.execute("INSERT INTO firewall_interface (host_id, " \
                        "interface_id, firewall_class_id) VALUES " \
                        "(%s, %s, %s)", 
                (host_id, interface_id, firewall_class_id))
                # Success
                return True
            except:
                (etype, value, tb) = sys.exc_info()
                # Assume this is because the record already exists
                pass
            # Insert failed, try update
            try:
                session.execute("UPDATE firewall_interface SET " \
                        "firewall_class_id=%s WHERE host_id=%s AND " \
                        "interface_id=%s", 
                        (firewall_class_id, host_id, interface_id))
            except:
                # Log the previous error
                log_error("Failed to insert firewall interface record!", \
                        (etype, value, tb))
                # Now log this error
                log_error("Failed to update firewall interface record!", \
                        sys.exc_info())
    
        # All good
        return True

    def getNetworkTemplateVariables(self):
        """Returns a dictionary containing template variables for the network
        See the getTemplateVariables function for more details.
        """

        # Call base class to get the basics
        variables = ccsd_service.getNetworkTemplateVariables(self)

        variables["firewall_classes"] = self.getFirewallClasses()

        return variables

    def getHostTemplateVariables(self, host_id):
        """Returns a dictionary containing template variables for a host

        See the getTemplateVariables function for more details.
        """

        # Determine the default class id
        values = self.getPropertyValues()
        default_class_id = values[DEFAULT_CLASS_PROPERTY]

        # Create an index of classes
        classes = {}
        for fclass in self.getFirewallClasses():
            classes[fclass["firewall_class_id"]] = fclass["firewall_class_name"]

        # Call base class to get the basics
        variables = ccsd_service.getHostTemplateVariables(self, host_id)

        # Include interface configurations
        interfaces = {}
        for iface in self.getInterfaces(host_id):
            if iface["firewall_class_id"] != -1:
                class_name = classes[iface["firewall_class_id"]]
            else:
                class_name = classes[default_class_id]
            interfaces[iface["name"]] = class_name
        variables["interfaces"] = interfaces
        
        return variables

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising Firewall service")
        
        try:
            # Read in schema and dump into database
            try:
                fp = open("%s/firewall.schema" % \
                        config_get("ccsd", "service_data_dir", \
                        DEFAULT_SERVICE_DATA_DIR))
                schema = fp.readlines()
                fp.close()
                session.execute("\n".join(schema), ())
            except:
                # Assume tables are already existing... try and proceed 
                # executes below will error if this assumption is false
                log_warn("Unable to create database tables!", sys.exc_info())
                # Session has been trashed at this point, start a new one
                session.begin("initialising Firewall service")

            # Create service entries
            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (firewall_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS server_id", ())
                
            # Make sure the default class file exists
            outputPath = session.revision.getConfigBase()
            default_classfile = "%s/services/firewall/default" % outputPath
            if not os.path.exists(default_classfile):
                fp = open(default_classfile, "w")
                fp.write("# Default - Allow everything\n\n")
                fp.write("# Run this on startup\n")
                fp.write("on_startup\n\n")
                fp.write("policy in ACCEPT\npolicy out ACCEPT\n")
                fp.write("policy forward-in ACCEPT\n")
                fp.write("policy forward-out ACCEPT\n\n")
                fp.write("if_feature rp_filter 0\n")
                fp.write("if_feature accept_redirects 0\n")
                fp.write("if_feature accept_source_route 0\n")
                fp.write("if_feature bootp_relay 0\n")
                fp.write("if_feature forwarding 1\n")
                fp.write("if_feature log_martians 0\n")
                fp.write("if_feature send_redirects 0\n")
                fp.flush()
                fp.close()
            # And that it has a database entry
            n = session.getCountOf("SELECT * FROM firewall_class WHERE " \
                    "firewall_class_name=%s", ("default"))
            if n == 0:
                session.execute("INSERT INTO firewall_class " \
                        "(firewall_class_id, firewall_class_name, " \
                        "description, file_path) VALUES (DEFAULT, " \
                        "%s, %s, %s)", ("default", "Default ALLOW " \
                        "rules", "services/firewall/default"))
            default_class_id = session.getCountOf("SELECT firewall_class_id " \
                    "FROM firewall_class WHERE firewall_class_name=%s", 
                    ("default"))

            # Setup the default class property
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, required) " \
                "VALUES (DEFAULT, %s, %s, 'integer', %s, 't')", \
                (service_id, DEFAULT_CLASS_PROPERTY, default_class_id))

            # Commit the changes
            session.commit()
            
            log_info("Created firewall service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise firewall database entries!", \
                    sys.exc_info())
            raise firewall_error("Failed to setup database tables!")

        return service_id

def ccs_init():
    registerService(firewall_service)
