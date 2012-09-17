# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# ssmtp Service - Configures an ssmtp service to run on a host
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

SMARTHOST_PROPERTY = "smarthost"

class ssmtp_error(ccs_service_error):
    pass

class ssmtp_service(ccsd_service):
    """Configures the ssmtp service on a host"""
    
    serviceName = "ssmtp"
    allowNewProperties = True
    networkService = False

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        
        session.execute("INSERT INTO service (service_id, service_name, " \
                "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                (ssmtp_service.serviceName))
        service_id = session.getCountOf("SELECT currval('" \
                "service_service_id_seq') AS server_id", ())

        # Insert basic properties
        session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'string', %s, 't')", \
                (service_id, SMARTHOST_PROPERTY, "smtp.%s" % \
                config_get("ccsd", "base_domain")))
        
        log_info("Created ssmtp service entries in database")
                
        return service_id

registerService(ssmtp_service)
