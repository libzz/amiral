# Copyright (C) 2006  The University of Waikato
#
# Amplet Service Module for the CRCnet Configuration System
# Configures an amp monitor on each host it is added to
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# No usage or redistribution rights are granted for this file unless
# otherwise confirmed in writing by the copyright holder.
#
from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC
from crcnetd._utils.ccsd_service import ccsd_service, ccs_service_error, \
        registerService
from crcnetd.modules.ccs_host import getHostID

ccs_mod_type = CCSD_SERVER

GROUP_PROPERTY = "amplet_group"

class amplet_error(ccs_service_error):
    pass

    
class amplet_service(ccsd_service):
    """Configures the amplet service on a host"""
    
    serviceName = "amplet"
    allowNewProperties = True
    networkService = True

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def createAmpletGroup(self, group_name, group_description):
        """Creates a new AMPlet Group"""
        session = getSessionE(self._session_id)

        session.execute("INSERT INTO amplet_groups (amplet_group_id, " \
                "group_name, group_description) VALUES (DEFAULT, %s, %s)", \
                    (group_name, group_description))
        return True

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def removeAmpletGroup(self, amplet_group_id):
        """Removes an AMPlet group area"""
        session = getSessionE(self._session_id)
        session.execute("DELETE FROM amplet_groups WHERE amplet_group_id=%s", \
                (amplet_group_id))
        return True

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True)
    def getAmpletGroups(self):
        """Returns details on the available OSPF areas"""
        session = getSessionE(self._session_id)

        return session.query("SELECT * FROM amplet_groups", ())
        
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getHostAmpletDetails")
    def getHostDetails(self, host_id):
        """Returns data relating to amplet"""
        session = getSessionE(self._session_id)

        service = ccsd_service.getHostDetails(self, host_id)

        return service
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True)
    def buildConnectedMesh(self):
        sql2 = "SELECT h.host_name, h.host_name || ':' || i.name as int_name, " \
        "i.ip_address from host h, " \
        "interface i join link l on l.link_id = i.link_id left join " \
        "customer_interface c on c.interface_id = i.interface_id right join " \
        "interface i2 on i2.link_id = l.link_id AND i2.host_id = %s where " \
        "h.host_id = i.host_id AND l.shared_network = 'f' AND c.customer_id " \
        "IS NULL AND l.link_id != 130"

        session = getSessionE(self._session_id)
        hosts = self.getEnabledHostList()
        namespace = {}
        for host in hosts:
            #print "@@@@@@@@%s@@@@@@@@" % host
            namespace[host] = []
            host_id = getHostID(self._session_id, host)
            res = session.query(sql2, host_id)
            for r in res:
                #print "%s %s" % (r['int_name'], r['ip_address'])
                namespace[host].append(r)

        return namespace


    def getNetworkTemplateVariables(self):
        """Returns a dictionary containing template variables for all hosts

        See the getTemplateVariables function for more details.
        """
        session = getSessionE(self._session_id)
        variables = {}
        name = self._service["service_name"]
        
        variables["service_name"] = name
        variables["%s_enabled" % name] = self.getState()
                
        # Include basic properties
        variables.update(self.getPropertyValues())
        
        # Include a list of hosts that the service is enabled on
        variables["direct_mesh"] = self.buildConnectedMesh()
        variables["hosts"] = self.getEnabledHostList()

        #Get list of central sites
        sql = "SELECT h.host_name from service_hostdata s, host h where " \
            "h.host_id = s.host_id AND service_id = %s AND service_prop_id = " \
            "(select service_prop_id from service_prop where prop_name = " \
            "'amplet_group') AND value = 'gtw'"
        variables['gtws'] = session.query(sql, (self.service_id))

        return variables
    
    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising amplet service")        
        try:

            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (amplet_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS server_id", ())

            session.execute("INSERT INTO service_prop (service_prop_id, " \
               "service_id, prop_name, prop_type, default_value, " \
               "required) VALUES (DEFAULT, %s, %s, 'string', 'Node', " \
               "'f')", (service_id, GROUP_PROPERTY))

            # Commit the changes
            session.commit()
            
            log_info("Created amplet service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise amplet database entries!", \
                    sys.exc_info())
            raise amplet_error("Failed to setup database tables!")

        return service_id

def ccs_init():
    registerService(amplet_service)
