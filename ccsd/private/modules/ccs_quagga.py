# Copyright (C) 2006  The University of Waikato
#
# Quagga Service Module for the CRCnet Configuration System
# Configures quagga to handle routing on a host
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

from crcnetd.modules.ccs_link import validateLinkClassId, ccs_link

ccs_mod_type = CCSD_SERVER

TELNETPASS_PROPERTY = "telnet_password"
ENABLEPASS_PROPERTY = "enable_password"
RD_STATIC_PROPERTY = "redistribute_static"
RD_CONNECTED_PROPERTY = "redistribute_connected"
MD5_KEY_PROPERTY = "md5_key"

class quagga_error(ccs_service_error):
    pass

class quagga_service(ccsd_service):
    """Configures the quagga service on a host"""
    
    serviceName = "quagga"
    allowNewProperties = True
    networkService = False

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def createOSPFArea(self, area_no, link_class_id):
        """Creates a new OSPF area, possibly bound to a link class"""
        session = getSessionE(self._session_id)
        
        try:
            area_no = int(area_no)
            if area_no < 1:
                raise quagga_error("Invalid area number!")
        except:
            (type, value, tb) = sys.exc_info()
            raise quagga_error("Invalid area number! - %s" % value)
        try:
            link_class_id = int(link_class_id)
        except:
            link_class_id = -1
    
        if link_class_id != -1:
            log_warn("Link Class ID: %s" % link_class_id)
            validateLinkClassId(self._session_id, link_class_id)
            session.execute("INSERT INTO quagga_ospf_area (area_no, " \
                    "link_class_id) VALUES (%s,%s)", (area_no, link_class_id))
        else:
            session.execute("INSERT INTO quagga_ospf_area (area_no) " \
                    "VALUES (%s)", (area_no))

        return 0

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def removeOSPFArea(self, area_no):
        """Removes an OSPF area"""
        session = getSessionE(self._session_id)

        try:
            area_no = int(area_no)
            if area_no < 1:
                raise quagga_error("Invalid area number!")
        except:
            raise quagga_error("Invalid area number!")

        session.execute("DELETE FROM quagga_ospf_area WHERE area_no=%s", \
                (area_no))

        return 0
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getQuaggaOSPFAreas")
    def getOSPFAreas(self):
        """Returns details on the available OSPF areas"""
        session = getSessionE(self._session_id)

        return session.query("SELECT a.*, lc.description AS link_class_desc " \
                "FROM quagga_ospf_area a LEFT JOIN link_class lc ON " \
                "a.link_class_id=lc.link_class_id", ())
    
    @staticmethod
    @catchEvent("serviceRemoved")
    def removeQuaggaService(eventName, session_id, host_id, **kwargs):
        """Watches events to detect when quagga has been removed from a host.
        
        When a removal is detected the quagga configuration for the host is
        cleared.
        """
        from crcnetd.modules.ccs_host import ccs_host
        
        # Bail out if the quagga service isn't configured yet
        if quagga_service.service_id == -1:
            return
        
        # Bail out if this isn't the quagga service being added
        if "service_id" not in kwargs.keys():
            return
        if kwargs["service_id"] != quagga_service.service_id:
            return
        
        session = getSessionE(session_id)
        
        # Clean up
        session.execute("DELETE FROM quagga_ospf_interface WHERE " \
                "host_id=%s", (host_id))

    @staticmethod
    @catchEvent("serviceAdded")
    def setupQuaggaService(eventName, session_id, host_id, **kwargs):
        """Watches events to detect when quagga has been added to a host.
        
        When a successful addition is detected the quagga configuration for the
        host is initialised.
        """
        from crcnetd.modules.ccs_host import ccs_host
        
        # Bail out if the quagga service isn't configured yet
        if quagga_service.service_id == -1:
            return
        
        # Bail out if this isn't the quagga service being added
        if "service_id" not in kwargs.keys():
            return
        if kwargs["service_id"] != quagga_service.service_id:
            return

        session = getSessionE(session_id)
        
        # Quagga service is being added, get a host instance
        host = ccs_host(session_id, host_id)

        # Enable OSPF on interfaces that have an area defined for their
        # link class.
        ifaces = host.getInterfaces()
        for idx,iface in ifaces.items():
            if not iface["interface_active"]:
                continue
            area_no = quagga_service.getLinkArea(session_id, iface["link_id"])
            if area_no == -1:
                continue
            sql = "INSERT INTO quagga_ospf_interface (host_id, " \
                    "interface_id, area_no, md5_auth) VALUES (%s, " \
                    "%s, %s, DEFAULT)"
            session.execute(sql, (host_id, iface["interface_id"], area_no))

    @staticmethod
    def getLinkArea(session_id, link_id):
        """Determines which OSPF area the link should fall into by default"""
        session = getSessionE(session_id)

        link = ccs_link(session_id, link_id)
        res = session.query("SELECT area_no FROM quagga_ospf_area WHERE " \
                "link_class_id=%s ORDER BY area_no LIMIT 1", \
                (link["class_id"]))
        if len(res) == 0:
            return -1

        return res[0]["area_no"]

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getHostQuaggaDetails")
    def getHostDetails(self, host_id):
        """Returns data relating to quagga on a host"""
        session = getSessionE(self._session_id)

        service = ccsd_service.getHostDetails(self, host_id)
        service["interfaces"] = self.getOSPFInterfaces(host_id)
        service["statics"] = self.getStaticRoutes(host_id)

        return service

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getQuaggaOSPFInterfaces")
    def getOSPFInterfaces(self, host_id):
        """Returns details on active OSPF interfaces for the host"""
        session = getSessionE(self._session_id)

        return session.query("SELECT i.*, CASE WHEN qi.interface_id IS NULL " \
                "THEN FALSE ELSE TRUE END AS ospf_enabled, qi.area_no, " \
                "qi.priority, qi.md5_auth, qi.md5_key FROM interface i " \
                "LEFT JOIN quagga_ospf_interface qi ON i.interface_id=" \
                "qi.interface_id WHERE i.host_id=%s", (host_id))
        
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getQuaggaStaticRoutes")
    def getStaticRoutes(self, host_id):
        """Returns details on static routes configured for the host"""
        session = getSessionE(self._session_id)

        return session.query("SELECT * FROM quagga_statics " \
                "WHERE host_id=%s ORDER BY prefix", (host_id))
        
    def getHostTemplateVariables(self, host_id):
        """Returns a dictionary containing template variables for a host

        See the getTemplateVariables function for more details.
        """
        md5_key = ""

        # Call base class to get the basics
        variables = ccsd_service.getHostTemplateVariables(self, host_id)

        # Network wide md5 key value
        try:
            md5_key = variables[MD5_KEY_PROPERTY]
        except KeyError:
            md5_key = ""

        # Include interface configurations
        interfaces = {}
        areas = []
        for iface in self.getOSPFInterfaces(host_id):
            interfaces[iface["name"]] = iface    
            if iface["md5_key"] is None or iface["md5_key"] == "":
                interfaces[iface["name"]]["md5_key"] = md5_key
            if iface["ospf_enabled"] and iface["area_no"] == "":
                iface["area_no"] = 0
            areas.append(iface["area_no"])
        variables["interfaces"] = interfaces

        # Choose a "default" area for this host, which is the lowest numbered
        # area that the host has an interface in, or 0 if the host has no 
        # interfaces explicitly in an OSPF area
        areas.sort()
        if len(areas) > 0:
            variables["area_no"] = areas[0]
        else:
            variables["area_no"] = 0

        # Include static routes
        statics = {}
        for static in self.getStaticRoutes(host_id):
            statics[static["prefix"]] = filter_keys(static)
        variables["statics"] = statics

        return variables
    
    @registerEvent("quaggaStaticCreated")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, \
            "quaggaCreateStatic")
    def createStatic(self, details):
        """Creates a static route on the specified host"""
        session = getSessionE(self._session_id)
        
        # Validate
        props = [ "host_id", "description", "prefix", "next_hop", "metric" ]
        for prop in props:
            if prop!="metric" and not prop in details.keys():
                raise ccs_quagga_error("Missing required property '%s'!" % \
                        prop)
            if prop in details.keys():
                validateStaticProp(self._session_id, prop, details[prop])

        # Build the SQL
        (sql, values) = buildInsertFromDict("quagga_statics", props, details)
        session.execute(sql, values)
        
        # Get the ID
        static_id = session.getCountOf("SELECT currval('" \
                    "quagga_statics_static_id_seq') AS static_id", ())
        
        # Raise the event
        triggerEvent(self._session_id, "quaggaStaticCreated", \
                service_id=self.service_id, host_id=details["host_id"], \
                static_id=static_id)
        
        return static_id
    
    @registerEvent("quaggaStaticRemoved")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, \
            "quaggaRemoveStatic")
    def removeStatic(self, static_id):
        """Creates a static route on the specified host"""
        session = getSessionE(self._session_id)
        
        # Build the SQL
        sql = "DELETE FROM quagga_statics WHERE static_id=%s"
        session.execute(sql, (static_id))
        
        # Raise the event
        triggerEvent(self._session_id, "quaggaStaticRemoved", \
                service_id=self.service_id, static_id=static_id)
        
        return self.returnSuccess()
    
    @registerEvent("quaggaStaticUpdated")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, \
            "quaggaUpdateStatic")
    def updateStatic(self, static_id, propName, propValue):
        """Updates the details of the static route.

        Returns SUCCESS.
        """
        session = getSessionE(self._session_id)
        
        ################## Validate incoming data ##################

        if propName not in ["description", "next_hop", "metric", "prefix"]:
            raise ccs_service_error("Unknown service property!")
        validateStaticProp(self._session_id, propName, propValue)
        
        ################## Update the database ##################
        
        propNull=False
        if propName in ["metric"]:
            if propValue == "":
                propNull=True
                
        if not propNull:
            sql = "UPDATE quagga_statics SET %s=%%s WHERE " \
                    "static_id=%%s" % propName
            session.execute(sql, (propValue, static_id))
        else:
            sql = "UPDATE quagga_ospf_interface SET %s=NULL WHERE " \
                    "static_id=%%s" % propName
            session.execute(sql, (static_id))

        # Raise the event
        triggerEvent(self._session_id, "quaggaStaticUpdated", \
                service_id=self.service_id,
                static_id=static_id, propName=propName)
            
        ################## Clean Up and Return ##################
        return self.returnSuccess()
        
    @registerEvent("ospfInterfaceEnabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def enableOSPFInterface(self, host_id, interface_id):
        """Enables OSPF on the specified interface"""
        session = getSessionE(self._session_id)
        
        n = session.getCountOf("SELECT count(*) FROM quagga_ospf_interface " \
                "WHERE host_id=%s and interface_id=%s", \
                (host_id, interface_id))
        if n != 0:
            raise ccs_quagga_error("OSPF already enabled on interface!")
        
        session.execute("INSERT INTO quagga_ospf_interface (host_id, " \
                "interface_id) VALUES (%s, %s)", (host_id, interface_id))
        
        # Raise the event
        triggerHostEvent(self._session_id, "ospfInterfaceEnabled", \
                service_id=self.service_id, host_id=host_id, \
                interface_id=interface_id)
        
        return True
    
    @registerEvent("ospfInterfaceDisabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def disableOSPFInterface(self, host_id, interface_id):
        """Disables OSPF on the specified interface"""
        session = getSessionE(self._session_id)
        
        session.execute("DELETE FROM quagga_ospf_interface WHERE host_id=%s " \
                "AND interface_id=%s", (host_id, interface_id))
        
        # Raise the event
        triggerHostEvent(self._session_id, "ospfInterfaceDisabled", \
                service_id=self.service_id, host_id=host_id, \
                interface_id=interface_id)
        
        return True
    
    @registerEvent("ospfInterfaceUpdated")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def updateOSPFInterface(self, host_id, interface_id, propName, propValue):
        """Updates the details of the service.

        Returns SUCCESS.
        """
        session = getSessionE(self._session_id)
        
        ################## Validate incoming data ##################

        if propName not in ["area_no", "priority", "md5_auth", "md5_key"]:
            raise ccs_service_error("Unknown service property!")
        validateOSPFIfaceProp(self._session_id, propName, propValue)

        n = session.getCountOf("SELECT count(*) FROM quagga_ospf_interface " \
                "WHERE host_id=%s and interface_id=%s", \
                (host_id, interface_id))
        if n != 1:
            raise ccs_quagga_error("OSPF not enabled on interface!")
        
        ################## Update the database ##################
        
        propNull=False
        if propName in ["md5_auth", "md5_key"]:
            if propValue == "":
                propNull=True
        else:
            try:
                propValue = int(propValue)
                if propValue == -1:
                    propNull=True
            except ValueError:
                propNull=True
                
        if not propNull:
            sql = "UPDATE quagga_ospf_interface SET %s=%%s WHERE " \
                    "host_id=%%s AND interface_id=%%s" % propName
            session.execute(sql, (propValue, host_id, interface_id))
        else:
            sql = "UPDATE quagga_ospf_interface SET %s=NULL WHERE " \
                    "host_id=%%s AND interface_id=%%s" % propName
            session.execute(sql, (host_id, interface_id))

        # Raise the event
        triggerHostEvent(self._session_id, "ospfInterfaceUpdated", \
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
        session.begin("initialising Quagga service")        
        try:

            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (quagga_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS server_id", ())

            # Read in schema and dump into database
            fp = open("%s/quagga.schema" % \
                    config_get("ccsd", "service_data_dir", \
                    DEFAULT_SERVICE_DATA_DIR))
            schema = fp.readlines()
            fp.close()
            session.execute("\n".join(schema), ())
            
            # Setup Properties
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'string', %s, 't')", \
                (service_id, TELNETPASS_PROPERTY, ""))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'string', %s, 't')", \
                (service_id, ENABLEPASS_PROPERTY, ""))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'boolean', %s, 't')", \
                (service_id, RD_STATIC_PROPERTY, "t"))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'boolean', %s, 't')", \
                (service_id, RD_CONNECTED_PROPERTY, "f"))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, required) VALUES " \
                "(DEFAULT, %s, %s, 'string', 'f')", \
                (service_id, MD5_KEY_PROPERTY))

            # Commit the changese
            session.commit()
            
            log_info("Created quagga service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise quagga database entries!", \
                    sys.exc_info())
            raise quagga_error("Failed to setup database tables!")

        return service_id
    
