# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Free Radius Integration - Adds support for configuration Free Radius to crcnetd
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
from crcnetd._utils.ccsd_service import ccsd_service, registerService, \
        getServiceID, ccs_service_error, getServiceInstance
from crcnetd._utils.ccsd_ca import ccs_ca

ccs_mod_type = CCSD_SERVER

class ccs_radius_error(ccsd_error):
    pass

AUTHIP_PROPERTY = "auth_ip"
ACCTIP_PROPERTY = "acct_ip"
AUTHPORT_PROPERTY = "auth_port"
ACCTPORT_PROPERTY = "acct_port"

@catchEvent("serviceAdded")
@catchEvent("serviceRemoved")
def handleHostApEvent(eventName, host_id, session_id, service_id):
    """Receives service callbacks to update the radius client table"""
    session = getSessionE(session_id)
    hostapService = -1
    ethernetService = -1

    # Ignore events that don't relate to the hostap or ethernet customer
    # services
    try:
        hostapService = getServiceID(session_id, "hostapd")
    except ccs_service_error:
        # Hostapd service not installed
        pass
    try:
        ethernetService = getServiceID(session_id, "ethernet_customer")
    except ccs_service_error:
        # Ethernet customer service not installed
        pass

    if int(service_id) not in [hostapService, ethernetService]:
        return

    if eventName == "serviceAdded":
        # Create a RADIUS client record for this host
        session.execute("INSERT INTO radius_client (host_id, secret) " \
                "VALUES (%s, %s)", (host_id, createPassword(16)))
    elif eventName == "serviceRemoved":
        # Remove the RADIUS client record for this host
        # XXX: Don't remove, the other service might still want it
        #session.execute("DELETE FROM radius_client WHERE host_id=%s", 
        #        (host_id))
        pass
    else:
        # Invalid event
        pass

@catchEvent("revisionPrepared")
def handleRevisionEvent(eventName, host_id, session_id, outputDir):
    """Receives callbacks to add extra information to the config revisions"""

    # Get a list of hosts running the RADIUS service
    radius = getServiceInstance(session_id, radius_service.serviceName)
    hosts = radius.getHostList()

    ca = ccs_ca()

    # Loop through each host and ensure that the certs/ directory is populated
    for host in hosts:
        try:
            # Check basic path existance
            hostdir = "%s/hosts/%s" % (outputDir, host)
            if not os.path.isdir(hostdir):
                # Host does not exist in the revision
                continue
            radiusdir = "%s/radius" % (hostdir)
            if not os.path.isdir(radiusdir):
                log_warn("Host '%s' does not have RADIUS templates!" % host)
                continue
            # Now check for the certs directory and the certificates
            certsdir = "%s/certs" % (radiusdir)
            ensureDirExists(certsdir)
            if not os.path.exists("%s/cacert.pem" % certsdir):
                cacert = ca.getFile("ca/cacert.pem")
                cacerts = ca.getFile("ca/cacerts.pem")
                fp = open("%s/cacert.pem" % certsdir, "w")
                fp.write(cacert)
                fp.write(cacerts)
                fp.close()
            if not os.path.exists("%s/dh" % certsdir):
                fp = open("%s/dh" % certsdir, "w")
                fp.close()
            if not os.path.exists("%s/random" % certsdir):
                log_command("openssl rand -out %s/random 1024" % certsdir)
            if not os.path.exists("%s/radius-key.pem" % certsdir):
                key = ca.getFile("ca/radius-key.pem")
                fp = open("%s/radius-key.pem" % certsdir, "w")
                fp.write(key)
                fp.close()
            if not os.path.exists("%s/radius-cert.pem" % certsdir):
                cert = ca.getFile("ca/radius-cert.pem")
                fp = open("%s/radius-cert.pem" % certsdir, "w")
                fp.write(cert)
                fp.close()
        except:
            log_error("Could not setup RADIUS certificates for %s" % host, \
                    sys.exc_info())

class radius_service(ccsd_service):
    """Configures the radius service"""
    
    serviceName = "radius"
    allowNewProperties = True
    networkService = False

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    def getClients(self):
        """Returns a list of RADIUS clients and their associated information"""
        session = getSessionE(self._session_id)

        res = session.query("SELECT * FROM radius_client_info", ())
        clients = {}
        for row in res:
            clients[row["host_name"]] = filter_keys(row)
        return clients

    def getNetworkTemplateVariables(self):
        variables = ccsd_service.getNetworkTemplateVariables(self)
        variables["clients"] = self.getClients()
        return variables

    def getHostTemplateVariables(self, host_id):
        """Returns a dictionary containing template variables for a host

        See the getTemplateVariables function for more details.
        """

        # Call base class to get the basics
        variables = ccsd_service.getHostTemplateVariables(self, host_id)
        return variables

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising RADIUS service")        
        try:

            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (radius_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS server_id", ())
            default_ip = getIP(config_get_required("network", "server_name"))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'string', %s, 'f')", \
                (service_id, AUTHIP_PROPERTY, default_ip))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'string', %s, 'f')", \
                (service_id, ACCTIP_PROPERTY, default_ip))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'integer', %s, 'f')", \
                (service_id, AUTHPORT_PROPERTY, 1812))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'integer', %s, 'f')", \
                (service_id, ACCTPORT_PROPERTY, 1813))
                
            # Commit the changese
            session.commit()
            
            log_info("Created radius service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise radius database entries!", \
                    sys.exc_info())
            raise ccs_radius_error("Failed to setup database tables!")

        return service_id

def ccs_init():
    registerService(radius_service)
    ca = ccs_ca()
    ca.ensureCertificateExists("radius")
