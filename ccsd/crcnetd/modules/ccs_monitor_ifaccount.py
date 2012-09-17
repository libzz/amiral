# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Interfaces Accounting
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
import os
import os.path
from time import time
import pyrad.packet
from pyrad.client import Client
from pyrad.dictionary import Dictionary

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_config import config_get, config_getboolean, \
        config_getint, config_get_required
from crcnetd._utils.ccsd_events import catchEvent
from crcnetd._utils.ccsd_clientserver import initThread
from crcnetd._utils.ccsd_tc import *

ccs_mod_type = CCSD_CLIENT

DEFAULT_CHECK_INTERVAL = 60 
DEFAULT_UPDATE_INTERVAL = 300

RADIUS_DICTIONARY = "/usr/share/radius/dictionary"

ACCT_START = 1
ACCT_STOP = 2
ACCT_INTERIM = 3
ACCT_ON = 7
ACCT_OFF = 8
TERM_LOST_CARRIER = 2
TERM_ADMIN_RESET = 6
TERM_ADMIN_REBOOT = 7
TERM_PORT_ERROR = 8
TERM_NAS_ERROR = 9
TERM_NAS_REQUEST = 10
TERM_NAS_REBOOT = 11

class ccs_ifaccount_error(ccsd_error):
    pass

_accountingInfo = {}    
_runIfAccount = False
radius_acct_server = None
radius_auth_server = None
radius_acct_queue = []
radius_auth_queue = []
radius_update_interval = DEFAULT_UPDATE_INTERVAL
nas_ip = None
nas_id = None

# Location of plan definitions, each entry should be in the format
#  plan_name downstream upstream
PLAN_FILE="/etc/ccsd/plans"

# The default speeds (kbps) to give a client if no plan is available that 
# matches what RADIUS returned for them
DOWNSTREAM_DEFAULT = 128
UPSTREAM_DEFAULT = 56

# Add 10% to all rates to account for tc inaccuracies
UPSTREAM_FUDGE_FACTOR = 1.2 # 20% for upstream as policing is even worse
DOWNSTREAM_FUDGE_FACTOR = 1.1

@catchEvent("shutdown")
def shutdownHandler(*args, **kwargs):
    global _runIfAccount, _accountingInfo
    
    #XXX: LOCKING? this is called from the mainloop, but deals with 
    # datastructures in the accounting thread...

    # Send stop records
    for ifname, iface in _accountingInfo.items():
        stopAccountingSession(ifname, TERM_ADMIN_REBOOT)
        sendAccountingOnOff(ifname, False)

    # XXX: If there are queued RADIUS packets, try our best not to loose them

    # Tell the processing loop to stop
    _runIfAccount = False

def parseUserFile(filename):
    """Reads the user <-> interface file and sets up the state dictionary"""
    global _accountingInfo

    fp = open(filename, "r")
    lines = fp.readlines()
    fp.close()
    for line in lines:
        # Comment lines start with a #
        if line.strip().startswith("#"): continue
        # All other lines have the format (space separated)
        # <ifname> <username> <ip>
        parts = line.strip().split()
        if len(parts) < 3:
            log_error("Ignoring invalid interface accounting line: %s" % \
                    line.strip())
            continue
        # Store information
        _accountingInfo[parts[0]] = {"username":parts[1], "ip":parts[2]}

def _addCommonAttributes(req, ifname):
    """Adds common attributes to a RADIUS packet"""
    global nas_id, nas_ip, _accountingInfo

    req["NAS-Identifier"] = nas_id
    req["NAS-IP-Address"] = nas_ip
    req["Called-Station-Id"] = _accountingInfo[ifname]["called"]
    req["Calling-Station-Id"] = _accountingInfo[ifname]["calling"]
    return req

def createRADIUSAuthPacket(ifname):
    """Creates a new RADIUS authentication packet and adds common attributes"""
    global radius_auth_server

    req=radius_auth_server.CreateAuthPacket(code=pyrad.packet.AccessRequest)
    return _addCommonAttributes(req, ifname)

