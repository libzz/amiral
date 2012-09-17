# Copyright (C) 2006  The University of Waikato
#
# Rlac Service Module for the CRCnet Configuration System
# Configures rlac to act as an authenticator on a host
#
# Author:       Chris Browning <chris@rurallink.co.nz>
# Version:      $Id: ccs_rlac.py 1623 2007-11-12 20:41:12Z ckb6 $
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

class rlac_error(ccs_service_error):
    pass

def rlacInterfaceEnabled(session_id, interface_id):
    """Returns true if the rlac service is enabled on the specified iface"""
    session = getSessionE(session_id)

    r = session.getCountOf("SELECT count(*) FROM rlac_interface WHERE " \
            "interface_id=%s", (interface_id))
    if r == 1:
        return True

    return False
    
def rlacHostEnabled(session_id, interface_id):
    """Returns true if the rlac service is enabled on the specified iface"""
    session = getSessionE(session_id)

    r = session.getCountOf("SELECT count(*) FROM rlac_interface WHERE " \
            "interface_id=%s", (interface_id))
    if r == 1:
        return True

    return False

class rlac_service(ccsd_service):
    """Configures the rlac service on a host"""
    
    serviceName = "rlac"
    allowNewProperties = True
    networkService = False

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    @registerEvent("rlacInterfaceEnabled")
    @registerEvent("rlacInterfaceDisabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def updateRlacInterface(self, host_id, interface_id, val):
        """Enables Rlac on the specified interface"""
        session = getSessionE(self._session_id)
        if val == "0":
            session.execute("DELETE FROM rlac_interface WHERE " \
                    "interface_id=%s", (interface_id))
            # Raise the event
            triggerHostEvent(self._session_id, "rlacInterfaceDisabled", \
                    service_id=self.service_id, host_id=host_id, \
                    interface_id=interface_id)
        else:
            if rlacInterfaceEnabled(self._session_id, interface_id):
                raise rlac_error("Rlac already enabled on interface!")
            else:
            
                session.execute("INSERT INTO rlac_interface (interface_id) " \
                        "VALUES (%s)", (interface_id))
            
            # Raise the event
            triggerHostEvent(self._session_id, "rlacInterfaceEnabled", \
                    service_id=self.service_id, host_id=host_id, \
                    interface_id=interface_id)
        
        return True

    @registerEvent("rlacInterfaceEnabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def enableRlacInterface(self, host_id, interface_id):
        """Enables Rlac on the specified interface"""
        session = getSessionE(self._session_id)
        
        if rlacInterfaceEnabled(self._session_id, interface_id):
            raise rlac_error("Rlac already enabled on interface!")
        
        session.execute("INSERT INTO rlac_interface (interface_id) " \
                "VALUES (%s,%s)", (interface_id))
        
        # Raise the event
        triggerHostEvent(self._session_id, "rlacInterfaceEnabled", \
                service_id=self.service_id, host_id=host_id, \
                interface_id=interface_id)
        
        return True

    @registerEvent("rlacInterfaceDisabled")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def disableRlacInterface(self, host_id, interface_id):
        """Disables Rlac on the specified interface"""
        session = getSessionE(self._session_id)
        
        session.execute("DELETE FROM rlac_interface WHERE " \
                "interface_id=%s", (interface_id))
        
        # Raise the event
        triggerHostEvent(self._session_id, "rlacInterfaceDisabled", \
                service_id=self.service_id, host_id=host_id, \
                interface_id=interface_id)
        
        return True

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def getLNSs(self):
        """Returns a list of LNS's that Rlac can talk to"""

        session = getSessionE(self._session_id)

        return session.query("SELECT * from rlac_lns", ())
        
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def getHostLNS(self, host_id):
        """Returns the LNS the host is configured to talk to"""

        session = getSessionE(self._session_id)

        return session.query("SELECT * from rlac_host WHERE host_id=%s", (host_id))

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def updateRlacHost(self, host_id, lns_id):
        """Updates Rlac on the specified host"""
        session = getSessionE(self._session_id)
        if lns_id == "0":
            session.execute("DELETE FROM rlac_host WHERE " \
                    "host_id=%s", (host_id))
        else:
            r = session.getCountOf("SELECT count(*) FROM rlac_host WHERE " \
                    "host_id=%s", (host_id))
            if r == 1:
                session.execute("UPDATE rlac_host SET lns_id=%s " \
                        "WHERE host_id = %s", (lns_id, host_id))
            else:
            
                session.execute("INSERT INTO rlac_host (host_id, lns_id) " \
                        "VALUES (%s, %s)", (host_id, lns_id))
            
        return True

    def getInterfaces(self, host_id):
        """Returns details about interface that have rlac enabled on them"""
        session = getSessionE(self._session_id)

        return session.query("SELECT i.*, CASE WHEN hi.interface_id IS NULL " \
                "THEN 0 ELSE 1 END AS rlac_enabled " \
                "FROM interface i LEFT JOIN rlac_interface hi ON " \
                "i.interface_id=hi.interface_id WHERE i.host_id=%s", (host_id))

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getHostRlacDetails")
    def getHostDetails(self, host_id):
        """Returns data relating to Rlac on a host"""
        session = getSessionE(self._session_id)

        service = ccsd_service.getHostDetails(self, host_id)
        service["interfaces"] = self.getInterfaces(host_id)
        
        #XXX FIXME
        service["network_default"] = 1
        service["lns"] = session.query("SELECT * FROM rlac_host WHERE host_id=%s", (host_id))

        return service

    def getHostTemplateVariables(self, host_id):
        """Returns a dictionary containing template variables for all hosts

        See the getTemplateVariables function for more details.
        """
        session = getSessionE(self._session_id)
        # Call base class to get the basics
        variables = ccsd_service.getHostTemplateVariables(self, host_id)

        # Make the function available to templates
        variables["rlacInterfaceEnabled"] = rlacInterfaceEnabled

        lns = session.query("SELECT ip_address FROM rlac_host JOIN rlac_lns USING (lns_id) WHERE host_id=%s", (host_id))

        if len(lns) == 0:
            lns = session.query("SELECT ip_address FROM rlac_lns WHERE lns_id=%s", (1))
        variables["lns"] = lns[0]

        return variables

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising Rlac service")        
        try:

            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (rlac_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS server_id", ())
                
            # Commit the changese
            session.commit()
            
            log_info("Created rlac service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise rlac database entries!", \
                    sys.exc_info())
            raise rlac_error("Failed to setup database tables!")

        return service_id

def ccs_init():
    registerService(rlac_service)
