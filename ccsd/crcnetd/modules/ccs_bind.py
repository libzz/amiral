# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# BIND Integration - Adds support for configuration of DNS zones
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
import os.path
import sys

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_config import config_get_required
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_service import ccsd_service, registerService, getServiceID
from crcnetd._utils.ccsd_server import exportViaXMLRPC

from crcnetd._utils.ccsd_ca import ccs_ca

from crcnetd.modules.ccs_link import ccs_link

ccs_mod_type = CCSD_SERVER

# The property name for the link to allocate DNS Server IPs from
DNS_SERVER_LINK_PROPERTY = "dns_server_link"

class ccs_bind_error(ccsd_error):
    pass

@catchEvent("serviceAdded")
@catchEvent("serviceRemoved")
def handleBindEvent(eventName, host_id, session_id, service_id):
    """Receives service callbacks to update the dns server table"""
    session = getSessionE(session_id)

    try:
        bindService = getServiceID(session_id, "bind")
    except ccs_bind_error:
        # BIND service not installed
        return False

    if int(service_id) != bindService:
        return False

    if eventName == "serviceAdded":
        session.execute("INSERT INTO dns_server (dns_server_id, " \
                "host_id, is_master) VALUES (DEFAULT, %s, 'f')", (host_id))
    elif eventName == "serviceRemoved":
        session.execute("DELETE FROM dns_server WHERE host_id=%s", (host_id))

    return True

class bind_service(ccsd_service):
    """Configures the bind service"""
    
    serviceName = "bind"
    allowNewProperties = True
    networkService = False

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def getDNSServer(self, host_id):
        """Returns details regarding the DNS server on the host"""
        session = getSessionE(self._session_id)

        res = session.query("SELECT * FROM dns_server WHERE host_id=%s", 
                (host_id))
        if len(res) != 1:
            raise ccs_bind_error("No DNS server on that host!")

        return filter_keys(res[0])

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def updateDNSServer(self, host_id, is_master, dns_ip_address):
        """Updates the details of the DNS service.

        Returns SUCCESS.
        """
        session = getSessionE(self._session_id)

        ################## Validate incoming data ##################
        if is_master=="t":
            is_master = "t"
        else:
            is_master = "f"
        if dns_ip_address == "":
            dns_ip_address="NULL"
        else:
            # Get the link that DNS Server IPs come from
            values = self.getPropertyValues()
            link_id = values[DNS_SERVER_LINK_PROPERTY]
            if link_id == -1:
                raise ccs_bnd_error("No link specified. Cannot set IP!")
            link = ccs_link(self._session_id, link_id)
            netblock = link["network_address"]
            # Check it's in a valid network
            if not inNetwork(ipnum(dns_ip_address), cidrToNetwork(netblock),
                    cidrToNetmask(netblock)):
                raise ccs_bind_error("Invalid DNS IP address")

        ################## Update the database ##################
        if dns_ip_address == "NULL":
            session.execute("UPDATE dns_server SET is_master=%s, " \
                    "dns_ip_address=NULL WHERE host_id=%s", 
                    (is_master, host_id))
        else:
            session.execute("UPDATE dns_server SET is_master=%s, " \
                    "dns_ip_address=%s WHERE host_id=%s", 
                    (is_master, dns_ip_address, host_id))
            
        ################## Clean Up and Return ##################
        return True

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def setBindLinkClassState(self, link_class_id, state):
        """Updates the DNS state for a link class"""
        session = getSessionE(self._session_id)

        if state:
            session.execute("INSERT INTO bind_link_class_reverse " \
                    "(link_class_id, no_rdns) VALUES (%s, %s)", 
                    (link_class_id, "t"))
        else:
            session.execute("DELETE FROM bind_link_class_reverse WHERE " \
                    "link_class_id=%s", (link_class_id))

        return True
    
    def getServers(self):
        """Returns a list of DNS servers and their associated information"""
        session = getSessionE(self._session_id)

        res = session.query("SELECT * FROM dns_server_info", ())
        servers = {}
        for row in res:
            servers[row["host_name"]] = filter_keys(row)
        return servers

    def getNetworkTemplateVariables(self):
        variables = ccsd_service.getNetworkTemplateVariables(self)
        variables["servers"] = self.getServers()
        return variables

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising BIND service")        
        try:
            # Read in schema and dump into database
            fp = open("%s/ccs_bind.schema" % \
                    config_get("ccsd", "service_data_dir", \
                    DEFAULT_SERVICE_DATA_DIR))
            schema = fp.readlines()
            fp.close()
            session.execute("\n".join(schema), ())

            # Create service table entry
            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (bind_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS service_id", ())

            # Setup the link property
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, required) " \
                "VALUES (DEFAULT, %s, %s, 'integer', -1, 't')", \
                (service_id, DNS_SERVER_LINK_PROPERTY))
                
            # Commit the changese
            session.commit()
            
            log_info("Created BIND service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise BIND database entries!", \
                    sys.exc_info())
            raise ccs_bind_error("Failed to setup BIND database tables!")

        return service_id

def ccs_init():
    registerService(bind_service)