def createRADIUSAcctPacket(ifname):
    """Creates a new RADIUS accounting packet and adds common attributes"""
    global radius_acct_server

    req=radius_acct_server.CreateAcctPacket(code= \
            pyrad.packet.AccountingRequest)
    return _addCommonAttributes(req, ifname)

def createRADIUSTrafficPacket(ifname):
    """Creates a new RADIUS packet and adds traffic information to it"""
    global _accountingInfo

    req = createRADIUSAcctPacket(ifname)
    req["Acct-Input-Octets"] = _accountingInfo[ifname]["current_rx"]
    req["Acct-Output-Octets"] = _accountingInfo[ifname]["current_tx"]
    return req

def buildSessionID(ifname):
    """Returns a new Acct-Session-Id for the specified interface
    
    The session ID consists of the last 8 characters of the interface MAC 
    address followed by '-' followed by the time in the format YYMMDDHHMMSS
    """
    global _accountingInfo

    # Build the macstr
    macstr = _accountingInfo[ifname]["called"].replace("-", "")[-8:]

    # Build the time str
    timestr = time.strftime("%y%m%d%H%M%S")

    # Combine and return
    return "%s-%s" % (macstr, timestr)

def dispatchPacket(ifname, req):
    """Helper function that dispatches a packet that doesn't need a callback"""
    return dispatchCallbackPacket(ifname, req, None)

def dispatchCallbackPacket(ifname, req, callback):
    """Dispatches a packet towards the RADIUS server

    If there are no packets in the queue an immediate attempt is made.
    If this attempt fails or there are already packets in the queue, and the
    packet is marked as queueable, it will be appended to the queue for
    dispatch when the server comes back online.

    Returns True if the packet was successfully dispatched, False if it 
    was discarded. NOTE: successfully dispatched may mean queued!
    """
    global radius_acct_server, radius_auth_server, radius_acct_queue
    global radius_auth_queue

    if req.code == pyrad.packet.AccountingRequest:
        server = radius_acct_server
        addFunc = addToAcctQueue
        queue = radius_acct_queue
        desc = "acct"
    else:
        server = radius_auth_server
        addFunc = addToAuthQueue
        queue = radius_auth_queue
        desc = "auth"

    # Are there packets on the queue
    if len(queue) > 0:
        return addFunc(ifname, req, callback)

    # Attempt to send the packet
    try:
        reply=server.SendPacket(req)
        if callback is not None:
            return callback(ifname, req, reply)
        else:
            return True
    except pyrad.client.Timeout:
        # Timeout
        log_warn("RADIUS timeout sending %s packet for %s" % (desc, ifname))
        return addFunc(ifname, req, callback)
    except:
        log_error("RADIUS %s transmit failed for %s!" % (desc, ifname),
                sys.exc_info())
        return False

    # Can we ever get here?
    return False

def addToAcctQueue(ifname, req, callback):
    # No point queuing Interim-Updates
    if req["Acct-Status-Type"] == ACCT_INTERIM:
        return False
    return _addToQueue(True, ifname, req, callback)

def addToAuthQueue(ifname, req, callback):
    return _addToQueue(False, ifname, req, callback)

def _addToQueue(acct, ifname, req, callback):
    """Adds a packet to the queue for transmission at a later time"""
    global radius_auth_queue, radius_acct_queue

    if acct:
        radius_acct_queue.append((ifname, req, callback, 0, 0))
        queue = radius_acct_queue
    else:
        radius_auth_queue.append((ifname, req, callback, 0, 0))
        queue = radius_auth_queue
    log_info("Added packet from %s to RADIUS %s transmit Queue. " \
            "%d packets queued" % 
            (ifname, acct and "acct" or "auth", len(queue)))
    return True

