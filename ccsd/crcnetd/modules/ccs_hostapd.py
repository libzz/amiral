# Copyright (C) 2006  The University of Waikato
#
# HostAPD Service Module for the CRCnet Configuration System
# Configures hostapd to act as an authenticator on a host
#
# Author:       Matt Brown <matt@crc.net.nz>
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
        registerService

ccs_mod_type = CCSD_SERVER

class hostapd_error(ccs_service_error):
    pass

def hostapdInterfaceEnabled(session_id, interface_id):
    """Returns true if the hostapd service is enabled on the specified iface"""
    session = getSessionE(session_id)

    r = session.query("SELECT auth FROM hostapd_interface WHERE " \
            "interface_id=%s", (interface_id))
    if len(r) == 1:
        return int(r[0]["auth"])

    return 0

class hostapd_service(ccsd_service):
    """Configures the hostapd service on a host"""
    
    serviceName = "hostapd"
    allowNewProperties = True
    networkService = True

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    @registerEvent("hostapdInterfaceEnabled")
    @registerEvent("hostapdInterfaceDisabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def updateHostAPdInterface(self, host_id, interface_id, val):
        """Enables HostAPd on the specified interface"""
        session = getSessionE(self._session_id)
        if val == "0":
            session.execute("DELETE FROM hostapd_interface WHERE " \
                    "interface_id=%s", (interface_id))
            # Raise the event
            triggerHostEvent(self._session_id, "hostapdInterfaceDisabled", \
                    service_id=self.service_id, host_id=host_id, \
                    interface_id=interface_id)
        else:
            if hostapdInterfaceEnabled(self._session_id, interface_id):
                #raise hostapd_error("HostAPd already enabled on interface!")
                session.execute("UPDATE hostapd_interface SET auth=%s " \
                        "WHERE interface_id = %s", (val, interface_id))
            else:
            
                session.execute("INSERT INTO hostapd_interface (interface_id, auth) " \
                        "VALUES (%s, %s)", (interface_id, val))
            
            # Raise the event
            triggerHostEvent(self._session_id, "hostapdInterfaceEnabled", \
                    service_id=self.service_id, host_id=host_id, \
                    interface_id=interface_id)
        
        return True

    @registerEvent("hostapdInterfaceEnabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def enableHostAPdInterface(self, host_id, interface_id):
        """Enables HostAPd on the specified interface"""
        session = getSessionE(self._session_id)
        
        if hostapdInterfaceEnabled(self._session_id, interface_id):
            raise hostapd_error("HostAPd already enabled on interface!")
        
        session.execute("INSERT INTO hostapd_interface (interface_id) " \
                "VALUES (%s)", (interface_id))
        
        # Raise the event
        triggerHostEvent(self._session_id, "hostapdInterfaceEnabled", \
                service_id=self.service_id, host_id=host_id, \
                interface_id=interface_id)
        
        return True

    @registerEvent("hostapdInterfaceDisabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def disableHostAPdInterface(self, host_id, interface_id):
        """Disables HostAPd on the specified interface"""
        session = getSessionE(self._session_id)
        
        session.execute("DELETE FROM hostapd_interface WHERE " \
                "interface_id=%s", (interface_id))
        
        # Raise the event
        triggerHostEvent(self._session_id, "hostapdInterfaceDisabled", \
                service_id=self.service_id, host_id=host_id, \
                interface_id=interface_id)
        
        return True

    def getInterfaces(self, host_id):
        """Returns details about interface that have hostapd enabled on them"""
        session = getSessionE(self._session_id)

        return session.query("SELECT i.*, CASE WHEN hi.interface_id IS NULL " \
                "THEN 0 ELSE hi.auth END AS hostapd_enabled " \
                "FROM interface i LEFT JOIN hostapd_interface hi ON " \
                "i.interface_id=hi.interface_id WHERE i.host_id=%s AND " \
                "i.master_interface='t'", (host_id))

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getHostHostAPdDetails")
    def getHostDetails(self, host_id):
        """Returns data relating to HostAPd on a host"""
        session = getSessionE(self._session_id)

        service = ccsd_service.getHostDetails(self, host_id)
        service["interfaces"] = self.getInterfaces(host_id)

        return service

    def getPlans(self):
        session = getSessionE(self._session_id)

        plans = {}

        for row in session.query("SELECT * FROM radius_plan", ()):
            plans[row["plan_name"]] = row

        return plans

    def getNetworkTemplateVariables(self):
        """Returns a dictionary containing template variables for all hosts

        See the getTemplateVariables function for more details.
        """

        # Call base class to get the basics
        variables = ccsd_service.getNetworkTemplateVariables(self)

        # Make the function available to templates
        variables["interfaceEnabled"] = hostapdInterfaceEnabled

        # List of RADIUS plans
        variables["plans"] = self.getPlans()

        return variables

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising HostAPD service")        
        try:

            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (hostapd_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS server_id", ())
                
            # Commit the changese
            session.commit()
            
            log_info("Created hostapd service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise hostapd database entries!", \
                    sys.exc_info())
            raise hostapd_error("Failed to setup database tables!")

        return service_id

def ccs_init():
    registerService(hostapd_service)
