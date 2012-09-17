#!/usr/bin/python
# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# CRCnet Monitor - Watchdog and System Recovery Support
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# No usage or redistribution rights are granted for this file unless
# otherwise confirmed in writing by the copyright holder.
import sys
import time
import thread

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_config import config_get
from crcnetd._utils.ccsd_events import catchEvent
from crcnetd._utils.ccsd_clientserver import registerRecurring

class ccs_watchdog_error(ccsd_error):
    pass

WATCHDOG_DEVICE = "/dev/watchdog"
CHECK_INTERVAL = 60
NOTIFY_INTERVAL = 300

ccs_mod_type = CCSD_CLIENT

do_watchdog = True
watchdog_running = False
gw_iface = ""
gw_ip = ""
dead_neighbour = 0
dead_neighbour_reconf = False

##############################################################################
# Utility Functions
##############################################################################
def doWatchdog():
    """Executed as a thread to keep the watchdog happy"""
    global do_watchdog, watchdog_running
    
    fp = open(WATCHDOG_DEVICE, "w")
    log_info("Watchdog device opened")
    watchdog_running = True
    
    while do_watchdog:
        # Tell the watchdog we're still alive
        fp.write("hi\n")
        fp.flush()
        # Wait for a bit
        time.sleep(5)

    # do_watchdog was set to false, exit gracefully
    fp.write("V\n")
    fp.close()
    log_info("Watchdog device gracefully closed")
    watchdog_running = False
    
    return 0

@catchEvent("shutdown")
def stopWatchdog(*args, **kwargs):
    """Catch shutdown events so we can tell the watchdog to stop gracefully"""
    global do_watchdog, watchdog_running

    log_info("Trying to stop watchdog")
    
    # If it's already stopped, exit
    if not watchdog_running or not do_watchdog:
        log_info("Watchdog not running")
        return 0

    # Tell it to stop
    do_watchdog = False

    # Wait until it has
    log_info("Waiting for watchdog device to close...")
    while watchdog_running:
        time.sleep(1)

    return 0

@registerRecurring(CHECK_INTERVAL)
def checkNetwork():
    """Called periodically to check that the network connections are ok"""
    global gw_iface, gw_ip, dead_neighbour
    
    # If CFengine is running then defer check
    if processExists("cfagent"):
        log_info("Deferring network status check while CFengine is running")
        return

    # Check if we have a default route first
    gw = getGatewayIP()
    
    if gw != "" and isHostUp(gw):
        # We can talk to the default gateway, no problem
        gw_iface = getGatewayIface()
        gw_ip = gw
        if dead_neighbour > 0:
            log_info("Default gateway is now reachable")
            dead_neighbour = 0
        return
    
    
    # If we know what interface used to be the default gateway check it
    if gw_iface != "":
        if checkIface(gw_iface, gw_ip):
            return
    
    # That interface can't be brought up for some reason
    # Check if the interfaces file exists
    if not os.path.exists("/etc/network/interfaces"):
        # There is no interface configuration file
        log_error("Interface configuration file missing!")
        if os.path.exists("/etc/network/interfaces.cfsaved"):
            try:
                remountrw("checkNetwork")
                log_command("cp /etc/network/interfaces.cfsaved " \
                        "/etc/network/interfaces 2>&1")
            finally:
                remountro("checkNetwork")
            log_info("Interface configuration restored from CFengine backup!")
        else:
            log_error("No backup interface configuration available!")
            # XXX: What to do here?
            return
        
    # Restart networking
    log_info("Attempting to restore network connectivity")
    log_command("/etc/init.d/networking restart 2>&1")
    return

def checkIface(ifname, neigh_ip=None):
    """Checks the connection status of the specified interface
    
    Returns True if the interface is up - even if the neighbour is not
    reachable. For now we just assume that it is configured correctly. If 
    it has been down for five minutes, we reconfigure the interface 
    """
    global dead_neighbour, dead_neighbour_reconf

    iface = getInterfaces(returnOne=ifname)
    if len(iface)!=1:
        return False
    iface = iface[0]
    if not iface["up"]:
        # Try and bring it up
        log_command("/sbin/ifup %s 2>&1" % ifname)

    iface = getInterfaces(returnOne=ifname)
    if len(iface)!=1:
        return False
    iface = iface[0]
    if not iface["up"]:
        # Failed to bring up
        log_info("Could not bring up interface %s" % ifname)
        return False

    # Interface that we used to use for the default gw is up
    # try and ping the other side
    if neigh_ip is None:
        ip = getNeighbourIP(ifname)
    else:
        ip = neigh_ip
    if isHostUp(ip):
        if dead_neighbour > 0:
            log_info("Neighbour %s on iface %s is now " \
                    "reachable" % (ip, ifname))
            dead_neighbour = 0
            dead_neighbour_reconf = False
        return True
    
    if dead_neighbour == 0:
        # Neighbour has just gone down - wait for another minute to guard
        # against random packet loss
        dead_neighbour = time.time()
        dead_neighbour_reconf = False
        log_info("Neighbour %s on iface %s is not reachable" % (ip, ifname))
        return True

    if dead_neighbour_reconf:
        # Iface configuration has already been reloaded
        d = time.time()-dead_neighbour
        if d > NOTIFY_INTERVAL:
            log_info("Neighbour %s on iface %s has been down " \
                    "for %s seconds!" % (ip, ifname, d))
        # XXX: Do we want to do something here if it's been
        # down for "ages"?
        return True

    # Reconfigure the interface incase something broke it
    log_command("/sbin/ifdown %s 2>&1" % ifname)
    log_command("/sbin/ifup %s 2>&1" % ifname)
    log_info("Reloaded iface %s in attempt to reach neighbour %s" % \
            (ifname, ip))
    dead_neighbour_reconf = True
    
    return True

##############################################################################
# Initialisation
##############################################################################
def ccs_init():
    
    thread.start_new_thread(doWatchdog, ())