def processRADIUSQueue():
    global radius_acct_queue, radius_auth_queue, radius_acct_server
    global radius_auth_server

    # Easy if there is nothing in the queue
    if len(radius_acct_queue) == 0 and len(radius_auth_queue) == 0:
        return
    
    tuples = [("acct", radius_acct_queue, radius_acct_server), 
            ("auth", radius_auth_queue, radius_auth_server)]

    # Otherwise work through the queue and try and send packets
    for desc, queue, server in tuples:
        idx = 0
        while len(queue) > idx:
            ifname, req, callback, attempts, errors = queue[idx]
            try:
                # Update attempt counter
                attempts+=1
                queue[idx] = (ifname, req, callback, attempts, errors)
                # Attempt to send the packet
                reply=server.SendPacket(req)
                # Remove the packet from the queue
                queue.pop(idx)
                if callback is not None:
                    callback(ifname, req, reply)
                # Move on to the next packet
                continue
            except pyrad.client.Timeout:
                # Timeout
                log_warn("RADIUS timeout sending queued %s packet for %s. " \
                        "Attempt #%d" % (desc, ifname, queue[idx][3]))
                # Give up, no point trying other packets if the server is dead
                break
            except:
                # Update error counter
                errors+=1
                queue[idx] = (ifname, req, callback, attempts, errors)
                if errors == 3:
                    queue.pop(idx)
                    log_error("Discarded RADIUS %s packet from %s " \
                            "after 3 failed transmissions from the queue" % \
                            (desc, ifname), sys.exc_info())
                else:
                    log_error("RADIUS %s transmit failed for %s! Attempt #d." \
                            " Failure %d/3" % \
                            (desc, ifname, queue[idx][3], errors), \
                            sys.exc_info())
            # Try the next packet
            idx+=1
        if desc == "acct":
            radius_acct_queue = queue
        else:
            radius_auth_queue = queue

def doRADIUSAuthentication(ifname):
    """Talks to the RADIUS server to authorise the interface in question

    Once a reply has been received the interface is enabled and the appropriate
    rate limits are imposed. 
    """
    global _accountingInfo
    
    # Create a new packet
    req = createRADIUSAuthPacket(ifname)
    req["User-Name"] = _accountingInfo[ifname]["username"]
    
    if dispatchCallbackPacket(ifname, req, finishRADIUSAuthentication):
        return True
    else:
        log_error("Failed to authenticate user for interface %s" % ifname)
        return False

def finishRADIUSAuthentication(ifname, req, reply):
    """Processes replies to RADIUS authentication requests"""
    global _accountingInfo

    _accountingInfo[ifname]["last_auth_check"] = time.time()

    # Did the authentication succeed?
    if reply.code != pyrad.packet.AccessAccept:
        log_info("Failed to authenticate '%s' on interface %s" % 
                (_accountingInfo[ifname]["username"], ifname))
        # Deny forwarded traffic from the interface
        setInterfaceForwardingState(ifname, False)
        # Set local state
        _accountingInfo[ifname]["authenticated"] = False
        _accountingInfo[ifname]["plan"] = "default"
        return True

    # Authentication succeeded
    log_info("Authentication succeeded for '%s' on interface %s" %
            (_accountingInfo[ifname]["username"], ifname))
    # Set local state
    _accountingInfo[ifname]["authenticated"] = True
    try:
        _accountingInfo[ifname]["plan"] = reply["Class"][0]
    except:
        _accountingInfo[ifname]["plan"] = "default"
    # Allow forwarded traffic from the interface
    setInterfaceForwardingState(ifname, True)
    # Setup interface rate limits
    setInterfaceRatelimits(ifname)
    # Initiate an accounting session
    startAccountingSession(ifname)
    return True