def validateStaticProp(session_id, propName, propValue):
    """Checks the value of the specified static route property is OK"""

    if propName == "description":
        if propValue == "":
            raise ccs_quagga_error("Description must not be blank!")
        else:
            return

    if propName == "prefix":
        validateCIDR(propValue)
        return

    if propName == "next_hop":
        try:
            n=ipnum(propValue)
            if n>0:
                return
            else:
                raise ccs_quagga_error("Invalid next hop value!")
        except:
            raise ccs_quagga_error("Invalid next hop value!")

    if propName == "metric":
        try:
            n=int(propValue)
            if n > 0 and n < 65536:
                return
            else:
                raise ccs_quagga_error("Invalid route metric!")
        except:
            raise ccs_quagga_error("Invalid route metric!")

    return
    
def validateOSPFIfaceProp(session_id, propName, propValue):
    """Checks that the value of the specified OSPF interface property is OK"""

    if propName == "md5_auth":
        if propValue != "t" and propValue != "f":
            raise ccs_quagga_error("MD5 Auth must be 't' or 'f'")
        else:
            return
    
    if propValue == "":
        return
    
    try:
        if propName == "area_no" or propName == "priority":
            a = int(propValue)
    except ValueError:
        raise ccs_quagga_error("%s must be an integer!" % propName)

    return

def ccs_init():
    registerService(quagga_service)
