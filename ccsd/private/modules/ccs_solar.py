# Copyright (C) 2006  The University of Waikato
#
# Solar Service Module for the CRCnet Configuration System
# Configures solar to act as an authenticator on a host
#
# Author:       Chris Browning <chris@rurallink.co.nz>
# Version:      $Id: ccs_solar.py 1623 2007-11-12 20:41:12Z ckb6 $
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

class solar_error(ccs_service_error):
    pass

class solar_service(ccsd_service):
    """Configures the solar service on a host"""
    
    serviceName = "solar"
    allowNewProperties = True
    networkService = False

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising Solar service")        
        try:

            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (solar_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS server_id", ())
                
            # Commit the changese
            session.commit()
            
            log_info("Created solar service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise solar database entries!", \
                    sys.exc_info())
            raise solar_error("Failed to setup database tables!")

        return service_id

def ccs_init():
    registerService(solar_service)