def setInterfaceRatelimits(ifname):
    """Setup ratelimits on the interface using tc"""
    global _accountingInfo
    
    downstream = -1
    upstream = -1
    plan = _accountingInfo[ifname]["plan"]

    # Clear any existing rate limits
    reset_interface_ratelimit(ifname)

    # Get the plan parameters from the file
    try:
        fp = open(PLAN_FILE, "r")
        lines = fp.readlines()
        fp.close()
    except:
        lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) != 3:
            continue
        if parts[0] == plan:
            upstream = int(parts[2]) * UPSTREAM_FUDGE_FACTOR
            downstream = int(parts[1]) * DOWNSTREAM_FUDGE_FACTOR
            break
    
    # Default to 128/56k if unknown plan specified
    if downstream == -1 and upstream == -1:
        log_warn("Unknown plan '%s' requested" % plan)
        downstream = DOWNSTREAM_DEFAULT
        upstream = UPSTREAM_DEFAULT

    # Egress traffic
    iface_enforce_qdisc(ifname, "1:", "htb", "root handle 1: htb default 5")
    iface_enforce_class(ifname, "1:100", "htb", 
            "parent 1:5 classid 1:100 htb rate %skbit burst 6k" % downstream)
    iface_enforce_qdisc(ifname, "100:", "sfq", 
            "parent 1:100 handle 100: sfq perturb 10", True)
    params = "protocol ip u32 match ip src 0.0.0.0/0 flowid 1:100"
    tc_log_command("/sbin/tc filter add dev %s %s %s" % \
            (ifname, FILTER_EGRESS, params))

    # Ingress traffic
    iface_enforce_qdisc(ifname, "ffff:", "ingress", "handle ffff: ingress")
    params = "protocol ip u32 match ip src 0.0.0.0/0 police rate %skbit " \
            "burst 10k drop flowid :ffff" % upstream
    tc_log_command("/sbin/tc filter add dev %s %s %s" % \
            (ifname, FILTER_INGRESS, params))

    log_info("Applied %s/%skbps ratelimit to %s" % 
            (downstream, upstream, ifname))

def sendAccountingOnOff(ifname, on=True, cause=TERM_NAS_REBOOT):
    """Sends an Accounting-On/Off packet to the RADIUS server"""
    
    # Setup the packet
    req = createRADIUSAcctPacket(ifname)
    if on:
        req["Acct-Status-Type"] = ACCT_ON
    else:
        req["Acct-Status-Type"] = ACCT_OFF
        req["Acct-Terminate-Cause"] = cause

    # Send
    if dispatchPacket(ifname, req):
        log_info("Dispatched RADIUS accounting %s for %s" % \
                (on and "on" or "off", ifname))
        return True
    else:
        log_error("Failed to send RADIUS accounting %s for %s" % \
                (on and "on" or "off", ifname))
        return False

def startAccountingSession(ifname):
    """Sets up a new session for the interface"""
    global _accountingInfo
    
    # Accounting is only allowed if the interface is authenticated
    if not _accountingInfo[ifname]["authenticated"]:
        return

    # Stop any existing session
    if _accountingInfo[ifname]["Acct-Session-Id"] != "":
        stopAccountingSession(ifname, TERM_USER_REQUEST)

    # Create a new packet
    req = createRADIUSAcctPacket(ifname)
    req["Acct-Status-Type"] = ACCT_START
    req["User-Name"] = _accountingInfo[ifname]["username"]
    req["Acct-Session-Id"] = buildSessionID(ifname)

    # Send the packet
    if dispatchPacket(ifname, req):
        log_info("Dispatched RADIUS session start for %s" % ifname)
        _accountingInfo[ifname]["Acct-Session-Id"] = req["Acct-Session-Id"][0]
        _accountingInfo[ifname]["last_update"] = time.time()
        _accountingInfo[ifname]["current_rx"] = 0
        _accountingInfo[ifname]["current_tx"] = 0
        return True
    else:
        log_error("Failed to start session on '%s'" % ifname)
        return False

