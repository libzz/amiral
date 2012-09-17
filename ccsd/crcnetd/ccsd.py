# Copyright (C) 2006  The University of Waikato 
#
# This file is part of the CRCnet Configuration System
#
# Provides startup code and services for the Configuration System Daemon Server
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
import sys

from _utils.ccsd_log import *
from _utils.ccsd_config import config_init
from _utils.ccsd_daemon import *
from version import ccsd_version, ccsd_revision

from _utils.ccsd_server import startCCSDServer, stopCCSDServer, \
        processClassMethods, reactor
from _utils.ccsd_session import initSessions, ccsd_session
from _utils import ccsd_service
from _utils import ccsd_cfengine
from _utils import ccsd_ca

#####################################################################
# Bootstrapping 
#####################################################################
def start():
    """Main entry point into the configuration daemon"""

    # Read configuration
    config_init()
    
    # Daemonise if necessary
    handleDaemonise()
    
    log_info("CRCnet Configuration System Daemon v%s (r%s)" % \
            (ccsd_version, ccsd_revision))
    
    # Initialise sessions
    initSessions()

    # Initialise modules
    modules = loadModules(CCSD_SERVER)
    for mod in modules:
        # Look for class methods to be registered with XMLRPC
        processClassMethods(mod)

    # Cfengine Configuration / Template System
    try:
        ccsd_cfengine.initCFengine()
    except:
        log_fatal("Failed to initialise CFengine integration!", sys.exc_info()) 
        
    # Initialise services
    processClassMethods(ccsd_service)
   
    # Initialise the certificate authority
    try:
        ccsd_ca.init_ca()
    except:
        log_fatal("Failed to initialise the CA!", sys.exc_info())
        
    # Call any module initialisation functions
    for mod in modules:
        if hasattr(mod, "ccs_init"):
            mod.ccs_init()
            
    # Load the server key/cert from the certification authority
    ca = ccsd_ca.ccs_ca()
    key = None
    cert = None
    cacert = None
    try:
        key = ca.loadkey("server-key.pem")
    except:
        log_fatal("Unable to read server key!", sys.exc_info())
    try:
        cert = ca.loadcert("server-cert.pem")
    except ccs_ca_error:
        log_fatal("Unable to read server certificate!", sys.exc_info())
    
    # Load the ca cert(s) too
    try:
        cacert = ca.loadCACerts()
    except:
        log_fatal("CA certificate is not available!", sys.exc_info())
    del ca

    # Setup RPC Server - starts a mainloop via twisted.internet.reactor
    startCCSDServer(key, cert, cacert)

    # And that's it... We sit in the mainloop until we get a signal or something
    # to exit. Nothing more to do here.
