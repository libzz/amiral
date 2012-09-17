# Copyright (C) 2006  The University of Waikato
#
# DHCP Service Module for the CRCnet Configuration System
# Configures a DHCP server to handle DHCP address assignment on a host
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

from crcnetd.modules.ccs_link import validateLinkClassId, ccs_link, \
        getInterfaceLink

ccs_mod_type = CCSD_SERVER

NS1_PROPERTY = "ns1"
NS2_PROPERTY = "ns2"
DOMAIN_PROPERTY = "domain"
DEFAULT_LEASE_TIME_PROPERTY = "default_lease_time"
MAX_LEASE_TIME_PROPERTY = "max_lease_time"

DEFAULT_LEASE_TIME = 600
MAX_LEASE_TIME = 7200

class dhcp_error(ccs_service_error):
    pass

class dhcp_service(ccsd_service):
    """Configures the dhcp service on a host"""
    
    serviceName = "dhcp"
    allowNewProperties = True
    networkService = False

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    @staticmethod
    @catchEvent("serviceRemoved")
    def removeDHCPService(eventName, session_id, host_id, **kwargs):
        """Watches events to detect when dhcp has been removed from a host.
        
        When a removal is detected the dhcp configuration for the host is
        cleared.
        """
        from crcnetd.modules.ccs_host import ccs_host
        
        # Bail out if the dhcp service isn't configured yet
        if dhcp_service.service_id == -1:
            return
        
        # Bail out if this isn't the dhcp service being added
        if "service_id" not in kwargs.keys():
            return
        if kwargs["service_id"] != dhcp_service.service_id:
            return
        
        session = getSessionE(session_id)
        
        # Clean up
        session.execute("DELETE FROM dhcp_interface WHERE host_id=%s", \
                (host_id))
        session.execute("DELETE FROM dhcp_statics WHERE host_id=%s", \
                (host_id))

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getHostDHCPDetails")
    def getHostDetails(self, host_id):
        """Returns data relating to dhcp on a host"""
        session = getSessionE(self._session_id)

        service = ccsd_service.getHostDetails(self, host_id)
        service["interfaces"] = self.getInterfaces(host_id)
        service["statics"] = self.getStatics(host_id)

        return service

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getDHCPInterfaces")
    def getInterfaces(self, host_id):
        """Returns details on active DHCP interfaces for the host"""
        session = getSessionE(self._session_id)

        return session.query("SELECT i.*, CASE WHEN di.interface_id IS NULL " \
                "THEN FALSE ELSE TRUE END AS dhcp_enabled, " \
                "substring(di.pool_min::text from '[.0-9]*') AS pool_min, " \
                "substring(di.pool_max::text from '[.0-9]*') AS pool_max," \
                "substring(di.router_ip::text from '[.0-9]*') AS router_ip " \
                "FROM interface i LEFT JOIN dhcp_interface di " \
                "ON i.interface_id=di.interface_id WHERE i.host_id=%s", \
                (host_id))
        
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getDHCPStatics")
    def getStatics(self, host_id):
        """Returns details on staticly managed IPs configured for the host"""
        session = getSessionE(self._session_id)

        return session.query("SELECT * FROM dhcp_statics " \
                "WHERE host_id=%s", (host_id))
        
    def getHostTemplateVariables(self, host_id):
        """Returns a dictionary containing template variables for a host

        See the getTemplateVariables function for more details.
        """

        # Call base class to get the basics
        variables = ccsd_service.getHostTemplateVariables(self, host_id)

        # Include interface configurations
        interfaces = {}
        for iface in self.getInterfaces(host_id):
            interfaces[iface["name"]] = iface    
        variables["interfaces"] = interfaces
        # XXX: Statics
        
        return variables
        
    @registerEvent("dhcpInterfaceEnabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def enableDHCPInterface(self, host_id, interface_id):
        """Enables DHCP on the specified interface"""
        session = getSessionE(self._session_id)
        
        n = session.getCountOf("SELECT count(*) FROM dhcp_interface " \
                "WHERE host_id=%s and interface_id=%s", \
                (host_id, interface_id))
        if n != 0:
            raise dhcp_error("DHCP already enabled on interface!")
        
        link = getInterfaceLink(self._session_id, interface_id)
        length = cidrToLength(link["network_address"])
        if length == 24:
            # Try and setup a default pool from 129 -> 253
            pool_max = link._maxIP(True)
            pool_min = link._minIP(True, 128)
        else:
            # Try and setup a default pool using the whole range
            pool_max = link._maxIP(True)
            pool_min = link._minIP(True)
        # Check all IPs in the pool are free
        ip = ipnum(pool_min)
        while ip < ipnum(pool_max):
            # Increment the bottom of the pool if an in Use IP is found
            if link._ipInUse(ip):
                pool_min=formatIP(ip+1)
            # Move through the pool
            ip+=1
        # Check the ppol still has some size
        if ipnum(pool_min) >= ipnum(pool_max):
            raise dhcp_error("Unable to allocate a DHCP pool on the link!")
        
        session.execute("INSERT INTO dhcp_interface (host_id, " \
                "interface_id, pool_min, pool_max) VALUES (%s, %s, %s, %s)", \
                (host_id, interface_id, pool_min, pool_max))
        
        # Raise the event
        triggerHostEvent(self._session_id, "dhcpInterfaceEnabled", \
                service_id=self.service_id, host_id=host_id, \
                interface_id=interface_id)
        
        return True
    
    @registerEvent("dhcpInterfaceDisabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def disableDHCPInterface(self, host_id, interface_id):
        """Disables DHCP on the specified interface"""
        session = getSessionE(self._session_id)
        
        session.execute("DELETE FROM dhcp_interface WHERE host_id=%s " \
                "AND interface_id=%s", (host_id, interface_id))
        
        # Raise the event
        triggerHostEvent(self._session_id, "dhcpInterfaceDisabled", \
                service_id=self.service_id, host_id=host_id, \
                interface_id=interface_id)
        
        return True
    
    @registerEvent("dhcpInterfaceUpdated")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def updateDHCPInterface(self, host_id, interface_id, propName, propValue):
        """Updates the details of the service.

        Returns SUCCESS.
        """
        session = getSessionE(self._session_id)
        propNull = False
        deferName = ""
        deferValue = ""
        
        ################## Validate incoming data ##################

        res = session.query("SELECT substring(pool_min::text from " \
                "'[.0-9]*') AS pool_min, substring(pool_max::text " \
                "from '[.0-9]*') AS pool_max FROM dhcp_interface WHERE " \
                "host_id=%s and interface_id=%s", (host_id, interface_id))
        if len(res) != 1:
            raise dhcp_error("DHCP not enabled on interface!")
        
        link = getInterfaceLink(self._session_id, interface_id)
        if propName == "pool_min":
            if not link.isValidIP(propValue):
                raise dhcp_error("Invalid minimum pool IP! Not in link.")
            mvalid = link.isValidIP(res[0]["pool_max"])
            if ipnum(res[0]["pool_max"]) <= ipnum(propValue) or not mvalid:
                if mvalid:
                    deferValue = "%s/32" % propValue
                    deferName = "pool_max"
                    propValue = res[0]["pool_max"]
                else:
                    deferValue = "%s/32" % link._maxIP(True)
                    deferName = "pool_max"
            propValue = "%s/32" % propValue
        elif propName == "pool_max":
            if not link.isValidIP(propValue):
                raise dhcp_error("Invalid maximum pool IP! Not in link.")
            mvalid = link.isValidIP(res[0]["pool_min"])
            if ipnum(res[0]["pool_min"]) >= ipnum(propValue) or not mvalid:
                if mvalid:
                    deferValue = "%s/32" % propValue
                    deferName = "pool_min"
                    propValue = res[0]["pool_min"]
                else:
                    deferValue = "%s/32" % link._minIP(True, 128)
                    deferName = "pool_min"
            propValue = "%s/32" % propValue
        elif propName == "router_ip":
            if propValue == "":
                propNull = True
            else:
                if not link.isValidIP(propValue):
                    raise dhcp_error("Invalid router IP! Not in link.")
                propValue = "%s/32" % propValue
        else:
            raise dhcp_error("Invalid property name!")
        
        ################## Update the database ##################
        
        if not propNull:
            sql = "UPDATE dhcp_interface SET %s=%%s WHERE " \
                    "host_id=%%s AND interface_id=%%s" % propName
            session.execute(sql, (propValue, host_id, interface_id))
        else:
            sql = "UPDATE dhcp_interface SET %s=NULL WHERE " \
                    "host_id=%%s AND interface_id=%%s" % propName
            session.execute(sql, (host_id, interface_id))
        if deferName != "":
            sql = "UPDATE dhcp_interface SET %s=%%s WHERE " \
                    "host_id=%%s AND interface_id=%%s" % deferName
            session.execute(sql, (deferValue, host_id, interface_id))

        # Raise the event
        triggerHostEvent(self._session_id, "dhcpInterfaceUpdated", \
                service_id=self.service_id, host_id=host_id, \
                interface_id=interface_id, propName=propName)
            
        ################## Clean Up and Return ##################
        return self.returnSuccess()

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising DHCP service")
        try:

            # Read in schema and dump into database
            try:
                fp = open("%s/dhcp.schema" % \
                        config_get("ccsd", "service_data_dir", \
                        DEFAULT_SERVICE_DATA_DIR))
                schema = fp.readlines()
                fp.close()
                session.execute("\n".join(schema), ())
            except ccs_service_error:
                # Assume tables are already existing... try and proceed 
                # executes below will error if this assumption is false
                log_warn("Unable to create database tables!", sys.exc_info())

            # Create the service entry
            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (dhcp_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS service_id", ())
                
            # Get the domain
            domain = config_get("network", "domain")
            if domain != None and domain != "":
                domain = ".%s" % domain
                required = "f"
            else:
                required = "t"
                
            # Setup Properties
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'string', %s, %s)", \
                (service_id, NS1_PROPERTY, "ns1%s" % domain, required))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'string', %s, %s)", \
                (service_id, NS2_PROPERTY, "ns2%s" % domain, required))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'string', %s, %s)", \
                (service_id, DOMAIN_PROPERTY, domain[1:], required))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'integer', %s, 'f')", \
                (service_id, DEFAULT_LEASE_TIME_PROPERTY, DEFAULT_LEASE_TIME))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'integer', %s, 'f')", \
                (service_id, MAX_LEASE_TIME_PROPERTY, MAX_LEASE_TIME)) 

            # Commit the changese
            session.commit()
            
            log_info("Created dhcp service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise dhcp database entries!", \
                    sys.exc_info())
            raise dhcp_error("Failed to setup database tables!")

        return service_id

def ccs_init():
    registerService(dhcp_service)
