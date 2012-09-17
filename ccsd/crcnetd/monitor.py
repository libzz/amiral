# Copyright (C) 2006  The University of Waikato 
#
# This file is part of the CRCnet Configuration System
#
# Provides startup code and services for the Configuration System Monitor Server
# The monitor server runs on individual biscuit PCs.
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
import os, os.path
import signal

from _utils.ccsd_log import *
from _utils.ccsd_config import config_init
from _utils.ccsd_daemon import *
from version import ccsd_version, ccsd_revision

from _utils.ccsd_clientserver import startCCSDServer, stopCCSDServer

#####################################################################
# Bootstrapping 
#####################################################################
def start():
    """Main entry point into the monitor server"""
    
    # Read configuration
    config_init()
    
    # Daemonise if necessary
    handleDaemonise()
    
    log_info("CRCnet Monitor v%s (r%s)" % (ccsd_version, ccsd_revision))
    
    # Setup signal handling 	 	 
    signal.signal(signal.SIGTERM, sighndlr) 	 	 
    signal.signal(signal.SIGINT, sighndlr) 
    
    # Initialise modules
    modules = loadModules(CCSD_CLIENT)
    
    # Call any module initialisation functions
    for mod in modules:
        if hasattr(mod, "ccs_init"):
            mod.ccs_init()
    
    # Setup Server - starts a mainloop
    startCCSDServer(None, None, None)
    
    # And that's it... We sit in the mainloop until we get a signal or something
    # to exit. Nothing more to do here.    