def stopAccountingSession(ifname, reason=TERM_ADMIN_RESET):
    """Stops the current session for the specified interface"""
    global _accountingInfo

    # Exit early if there is no session active
    if _accountingInfo[ifname]["Acct-Session-Id"] == "":
        return False

    # Create a new packet
    req = createRADIUSTrafficPacket(ifname)
    req["Acct-Status-Type"] = ACCT_STOP
    req["User-Name"] = _accountingInfo[ifname]["username"]
    req["Acct-Session-Id"] = _accountingInfo[ifname]["Acct-Session-Id"]
    duration = time.time() - _accountingInfo[ifname]["session_start"]
    req["Acct-Session-Time"] = duration
    req["Acct-Terminate-Cause"] = reason

    # Send the packet
    if dispatchPacket(ifname, req):
        log_info("Dispatched RADIUS session stop for %s" % ifname)
        # Reset the state 
        _accountingInfo[ifname]["Acct-Session-Id"] = ""
        for key in ["session_start", "initial_rx", "initial_tx", "current_rx",
                "current_tx"]:
            _accountingInfo[ifname][key] = -1
        return True
    else:
        log_error("Failed to stop session '%s' on '%s'" % \
                (_accountingInfo[ifname]["Acct-Session-Id"], ifname))
        log_error("Failed session information: duration=%s, rx=%s, tx=%s" % \
                (duration, _accountingInfo[ifname]["current_rx"], \
                _accountingInfo[ifname]["current_tx"]))
        return False

def sendUpdatePacket(ifname):
    """Sends a interim-update packet for the specified interface"""
    global _accountingInfo

    # Exit early if there is no session active
    if _accountingInfo[ifname]["Acct-Session-Id"] == "":
        return False

    # Create a new packet
    req = createRADIUSTrafficPacket(ifname)
    req["Acct-Status-Type"] = ACCT_INTERIM
    req["User-Name"] = _accountingInfo[ifname]["username"]
    req["Acct-Session-Id"] = _accountingInfo[ifname]["Acct-Session-Id"]
    duration = time.time() - _accountingInfo[ifname]["session_start"]
    req["Acct-Session-Time"] = duration

    # Send the packet
    if dispatchPacket(ifname, req):
        log_info("Dispatched RADIUS Interim-Update for %s" % ifname)
        _accountingInfo[ifname]["last_update"] = time.time()
        return True
    else:
        return False

def processInterimUpdates():
    """Sends interim updates for interfaces that need them"""
    global _accountingInfo, radius_update_interval

    for ifname, iface in _accountingInfo.items():
        # Accounting is only allowed if the interface is authenticated
        if not _accountingInfo[ifname]["authenticated"]: continue
        age = time.time() - _accountingInfo[ifname]["last_update"]
        if age > radius_update_interval:
            sendUpdatePacket(ifname)

def updateTrafficCounters():
    """Reads the current interface traffic counters and updates state"""
    global _accountingInfo

    traffic = getTrafficCounters()
    for ifname, iface in _accountingInfo.items():
        # XXX: Check for wrap
        _accountingInfo[ifname]["current_rx"] = traffic[ifname]["rx"] - \
                _accountingInfo[ifname]["initial_rx"]
        _accountingInfo[ifname]["current_tx"] = traffic[ifname]["tx"] - \
                _accountingInfo[ifname]["initial_tx"]

def initialiseInterfaceState():
    """Checks the initial state of interface and starts accounting sessions"""
    global _accountingInfo
    
    interfaces = getInterfaces()
    traffic = getTrafficCounters()
    for iface in interfaces:
        ifname = iface["name"]
        # Skip interfaces that are not being accounted
        if ifname not in _accountingInfo.keys(): continue
        # Skip interfaces that are currently down
        if not iface["up"]: continue
        # Retrieve initial traffic usage for the interface
        rx = 0
        tx = 0
        if ifname in traffic.keys():
            rx = traffic[ifname]["rx"]
            tx = traffic[ifname]["tx"]
        else:
            log_warn("No traffic counters for interface: %s" % ifname)
        # Get interface and peer mac addresses, formatted in the same fashion
        # as hostapd. We use the first peer mac that we find on the link...
        _accountingInfo[ifname]["called"] = \
                iface["mac"].upper().replace(":", "-")
        peerMac = "00-00-00-00-00-00"
        for ip, mac in getLinkMACs(ifname).items():
            peerMac = mac.upper().replace(":", "-")
            break
        _accountingInfo[ifname]["calling"] = peerMac
        # Store initial traffic
        _accountingInfo[ifname]["initial_rx"] = rx
        _accountingInfo[ifname]["initial_tx"] = tx
        _accountingInfo[ifname]["session_start"] = time.time()
        _accountingInfo[ifname]["Acct-Session-Id"] = ""
        _accountingInfo[ifname]["authenticated"] = False
        _accountingInfo[ifname]["last_auth_check"] = -1
        # Tell RADIUS this interface is now online
        sendAccountingOnOff(ifname)
        # Send a RADIUS authentication request to get the ratelimit details
        doRADIUSAuthentication(ifname)

def ifAccountThread():
    """Runs as a thread to account from traffic on an interface"""
    global _accountingInfo, _runIfAccount, nas_id, nas_ip
    global radius_update_interval, radius_acct_server, radius_auth_server

    try:
        # Is interface accounting enabled
        enabled = config_getboolean("accounting", "enabled", True)
        if not enabled:
            log_info("Interface accounting disabled.")
            return
        _runIfAccount = True;

        # What interval shall we check hosts at
        check_interval = config_get("accounting", "check_interval", 
                DEFAULT_CHECK_INTERVAL)
        radius_update_interval = config_getint("accounting", "update_interval",
                DEFAULT_UPDATE_INTERVAL)

        # Initialise the interface list
        default_user_file = "%s/accounting_users" % \
                os.path.dirname(DEFAULT_CONFFILE)
        user_file = config_get("accounting", "user_file", default_user_file)
        if not os.path.exists(user_file):
            log_error("Interface accounting disabled. No user file: %s" % \
                    user_file)
            _runIfAccount = False
            return
        
        # Initialise the RADIUS connection
        try:
            dummy0 = getInterfaces(returnOne="dummy0")[0]
            dummy0ip = dummy0["address"].split("/")[0]
        except:
            log_error("Could not determine host loopback address!", 
                    sys.exc_info())
            dummy0ip = "127.0.0.1"
        acct_server = config_get("accounting", "acct_server", "radius")
        acct_secret = config_get_required("accounting", "acct_secret")
        auth_server = config_get("accounting", "auth_server", "radius")
        auth_secret = config_get_required("accounting", "auth_secret")
        nas_id = config_get("accounting", "nas_id", getFQDN())
        nas_ip = config_get("accounting", "nas_ip", dummy0ip)
        radius_acct_server=Client(server=acct_server, secret=acct_secret,
            dict=Dictionary(RADIUS_DICTIONARY))
        radius_auth_server=Client(server=auth_server, secret=auth_secret,
            dict=Dictionary(RADIUS_DICTIONARY))
        # FreeRADIUS at least auths based on IP address, make sure our
        # packets come from the right place
        radius_acct_server.bind((nas_ip, 0))
        radius_auth_server.bind((nas_ip, 0))

        # Read and parse the user file
        parseUserFile(user_file)

        # Initialise interface state
        initialiseInterfaceState()
        
        # Loop forever reading byte counters as appropriate
        while _runIfAccount:
            # wait a bit before checking
            time.sleep(check_interval)
            # Send any queued packets
            processRADIUSQueue()
            # Try and re-authenticate any dead interfaces
            for ifname, iface in _accountingInfo.items():
                if iface["authenticated"]: continue
                age = time.time() - iface["last_auth_check"]
                if age > radius_update_interval:
                    doRADIUSAuthentication(ifname)
            # Update traffic details
            updateTrafficCounters()
            # Generate interim-updates
            processInterimUpdates()

    except:
        (etype, value, tb) = sys.exc_info()
        log_error("Exception in interface accounting thread! - %s" % value, 
                (etype, value, tb))

    log_info("Exiting interface accounting thread")
        
def ccs_init():
    # Start the accounting information thread
    initThread(ifAccountThread, ())
