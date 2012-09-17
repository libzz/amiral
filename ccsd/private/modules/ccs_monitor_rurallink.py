# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Rural Link autoconfiguration and management functionality
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# No usage or redistribution rights are granted for this file unless
# otherwise confirmed in writing by the copyright holder.
import sys
import os, os.path
import crypt
import re
import iwtools
import httplib
import socket
import urllib
from md5 import md5
from telnetlib import Telnet
from BaseHTTPServer import BaseHTTPRequestHandler

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_clientserver import registerPage, registerRealm, \
        registerDir, AsyncHTTPServer, CCSDHandler, registerRecurring
from crcnetd._utils.ccsd_config import config_getboolean, pref_get, pref_set, \
        pref_getboolean
from crcnetd._utils.ccsd_events import catchEvent
from crcnetd._utils.interfaces import debian_interfaces
from crcnetd._utils.dhcpd import dhcpd_conf

from ccs_monitor_web import registerMenu, registerMenuItem, returnPage, \
        MENU_TOP, MENU_BOTTOM, MENU_GROUP_GENERAL, MENU_GROUP_HOME, \
        CPE_ADMIN_REALM, getMonitorPrefs, getRealm, ADMIN_USERNAME, \
        generateSelect, HTable, DEFAULT_RESOURCE_DIR, homepage, \
        DEFAULT_PREF_FILE

from ccs_monitor_status import getSSMeter, initialiseNetworkMap

class ccs_rurallink_error(ccsd_error):
    pass

ccs_mod_type = CCSD_CLIENT

SERIALNO_FILE = "/etc/rlserial"
DEFAULT_PASSWORD = "rurallink"
DEFAULT_INTERNAL_IFNAME = "int"
DEFAULT_BACKHAUL_IFNAME = "bhaul"
DEFAULT_ISP_IFNAME = "ext"
DEFAULT_AP0_IFNAME = "ap0"
RL_ESSID_PREFIX = "rl-"
DHCP_DEFAULTS = "/etc/default/dhcp3-server"
ASSOC_STORE_DIR = "/var/lib/ccsd/"
HOSTNAME_CHAR_RE = "^[A-za-z0-9\-]*$"
MAP_UPDATE_INTERVAL = 60*30

BCL_IFACE="bcl"
BCL_CONF="/etc/ppp/peers/bcl"
PAP_SECRETS="/etc/ppp/pap-secrets"

ISP_BCL = "bcl"
ISP_DSL = "dsl"
ISP_ETH = "eth"
RL_ISPS = { ISP_BCL:"BCL (Xtra Wireless)", ISP_DSL:"DSL Connection", \
        ISP_ETH:"Ethernet Connection" }
    
DSL_MODEM_IP = "10.1.1.1"
DSL_CPE_IP = "10.1.1.254"
DSL_NETMASK = "8"
DSL_TELNET_TIMEOUT = 2

# How often (seconds) to check DNS settings
DNS_UPDATE_INTERVAL = 60

# How often (seconds) to check routing
ROUTE_CHECK_INTERVAL = 60

# How often (seconds) to phone home 
PHONE_HOME_INTERVAL = 60 * 30

# How often to check that our upstream connection is working
UPSTREAM_CHECK_INTERVAL = 60

# Default XMLRPC server to phone home to
DEFAULT_HOME_URL = "https://phonehome.rurallink.co.nz:5566/RPC2"

# SSL certificate file locations
DEFAULT_CERT_FILE = "/etc/ccsd/cert.pem"
DEFAULT_KEY_FILE = "/etc/ccsd/key.pem"

# How many bits of WEP key to use
WEP_KEY_BITS = 104
WEP_KEY_LENGTH =  WEP_KEY_BITS / 8

ISP_IF_DISCONNECT = """<a href="/rladmin/isp-disconnect">[Disconnect]</a>"""
ISP_IF_CONNECT = """<a href="/rladmin/isp-connect">[Connect]</a>"""
ISP_IF_RELOAD = """<script language="javascript" type="text/javascript">
remaining=30
function progress() {
    remaining--;
    if (remaining == 0) {
        clearInterval(id);
        reload();
        return;
    }
    $("rem").innerHTML=remaining;
}
function reload() {
    l = document.location.toString();
    if (l.indexOf("isp-connect")!=-1) {
        newL = l.substring(0, l.length-12);
    } else {
        newL = l.substring(0, l.length-15);
    }
    document.location = newL;
}
id = window.setInterval(progress, 1000);
</script>
"""

RL_NODE = -1
RL_INTERNAL = 0
RL_AP0 = 1
RL_AP1 = 2
RL_AP2 = 3

channels = {1:"01 - 2.412Ghz *", 2:"02 - 2.417Ghz", 3:"03 - 2.422Ghz", 
    4:"04 - 2.427Ghz", 5:"05 - 2.432Ghz", 6:"06 - 2.437Ghz *", 
    7:"07 - 2.442Ghz", 8:"08 - 2.447Ghz", 9:"09 - 2.452Ghz", 
    10:"10 - 2.457Ghz", 11:"11 - 2.462Ghz *"}

DEFAULT_TRAFFIC_PASSWD_FILE = "/var/lib/ccsd/passwd"
USERNAME_CHAR_RE = "[A-za-z0-9]"
FIREWALL_NET_OPTIONS = { "allow":"Always allow Internet access", \
        "deny":"Always deny Internet access", \
        "password":"Require a username and password for Internet access"}
DEFAULT_INTERNAL_POLICY = "allow"
DEFAULT_AP0_POLICY = "password"

# How often (seconds) to retrieve traffic stats from iptables
TRAFFIC_UPDATE_INTERVAL = 60

# These parameters are currently configured to generate a /26 for 
# each node based on the RL_BASE of 12 bits + 14 bits of serial 
# number. Two bits are then allocated for a function on each node
# giving a total of 4 /28s per node.
# RL_BASE = hex(172.16.0.0)
RL_BASE_S = "172.16.0.0"
RL_MASK_S = "255.240.0.0"
RL_BASE = 0xAC100000
BASE_BITS = 12
SERIAL_BITS = 14
FUNCTION_BITS = 2

# The following constants are calculated automatically from the values above
BASE_SHIFT = 32 - BASE_BITS
SERIAL_SHIFT = BASE_SHIFT - SERIAL_BITS
FUNCTION_SHIFT = SERIAL_SHIFT - FUNCTION_BITS

BASE_MASK = (((2 ** BASE_BITS) - 1) << BASE_SHIFT)
SERIAL_MASK =  (((2 ** SERIAL_BITS) - 1) << SERIAL_SHIFT)
FUNCTION_MASK = (((2 ** FUNCTION_BITS) - 1) << FUNCTION_SHIFT)

rl_serialno = -1
rl_password = DEFAULT_PASSWORD
rl_masterip = None
rl_mastername = ""
rl_isptype = None
rl_lastmapupdate = 0
rl_trafficusers = {}
unallocated_traffic=0

##############################################################################
# Utility Functions
##############################################################################
def generateRLNetwork(serialno, function):
    """Generates a network address for the specified device and function
    
    Returns a tuple with two items. The first is the network address. The
    second describes how many bits long the netmask is.
    """
    
    if function == RL_NODE:
        function = 0
        mask = 32 - SERIAL_SHIFT
    else:
        mask = 32 - FUNCTION_SHIFT
    
    return (RL_BASE | ((serialno << SERIAL_SHIFT) & SERIAL_MASK) | \
            ((function << FUNCTION_SHIFT) & FUNCTION_MASK), mask)

def isValidRLSerialNo(serialno):

    if int(serialno) <= 0:
        return False
    if int(serialno) > (2**SERIAL_BITS):
        return False

    return True

def setupAssociation(gw, apname):
    """Send a request to the AP to let us associate"""
    global rl_password, rl_serialno, rl_mastername, rl_masterip
    
    name = socket.gethostname()
    nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)

    data = "password=%s&serialno=%s" % (rl_password, rl_serialno)
    try:
        conn = httplib.HTTPConnection(gw)
        conn.putrequest('POST', "/register_client/%s" % name, data)
        conn.putheader('content-length', str(len(data)))
        conn.endheaders()
        conn.send(data)
        rv = conn.getresponse()
        conn.close()
    except:
        (type, value, tb) = sys.exc_info()
        log_error("Failed to connect to upstream server - %s" % value)
        return False
    
    if rv.status == 200:
        log_info("Associated with upstream node %s" % apname)
        pref_set("rurallink", "backhaul_assoc", apname, getMonitorPrefs())
        retrieveMasterIP()
        registerSubClients()
        registerMenuItem(MENU_TOP, MENU_GROUP_HOME, \
                "http://%s/" % rl_masterip, "Master Node Homepage")
        if retrieveNodemapFile(nm_filename):
            setupStatusMap(nm_filename, rl_mastername)
        return True

    pref_set("rurallink", "backhaul_assoc", "", getMonitorPrefs())
    log_error("Client registration failed: %s" % rv.reason)
    return False

def getWEPKey(asHexString=False):
    """Returns a WEP key for the device to use based on its password"""
    global rl_password
    
    sum = md5(rl_password).hexdigest()
    key = sum[-1*WEP_KEY_LENGTH:]
    if not asHexString:
        return key
    
    # Each char is one byte, which gives two hexadecimal characters
    string = ""
    pos=0
    for char in key:
        string += "%X" % ord(char)
        pos+=2
        if (pos%4)==0:
            string += "-"
    return string.strip("-")

def configureBhaulInterface(essid):
    """Configure an interface to talk to an access point"""
    global backhaul_ifname, backhaul_vbase, rl_password

    try:
        # If there is no backhaul interface it can't be configured
        if backhaul_ifname is None:
            log_error("No backhaul interface to configure!")
            return False
        
        # Take interface down
        log_command("/sbin/ifdown %s 2>&1" % backhaul_ifname)
        
        # Write /etc/network/interfaces stanza
        ifaces = debian_interfaces()
        iface = {"name":backhaul_ifname, "family":"inet", "method":"dhcp"}
        if backhaul_vbase is not None:
            iface["madwifi_base"] = backhaul_vbase
            iface["wireless_standard"] = "g"
        iface["wireless_mode"] = "Managed"
        iface["wireless_essid"] = essid
        iface["wireless_key"] = "s:%s" % getWEPKey()
        try:
            remountrw("configureBhaulInterface")
            ifaces[backhaul_ifname] = iface
            ifaces.write()
        finally:
            remountro("configureBhaulInterface")
        
        # Bring Up, restart services
        log_command("/sbin/ifup %s 2>&1" % backhaul_ifname)
        ifaces = getInterfaces(returnOne=backhaul_ifname)
        if len(ifaces) != 1 or not ifaces[0]["up"]:
            # Failed
            log_error("Failed to bring up backhaul interface (%s)" % \
                    backhaul_ifname)
            return False

        # Get our interface IP address
        gw = getGatewayIP()
        
        # Check connectivity
        if not isHostUp(gw):
            # Cannot associate now...
            return False
    
        # Send an association request
        parts = essid.split("-")
        apname = "-".join(parts[1:-1])
        return setupAssociation(gw, apname)
    except:
        log_error("Unexpected exception while configuring backhaul!", 
                sys.exc_info())
        return False
    
def getBackhaulStatus():
    """Returns a tuple describing the status of the backhaul link"""
    global backhaul_ifname

    nopeer = {"snr":0,"signal":0,"noise":0}
    
    if backhaul_ifname is None:
        return None
    
    ifaces = getInterfaces(returnOne=backhaul_ifname)
    if len(ifaces) != 1:
        return ("critical", "Backhaul interface not found", nopeer)
    iface = ifaces[0]
    wiface = iwtools.get_interface(backhaul_ifname)
    
    # Check if the interface is configured on a ruralllink network
    if wiface:
        essid = wiface.get_essid()
        if not essid.startswith(RL_ESSID_PREFIX):
            return ("critical", "Not attached to RuralLink device", nopeer)
        parts = essid.split("-")
        peer = "-".join(parts[1:-1])
        stats = wiface.get_stats()
    else:
        peer = ""
        stats = nopeer

    assoc = pref_get("rurallink", "backhaul_assoc", getMonitorPrefs(), "")
    if assoc=="" or assoc!=peer:
        # No record of association 
        return ("warning", "%s - Not authenticated" % peer, stats) 
    
    return ("ok", "%s" % peer, stats)

def ensureBackhaulUp():
    """Ensures that the backhaul interface is up"""
    global backhaul_ifname, backhaul_vbase

    ifaces = getInterfaces(returnOne=backhaul_ifname)
    if len(ifaces) != 1:
        # Try and create it if possible
        if backhaul_vbase is not None:
            log_command("/usr/bin/wlanconfig %s create nounit " \
                    "wlandev %s wlanmode sta &>/dev/null"  % \
                    (backhaul_ifname, backhaul_vbase))
            ifaces = getInterfaces(returnOne=backhaul_ifname)
    if len(ifaces) != 1:
        raise ccs_rurallink_error("Backhaul interface (%s) does not " \
                "exist. Cannot bring up!" % backhaul_ifname)
    iface = ifaces[0]
    
    # Exit now if the interface is already up
    if iface["up"]:
        return True
    
    # Bring it up
    if log_command("/sbin/ip link set up dev %s 2>&1" % \
            backhaul_ifname) != None:
        raise ccs_rurallink_error("Failed to bring up backhaul interface " \
                "(%s)!" % backhaul_ifname)

    # Assume it came up ok
    return True

def retrieveMasterIP():
    """Asks the parent node for the IP address of the Master node"""
    global rl_masterip, rl_mastername
    
    # Get default gateway's IP
    gw = getGatewayIP()
    
    # Check connectivity
    if not isHostUp(gw):
        # Cannot associate now...
        return True

    try:
        conn = httplib.HTTPConnection(gw)
        conn.putrequest('GET', "/masterip")
        conn.endheaders()
        rv = conn.getresponse()
        conn.close()
    except:
        (type, value, tb) = sys.exc_info()
        log_error("Failed to connect to upstream server - %s" % value)
        return None
    
    if rv.status == 200:
        rl_masterip = rv.read()
        pref_set("rurallink", "masterip", rl_masterip, getMonitorPrefs())
        rl_mastername = getNodeName(rl_masterip)
        return rl_masterip
    
    return None
    
def isMasterNode():
    """Returns True if this node is configured to act as a Master

    If there is no configuration information available we use a simple
    heuristic: If there is only one wireless interface we are a Master.
    """

    is_master = config_getboolean("rurallink", "is_master", None)
    if is_master is not None:
        return is_master

    return False

def allocateChannel(ifname):
    """Uses a heuristic to find the best channel to use for a new AP

    - Checks for channel use on other interfaces and removes them
    - Scans for other channels it can hear and removes them
    -
    - Uses 1,6,11 if available
    - Otherwise picks a random channel out of the remaining list
    """
    global backhaul_ifname, channels
    
    achannels = channels.keys()
    
    # Remove channels in use on other wireless interfaces
    if backhaul_ifname is not None:
        wiface = iwtools.get_interface(backhaul_ifname)
        if wiface:
            try:
                channel = wiface.get_channel()
            except:
                log_error("Could not determine channel of backhaul " \
                        "interface!", sys.exc_info())
                channel = -1
            if channel != -1:
                log_debug("Removing channel %d from list. In use on %s" % \
                        (channel, backhaul_ifname))
                achannels.pop(channel-1)

    # Remove channels that we see in a scan - may not be able to scan if the
    # interface doesn't yet exist...
    wiface = iwtools.get_interface(ifname)
    if wiface:
        try:
            essid = wiface.get_essid()
            scanres = wiface.scanall()
        except:
            pass
        n=0
        for network in scanres:
            # Skip the network on the interface we're allocating for
            if network.essid == essid:
                continue
            log_debug("Removing channel %d from list. In use on network %s" % \
                    (network.channel, network.essid))
            achannels.pop(network.channel-1)
    
    log_debug("Available channels: %s" % achannels)
    if 1 in achannels:
        channel = 1
    elif 6 in achannels:
        channel = 6
    elif 11 in achannels:
        channel = 11
    else:
        random.seed()
        channel = random.choice(achannels)
    log_info("Allocating channel %s to %s" % (channel, ifname))

    return channel

def addRoute(network, mask, dest, dev):
    """Adds a route to the route table if it does not already exist"""
    
    routes = getRoutes()
    found = False
    for route in routes:
        if network=="default":
            if route["network"]=="0.0.0.0" and route["netmask"]=="0.0.0.0":
                found = True
                break
        else:
            if route["network"]==formatIP(network) and \
                    route["netmask"]==formatIP(bitsToNetmask(mask)):
                found = True
                break
    if not found:
        if network != "default":
            cidr = "%s/%s" % (formatIP(network), mask)
        else:
            cidr = network
        rv = log_command("/sbin/ip route add %s via %s dev %s 2>&1" % \
                (cidr, dest, dev))
        if rv != None:
            return False

    return True

def delRoute(network, mask, dest, dev):
    """Removes a route from the route table"""
    if network != "default":
        cidr = "%s/%s" % (formatIP(network), mask)
    else:
        cidr = network
    rv = log_command("/sbin/ip route del %s via %s dev %s &>/dev/null" % \
            (cidr, dest, dev))

    return True

def changeHostname(hostname):
    """Changes the device's hostname"""
    global ap0_ifname
    
    updateInterfaces = False
   
    # Check the hostname format is correct
    if re.match(HOSTNAME_CHAR_RE, hostname) is None:
        raise ccs_rurallink_error("Invalid character in hostname")
    
    hostname = hostname.lower()

    # Update Access Point ESSID 
    if ap0_ifname is not None:
        interfaces = debian_interfaces()
        iface = interfaces[ap0_ifname]
        iface["wireless_essid"] = "rl-%s-ap0" % hostname
        interfaces[ap0_ifname] = iface
        updateInterfaces = True
        
    # Save it 
    try:
        remountrw("changeHostname")
        fp = open("/etc/hostname", "w")
        fp.write("%s\n" % hostname)
        fp.close()
        if updateInterfaces:
            interfaces.write()
    finally:
        remountro("changeHostname")
    
    # Update running config
    log_command("/bin/hostname -F /etc/hostname 2>&1")
    if updateInterfaces:
        log_command("/sbin/iwconfig %s essid rl-%s-ap0" % \
                (ap0_ifname, hostname))
    log_command("/etc/init.d/sysklogd restart 2>&1")

    return True

def retrieveNodemapFile(path):
    """Retrieves the network nodemap from the master node"""
    global rl_masterip
    conn = None

    # Cannot update if we don't have a master node yet!
    if rl_masterip is None:
        return False
    
    try:
        conn = httplib.HTTPConnection(rl_masterip)
        conn.putrequest('GET', "/nodemap")
        conn.endheaders()
        rv = conn.getresponse()
    except:
        (type, value, tb) = sys.exc_info()
        log_error("retrieveNodemapFile from %s failed: %s" % \
                (rl_masterip, value))
        if conn is not None: conn.close()
        return False

    if rv.status == 200:
        map = rv.read()
        try:
            remountrw("retrieveNodemapFile")
            fp = open(path, "w")
            fp.write(map)
            fp.close()
            remountro("retrieveNodemapFile")
        except IOError:
            remountro("retrieveNodemapFile")
            log_error("Could not open nodemap destination for writing!", \
                    sys.exc_info())
            return False
        if conn is not None: conn.close()
        return True

    log_error("retrieveNodemapFile received an invalid response (%s) " \
            "from %s - %s!" % (rv.status, rl_masterip, rv.reason))
    if conn is not None: conn.close()
    return False
    
def buildNodemapFile(path):
    """Builds a nodemap suitable for use with the status graph"""
    global rl_isptype, ap0_ifname
    
    try:
        remountrw("buildNodemapFile")
        fp = open(path, "w")

        # Get ISP adddress - assume this is our default gateway
        # XXX: Also assume that we're connected to our ISP within a /24. This
        # assumption seems to hold for BCL...
        ispaddr = "%s/24" % getGatewayIP()
        if len(ispaddr) < 10:
            ispaddr = ""

        # Write out the "infrastructure bits"
        fp.write("""# CRCnet Monitor Autogenerated Nodemap
rurallink "Rural Link Server" 192.107.171.165/28
%s "%s" %s 192.107.171.174/28
""" % (rl_isptype, RL_ISPS[rl_isptype], ispaddr))

        # Write out this (master node)
        ispifname = getISPIfName()
        hostname = socket.gethostname()
        addresses = ""
        for i in getInterfaces():
            if i["name"] == ispifname:
                # Hack the netmask to be a /24 rather than /32 so the map
                # is happy
                parts = i["address"].split("/")
                addresses += "%s/24 " % (parts[0])
            else:
                addresses += "%s " % i["address"]
        fp.write("""%s "%s (Master Node)" %s\n""" % \
            (hostname, hostname, addresses))
        
        # Write out the clients that we have registered
        if ap0_ifname is not None:
            for client in getAssociatedClients(ap0_ifname):
                fp.write(doNodemapClient(client))
                # Check for subclients
                for subclient in getAssociatedSubClients(client["ip"]):
                    fp.write(doNodemapClient(subclient))

        # Close the file
        fp.close()
        remountro("buildNodemapFile")
    except IOError:
        remountro("buildNodemapFile")
        log_error("Could not open nodemap destination for writing!", \
                sys.exc_info())
        return False
    
    return True
     
def doNodemapClient(client):
    """Returns a line suitable for addition to the nodemap

    We include the client's name, the IP address they have configured for
    backhaul and the IP address that they would use as a gateway for their
    internal and AP networks. 

    The Internal and AP networks will only show on the status map if there are
    clients registered on them.
    """
    
    # Backhaul IP
    addresses = "%s/%s " % (client["ip"], 32 - FUNCTION_SHIFT)
    
    # Internal Network
    (network, bits) = generateRLNetwork(int(client["serialno"]), \
            RL_INTERNAL)
    netmask = bitsToNetmask(bits)
    bcast = ipbroadcast(network, netmask)
    addresses += "%s/%s " % (formatIP(bcast-1), bits)
    
    # AP0 Network
    (network, bits) = generateRLNetwork(int(client["serialno"]), \
            RL_AP0)
    netmask = bitsToNetmask(bits)
    bcast = ipbroadcast(network, netmask)
    addresses += "%s/%s " % (formatIP(bcast-1), bits)
    
    # Return the line
    return """%s "%s" %s\n""" % (client["name"], client["name"], addresses)

def getNodeName(ip):
    """Performs an HTTP request to determine the name of the device"""
    conn = None
    
    try:
        conn = httplib.HTTPConnection(ip)
        conn.putrequest('GET', "/rlname")
        conn.endheaders()
        rv = conn.getresponse()
    except:
        (type, value, tb) = sys.exc_info()
        log_error("getNodeName failed to connect to %s: %s" % (ip, value))
        if conn is not None: conn.close()
        return ""

    if rv.status == 200:
        name = rv.read()
        if conn is not None: conn.close()
        return name.strip()

    log_error("getNodeName received an invalid response from %s!" % ip)
    if conn is not None: conn.close()
    return ""

# Client Association Routines
# - Clients are the devices directly connected to this AP
###############################################################################
def getAssociatedClients(ifname):
    """Returns a list of associated clients"""
    clients = []
    
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, ifname), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
        
    for line in lines:
        parts = line.split()
        clients.append({"serialno":parts[0], "name":parts[1], "ip":parts[2], \
                "mac":parts[3]})

    return clients
    
def isClientAssociated(client_serialno, client_name, client_ip):
    """Returns true if the client has successfully associate before"""
    global ap0_ifname
    in_iface = ap0_ifname
    if in_iface is None:
        log_warn("Invalid input interface in isClientAssociated")
        return False
    mac = getNeighbourMAC(client_ip)
    if mac == "":
        log_error("Cannot determinate client MAC in isClientAssociated")
        return False
    
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, in_iface), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        log_error("Could not open %s/%s.assoc to read associations!" % \
                (ASSOC_STORE_DIR, in_iface), sys.exc_info())
        lines = []
        
    for line in lines:
        parts = line.split()
        if int(parts[0]) != int(client_serialno):
            continue
        if parts[2] != client_ip or parts[3] != mac:
            log_info("Mismatched association for (%s) found" % client_name)
            return parts[2]
        log_info("Association for (%s) found" % client_name)
        return parts[1]

    log_info("No association for (%s) found" % client_name)
    return ""

def updateClientAssociation(client_serialno, client_name, client_ip):
    global ap0_ifname
    in_iface = ap0_ifname
    if in_iface is None:
        return False
    mac = getNeighbourMAC(client_ip)
    if mac == "":
        return False
    
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, in_iface), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
    try:
        remountrw("updateClientAssociation")
        fp = open("%s/%s.assoc.tmp" % (ASSOC_STORE_DIR, in_iface), "w")

        for line in lines:
            parts = line.split()
            if int(parts[0]) == int(client_serialno):
                parts[1] = client_name
                parts[2] = client_ip
                parts[3] = mac
                line = "%s\n" % " ".join(parts)
            fp.write(line)
        fp.close()
        os.system("mv %s/%s.assoc.tmp %s/%s.assoc" % \
            (ASSOC_STORE_DIR, in_iface, ASSOC_STORE_DIR, in_iface))
        remountro("updateClientAssociation")
    except IOError:
        remountro("updateClientAssociation")
        log_error("Unable to update client association!", sys.exc_info())
        return False

    log_info("Updated client association details for client #%s (%s)" % \
            (client_serialno, client_name))

    # Update the status map
    if isMasterNode():
        nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)  
        if buildNodemapFile(nm_filename):
            setupStatusMap(nm_filename, socket.gethostname())

    return True

def removeClientAssociation(client_serialno):
    """Removes a particular client association from an interface"""
    global ap0_ifname
    in_iface = ap0_ifname
    if in_iface is None:
        return False

    # Open association file and retrieve list of clients
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, in_iface), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
    
    # Find the client association entry
    client = None
    n=0
    for line in lines:
        parts = line.split()
        if int(parts[0]) == int(client_serialno):
            client = parts
            del lines[n]
            break
        n+=1

    # Already disassociated
    if client is None:
        return True

    # Remove static DHCP entry
    del dhcp[client[3]]
    # Remove routes
    (network, mask) = generateRLNetwork(int(client[0]), RL_NODE)
    delRoute(network, mask, client[2], iface)
    
    # Update the associations
    try:
        remountrw("removeClientAssociation")
        fp = open("%s/%s.assoc.tmp" % (ASSOC_STORE_DIR, in_iface), "w")
        for line in lines:
            fp.write(line)
        fp.close()
        os.system("mv %s/%s.assoc.tmp %s/%s.assoc" % \
                (ASSOC_STORE_DIR, in_iface, ASSOC_STORE_DIR, in_iface))
        dhcp.write()
        remountro("removeClientAssociation")
    except IOError:
        remountro("removeClientAssociation")
        log_error("Unable to update client association!", sys.exc_info())
        return False

    # Tell our parent node this client is no longer registered with us
    if not isMasterNode() and gw_ip != "":
        name = socket.gethostname()
        body = "password=%s&serialno=%s&client_serialno=%s" % \
                (rl_password, rl_serialno, client_serialno)
        conn = httplib.HTTPConnection(gw_ip)
        conn.request("POST", "/unregister_subclient/%s" % name, body)
        rv = conn.getresponse()
        conn.close()        
        if rv.status != 200:
            log_error("Could not notify parent host of subclient dereg!")

    # Check for subclients and remove if necessary
    removeSubclientAssociations(client[2])

    # Update the status map
    if isMasterNode():
        nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)  
        if buildNodemapFile(nm_filename):
            setupStatusMap(nm_filename, socket.gethostname())
    
    # Restart DHCP and Reload Firewall 
    log_command("/etc/init.d/dhcp3-server restart 2>&1")
    log_command("/etc/init.d/firewall start & 2>&1")
    log_info("Removed association for client #%s (%s)" % \
            (client_serialno, client[1]))
    return True

def removeClientAssociations(iface=None):
    """Removes all associated clients from an interface in one foul swoop"""
    
    global rl_masterip, rl_password, ap0_ifname
    
    if iface is None:
        iface = ap0_ifname
    if iface is None:
        return False
    
    # Open association file and retrieve list of clients
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, iface), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
        
    # Get DHCP and routing configuration details
    dhcp = dhcpd_conf()

    # Get rid of each clients association data 
    for line in lines:
        parts = line.split()
        # Remove static DHCP entry
        del dhcp[parts[3]]
        # Remove routes
        (network, mask) = generateRLNetwork(int(parts[0]), RL_NODE)
        delRoute(network, mask, parts[2], iface)

    # Update the association and DHCP configuration
    try:
        remountrw("removeClientAssociations")
        dhcp.write()
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, iface), "w")
        fp.close()
        remountro("removeClientAssociations")
    except IOError:
        remountro("removeClientAssociations")
        log_error("Unable to remove all client associations on %s!" % iface, \
                sys.exc_info())
        return False

    # Restart DHCP and Reload Firewall 
    log_command("/etc/init.d/dhcp3-server restart 2>&1")
    log_command("/etc/init.d/firewall start & 2>&1")
    
    return True

def setupClientAssociation(client_serialno, client_name, client_ip):
    global rl_password, rl_masterip
    
    in_iface = getIfaceForIP(client_ip)
    if in_iface == "":
        return False
    mac = getNeighbourMAC(client_ip)
    if mac == None:
        log_error("Could not determine client's MAC address!")
        return False
    gw_ip = getGatewayIP()
    
    try:
        try:
            remountrw("setupClientAssociation")
            fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, in_iface), "a")
            fp.write("%s %s %s %s\n" % \
                    (client_serialno, client_name, client_ip, mac))
            fp.close()

            # Setup static DHCP entry
            dhcp = dhcpd_conf()
            dhcp[mac] = {"mac":mac, "fixed-address":client_ip, \
                    "name":client_name, \
                    "comment":"Static entry for associated device " \
                    "Serial #: %s" % \
                    client_serialno}
            dhcp.write()
        finally:
            remountro("setupClientAssociation")
    except IOError:
        remountro("setupClientAssociation")
        log_error("Unable to setup client association!", sys.exc_info())
        return False
    
    # POST serial/name to parent device
    doSubClientRegistration(client_name, client_serialno, client_ip)
    
    # add routes
    (network, mask) = generateRLNetwork(int(client_serialno), RL_NODE)
    if not addRoute(network, mask, client_ip, in_iface):
        log_error("Failed to add client networks route for %s (%s)!" % \
                (client_name, client_serialno))

    # Update the status map
    if isMasterNode():
        nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)  
        if buildNodemapFile(nm_filename):
            setupStatusMap(nm_filename, socket.gethostname())

    # Restart DHCP and Reload Firewall 
    log_command("/etc/init.d/dhcp3-server restart 2>&1")
    log_command("/etc/init.d/firewall start & 2>&1")

    return True

def registerClients():
    """Register all our clients with the parent node.

    Called when we've just associated successfully to the parent node
    """
    global rl_password, rl_serialno, ap0_ifname
    iface = ap0_ifname
    if iface is None:
        return False

    gw_ip = getGatewayIP()
    
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, in_iface), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
        
    for line in lines:
        parts = line.split()
        # Register this client with our parent node
        doSubClientRegistration(parts[1], parts[0], parts[2])
        # Check if the client has any subclients and register them
        registerSubClients(parts[2])
    
def initialiseClientRoutes():
    """Setup routes to ensure that we can talk to all clients"""
    global ap0_ifname
    # XXX: There is only one interface that can handle clients atm
    # XXX: But this will need to be extended in future if we have nodes with
    # XXX: 2 APs
    iface = ap0_ifname
    if iface is None:
        return False

    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, iface), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
        
    for line in lines:
        parts = line.split()
        (network, mask) = generateRLNetwork(int(parts[0]), RL_NODE)
        if not addRoute(network, mask, parts[2], iface):
            log_error("Failed to initialise client route for %s (%s)!" % \
                    (parts[1], parts[0]))
        initialiseSubClientRoutes(parts[2])
    
def resetNodeAssociations():
    """Called when the node's password changes

    - Tells the parent node that we're disassociating
    - Removes all client associations
    """
    global rl_masterip
    
    name = socket.gethostname()

    # Tell parent that we're disassociating
    if not isMasterNode() and rl_masterip is not None:
        body = "password=%s&serialno=%s" % \
                (rl_password, client_serialno, client_ip)
        conn = httplib.HTTPConnection(rl_masterip)
        conn.request("POST", "/unregister_client/%s" % name, body)
        rv = conn.getresponse()
        conn.close()        
        if rv.status != 200:
            log_error("Could not notify parent that we were unregistering!")
    # Mark backhaul as not associated
    pref_set("rurallink", "backhaul_assoc", "", getMonitorPrefs())

    # Disassociate all the clients
    removeClientAssociations()

# Sub client Association Routines
# - Sub clients are the clients of this APs directly connected clients
###############################################################################
def getAssociatedSubClients(ip):
    """Returns a list of associated sub clients"""
    subclients = []
    
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, ip), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
        
    for line in lines:
        parts = line.split()
        subclients.append({"serialno":parts[0], "name":parts[1], \
                "ip":parts[2]})

    return subclients

def isSubClientAssociated(client_ip, subclient_serialno, subclient_name, \
        subclient_ip):
    """Returns true if the subclient has been registered"""
    
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, client_ip), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        log_error("Could not read subclient association file!", sys.exc_info())
        lines = []
        
    for line in lines:
        parts = line.split()
        if int(parts[0]) != int(subclient_serialno):
            continue
        if parts[2] != subclient_ip:
            log_info("Mismatched subclient association for (%s) of %s " \
                    "found" % (subclient_name, client_ip))
            return parts[2]
        log_info("Association for subclient (%s) of %s found" % \
                (subclient_name, client_ip))
        return parts[1]

    log_info("Subclient (%s) of %s is not associated" % \
            (subclient_name, client_ip))
    return ""

def updateSubClientAssociation(client_ip, subclient_serialno, \
        subclient_name, subclient_ip):
    
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, client_ip), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
    try:
        remountrw("updateSubClientAssociation")
        fp = open("%s/%s.assoc.tmp" % (ASSOC_STORE_DIR, client_ip), "w")
    
        updated=False
        for line in lines:
            parts = line.split()
            if int(parts[0]) == int(subclient_serialno):
                parts[1] = subclient_name
                parts[2] = subclient_ip
                line = "%s\n" % " ".join(parts)
            fp.write(line)
        fp.close()
        os.system("mv %s/%s.assoc.tmp %s/%s.assoc" % \
                (ASSOC_STORE_DIR, client_ip, ASSOC_STORE_DIR, client_ip))
        remountro("updateSubClientAssociation")
    except IOError:
        remountro("updateSubClientAssociation")
        log_error("Unable to update subclient association!", sys.exc_info())
        return False
    
    # Reload Firewall 
    log_command("/etc/init.d/firewall start & 2>&1")

    # Update the status map
    if isMasterNode():
        nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)  
        if buildNodemapFile(nm_filename):
            setupStatusMap(nm_filename, socket.gethostname())

    return True

def removeSubClientAssociation(client_ip, subclient_serialno):
    """Removes a particular subclient association"""
    global rl_password, rl_serialno
    
    gw_ip = getGatewayIP()

    # Open association file and retrieve list of subclients
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, client_ip), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
    
    # Find the subclient association entry
    subclient = None
    n=0
    for line in lines:
        parts = line.split()
        if int(parts[0]) == int(subclient_serialno):
            subclient = parts
            del lines[n]
            break
        n+=1

    # Already disassociated
    if subclient is None:
        return True
    
    iface = getIfaceForIP(client_ip)
    if iface == "":
        return False
    
    # Tell our parent node this client is no longer registered with us
    if not isMasterNode() and gw_ip != "":
        name = socket.gethostname()
        body = "password=%s&serialno=%s&client_serialno=%s" % \
            (rl_password, rl_serialno, client[0])
        conn = httplib.HTTPConnection(gw_ip)
        conn.request("POST", "/unregister_subclient/%s" % name, body)
        rv = conn.getresponse()
        conn.close()        
        if rv.status != 200:
            log_error("Parent notification failed: Subclient " \
                    "disassociation of %s (@ %s)!" % (client[0], client_ip))

    # Remove routes
    (network, mask) = generateRLNetwork(int(subclient[0]), RL_NODE)
    delRoute(network, mask, client_ip, iface)
    
    # Update the associations
    try:
        remountrw("removeSubclientAssociation")
        fp = open("%s/%s.assoc.tmp" % (ASSOC_STORE_DIR, client_ip), "w")
        for line in lines:
            fp.write(line)
        fp.close()
        os.system("mv %s/%s.assoc.tmp %s/%s.assoc" % \
                (ASSOC_STORE_DIR, client_ip, ASSOC_STORE_DIR, client_ip))
        dhcp.write()
        remountro("removeSubclientAssociation")
    except IOError:
        remountro("removeSubclientAssociation")
        log_error("Unable to remove subclient association!", sys.exc_info())
        return False
    
    # Reload Firewall 
    log_command("/etc/init.d/firewall start & 2>&1")
    
    # Update the status map
    if isMasterNode():
        nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)  
        if buildNodemapFile(nm_filename):
            setupStatusMap(nm_filename, socket.gethostname())

    return True

def removeSubClientAssociations(client_ip):
    """Remove all subclients that were registered against the specified IP

    Called when the node at the specified IP has disassociated
    """
    global rl_password, rl_serialno
    
    gw_ip = getGatewayIP()
    
    # Open association file and retrieve list of subclients
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, client_ip), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
        
    # Remove the association file
    try:
        remountrw("removeSubClientAssociations")
        log_command("/bin/rm -f %s/%s.assoc 2>&1" % \
            (ASSOC_STORE_DIR, client_ip))
    finally:
        remountro("removeSubClientAssociations")
    
    # Go through each associated subclient and unregister it
    for line in lines:
        parts = line.split()
        (network, mask) = generateRLNetwork(int(parts[0]), RL_NODE)
        delRoute(network, mask, client_ip, iface)
        # Tell our parent node this client is no longer registered with us
        if not isMasterNode() and gw_ip != "":
            name = socket.gethostname()
            body = "password=%s&serialno=%s&client_serialno=%s" % \
                (rl_password, rl_serialno, parts[0])
            conn = httplib.HTTPConnection(gw_ip)
            conn.request("POST", "/unregister_subclient/%s" % name, body)
            rv = conn.getresponse()
            conn.close()        
            if rv.status != 200:
                log_error("Parent notification failed: Subclient " \
                        "disassociation of %s (@ %s)!" % (parts[0], client_ip))
    
    # Reload Firewall 
    log_command("/etc/init.d/firewall start & 2>&1")

def setupSubClientAssociation(client_ip, subclient_serialno, \
        subclient_name, subclient_ip):
    global rl_password
    
    iface = getIfaceForIP(client_ip)
    if iface == "":
        return False
        
    try:
        remountrw("setupSubClientAssociation")
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, client_ip), "a")
        fp.write("%s %s %s\n" % \
                (subclient_serialno, subclient_name, subclient_ip))
        fp.close()
        remountro("setupSubClientAssociation")
    except IOError:
        remountro("setupSubClientAssociation")
        log_error("Unable to setup subclient association!", sys.exc_info())
        return False
    
    # Tell parent
    doSubClientRegistration(subclient_name, subclient_serialno, subclient_ip)
    
    # add routes
    (network, mask) = generateRLNetwork(int(subclient_serialno), RL_NODE)
    if not addRoute(network, mask, client_ip, iface):
        log_error("Failed to add subclient networks route for %s (%s)!" % \
                (subclient_name, subclient_serialno))

    # Reload Firewall 
    log_command("/etc/init.d/firewall start & 2>&1")

    # Update the status map
    if isMasterNode():
        nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)  
        if buildNodemapFile(nm_filename):
            setupStatusMap(nm_filename, socket.gethostname())

    return True

def doSubClientRegistration(client_name, client_serialno, client_ip):
    """Sends notification of a subclient to the parent node"""
    global rl_password, rl_serialno
    
    # Master Node's have no-one to notify
    if isMasterNode():
        return True

    # Can't notify if there is no upstream node available
    gw_ip = getGatewayIP()
    if gw_ip == "":
        return False

    # POST serial/name to parent device
    try:
        name = socket.gethostname()
        body = "password=%s&serialno=%s&client_name=%s&client_serialno=%s&" \
                "client_ip=%s" % (rl_password, rl_serialno, client_name, \
                client_serialno, client_ip)
        conn = httplib.HTTPConnection(gw_ip)
        conn.request("POST", "/register_subclient/%s" % name, body)
        rv = conn.getresponse()
        conn.close()
        if rv.status != 200:
            log_error(" Error (%s) notifying parent host of new client - " \
                    "%s!" % (rv.status, rv.reason))
            return False
    except:
        log_error("Failed to notify parent of new client!", sys.exc_info())
        return False

    return True

def registerSubClients(client_ip=None):
    """Register all the subclients of a client with the parent node.

    Called when we've just associated successfully to the parent node
    """
    global rl_password, rl_serialno, ap0_ifname

    if client_ip is None:
        # No client specified, do all clients
        clients = getAssociatedClients(ap0_ifname)
        for client in clients:
            registerSubClients(client["ip"])
        return ""
        
    gw_ip = getGatewayIP()
    
    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, client_ip), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
        
    for line in lines:
        parts = line.split()
        # Register this subclient with our parent node
        doSubClientRegistration(parts[1], parts[0], parts[2])
        
    return ""

def initialiseSubClientRoutes(client_ip):
    """Setup routes to ensure that we can talk to all subclients"""

    iface = getIfaceForIP(client_ip)

    try:
        fp = open("%s/%s.assoc" % (ASSOC_STORE_DIR, client_ip), "r")
        lines = fp.readlines()
        fp.close()
    except IOError:
        lines = []
        
    for line in lines:
        parts = line.split()
        (network, mask) = generateRLNetwork(int(parts[0]), RL_NODE)
        if not addRoute(network, mask, client_ip, iface):
            log_error("Failed to initialise subclient route for %s (%s)!" % \
                    (parts[1], parts[0]))

# Traffic Management 
##############################################################################
def readTrafficUsers():
    """Loads the list of users from the password file"""

    passwdfile =  config_get("traffic", "passwd_file", \
            DEFAULT_TRAFFIC_PASSWD_FILE)
    
    users = {}
    
    fp = open(passwdfile, "r")
    i=0
    for line in fp.readlines():
        parts = line.strip().split(":")
        i+=1
        if (len(parts)!=3):
            log_warning("Skipping invalid line (%d) in password file!" % i)
            continue
        if parts[2]=="t":
            s = True
        else:
            s = False
        # Store the user
        users[parts[0]] = {"username":parts[0],"passwd":parts[1],"enabled":s}
    fp.close()

    return users
        
def writeTrafficUsers():
    """Writes the list of users from the array to the password file"""
    global rl_trafficusers
    
    passwdfile =  config_get("traffic", "passwd_file", \
            DEFAULT_TRAFFIC_PASSWD_FILE)
    
    try:
        remountrw("writeTrafficUsers")
        fp = open(passwdfile, "w")
        for username, user in rl_trafficusers.items():
            line = "%s:%s:%s\n" % (username, user["passwd"], \
                    user["enabled"] and "t" or "f")
            fp.write(line)
        fp.close()
    finally:
        remountro("writeTrafficUsers")
        
def checkFirewall():
    """Checks that the firewall is correctly loaded and running"""

    fw_start = """<a href="/traffic/firewall/start">[Start Firewall]</a>"""
    fw_stop = """<a href="/traffic/firewall/stop">[Stop Firewall]</a>"""
    
    # Check for the fw-in, fw-out, fw-forward chains in the filter table
    # if these are loaded we assume that the firewall script has been started
    if getChainRules("fw-in") is None:
        return ("critical", "Firewall is not running", fw_start)
    if getChainRules("fw-out") is None:
        return ("critical", "Firewall is not running", fw_start)
    if getChainRules("fw-forward") is None:
        return ("critical", "Firewall is not running", fw_start)

    # Seems ok
    return ("ok", "Firewall running", fw_stop)

def doFirewall(mode):
    """Sets the firewall to the specified mode"""

    if mode not in ["start", "stop", "reload"]:
        raise ccs_rurallink_error("Unknown firewall mode!")
    if mode == "reload":
        mode = "start"
    
    # Try and do it
    if log_command("/etc/init.d/firewall %s 2>&1" % mode) == None:
        return True

    return False
    
def isAllowed(ip_address):
    """Returns true if the captive portal is currently allowing the IP"""

    # Find which interface the user will be coming in from
    iface = getIfaceForIP(ip_address)
    
    # Check the the necessary pre-routing chain exists and is setup for
    # captive-portalling
    rules = getChainRules("%s-prerouting-in" % iface, "nat") 
    if rules is None:
        log_warn("Cannot check status of %s (%s). %s-prerouting-in is bad!" % \
                (ip_address, username, iface))
        return False
    
    # Look for the IP in the source field
    for rule in rules:
        if rule["source"] == ip_address and rule["target"]=="ACCEPT":
            return True
        
    # Not found
    return False

def removeAllowRule(ip_address):
    """Removes an IP address from the captive portals allow list"""
    global rl_trafficusers
    
    # Do final traffic accounting
    updatetraffic()
    
    # Find which interface the user will be coming in from
    iface = getIfaceForIP(ip_address)

    # Remove from pre-routing
    log_command("/sbin/iptables -D %s-prerouting-in -t nat -s %s/32 " \
                "-j ACCEPT 2>&1" % (iface, ip_address))

    # Remove from forward
    log_command("/sbin/iptables -D %s-forward-in -s %s/32 " \
                "-j fw-forward-out 2>&1" % (iface, ip_address))

    # Remove from accounting
    log_command("/sbin/iptables -D accounting -s %s/32 -j RETURN 2>&1" % \
        ip_address)
    log_command("/sbin/iptables -D accounting -d %s/32 -j RETURN 2>&1" % \
        ip_address)
    
    # Remove from user record
    for username, user in rl_trafficusers.items():
        if user["ip"] == ip_address:
            user["ip"] = None
    
    log_info("Internet Access disabled for %s" % (ip_address))
    return True

def addAllowRule(ip_address, username):
    """Adds the specified IP address to teh captive portals allow list

    This is called once the user has authenticated to allow them to access the
    Internet.
    """
    global rl_trafficusers

    # Check whether the user is already logged in from another IP and 
    # log them out if they are
    if rl_trafficusers[username]["ip"] is not None:
        removeAllowRule(ip_address)
        
    # Find which interface the user will be coming in from
    iface = getIfaceForIP(ip_address)

    # Check the the necessary pre-routing chain exists and is setup for
    # captive-portalling
    rules = getChainRules("%s-prerouting-in" % iface, "nat") 
    if rules is None:
        log_warn("Cannot allow %s (%s) on %s. No chain!" % \
                (ip_address, username, iface))
        return False

    # Last rule will be a redirect if we are captive portalling
    if rules[len(rules)-1]["target"] != "REDIRECT":
        log_error("Cannot allow %s (%s) on %s. No redirect rule!" % \
                (ip_address, username, iface))
        return False
    
    # The first three rules should be RFC1918 allows
    for i in range(0,3):
        if rules[i]["target"] != "ACCEPT":
            log_error("Cannot allow %s (%s) on %s. Missing ACCEPT on a " \
                    "RFC1918 rule!" % (ip_address, username, iface))
            return False
        if rules[i]["destination"] not in RFC1918:
            log_error("Cannot allow %s (%s) on %s. Initial rule (%s)" \
                    "is not RFC1918!" % \
                    (ip_address, username, iface, rules[i]["destination"]))
            return False

    # All good, insert into position 4 in the chain, ie. after RFC1918 rules
    if log_command ("/sbin/iptables -I %s-prerouting-in 4 -t nat -s %s/32 " \
            "-j ACCEPT 2>&1" % (iface, ip_address)) != None:
        # Failed to add rule
        log_error("Failed to add allow rule for %s (%s) on %s-prerouting!" % \
                (ip_address, username, iface))
        return False
    
    # And the same for the forward chain at postion 5 as there is an extra
    # macfilter rule at the start of this chain
    # XXX: Macfilter is disabled as of r832 so use position 4, the firewall
    # contains provision for macfilter to be re-enabled as an option in future
    # so this may need some more work
    if log_command("/sbin/iptables -I %s-forward-in 4 -s %s/32 " \
            "-j fw-forward-out 2>&1" % (iface, ip_address)) != None:
        # Failed to add rule
        log_error("Failed to add allow rule for %s (%s) on %s-forward!" % \
                (ip_address, username, iface))
        # Try and re-enable the captive portal for the user!
        log_command("/sbin/iptables -D %s-prerouting-in -t nat -s %s/32 " \
                "-j ACCEPT &>/dev/null 2>&1" % (iface, ip_address))
        return False

    # Setup accounting entries
    if log_command("/sbin/iptables -A accounting -s %s/32 -j RETURN 2>&1 && " \
            "/sbin/iptables -A accounting -d %s/32 -j RETURN 2>&1" % \
            (ip_address, ip_address)) != None:
        # Failed to add rule
        log_warn("Failed to initialise accounting for %s @ %s!" % \
                (username, ip_address))
        
    # Record IP against this user for accounting 
    rl_trafficusers[username]["ip"] = ip_address
    
    log_info("Internet Access enabled for %s @ %s" % (username, ip_address))
    return True

@registerRecurring(TRAFFIC_UPDATE_INTERVAL)
def updatetraffic():
    """Called regularly to read the appropriate traffic information"""
    global rl_trafficusers
    
    ifaces = getInterfaceNames()
    
    # Check for host specific rules in the accounting chain
    rules = getChainRules("accounting")
    if rules is None:
        return
    # Collect stats
    for rule in rules:
        # Can't do any traffic if you were denied!
        if rule["target"] != "RETURN":
            continue
        # Skip non-host rules
        source = rule["source"].split("/")[0]
        dest = rule["destination"].split("/")[0]
        if rule["source"].find("/") != -1 and \
                cidrToLength(rule["source"])!=32:
            if rule["destination"].find("/") != -1 and \
                    cidrToLength(rule["destination"])!=32:
                # Neither source or destination are a host 
                continue
            else:
                ip_address = dest
        else:
            ip_address = source
        # Try and find the user associated with this host
        for username, user in rl_trafficusers.items():
            if user["ip"] == ip_address:
                user["traffic"] += int(rule["bytes"])
                break

    # Zero the chain
    log_command("/sbin/iptables -Z accounting &>/dev/null")
        
class CaptivePortalHandler(BaseHTTPRequestHandler):

    pages = {}
    dirs = {}
    realms = {}
    
    def __init__(self, request, client_address, server):
        self.cookies = {}
        self.cookie_names = []
        self.username = ""
        # Call base handler
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def findIfaceIP(self, client_ip):
        """Returns the IP address of the interface this client uses

        We assume that we don't have assymetric routing and that the iface
        that we would talk to the client on is the same as the packet is
        received from.
        """
    
        ip = getIfaceIPForIP(client_ip)
        if ip == "":
            # Uh-oh, just return HTTP Host!
            return self.headers.get("Host").strip()
    
        return ip

    def getPostData(self):
        """Returns a dictionary of posted variables"""

        vars = {}

        data = self.rfile.read(int(self.headers["content-length"]))
        for pair in data.split("&"):
            parts = pair.split("=")
            if len(parts)<2:
                continue
            vars[parts[0]] = parts[1]

        return vars
                
    def authSuccess(self, url):

        host = self.headers.get("Host").strip()
        output = """<div class="content"><h2>Access Granted</h2>
<br />
Thank you, your username and password have been accepted and you now have
access to the Internet.<br />
<br />
<b>NOTE:You must return to this website (<a href="http://%s/">http://%s/</a>) 
when you have finished using the computer to end your Internet session. If you
do not end your Internet session you may be liable for all bandwidth charges
incurred until your session is ended.</b><br />
<br />
<br />
<a href="%s">Click here to continue on to %s &gt;&gt;</a><br />
<br />
""" % (host, host, url, url)

        returnPage(self, "Access Granted", output)
        
    def logoutSuccess(self):

        host = self.headers.get("Host").strip()
        output = """<div class="content"><h2>Session Ended</h2>
<br />
Thank you, your Internet session has been ended. You may now close the
web browser.<br />
<br />
"""

        returnPage(self, "Session Ended", output)

    def authRequired(self, message, back):
    
        if message != "":
            message = "<br /><span class=\"error\"><b>ERROR:</b> %s</span>" \
                    "<br />" % message

        # Determine the captive-portal host the user should submit to
        url = "http://%s:%s" % \
                (self.findIfaceIP(self.client_address[0]), \
                self.server.server_port)
        
        output = """<div class="content"><h2>Authentication Required</h2>
<br />
Authentication is required before you can access the Internet. Please enter
your username and password below.<br />
%s
<br />
<form method="POST" action="%s/captive-portal">
<input type="hidden" name="back" value="%s" />
<table>
<tr>
<th width="20%%">Username</th>
<td><input type="input" value="" name="username"></td>
</tr>
<tr>
<th width="20%%">Password</th>
<td><input type="password" value="" name="password"></td>
</tr>
<tr>
<td>&nbsp;</td>
<td><input type="submit" value="Enable Internet Access &gt;&gt;"></td>
</tr>
</table>
""" % (message, url, back)

        returnPage(self, "Authentication Required", output)
        
    def handleAuthenticated(self):
        global rl_trafficusers

        # Determine the captive-portal host the user should submit to
        url = "http://%s:%s" % \
                (self.findIfaceIP(self.client_address[0]), \
                self.server.server_port)

        # How much traffic has the user done?
        datastr = "an unknown amount"
        for username, user in rl_trafficusers.items():
            if user["ip"] != self.client_address[0]:
                continue
            # Found user
            datastr = formatBytes(user["traffic"])
            break
        
        output = """<div class="content"><h2>Session Active</h2>
<br />
Your Internet session is currently active and you should have no problems
browsing websites.<br />
<br />
You have transferred <b>%s</b> of data.<br />
<br />
If you would like to end your Internet session please click the button below.
<br /><br />
<form method="POST" action="%s/captive-portal">
<input type="hidden" name="logout" value="yes" />
<table>
<tr>
<td>&nbsp;</td>
<td><input type="submit" value="Logout (End Internet Session) &gt;&gt;"></td>
</tr>
</table>
""" % (datastr, url)

        returnPage(self, "Authentication Required", output)
        
    def handleRequest(self, method):
        """Looks to see if we know how to handle the path and passes it off"""
        global rl_trafficusers
        
        # Handle static directories from the real webserver
        #########################################################
        dirname = os.path.dirname(self.path)
        if dirname in CCSDHandler.dirs.keys():
            # Try and send the file back
            filename = os.path.basename(self.path)
            data = ""
            try:
                fp = open("%s/%s" % (CCSDHandler.dirs[dirname], filename), "r")
                data = fp.read()
                fp.close()
            except:
                self.send_error(404, "The specified resource does not exist!")
                return
            length = len(data)
            self.send_response(200)
            self.send_header("Length", length)
            self.end_headers()
            self.wfile.write(data)
            return
        
        # Handled POSTed authentication data
        #########################################################
        if self.path.startswith("/captive-portal") and method == "POST":
            data = self.getPostData()
            # Logout
            if "logout" in data.keys() and data["logout"]=="yes":
                removeAllowRule(self.client_address[0])
                self.logoutSuccess()
                return
            # Verify authentication
            back = ""
            if "back" in data.keys():
                back = urllib.unquote(data["back"])
            if "username" not in data.keys() or "password" not in data.keys():
                # No auth data present
                self.authRequired("Invalid authentication request!", back)
                return
            if data["username"] not in rl_trafficusers.keys():
                # Invalid Username 
                self.authRequired("Invalid username or password!", back)
                return
            passwd = rl_trafficusers[data["username"]]["passwd"]
            if crypt.crypt(data["password"], passwd) != passwd:
                # Invalid password
                self.authRequired("Invalid username or password!", back)
                return
            if not rl_trafficusers[data["username"]]["enabled"]:
                # Account disabled
                self.authRequired("Your account is disabled!", back)
                return
            
            # Success - Enable Firewall
            if not addAllowRule(self.client_address[0], data["username"]):
                self.authRequired("An error occured while trying to " \
                        "enable your Internet access. Please try again " \
                        "shortly.", "")
                return
            
            # Tell the user
            if back == "": back = "http://www.google.com/"
            self.authSuccess(back)
            return

        # Status Query 
        #########################################################
        if self.path.startswith("/captive-portal-status"):
            if isAllowed(self.client_address[0]):
                datastr = "unknown 0"
                for username, user in rl_trafficusers.items():
                    if user["ip"] != self.client_address[0]:
                        continue
                    # Found user
                    datastr = "%s %s" % \
                            (username, formatBytes(user["traffic"]))
                    break
                data = "OK - %s" % datastr
                self.send_response(200)
            else:
                data = "AUTHENTICATION REQUIRED"
                self.send_error(403, "Authentication required")
            self.send_header("Length", len(data))
            self.end_headers()
            self.wfile.write(data)
            self.finish()
            return

        # Check for an already authenticated user
        #########################################################
        if isAllowed(self.client_address[0]):
            self.handleAuthenticated()
            return

        # Send a 403 if the request is coming from crcnet-monitor
        #########################################################
        useragent = self.headers.get("User-agent").strip()
        if useragent.find("crcnet-monitor") != -1:
            self.send_error(403, "Authentication required")
            self.end_headers()
            self.finish()
            return
        
        # Send the Login Required form
        #########################################################
        back = ""
        if not self.path.startswith("/captive-portal"):
            back = "http://%s%s" % \
                    (self.headers.get("Host").strip(), self.path)
        self.authRequired("", back)
        return
    
    def do_GET(self):
        return self.handleRequest("GET")
    def do_POST(self):
        return self.handleRequest("POST")
            
    # No logging for now
    def log_error(self, *args):
        pass
    def log_request(self, code='-', size='-'):
        pass

def getChainRules(chain, table="filter"):
    """Returns all the rules for the specified chain in the table"""

    rules = []
    
    fh = os.popen("/sbin/iptables --line-numbers -nxvL %s -t %s" % \
            (chain, table))
    output = fh.readlines()
    rv = fh.close()
    if rv != None :
        output = "".join(output)
        if len(output) > 0: log_debug("iptables output:\n%s" % output)
        # Chain probably doesn't exit
        return None

    # Parse each line and store it, first line is chain name
    names = output[1].split() # second line is headers
    names.append("extra")
    for line in output[2:]: # data starts on the third line
        parts = line.split()
        if len(parts) > len(names):
            pmax = len(names)-1
            parts[pmax] = " ".join(parts[pmax:])
            parts = parts[:len(names)]
        obj = dict(zip(names, parts))
        rules.append(obj)

    return rules

# ISP 
##############################################################################
def checkBCLPeerFile():
    """Checks whether the PPP peers file for the BCL connection exists.

    If it does not it is created from a default.
    """

    if os.path.exists(BCL_CONF):
        return True

    # Need to create the default
    try:
        remountrw("checkBCLPeerFile")

        fp = open(BCL_CONF, "w")
        fp.write("""# CRCnet-monitor created PPPoE configuration for BCL
#        
# See the manual page pppd(8) for information on all the options.
#

# The BCL module of crcnet-monitor will keep this line up to date
user default

# PPPoE
pty "/usr/sbin/pppoe -I int -T 80 -m 1452"

# Connection Settings
noipdefault
usepeerdns
defaultroute

# Default PPP settings
hide-password
lcp-echo-interval 20
lcp-echo-failure 3
connect /bin/true
noauth
persist
maxfail 0
holdoff 5
mtu 1492
noaccomp
default-asyncmap
""")
        fp.close()
        
    finally:
        remountro("checkBCLPeerFile")
        
    # Check whether we succeeded or not
    if os.path.exists(BCL_CONF):
        return True
    return False

def updateBCL(user, passwd):
    # Do filesystem manipulation
    try:
        # Remount RW so we can write to files
        remountrw("updateBCL")
        # Check whether the files exists
        checkBCLPeerFile()
        ensureFileExists(PAP_SECRETS)
        # Update the username in the PPP options file
        if not filterFile("^user.*$", "user %s" % user, BCL_CONF):
            raise ccs_rurallink_error("Unable to set username!")
        # Update the username / password in pap-secrets
        if not filterFile("^\"%s\".*$" % user, "\"%s\"\t*\t\"%s\"" % \
                (user, passwd), PAP_SECRETS):
            # Couldn't replace username/password, append new
            # XXX: This will leave the old username/password in the
            # pap-secrets file 
            if not appendFile("\"%s\"\t*\t\"%s\"\n" % \
                    (user, passwd), PAP_SECRETS):
                raise ccs_rurallink_error("Unable to set password!")
        # Ensure that there is an interfaces file entry for the BCL connection
        ifaces = debian_interfaces()
        ifaces[ISP_BCL] = {"name":ISP_BCL, "family":"inet", "method":"ppp", \
                "auto":True, "provider":ISP_BCL}
        ifaces.write()
        log_info("BCL authentication credentials updated")
    finally:
        # Make sure we don't leave the FS read-write
        remountro("updateBCL")

    # Success
    return True

def getBCLUser():
    """Returns the username that is currently configured for BCL access"""

    # Open file and read all lines
    try:
        fp = open(BCL_CONF, "r")
    except:
        fp = False
    if not fp:
        return "<i>No username configured</i>"
    lines = fp.readlines()
    fp.close()
    
    # Find the user line
    for line in lines:
        if re.match("^user.*$", line) is None:
            continue
        # User line found
        parts = line.split()
        if len(parts) != 2:
            return "<i>Unable to read username</i>"
        return parts[1]
        
    return "<i>No username configured</i>"

def connectBCL():
    """Tried to bring up the BCL internet connection"""
    
    ifname = getISPIfName()
    if log_command("/sbin/ifup %s 2>&1" % ifname) is None:
        return "warning", \
            "Connecting... <span id=\"rem\">30</span>s remaining.", \
            ISP_IF_RELOAD
    else:
        return "critical", "BCL connection attempt failed.", ISP_IF_CONNECT
    
def disconnectBCL():
    """Tries to bring down the BCL internet connection"""
    
    ifname = getISPIfName()
    if log_command("/sbin/ifdown %s 2>&1; poff 2>&1" % ifname) is None:
        return "ok", \
            "Disconnecting... <span id=\"rem\">30</span>s remaining.", \
            ISP_IF_RELOAD
    else:
        stat = getISPStatus()
        return stat[2:]

def getBCLStatus():
    """Returns the status of the BCL internet connection"""
    
    gwstatus, gwtext = getISPGatewayStatus()
    ifname = getISPIfName()

    if gwstatus == "ok":
        ifstatus = "ok"
        iftext = "Connected"
        ifaction = ISP_IF_DISCONNECT
    else:
        # Default gateway is not ok. Iface probably isn't either
        ifaces = getInterfaces(returnOne=ifname)
        ifstatus = ""
        for iface in ifaces:
            if iface["name"] != ifname:
                continue
            # ISP Interface
            if iface["up"]:
                ifstatus = "ok"
                iftext = "Connected - %s" % iface["address"]
                ifaction = ISP_IF_DISCONNECT
            else:
                ifstatus = "warning"
                iftext = "Disconnected"
                ifaction = ISP_IF_CONNECT
            break
        if ifstatus == "":
            ifstatus = "critical"
            iftext = "Disconnected"
            ifaction = ISP_IF_CONNECT

    return (gwstatus, gwtext, ifstatus, iftext, ifaction)

def getDSLAdminPassword():
    """Returns the admin password for a DSL device connected to this CPE
        
    The admin password is the last 8 characters of an MD5 hash generated from
    the mac address of the internal interface of this CPE.
    """
    global int_ifname
    
    if int_ifname is None:
        raise ccs_rurallink_error("DSL password cannot be generated " \
            "without an internal interface!")
    ifaces = getInterfaces(returnOne=int_ifname)
    if len(ifaces) != 1:
        raise ccs_rurallink_error("Could not find internal interface to " \
            "generate DSL password from!")
    mac = ifaces[0]["mac"].lower()
    return md5(mac).hexdigest()[-8:]
    
def DSLLogin():
    """Attempts to login to the DSL modem via telnet

    Tries the password that a modem attached to this device should be using
    before falling back to the default admin/admin
    """
    
    # Possible return strings from a login attempt
    login_regexps = ["login:", "\$"]

    if not isHostUp(DSL_MODEM_IP):
        raise ccs_rurallink_error("Unable to contact DSL modem!")
    
    conn = Telnet(DSL_MODEM_IP)
    
    # Wait for the login prompt
    r = conn.read_until("login:", DSL_TELNET_TIMEOUT)
    if not r.endswith("login:"):
        log_debug("DSL Modem: Unexpected string upon connect\n%s" % r)
        conn.close()
        raise ccs_rurallink_error("Could not login to DSL modem. " \
            "Unexpected string!")
    
    for password in [getDSLAdminPassword(), "admin"]:
        # Send the admin username
        conn.write("admin\n")
        
        # Wait for the password prompt
        r = conn.read_until("password:", DSL_TELNET_TIMEOUT)
        if not r.endswith("password:"):
            log_debug("DSL Modem: Unexpected string after sending " \
                "username\n%s" % r)
            conn.close()
            raise ccs_rurallink_error("Could not login to DSL modem. " \
                "Unexpected string!")
        
        # Send the password
        conn.write("%s\n" % password)
        
        # Wait for the appropriate prompt
        index, match, text = conn.expect(login_regexps, DSL_TELNET_TIMEOUT)
        if index == -1:
            log_debug("DSL Modem: Unexpected error after sending " \
                "password\n%s" % text)
            conn.close()
            raise ccs_rurallink_error("Could not login to DSL modem. " \
                "Unexpected string!")
        if index == 1:
            # Logged in successfully
            return conn
        
    # Could not login
    conn.close()
    return None
    
def updateDSL(username, password):
    """Connects to the DSL modem and updates the username/password

    Currently we only support the D-Link DSL-504T and DSL-302G modems
    and we assume they are in their factory default configuration before
    we talk to them. E.g. The modem is at 10.1.1.1
    """
    
    # Try and configure the DSL modem if necessary
    if not DSLModemConfigured():
        configureDSLModem()

    conn = DSLLogin()
    if conn is None:
        raise ccs_rurallink_error("Unable to login to DSL modem!")
      
    # Update the username and password
    conn.write("modify ppp security ifname ppp-0 login %s passwd %s\n" % \
        (username, password))
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)

    if r.find("Set Done") == -1:
        conn.close()
        raise ccs_rurallink_error("Failed to update modem auth details!")         
    # Commit the changes
    conn.write("commit\n")
    conn.close()
    
    log_info("DSL authentication credentials updated")
    
    return True

def getDSLUser():
    """Retrieves the currently configured user on the DSL modem"""
    
    conn = None
    try:
        conn = DSLLogin()
    except:
        pass
    if conn is None:
        return "<i>Could not connect to DSL modem</i>"

    # Ask for the auth credentials
    conn.write("get ppp security ifname ppp-0\n")
    
    # Wait for the prompt
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    conn.close()
    
    # Try and extract the login name out of the response
    lines = r.strip().split("\n")
    for line in lines:
        if line.strip().startswith("Login"):
            try:
                return line.split(":")[1].strip()
            except:
                return "<i>Unable to read username</i>"
                
    # Not found
    return "<i>No username configured</i>"
    
def getDSLNameservers():
    """Retrieves the ISP allocated nameservers"""
    dns1 = None
    dns2 = None
    conn = None
    try:
        conn = DSLLogin()
    except:
        pass
    if conn is None:
        return None, None

    # Ask for the DHCP server configuration details
    conn.write("get dhcp server cfg\n")
    
    # Wait for the prompt
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    conn.close()
        	
    # Extract DHCP server addresses
    lines = r.strip().split("\n")
    for line in lines:
        if line.strip().startswith("Def Pri"):
            try:
                parts = line.split(":")
                dns1 = parts[1].split()[0].strip()
                dns2 = parts[2].strip()
            except:
                log_error("Could not parse DNS servers from DSL modem!")
                log_debug(line.strip())
            break
    if dns1 == "0.0.0.0": dns1 = None
    if dns2 == "0.0.0.0": dns2 = None

    # Return them
    return dns1, dns2

def connectDSL():
    """Tells the modem to connect"""

    # Try and configure the DSL modem if necessary
    if not DSLModemConfigured():
        configureDSLModem()
        
    conn = DSLLogin()
    if conn is None:
        return "critical", "Unable to login to DSL modem!", ISP_IF_CONNECT

    # Send the command
    conn.write("modify ppp intf ifname ppp-0 start\n")
    
    # Wait for the prompt
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    conn.close()

    if r.find("Set Done") == -1:
        return "critical", "DSL modem failed to connect!", ISP_IF_CONNECT

    return "warning", "Connecting... <span id=\"rem\">30</span>s remaining.", \
        ISP_IF_RELOAD
        
def disconnectDSL():
    """Tells the modem to disconnect"""

    conn = DSLLogin()
    if conn is None:
        return "critical", "Unable to login to DSL modem!", ISP_IF_CONNECT

    # Send the command
    conn.write("modify ppp intf ifname ppp-0 stop\n")
    
    # Wait for the prompt
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    conn.close()

    if r.find("Set Done") == -1:
        return "critical", "DSL modem failed to disconnect!", ISP_IF_DISCONNECT

    return "warning", \
        "Disconnecting... <span id=\"rem\">30</span>s remaining.", \
        ISP_IF_RELOAD
        
def getDSLStatus():
    """Returns the status of the DSL internet connection"""
    
    gwstatus, gwtext = getISPGatewayStatus()

    # Check we can talk to the DSL modme
    if not isHostUp(DSL_MODEM_IP):
        return gwstatus, gwtext, "critical", "DSL Modem disconnected", ""

     # Try and configure the DSL modem if necessary
    if not DSLModemConfigured():
        return gwstatus, gwtext, "critical", "DSL Modem unconfigured", ""
   
    conn = DSLLogin()
    if conn is None:
        return gwstatus, gwtext, "critical", \
            "Unable to login to DSL modem!", ISP_IF_CONNECT
    
    # Check if DSL is up... look for the AAL interface first
    conn.write("get interface stats ifname aal5-0\n")
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    m = re.search("Operational Status.*:(.*)\n", r)
    if m is None or len(m.groups())==0:
        log_error("Could not retrieve aal5-0 status from DSL modem")
    else:
        status = m.groups()
        if status[0].strip() == "Down":
            # No DSL connection
            conn.close()
            return gwstatus, gwtext, "critical", "No DSL signal", ""
        # DSL is up

    # Check if PPP is up
    conn.write("get interface stats ifname ppp-0\n")
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    m = re.search("Operational Status.*:(.*)\n", r)
    if m is None or len(m.groups())==0:
        log_error("Could not retrieve ppp-0 status from DSL modem")
    else:
        status = m.groups()
        if status[0].strip() == "Down":
            # No PPP connection
            conn.close()
            return gwstatus, gwtext, "warning", "Disconnected", ISP_IF_CONNECT

    # PPP is up, should all be OK
    return gwstatus, gwtext, "ok", "Connected", ISP_IF_DISCONNECT
    
def getDSLGatewayIP():
    """Returns the default gateway being used by the DSL modem"""
    
    conn = None
    try:
        conn = DSLLogin()
    except:
        pass
    if conn is None:
        return ""
        
    # Get the DSL Modems route table
    conn.write("get ip route\n")
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    conn.close()
    
    # Parse the table
    lines = r.split("\n")
    for line in lines[2:]:
        parts = line.strip().split()
        if parts[0] == "0.0.0.0":
            return parts[2].strip()
    
    return ""

def DSLModemConfigured():
    """Checks whether the DSL modem is configured for RuralLink use"""
    
    conn = None
    try:
        conn = DSLLogin()
    except:
        pass
    if conn is None:
        return False
    
    # Look for "RuralLink" in the vendor string
    conn.write("get system\n")
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    conn.close()
    
    if r.find(": RuralLink") != -1:
        return True

    return False
    
def configureDSLModem():
    """Updates the DSL modems configuration to bend it to our will..."""
    global rl_serialno
    
    conn = DSLLogin()
    if conn is None:
        raise ccs_rurallink_error("Unable to login to DSL modem!")

    # Turn off the DHCP server
    conn.write("modify dhcp server cfg disable\n")
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    if r.find("Set Done") == -1:
        log_error("Failed to disable DHCP server on DSL modem")
        log_debug("%s" % r)

    # Pass SSH traffic through to our server on port 2001
    conn.write("create nat rule entry ruleid 2 rdr destportfrom num 2001 " \
        "destportto num 2001 lcladdrfrom %s lcladdrto %s\n" % \
        (DSL_CPE_IP, DSL_CPE_IP))
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    if r.find("Entry Created") == -1:
        log_error("Failed to setup SSH pinhole on DSL modem")
        log_debug("%s" % r)
        
    # Add route to the wireless network
    conn.write("create ip route ip %s mask %s gwyip %s\n" % \
        (RL_BASE_S, RL_MASK_S, DSL_CPE_IP))
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    if r.find("Entry Created") == -1:
        log_error("Failed to setup wireless network route on DSL modem")
        log_debug("%s" % r)

    # Configure the password
    password = getDSLAdminPassword()
    auth=False
    conn.write("passwd\n")
    for oldpass in [password, "admin"]:
        r = conn.read_until("Old Password:", DSL_TELNET_TIMEOUT)
        if not r.endswith("Old Password:"):
            log_debug("DSL Modem: Unexpected string after sending " \
                "password change request\n%s" % r)
            break
        # Send the password
        conn.write("%s\n" % oldpass)
        # Wait for the appropriate prompt
        index, match, text = conn.expect(["Error:", "New Password:"], \
            DSL_TELNET_TIMEOUT)
        if index == -1:
            log_debug("DSL Modem: Unexpected error after sending " \
                "password\n%s" % text)
            break
        if index == 1:
            # Logged in successfully
            auth = True
            break
        else:
            # Gobble 
            conn.read_until("$")
            conn.write("passwd\n")

    if auth:
        # Change the password
        conn.write("%s\n" % password)
        r = conn.read_until("New Password:", DSL_TELNET_TIMEOUT)
        if not r.endswith("New Password:"):
            log_error("Failed to set new DSL modem password")
            log_debug("DSL Modem: Unexpected string after sending " \
                "new password\n%s" % r)
        else:
            conn.write("%s\n" % password)
            r = conn.read_until("$", DSL_TELNET_TIMEOUT)
            if r.find("Set Done") == -1:
                log_error("Failed to change DSL modem password")
                log_debug("%s" % r)

    # Configure the device name 
    conn.write("modify system name \"rl-dsl-%s\"\n" % rl_serialno)
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    if r.find("Set Done") == -1:
        log_error("Failed to modify system name on DSL modem")
        log_debug("%s" % r)
    conn.write("modify system contact \"help@rurallink.co.nz\"\n")
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    if r.find("Set Done") == -1:
        log_error("Failed to modify system contact on DSL modem")
        log_debug("%s" % r)
    conn.write("modify system vendor \"RuralLink\"\n")
    r = conn.read_until("$", DSL_TELNET_TIMEOUT)
    if r.find("Set Done") == -1:
        log_error("Failed to modify vendor on DSL modem")
        log_debug("%s" % r)
    
    # Commit the changes
    conn.write("commit\n")
    conn.close()

    return True

def connectETH():
    """Tells the internal interface which is used for backhaul to connect"""
    global int_ifname
    
    # Try and configure the DSL modem if necessary
    if not ETHBackhaulConfigured():
        configureETHBackhaul()
        
    # Take interface down
    log_command("/sbin/ifdown %s 2>&1" % int_ifname)

    # Then bring it back up
    log_command("/sbin/ifup %s 2>&1" % int_ifname)

    return "warning", "Connecting... <span id=\"rem\">30</span>s remaining.", \
        ISP_IF_RELOAD
        
def disconnectETH():
    """Tells the internal interface which is used for backhaul to disconnect"""
    global int_ifname
    
    # Essentially a NOP, removing the ethernet interface is a bad idea
    return "warning", "Cannot disconnect internal ethernet interface!", ""
        
def getETHStatus():
    """Returns the status of the Ethernet backhaul connection"""
    global int_ifname, rl_serialno
    
    gwstatus, gwtext = getISPGatewayStatus()

     # Try and configure the DSL modem if necessary
    if not ETHBackhaulConfigured():
        return gwstatus, gwtext, "critical", \
                "Ethernet backhaul unconfigured", ISP_IF_CONNECT
   
    # Is the interface up
    ifaces = getInterfaces(returnOne=int_ifname)
    if len(ifaces) != 1:
        return gwstatus, gwtext, "critical", \
                "Cannot find Ethernet backhaul interface", ""
    iface = ifaces[0]
    if not iface["up"]:
        return gwstatus, gwtext, "critical", "Ethernet backhaul down", \
                ISP_IF_CONNECT
                
    # Retrieve ethernet details
    ethmode = pref_get("rurallink", "ethmode", getMonitorPrefs(), "dhcp")
    ethip = pref_get("rurallink", "ethip", getMonitorPrefs(), "")
    ethnetmask = pref_get("rurallink", "ethnetmask", getMonitorPrefs(), "")
                
    # Is it configured right?
    if ethmode == "dhcp":
        # Retrieve the IP pump says we should have
        res = os.popen("/sbin/pump -s -i %s 2>/dev/null" % int_ifname).read()
        ippos = res.find("IP:")
        if ippos == -1:
            return gwstatus, gwtext, "warning", "No current DHCP lease", \
                    ISP_IF_CONNECT
        ip = res[ippos+4:res.find("\n", ippos)]
        # Check if we have it
        if not iface["address"].startswith(ip):
            return gwstatus, gwtext, "warning", \
                    "Invalid address configured!", ISP_IF_CONNECT
    else:
        bits = netmaskToBits(ipnum(ethnetmask))
        if iface["address"] != "%s/%s" % (ethip, bits):
            return gwstatus, gwtext, "warning", \
                    "Invalid address configured!", ISP_IF_CONNECT
    
    # Interface is up, should all be OK
    return gwstatus, gwtext, "ok", "Connected", ""
    
def getETHGatewayIP():
    """Returns the default gateway being used by the Ethernet Backhaul"""
    global int_ifname
    
    # Get the interface status from pump
    result = os.popen("/sbin/pump -s -i %s 2>/dev/null" % int_ifname).read()
    gwpos = result.find("Gateway:")
    if gwpos == -1:
        return ""
    return result[gwpos+9:result.find("\n", gwpos)]

def getETHNameservers():
    """Returns the default gateway being used by the Ethernet Backhaul"""
    global int_ifname
    dns1 = None
    dns2 = None
    
    # Get the interface status from pump
    r = os.popen("/sbin/pump -s -i %s 2>/dev/null" % int_ifname).read()
    
    # Extract DHCP server addresses
    lines = r.strip().split("\n")
    for line in lines:
        if line.strip().startswith("Nameservers"):
            try:
                parts = line.split(":")
                nses = parts[1].split()
                dns1 = nses[0].strip()
                if len(nses) > 1:
                    dns2 = nses[1].strip()
            except:
                log_error("Could not parse DNS servers from pump output!")
                log_debug(line.strip())
            break
    return dns1, dns2

def ETHBackhaulConfigured():
    """Checks whether the ethernet backhaul is configured for RuralLink use"""
    global int_ifname
    
    ethmode = pref_get("rurallink", "ethmode", getMonitorPrefs(), "dhcp")
    interfaces = debian_interfaces()
    iface = interfaces[int_ifname]
    if ethmode == "dhcp":
        # Grab the interfaces configuration and look for a method called DHCP
        if iface["method"]=="dhcp":
            return True
    else:
        # Check IP is correct
        ethip = pref_get("rurallink", "ethip", getMonitorPrefs(), "")
        if iface["address"]==ethip:
            return True

    return False
    
def configureETHBackhaul():
    """Updates the internal interface configuration for ethernet backhaul"""

    # Call the function that checks the master interface configuration
    checkMasterInterfaces()

    return True

def changeISP(newisp):
    global rl_isptype, int_ifname
    
    if newisp not in RL_ISPS.keys():
        raise ccs_rurallink_error("Invalid ISP specified")

    try:
        # Disconnect the old ISP
        ISPDisconnect()
    except ccs_rurallink_error:
        # And error occurred while trying to disconnect
        log_warn("Could not disconnect %s before changing to %s!" % \
                (rl_isptype, newisp))
        
    # Update the type
    rl_isptype = newisp
    pref_set("rurallink", "isptype", rl_isptype, getMonitorPrefs())
    ISPConfigure()
    log_info("ISP changed to %s" % rl_isptype)

    # Setup routes
    initialiseISPRoutes()

def updateISP(username, password):
    global rl_isptype

    if rl_isptype == ISP_BCL:
        updateBCL(username, password)
    elif rl_isptype == ISP_DSL:
        updateDSL(username, password)
    elif rl_isptype == ISP_ETH:
        # Ethernet ISP has no authentication details
        pass
    else:
        raise ccs_rurallink_error("No other ISPs implemented")
    
def getISPIfName():
    global rl_isptype, int_ifname
    
    # Get the name of the interface
    if rl_isptype == ISP_BCL:
        return BCL_IFACE
    elif rl_isptype == ISP_DSL:
        return int_ifname
    elif rl_isptype == ISP_ETH:
        return int_ifname
    else:
        return DEFAULT_ISP_IFNAME
    
def getISPUser():
    global rl_isptype
    
    if rl_isptype == ISP_BCL:
        return getBCLUser()
    elif rl_isptype == ISP_DSL:
        return getDSLUser()
    elif rl_isptype == ISP_ETH:
        return ""
    else:
        raise ccs_rurallink_error("No other ISPs implemented")

def getISPGatewayStatus():
        
    # Interface Status
    dg = getISPGatewayIP()
    if dg != "":
        # Got IP try and ping it
        command = "fping -am  %s" % dg
        result = os.popen("%s 2>/dev/null" % command).readlines()
        if len(result):
            if getGatewayIface() == getISPIfName():
                gwstatus = "ok"
                gwtext = "OK - %s reachable" % dg
            else:
                gwstatus = "warning"
                gwtext = "WARNING - ISP connection is not used!"
        else:
            gwstatus = "critical"
            gwtext = "CRITICAL - %s not reachable" % dg
    else:
        gwstatus = "critical"
        gwtext = "CRITICAL - No default gateway"
    
    return gwstatus, gwtext

def getISPGatewayIP():
    global rl_isptype
    
    if rl_isptype == ISP_BCL:
        return getGatewayIP()
    elif rl_isptype == ISP_DSL:
        return getDSLGatewayIP()
    elif rl_isptype == ISP_ETH:
        return getETHGatewayIP()
    else:
        raise ccs_rurallink_error("Unknown ISP passed to getISPGatewayIP!")

def ISPConnect():
    global rl_isptype
    
    if rl_isptype == ISP_BCL:
        ifstatus, iftext, ifaction = connectBCL()
    elif rl_isptype == ISP_DSL:
        ifstatus, iftext, ifaction = connectDSL()
    elif rl_isptype == ISP_ETH:
        ifstatus, iftext, ifaction = connectETH()
    else:
        raise ccs_rurallink_error("Unknown ISP type passed to ISPConnect!")
    
    gwstatus, gwtext = getISPGatewayStatus()
    return (gwstatus, gwtext, ifstatus, iftext, ifaction)
    
def ISPDisconnect():
    global rl_isptype
           
    if rl_isptype == ISP_BCL:
        ifstatus, iftext, ifaction = disconnectBCL()
    elif rl_isptype == ISP_DSL:
        ifstatus, iftext, ifaction = disconnectDSL()
    elif rl_isptype == ISP_ETH:
        ifstatus, iftext, ifaction = disconnectETH()
    else:
        raise ccs_rurallink_error("Unknown ISP type passed to ISPDisconnect!")

    gwstatus, gwtext = getISPGatewayStatus()
    return (gwstatus, gwtext, ifstatus, iftext, ifaction)

def ISPConfigure():
    global rl_isptype
    
    if rl_isptype == ISP_BCL:
        # Nop - will be configured when username/password is setup
        pass
    elif rl_isptype == ISP_DSL:
        configureDSLModem()
    elif rl_isptype == ISP_ETH:
        configureETHBackhaul()
    else:
        raise ccs_rurallink_error("Unknown ISP type passed to ISPConfigure!")

def getISPStatus():
    global rl_isptype
    
    if rl_isptype == ISP_BCL:
        return getBCLStatus()
    elif rl_isptype == ISP_DSL:
        return getDSLStatus()
    elif rl_isptype == ISP_ETH:
        return getETHStatus()
    else:
        raise ccs_rurallink_error("Unknown ISP type passed to getISPStatus!")

def getISPNameservers():
    global rl_isptype

    if rl_isptype == ISP_BCL:
        # PPP manages nameservers itself
        return None, None
    elif rl_isptype == ISP_DSL:
        return getDSLNameservers()
    elif rl_isptype == ISP_ETH:
        return getETHNameservers()
    else:
        raise ccs_rurallink_error("Unknown ISP type passed to ISPNameservers!")
    
def initialiseISPRoutes():
    global rl_isptype, int_ifname
    
    if rl_isptype == ISP_DSL:
        # Add DSL alias IP
        log_command("/sbin/ip addr add %s/%s dev %s &>/dev/null" % \
                (DSL_CPE_IP, DSL_NETMASK, int_ifname))
        addRoute("default", 0, DSL_MODEM_IP, int_ifname)
    elif rl_isptype == ISP_BCL:
        # Remove DSL alias IP
        log_command("/sbin/ip addr del %s/%s dev %s &>/dev/null" % \
                (DSL_CPE_IP, DSL_NETMASK, int_ifname))
        delRoute("default", 0, DSL_MODEM_IP, int_ifname)
    else:
        # Remove DSL alias IP
        log_command("/sbin/ip addr del %s/%s dev %s &>/dev/null" % \
                (DSL_CPE_IP, DSL_NETMASK, int_ifname))
        # Don't remove the default route... up/downing the interface
        # and pump will ensure that it points to the correct gateway

@registerRecurring(ROUTE_CHECK_INTERVAL)
def checkRoutes():
    """Checks that the routing is setup correctly"""

    if isMasterNode():
        initialiseISPRoutes()
    initialiseClientRoutes()

@registerRecurring(DNS_UPDATE_INTERVAL)
def updateDNS():
    """Checks that pdnsd has appropriate name servers configured"""
    global rl_isptype, rl_masterip
    
    if isMasterNode() or rl_masterip is None:
        if rl_isptype == ISP_DSL or rl_isptype == ISP_ETH:
            # Check if pdnsd has any servers
            fh = os.popen("/usr/sbin/pdnsd-ctl status | grep ip: | " \
                "grep -v ping")
            lines = fh.readlines()
            rv = fh.close()
            if rv is not None or len(lines)==0:
                # It doesn't, get some
                ns1, ns2 = getISPNameservers()
                if ns1 is not None:
                    log_command("/usr/sbin/pdnsd-ctl server pppdns1 up %s " \
                        "2>&1" % ns1)
                    log_info("Set NS1 to %s" % ns1)
                if ns2 is not None:
                    log_command("/usr/sbin/pdnsd-ctl server pppdns2 up %s " \
                        "2>&1" % ns2)
                    log_info("Set NS2 to %s" % ns2)
        # Use localhost as our nameserver
        ns = "127.0.0.1"
    else:
        ns = rl_masterip

    # Check that resolv.conf is correct
    fp = open("/etc/resolv.conf", "r")
    lines = fp.readlines()
    fp.close()
    
    update = False
    for line in lines:
        parts = line.split()
        if line.startswith("search"):
            if parts[1].strip() != "rurallink.co.nz":
                update=True
                break
        elif line.startswith("nameserver"):
            if parts[1].strip() != ns:
                update=True
                break
    if update:
        try:
            remountrw("updateDNS")
            fp = open("/etc/resolv.conf", "w")
            fp.write("search rurallink.co.nz\n")
            fp.write("nameserver %s\n" % ns)
            fp.close()
            remountro("updateDNS")
        except:
            log_error("Could not write resolv.conf!", sys.exc_info())
            remountro("updateDNS")

    # Check DHCP is serving the correct nameserver
    checkDHCPServer()
    
@registerRecurring(PHONE_HOME_INTERVAL)
def phoneHome():
    """When running as a master node, phone home regularly

    - The admin can disable this via the rladmin page
    - Sends an XMLRPC request to the rurallink server with details of the
      current RW IP and associated clients
    - Details on traffic is also reported unless the admin has disabled it
    """
    global rl_serialno, rl_password, rl_trafficusers
    global ap0_ifname
    
    # Client nodes don't phone home
    if not isMasterNode():
        log_debug("not phoning home, not master")
        return
    
    # Check if phoning home has been disabled
    phonehome = pref_getboolean("rurallink", "phonehome", getMonitorPrefs(), \
            True)
    if not phonehome:
        log_debug("not phoning home, disabled")
        return

    # Don't bother trying to phone home if the internet connection is down
    gwstatus, gwtext, ispstatus, isptext, ispaction = getISPStatus()
    if gwstatus == "critical" or ispstatus != "ok":
        log_info("Deferring phone home operation. No internet connection!")
        return

    # Build the information to send home
    info = {}

    try:
        uptime = float(open("/proc/uptime").readlines()[0].split()[0])
    except:
        log_warn("Failed to retrieve uptime", sys.exc_info())
        uptime = -1
    
    # This device
    info["serialno"] = rl_serialno
    info["hostname"] = socket.gethostname()
    info["uptime"] = uptime
    
    # Client devices
    info["clients"] = []
    if ap0_ifname is not None:
        clients = getAssociatedClients(ap0_ifname)
        for client in clients:
            client["clients"] = getAssociatedSubClients(client["ip"])
            info["clients"].append(client)

    # Traffic Statistics
    info["traffic"] = {}
    traffic = pref_getboolean("traffic", "send_reports", getMonitorPrefs(), \
            True)
    if traffic:        
        for username,user in rl_trafficusers.items():
            info["traffic"][username] = user["traffic"]
   
    # Connect and send the report
    try:
        home_url = config_get("rurallink", "home_url", DEFAULT_HOME_URL)
        key_file = config_get(None, "key_file", DEFAULT_KEY_FILE)
        cert_file = config_get(None, "cert_file", DEFAULT_CERT_FILE)
        s = xmlrpclib.ServerProxy(home_url, \
                CCSTransport(key_file, cert_file))
        if s.phoneHome({}, info):
            log_info("Phoned home successfully")
        else:
            log_error("Phone home call failed!")
    except:
        log_error("Exception while trying to phone home!", sys.exc_info())

@registerRecurring(UPSTREAM_CHECK_INTERVAL)
def checkUpstream():
    global int_ifname, backhaul_ifname, ext_ifname, backhaul_vbase
    global rl_isptype
    needsUp = False

    if not isMasterNode():
        # Check that the backhaul is up
        ifaces = {}
        for i in getInterfaces(True): ifaces[i["name"]] = i
        if backhaul_ifname not in ifaces.keys():
            if checkClientInterfaces():
                needsUp = True
        else:
            if not ifaces[backhaul_ifname]["up"]:
                needsUp = True
        if needsUp:
            log_info("Attempting to bring backhaul interface up")
            log_command("/sbin/ifdown %s 2>&1" % backhaul_ifname)
            log_command("/sbin/ifup %s 2>&1" % backhaul_ifname)
        return

    # Check the various internet connection options are connected
    gwstatus, gwtext, ispstatus, isptext, ispaction = getISPStatus()
    if ispstatus != "ok" or gwstatus == "critical":
        # Attempt to reconnect the ISP
        log_info("Attempting to reconnect to the ISP")
        ISPDisconnect()
        ISPConnect()

##############################################################################
# Initialisation
##############################################################################
def ccs_init():
    global rl_serialno, rl_password, rl_trafficusers
    global int_ifname, ap0_ifname, backhaul_ifname, ext_ifname
    global backhaul_vbase, ap0_vbase, rl_masterip, rl_isptype
    global rl_mastername
    
    ifs_changed = False
    
    # Read the serial number for this device from a file
    try:
        fp = open(SERIALNO_FILE, "r")
        rl_serialno = int(fp.read())
        if rl_serialno <= 0 or rl_serialno > (2**16):
            raise Exception("Invalid serial number!")
        fp.close()
        log_info("RuralLink Serial No: %s" % rl_serialno)
    except:
        (type, value, tb) = sys.exc_info()
        log_fatal("Could not initialise RuralLink module! - %s" % value, \
                (type, value, tb))

    registerMenuItem(MENU_TOP, MENU_GROUP_GENERAL, \
            "/rladmin", "CPE Administration")

    # Override the default bottom menu links
    registerMenu(MENU_BOTTOM, "External Links", reset=True)
    registerMenuItem(MENU_BOTTOM, MENU_GROUP_GENERAL, \
            "http://www.rurallink.co.nz/", "Rural Link Homepage")
    registerMenuItem(MENU_BOTTOM, MENU_GROUP_GENERAL, \
            "http://www.google.com/", "Google")
    
    # Retrieve the network password
    rl_password = pref_get("rurallink", "password", getMonitorPrefs(), \
            DEFAULT_PASSWORD)

    # Retrieve interface configuration details from the configuration file
    int_ifname = config_get("rurallink", "internal_ifname", \
            DEFAULT_INTERNAL_IFNAME)
    ap0_ifname = config_get("rurallink", "ap0_ifname", DEFAULT_AP0_IFNAME)
    backhaul_ifname = config_get("rurallink", "backhaul_ifname", \
            DEFAULT_BACKHAUL_IFNAME)
    ext_ifname = "ppp0"
    ap0_vbase = config_get("rurallink", "ap0_vbase", None)
    backhaul_vbase = config_get("rurallink", "backhaul_vbase", None)
    
    # Check interface configurations
    if isMasterNode():        
        # Retrieve the ISP we're connecting to
        rl_isptype = pref_get("rurallink", "isptype", \
                getMonitorPrefs(), ISP_BCL)
        initialiseISPRoutes()

        ifs_changed = checkMasterInterfaces()
    else:
        ifs_changed = checkClientInterfaces()

    # Install the setup wizard if required
    rl_wizardrun = pref_getboolean("rurallink", "wizardrun", \
            getMonitorPrefs(), False)
    if not rl_wizardrun:
        # Replace the CPE homepage with the setup wizard
        log_info("Installing Rural Link setup wizard")
        @registerPage("/", force=True)
        def setupwizard(request, method):
            return rlwizard(request, method)
        
        # Make sure the internal interface is up and DHCP is running
        log_command("/sbin/ifdown %s 2>&1" % int_ifname)
        log_command("/sbin/ifup %s 2>&1" % int_ifname)
        t = ap0_ifname
        ap0_ifname = None
        checkDHCPServer()
        ap0_ifname = t
    else:
        if ifs_changed:
            # Reload interfaces to pick up any new configuration
            log_command("/etc/init.d/networking restart 2>&1")
            # Force a DHCP restart to pick up any new interfaces too
            checkDHCPServer(True)

    # Check if we know the master device to talk to
    nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)
    if not isMasterNode():
        rl_masterip = pref_get("rurallink", "masterip", \
                getMonitorPrefs(), None)
        rl_mastername = ""
        if rl_masterip is None:
            # No master IP recorded, see if we can retrieve on
            retrieveMasterIP()
       
        # Fetch more stuff if we have a master IP now
        if rl_masterip is not None:
            # Get the name of the master node
            rl_mastername = getNodeName(rl_masterip)
            
            # Initialise the status map
            if retrieveNodemapFile(nm_filename):
                setupStatusMap(nm_filename, rl_mastername)

            # Create a link to the master node
            registerMenuItem(MENU_TOP, MENU_GROUP_HOME, \
                    "http://%s/" % rl_masterip, "Master Node Homepage")

    else:
        # Master node can get its own IP when it needs it...
        rl_masterip = None
        
        # Initialise the status map
        if buildNodemapFile(nm_filename):
            setupStatusMap(nm_filename, socket.gethostname())
            
        # Initialise traffic management
        try:
            passwdfile =  config_get("traffic", "passwd_file", \
                    DEFAULT_TRAFFIC_PASSWD_FILE)
            ensureFileExists(passwdfile)
            rl_trafficusers = readTrafficUsers()
        except:
            log_error("Could not load users! Traffic management " \
                    "functionality disabled.", sys.exc_info())
            rl_trafficusers = {}
            return
        
        # Ensure that default traffic management policies are set in the
        # preferences file for the firewall to use
        ap0_policy = pref_get("traffic", "ap0_policy", \
                getMonitorPrefs(), None)
        int_policy = pref_get("traffic", "internal_policy", \
                getMonitorPrefs(), None)
        if ap0_policy is None:
            ap0_policy = DEFAULT_AP0_POLICY
            pref_set("traffic", "ap0_policy", ap0_policy, getMonitorPrefs())
        if int_policy is None:
            int_policy = DEFAULT_INTERNAL_POLICY
            pref_set("traffic", "internal_policy", int_policy, \
                    getMonitorPrefs())

        # Initialise the counters
        for username,user in rl_trafficusers.items():
            rl_trafficusers[username]["traffic"] = 0
            rl_trafficusers[username]["ip"] = None
            
        # Initialise the captive portal server
        httpd = AsyncHTTPServer(('', 81), CaptivePortalHandler)
        log_info("Captive Portal Initialised. Traffic management in place.")
     
    # Reload the firewall
    log_command("/etc/init.d/firewall start & 2>&1")

    # Make sure DNS is correctly setup, this will restart DHCP as well
    updateDNS()
    
    if rl_wizardrun:
        # Initialise routes for the clients
        initialiseClientRoutes()

@catchEvent("statusMapRequested")
def updateStatusMap(*args, **kwargs):
    """Called when the status map is requested, so we can update it"""
    global rl_lastmapupdate, rl_mastername
    
    nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)

    # Updated recently, no need to update again
    if rl_lastmapupdate!=0 and \
            time.time() < rl_lastmapupdate+MAP_UPDATE_INTERVAL:
        return None
    
    if isMasterNode():
        if buildNodemapFile(nm_filename):
            setupStatusMap(nm_filename, socket.gethostname())
    else:
        if retrieveNodemapFile(nm_filename):
            setupStatusMap(nm_filename, rl_mastername)

    
def setupStatusMap(nodemapfile, gateway):
    global rl_lastmapupdate

    try:
        initialiseNetworkMap(nodemapfile,socket.gethostname(),gateway,gateway)
        rl_lastmapupdate = time.time()
    except:
        log_error("Could not setup network map using Rural Link data!", \
                sys.exc_info())
        return

def checkDHCPServer(forceRestart=False):
    """Checks that the DCHP server is running on the appropriate interfaces

    If not the configuration is fixed so that it is.
    """
    global int_ifname, ap0_ifname, rl_masterip, rl_serialno, rl_isptype
    global rl_serialno
    
    dhcp = dhcpd_conf()
    interfaces = debian_interfaces()
    changed = False
    iflist = []
    
    if rl_isptype != ISP_ETH:
        if int_ifname != None and int_ifname in interfaces.keys():
            net = interfaces[int_ifname]["network"]
            if net not in dhcp.keys():
                netmask = interfaces[int_ifname]["netmask"]
                lo = formatIP(ipnum(net)+1)
                hi = formatIP(ipnum(interfaces[int_ifname]["broadcast"])-2)
                address = interfaces[int_ifname]["address"]
                # Create a subnet block for the internal interface
                dhcp[net] = {"network":net, "netmask":netmask, \
                        "range":"%s %s" % (lo, hi), \
                        "options":{"routers":address}}
                changed = True
            iflist.append(int_ifname)
    else:
        network, bits = generateRLNetwork(rl_serialno, RL_INTERNAL)
        net = formatIP(network)
        if net in dhcp.keys():
            del dhcp[net]
            changed = True

    if ap0_ifname != None and ap0_ifname in interfaces.keys():
        net = interfaces[ap0_ifname]["network"]
        if net not in dhcp.keys():
            netmask = interfaces[ap0_ifname]["netmask"]
            lo = formatIP(ipnum(net)+2)
            hi = formatIP(ipnum(interfaces[ap0_ifname]["broadcast"])-1)
            address = interfaces[ap0_ifname]["address"]
            # Create a subnet block for the AP0 interface
            dhcp[net] = {"network":net, "netmask":netmask, \
                    "range":"%s %s" % (lo, hi), "options":{"routers":address}}
            changed = True
        iflist.append(ap0_ifname)

    # Ensure the appropriate interfaces are enabled
    iline = "INTERFACES=\"%s\"" % " ".join(iflist)
    lines = open(DHCP_DEFAULTS, "r").readlines()
    found = False
    for line in lines:
        if line.strip() == iline:
            found=True
            break
        
    # Check DNS settings in the configuration file
    for line in dhcp._content:
        if type(line) != type(""):
            continue
        # Check Nameserver
        if line.strip().startswith("option domain-name-servers"):
            if isMasterNode() or rl_masterip is None:
                # Use our ap0 IP address as the Nameserver
                network, bits = generateRLNetwork(rl_serialno, RL_AP0)
                ns = formatIP(network+1)
            else:
                ns = rl_masterip
            if line.find(ns) == -1:
                dhcp._content[dhcp._content.index(line)] = \
                    "option domain-name-servers %s;\n" % ns
                changed = True
            continue
        # Check domain name
        if line.strip().startswith("option domain-name"):
            if line.find("rurallink.co.nz") == -1:
                dhcp._content[dhcp._content.index(line)] = \
                    "option domain-name \"rurallink.co.nz\";\n"
                changed = True
            continue
                
    if changed or not found:
        try:
            remountrw("checkDHCPServer")
            filterFile("^INTERFACES.*$", iline, DHCP_DEFAULTS)
            dhcp.write()
        finally:
            remountro("checkDHCPServer")
        log_command("/etc/init.d/dhcp3-server restart 2>&1")
    else:
        # Check that the server is running
        if not processExists("dhcpd3"):
            log_command("/etc/init.d/dhcp3-server start 2>&1")
        elif forceRestart:
            log_command("/etc/init.d/dhcp3-server restart 2>&1")

def createInternalConfig(old):
    global rl_serialno, int_ifname, rl_isptype
    network, bits = generateRLNetwork(rl_serialno, RL_INTERNAL)
    netmask = bitsToNetmask(bits)
    bcast = ipbroadcast(network, netmask)

    # Merge current configuration
    iface = old

    # Set the common fixed bits
    iface["name"] = int_ifname
    iface["auto"]=True
    iface["family"] = "inet"

    # DHCP if using ethernet backhaul
    if rl_isptype == ISP_ETH:
        # Retrieve ethernet details
        ethmode = pref_get("rurallink", "ethmode", getMonitorPrefs(), "dhcp")
        ethip = pref_get("rurallink", "ethip", getMonitorPrefs(), "")
        ethnetmask = pref_get("rurallink", "ethnetmask", getMonitorPrefs(), "")
        ethgw = pref_get("rurallink", "ethgw", getMonitorPrefs(), "")
        
        if ethmode == "dhcp":
            iface["method"] = "dhcp"
            for i in ["address", "netmask", "network", "broadcast"]:
                try:
                    del iface[i]
                except KeyError:
                    pass
        else:
            network = ipnetwork(ipnum(ethip), ipnum(ethnetmask))
            bcast = ipbroadcast(ipnum(ethip), ipnum(ethnetmask))
            iface["method"] = "static"
            iface["address"] = ethip
            iface["netmask"] = ethnetmask
            iface["network"] = formatIP(network)
            iface["broadcast"] = formatIP(bcast)
            iface["gateway"] = ethgw
    else:
        # Now set the fixed bits for a static address
        iface["address"] = formatIP(bcast-1)
        iface["netmask"] = formatIP(netmask)
        iface["network"] = formatIP(network)
        iface["broadcast"] = formatIP(bcast)
        iface["method"] = "static"
    
    return iface

def createBackhaulConfig(old):
    global rl_serialno, backhaul_vbase, backhaul_ifname

    # Setup bits the current configuration can override
    iface = {}
    if backhaul_vbase is not None:
        iface["madwifi_base"] = backhaul_vbase
    iface["wireless_standard"] = "g"
    iface["wireless_essid"] = "rl-bhaul-%s" % rl_serialno

    # Merge current configuration
    iface.update(old)

    # Now set the fixed bits
    iface["wireless_key"] = "s:%s" % getWEPKey()
    iface["wireless_mode"] = "Managed"
    iface["name"]=backhaul_ifname
    iface["family"]="inet"
    iface["method"]="dhcp"
    iface["auto"]=True
    
    return iface
    
def createAP0Config(old):
    global rl_serialno, ap0_vbase, ap0_ifname
    network, bits = generateRLNetwork(rl_serialno, RL_AP0)
    netmask = bitsToNetmask(bits)
    
    # Setup the bits that a current configuration can override
    iface = {}
    if ap0_vbase is not None:
        iface["madwifi_base"] = ap0_vbase
    iface["wireless_standard"] = "g"
    iface["wireless_essid"] = "rl-%s-ap0" % socket.gethostname()
    iface["wireless_channel"] = allocateChannel(ap0_ifname)
    
    # Merge current configuration
    iface.update(old)
    
    # Now set the fixed bits
    iface["wireless_key"] = "s:%s" % getWEPKey()
    iface["wireless_mode"] = "Master"
    iface["address"] = formatIP(network+1)
    iface["netmask"] = formatIP(netmask)
    iface["network"] = formatIP(network)
    iface["broadcast"] = formatIP(ipbroadcast(network, netmask))
    iface["name"]=ap0_ifname
    iface["family"]="inet"
    iface["method"]="static"
    iface["auto"]=True
    
    return iface
            
def checkClientInterfaces():
    """Checks that the appropriate interfaces for a client node are present

    A client node can be a repeater, a CPE repeater or simply a CPE.

    Also checks that the IP addresses and service configuration is correct
    given the serial number for this device.
    """
    global int_ifname, ap0_ifname, backhaul_ifname, ext_ifname
    global backhaul_vbase, ap0_vbase
    
    ifaces = {}
    for i in getInterfaces(True): ifaces[i["name"]] = i
    interfaces = debian_interfaces()
    changed = False
    needsUp = False
    
    # No external interface when not acting as a Master
    ext_ifname = None
    
    # Check backhaul devices exist
    if backhaul_ifname not in ifaces.keys():
        # Doesn't exist, and not configured, check for vbase
        if backhaul_vbase is None or backhaul_vbase not in ifaces.keys():
            log_fatal("Invalid backhaul interface! = %s" % backhaul_ifname)
        needsUp = True
    else:
        if not ifaces[backhaul_ifname]["up"]:
            needsUp = True
    
    # Check backhaul configuration
    if backhaul_ifname not in interfaces.keys():
        interfaces[backhaul_ifname] = createBackhaulConfig({})
        changed = True
    else:
        iface = interfaces[backhaul_ifname]
        if iface["method"]!="dhcp" or not iface["auto"]:
            log_warn("backhaul interface reconfigured")
            interfaces[backhaul_ifname] = createBackhaulConfig(iface)
            changed=True
    
    # Check that the internal interface is correctly configured if it exists
    if int_ifname not in ifaces.keys():
        int_ifname = None
    else:
        network, bits = generateRLNetwork(rl_serialno, RL_INTERNAL)
        netmask = bitsToNetmask(bits)
        bcast = ipbroadcast(network, netmask)
        if not ifaces[int_ifname]["up"]:
            needsUp = True
        # Verify internal interface configuration
        if int_ifname not in interfaces.keys():
            interfaces[int_ifname] = createInternalConfig({})
            changed = True
        else:
            iface = interfaces[int_ifname]
            if "address" not in iface.keys() or (iface["address"] != \
                    formatIP(bcast-1) or iface["method"]!="static" or \
                    not iface["auto"]):
                log_warn("Internal interface reconfigured")
                interfaces[int_ifname] = createInternalConfig({})
                changed = True
            
    # Check AP0 devices exist
    if ap0_ifname not in ifaces.keys():
        # Doesn't exist, and not configured, check for vbase
        if ap0_vbase is None or ap0_vbase not in ifaces.keys():
            ap0_ifname = None
            ap0_vbase = None
        needsUp = True
    else:
        if not ifaces[ap0_ifname]["up"]:
            needsUp = True
        
    if ap0_ifname is not None:
        # Check AP0 configuration
        if ap0_ifname not in interfaces.keys():
            interfaces[ap0_ifname] = createAP0Config({})
            changed = True
        else:
            iface = interfaces[ap0_ifname]
            network, bits = generateRLNetwork(rl_serialno, RL_AP0)
            if "address" not in iface.keys() or (iface["address"] != \
                    formatIP(network+1) or iface["method"]!="static" or \
                    not iface["auto"]):
                log_warn("AP0 interface reconfigured")
                interfaces[ap0_ifname] = createAP0Config(iface)
                changed=True
            
    if changed:
        try:
            remountrw("checkClientInterfaces")
            interfaces.write()
        finally:
            remountro("checkClientInterfaces")
    
    return (changed or needsUp)

def checkMasterInterfaces():
    """Checks that the appropriate interfaces for a master node are present

    Also checks that the IP addresses and service configuration is correct
    given the serial number for this device. 

    Corrects and reconfigures the device if not.
    """
    global int_ifname, ap0_ifname, backhaul_ifname, ext_ifname
    global backhaul_vbase, ap0_vbase, rl_isptype
        
    backhaul_ifname = None
    
    # Get some information about the state of the interfaces on the system
    ifaces = {}
    for i in getInterfaces(True): ifaces[i["name"]] = i
    interfaces = debian_interfaces()
    changed = False
    needsUp = False
    
    # Check that the internal interface is correctly configured if it exists
    if int_ifname not in ifaces.keys():
        int_ifname = None
    else:
        network, bits = generateRLNetwork(rl_serialno, RL_INTERNAL)
        netmask = bitsToNetmask(bits)
        bcast = ipbroadcast(network, netmask)
        if not ifaces[int_ifname]["up"]:
            needsUp = True
        # Verify internal interface configuration
        if int_ifname not in interfaces.keys():
            interfaces[int_ifname] = createInternalConfig({})
            changed = True
        else:
            iface = interfaces[int_ifname]
            if rl_isptype == ISP_ETH:
                # Retrieve ethernet details
                ethmode = pref_get("rurallink", "ethmode", getMonitorPrefs(), \
                        "dhcp")
                ethip = pref_get("rurallink", "ethip", getMonitorPrefs(), "")
                if ethmode == "dhcp":
                    # If we're using ethernet backhaul needs DHCP config here
                    if iface["method"]!="dhcp":
                        log_warn("Internal interface reconfigured")
                        interfaces[int_ifname] = createInternalConfig({})
                        changed = True
                else:
                    # Check IP is correct
                    if "address" not in iface.keys() or \
                            iface["address"] != ethip:
                        log_warn("Internal interface reconfigured")
                        interfaces[int_ifname] = createInternalConfig({})
                        changed = True
            else:
                if "address" not in iface.keys() or (iface["address"] != \
                        formatIP(bcast-1) or iface["method"]!="static" or \
                        not iface["auto"]):
                    log_warn("Internal interface reconfigured")
                    interfaces[int_ifname] = createInternalConfig({})
                    changed = True
        
    # Check AP0 devices exist
    if ap0_ifname not in ifaces.keys():
        # Doesn't exist, and not configured, check for vbase
        if ap0_vbase is None or ap0_vbase not in ifaces.keys():
            log_fatal("Invalid AP0 interface! - %s (%s)" % \
                        (ap0_ifname, ap0_vbase))
        needsUp = True
    else:
        if not ifaces[ap0_ifname]["up"]:
            needsUp = True
    
    if ap0_ifname is not None:
        # Check AP0 configuration
        if ap0_ifname not in interfaces.keys():
            interfaces[ap0_ifname] = createAP0Config({})
            changed = True
        else:
            iface = interfaces[ap0_ifname]
            network, bits = generateRLNetwork(rl_serialno, RL_AP0)
            if "address" not in iface.keys() or (iface["address"] != \
                    formatIP(network+1) or iface["method"]!="static" or \
                    not iface["auto"]):
                log_warn("AP0 interface reconfigured")
                interfaces[ap0_ifname] = createAP0Config(iface)
                changed=True
    
    # Write out the interfaces configuration if it changed
    if changed:
        try:
            remountrw("checkMasterInterfaces")
            interfaces.write()
        finally:
            remountro("checkMasterInterfaces")

    return (changed or needsUp)
    
##############################################################################
# Content Pages
##############################################################################

@registerPage("/disablewizard")
def disableWizard(request, method):
    global ap0_ifname, rl_isptype, int_ifname
    
    pref_set("rurallink", "wizardrun", True, getMonitorPrefs())

    @registerPage("/", force=True)
    def restoreHomepage(request, method):
        return homepage(request, method)

    # Reload the network configuration
    log_command("/etc/init.d/networking restart 2>&1")
    
    # Reload the firewall
    log_command("/etc/init.d/firewall start & 2>&1")
    
    # Check services are running
    checkDHCPServer()
    
    # Otherwise return success
    content = """
<div class="wizard" id="step5"> 
<h2>Rural Link CPE Setup Wizard</h2><br />
<div class="progressbar">
    <div>
        <span class="stepno">1</span><br />
        <span class="stepdesc">Introduction</span>
    </div>
    <div class="future">
        <span class="stepno">2</span><br />
        <span class="stepdesc">Set Hostname</span>
    </div>
    <div class="future">
        <span class="stepno">3</span><br />
        <span class="stepdesc">Set Password</span>
    </div>
    <div class="future">
        <span class="stepno">4</span><br />
        <span class="stepdesc">Configure Uplink</span>
    </div>
    <div class="future">
        <span class="stepno">5</span><br />
        <span class="stepdesc">Configuration Complete</span>
    </div>
</div>
<br clear="all" />
Your Rural Link device configuration has now been finalised, we hope you enjoy
using it. 

If you have any questions or require assistance in the future please contact
the Rural Link helpdesk on <b>+64 7 857 0820</b><br />
<br />
</div>
"""
    returnPage(request, "Wizard Completed", content)

@registerPage("/setupwizard", requireAuth=True, realm=CPE_ADMIN_REALM)
def rlwizard(request, method):
    global rl_password, ap0_ifname, backhaul_ifname, rl_isptype

    ajaxWizard = config_getboolean("rurallink", "ajaxWizard", True)
    posterr = ""
    postmsg = ""
    step = 1
    
    if method == "POST":
        data = request.getPostData()
        if "isAjax" in data.keys():
            ajaxWizard = True
        process=True
        if not ajaxWizard:
            # Check forward/next progress, only process post vars on forward
            if "direction" not in data.keys():
                posterr = "Missing required POST values"
                process=False
            else:
                if data["direction"] != "next":
                    process=False
        # Incoming data
        if process and "wizard_hostname" in data.keys():
            try:
                # Remove all associations
                changeHostname(data["wizard_hostname"])
                postmsg = "Hostname updated"
            except:
                log_error("Failed to change hostname!", sys.exc_info())
                posterr="Unable to update hostname"
        elif process and "wizard_password" in data.keys():
            try:
                if data["wizard_password"] == "":
                    raise ccs_rurallink_error("Cannot set blank password!")
                if len(data["wizard_password"]) < 8:
                    raise ccs_rurallink_error("Password must be at " \
                            "least 8 characters!")
                rl_password = data["wizard_password"]
                admin_pass = crypt.crypt(rl_password, createSalt())
                pref_set("rurallink", "password", rl_password, \
                        getMonitorPrefs())
                # Change the CPE administration password as well
                pref_set(None, "admin_password", admin_pass, \
                        getMonitorPrefs())
                realm = getRealm()
                realm["users"][ADMIN_USERNAME] = admin_pass
                registerRealm(CPE_ADMIN_REALM, realm, overwrite=True)
                postmsg = " Password updated"
                # Reconfigure interfaces as WEP key will have changed
                ifaces = debian_interfaces()
                if backhaul_ifname is not None:
                    ifaces[backhaul_ifname] = \
                            createBackhaulConfig(ifaces[backhaul_ifname])
                    log_command("/sbin/iwconfig %s key s:%s" % \
                            (backhaul_ifname, getWEPKey()))
                if ap0_ifname is not None:
                    ifaces[ap0_ifname] = \
                            createAP0Config(ifaces[ap0_ifname])
                    log_command("/sbin/iwconfig %s key s:%s" % \
                            (ap0_ifname, getWEPKey()))
                try:
                    remountrw("rladmin-password")
                    ifaces.write()
                finally:
                    remountro("rladmin-password")
            except:
                (etype, value, tb) = sys.exc_info()
                log_error("Failed to change password!", (etype, value, tb))
                posterr = "Unable to update password - %s" % value
        elif process and "wizard_essid" in data.keys():
            try:
                if not configureBhaulInterface(data["wizard_essid"]):
                    log_error("Failed to associate!", sys.exc_info())
                    posterr = "Unable to associate"
                else:
                    postmsg = "Associated Successfully"
            except:
                log_error("Unexpected error configuring backhaul interface",
                        sys.exc_info())
                posterr = "Unable to associate"
        elif process and "wizard_ispusername" in data.keys():
            try:
                if "wizard_isppassword" not in data.keys():
                    raise ccs_rurallink_error("Missing post variables!")
                if not ajaxWizard:
                    # ISP type will be here too
                    changeISP(data["wizard_isptype"])
                    # And potentially ethernet information
                    if data["wizard_isptype"] == ISP_ETH:
                        elems = {"ethip":"IP", "ethnetmask":"netmask", \
                                "ethgw":"gateway"}
                        # Validate incoming data
                        if data["wizard_ethmode"] not in ["dhcp", "static"]:
                            raise ccs_rurallink_error("Invalid Ethernet mode!")
                        if data["wizard_ethmode"] == "static":
                            for n in elems:
                                e = "wizard_%s" % n
                                if e not in data.keys():
                                    raise ccs_rurallink_error("Ethernet " \
                                            "%s not specified!" % elems[e])
                                if not isValidIP(data[e]):
                                    raise ccs_rurallink_error("Invalid " \
                                            "Ethernet %s" % elems[e])
                                network = ipnetwork( \
                                        ipnum(data["wizard_ethip"]), \
                                        ipnum(data["wizard_ethnetmask"]))
                                if not inNetwork(ipnum(data["wizard_ethgw"]), \
                                       network, \
                                       ipnum(data["wizard_ethnetmask"])):
                                    raise ccs_rurallink_error("Invalid " \
                                            "gateway address!")
                        # Set the mode
                        pref_set("rurallink", "ethmode", \
                                data["wizard_ethmode"], getMonitorPrefs())
                        # Set static IP details if necessary
                        if data["wizard_ethmode"] == "static":
                            for n in elems:
                                e = "wizard_%s" % n
                                pref_set("rurallink", n, data[e], \
                                        getMonitorPrefs())
                        # Regenerate the interface configuration
                        checkMasterInterfaces()
                username = urllib.unquote(data["wizard_ispusername"]).strip()
                password = urllib.unquote(data["wizard_isppassword"]).strip()
                updateISP(username, password)
                postmsg = "ISP details configured"
            except:
                log_error("Exception setting ISP password", sys.exc_info())
                posterr = "Failed to update ISP username and password"
        elif process and "wizard_isptype" in data.keys():
            try:
                changeISP(data["wizard_isptype"])
                # And potentially ethernet information
                if data["wizard_isptype"] == ISP_ETH:
                    elems = {"ethip":"IP", "ethnetmask":"netmask", \
                            "ethgw":"gateway"}
                    # Validate incoming data
                    if data["wizard_ethmode"] not in ["dhcp", "static"]:
                        raise ccs_rurallink_error("Invalid Ethernet mode!")
                    if data["wizard_ethmode"] == "static":
                        for n in elems:
                            e = "wizard_%s" % n
                            if e not in data.keys():
                                raise ccs_rurallink_error("Ethernet " \
                                        "%s not specified!" % elems[e])
                            if not isValidIP(data[e]):
                                raise ccs_rurallink_error("Invalid " \
                                        "Ethernet %s" % elems[e])
                            network = ipnetwork( \
                                    ipnum(data["wizard_ethip"]), \
                                    ipnum(data["wizard_ethnetmask"]))
                            if not inNetwork(ipnum(data["wizard_ethgw"]), \
                                   network, \
                                   ipnum(data["wizard_ethnetmask"])):
                                raise ccs_rurallink_error("Invalid " \
                                        "gateway address!")
                    # Set the mode
                    pref_set("rurallink", "ethmode", \
                            data["wizard_ethmode"], getMonitorPrefs())
                    # Set static IP details if necessary
                    if data["wizard_ethmode"] == "static":
                        for n in elems:
                            e = "wizard_%s" % n
                            pref_set("rurallink", n, data[e], \
                                    getMonitorPrefs())
                    # Regenerate the interface configuration
                    checkMasterInterfaces()
                postmsg = "ISP type set"
            except:
                log_error("Exception setting ISP type", sys.exc_info())
                posterr = "Failed to set ISP type"
        elif ajaxWizard:
            posterr = "Invalid POST method for this page!"

        if ajaxWizard:
            if posterr != "":
                # Return an error if an error message was set
                request.send_error(400, posterr)
                request.end_headers()
            else:
                # Otherwise return success
                request.send_response(200, postmsg)
                request.end_headers()
            request.finish()
            return
        else:
            # Move forward if the request succeeded
            if process:
                if posterr == "":
                    step = int(data["step"])+1
                else:
                    step = int(data["step"])
            else:
                step = int(data["step"])-1
    else:
        # Allow a query parameter to set the default step
        for part in request.query.split("&"):
            if part.find("step") != -1:
                parts = part.split("=")
                try:
                    step = int(parts[1])
                except:
                    log_error("Invalid step specific in query parameters")
    
    # Validate steps
    if step < 1: step = 1 
    if step > 5: step = 5
    
    # Get the template
    resourcedir = config_get("www", "resourcedir", DEFAULT_RESOURCE_DIR)
    tfile = "%s/page.html" % resourcedir
    try:
        fd = open(tfile, "r")
        template = fd.read()
        fd.close()
    except:
        log_error("Page template not available!", sys.exc_info())
        # Return a very cruddy basic page
        template = "<html><head><title>%TITLE%</title></head>" \
                "<body><h2>Menu</h2><br />%MENU%<br /><hr />" \
                "<h2>%TITLE%</h2><br />%CONTENT%</body></html>"
        
    hostname = socket.gethostname()
    content = ""
    statustxt = ""    
    # Setup the form if we are not using the wizard
    if not ajaxWizard:
        content += """
<form method="POST" action="/" id="wizardForm">
<input type="hidden" name="step" value="%s">
<input type="hidden" name="postWizard" id="postWizard" value="yes">
<input type="hidden" name="direction" id="direction" value="next">
<style type="text/css">
#step2.wizard,#step3.wizard,#step4.wizard,#step5.wizard {
    display: block;
}
</style>
""" % step
        if posterr != "":
            statustxt = """<span class="error">%s</span><br /><br />""" % \
                    posterr
    
    # Generate page content for each step
    if step==1 or ajaxWizard:
        content += """
<div class="wizard" id="step1"> 
<h2>Rural Link CPE Setup Wizard</h2><br />
<div class="progressbar">
    <div>
        <span class="stepno">1</span><br />
        <span class="stepdesc">Introduction</span>
    </div>
    <div class="future">
        <span class="stepno">2</span><br />
        <span class="stepdesc">Set Hostname</span>
    </div>
    <div class="future">
        <span class="stepno">3</span><br />
        <span class="stepdesc">Set Password</span>
    </div>
    <div class="future">
        <span class="stepno">4</span><br />
        <span class="stepdesc">Configure Uplink</span>
    </div>
    <div class="future">
        <span class="stepno">5</span><br />
        <span class="stepdesc">Configuration Complete</span>
    </div>
</div>
<br clear="all" />
%s
Welcome to your new Rural Link device. This wizard will help you configure and
setup your network in a few simple steps. If you have any questions or require
assistance configuring your network please contact the Rural Link helpdesk on
<b>+64 7 857 0820</b><br />
<br />
<a href="javascript:nextStep()" class="next">Next&nbsp;Step&nbsp;&nbsp;&gt;&gt;</a>
<br clear="all" />
</div>
""" % statustxt

    if step==2 or ajaxWizard:
        content += """
<div class="wizard" id="step2"> 
<h2>Rural Link CPE Setup Wizard - Set Hostname</h2><br />
<div class="progressbar">
    <div class="past">
        <span class="stepno">1</span><br />
        <span class="stepdesc">Introduction</span>
    </div>
    <div>
        <span class="stepno">2</span><br />
        <span class="stepdesc">Set Hostname</span>
    </div>
    <div class="future">
        <span class="stepno">3</span><br />
        <span class="stepdesc">Set Password</span>
    </div>
    <div class="future">
        <span class="stepno">4</span><br />
        <span class="stepdesc">Configure Uplink</span>
    </div>
    <div class="future">
        <span class="stepno">5</span><br />
        <span class="stepdesc">Configuration Complete</span>
    </div>
</div>
<br clear="all" />
%s
Please enter an identifying name for this device in the field below. The name
must consist only of the lowercase characters <b>a-z</b> the digits <b>0-9</b>
and the hyphen <b>-</b>. It is recommended that you choose a standard prefix
to use for all your Rural Link devices.<br /><br />
<table>
<tr>
    <th>Hostname:</th>
    <td>
    <input type="text" id="wizard_hostname" name="wizard_hostname" value="%s">
    </td>
</tr>
</table>
<br />
<a href="javascript:prevStep()" class="prev">&lt;&lt;&nbsp;&nbsp;Prev&nbsp;Step</a>
<a href="javascript:nextStep()" class="next">Next&nbsp;Step&nbsp;&nbsp;&gt;&gt;</a>
<br clear="all" />
</div>
""" % (statustxt, hostname)


    if step==3 or ajaxWizard:
        if isMasterNode():
            passworddetails = """Please enter an administration password for 
your Rural Link device in the field below. This password will be required by
any other wireless device wanting to connect to your network. This password is
also used to restrict access to the administration interface of your Rural 
Link device."""
        else:
            passworddetails = """Please enter your Rural Link device password
in the field below. This password is used to authenticate your Rural Link
devices to each other (you chose it when you intially configured your master
device).  This password is also used to restrict access to the administration
interface of each Rural Link device on your network."""

        content += """
<div class="wizard" id="step3"> 
<h2>Rural Link CPE Setup Wizard - Set Password</h2><br />
<div class="progressbar">
    <div class="past">
        <span class="stepno">1</span><br />
        <span class="stepdesc">Introduction</span>
    </div>
    <div class="past">
        <span class="stepno">2</span><br />
        <span class="stepdesc">Set Hostname</span>
    </div>
    <div>
        <span class="stepno">3</span><br />
        <span class="stepdesc">Set Password</span>
    </div>
    <div class="future">
        <span class="stepno">4</span><br />
        <span class="stepdesc">Configure Uplink</span>
    </div>
    <div class="future">
        <span class="stepno">5</span><br />
        <span class="stepdesc">Configuration Complete</span>
    </div>
</div>
<br clear="all" />
%s
%s<br /><br />
<b>Note:&nbsp;</b><br />
<ul>
<li>This password is only used on your wireless network and must
be different to the password used to connect to your ISP.</li>
<li>The password must be at least 8 characters long.</li>
</ul>
<br />
<table>
<tr>
    <th>Device Password:</th>
    <td>
    <input type="text" id="wizard_password" name="wizard_password" value="">
    </td>
</tr>
</table>
<br />
<a href="javascript:prevStep()" class="prev">&lt;&lt;&nbsp;&nbsp;Prev&nbsp;Step</a>
<a href="javascript:nextStep()" class="next">Next&nbsp;Step&nbsp;&nbsp;&gt;&gt;</a>
<br clear="all" />
</div>
""" % (statustxt, passworddetails)

    if step==4 or ajaxWizard:
        # Setup Uplink configuration
        if isMasterNode():
            # Get ISP connection details
            uplinkdetails = """
Please select your ISP from the list below and enter the username and password
supplied to you by your ISP.<br /><br />
<b>Note:&nbsp;</b>This password is assigned by your ISP and is different to the
password your chose in the previous step.<br /><br />
<table>        
<tr>
<th width="20%%">Connection Type</th>
<td>%s</td>
</tr>
<tr id="wizard_ispusername_row">
<th width="20%%">Username</th>
<td>
<input type="input" value="" id="wizard_ispusername" name="wizard_ispusername">
</td>
</tr>
<tr id="wizard_isppassword_row">
<th width="20%%">Password</th>
<td>
<input type="text" value="" id="wizard_isppassword" name="wizard_isppassword">
</td>
</tr>
<tr id="wizard_ethmode_row" style="display:none;">
<th width="20%%">Operating Mode</th>
<td>
<select id="wizard_ethmode" name="wizard_ethmode" value="dhcp">
<option value="dhcp" selected>DHCP</option>
<option value="static">Static IP</option>
</select>
</td>
</tr>
<tr id="wizard_ethip_row" style="display:none;">
<th width="20%%">IP Address</th>
<td>
<input type="text" value="" id="wizard_ethip" name="wizard_ethip">
</td>
</tr>
<tr id="wizard_ethnetmask_row" style="display:none;">
<th width="20%%">Netmask</th>
<td>
<input type="text" value="" id="wizard_ethnetmask" name="wizard_ethnetmask">
</td>
</tr>
<tr id="wizard_ethgw_row" style="display:none;">
<th width="20%%">Default Gateway</th>
<td>
<input type="text" value="" id="wizard_ethgw" name="wizard_ethgw">
</td>
</tr>
</table>
<br />
""" % generateSelect("wizard_isptype", ISP_BCL, RL_ISPS)
        else:
            # Get Backhaul connection details
            (html, othernets) = getBackhaulHTML(False, "wizard_")
            uplinkdetails = """Please select the device you wish to connect
to from the list below.<br /><br />
If the device you wish to connect to is not shown and you have verified that 
it is correctly configured, you may click below to perform another scan.<br />
<br />
<b>Note:</b> After selecting an upstream device it may take up to 1 minute
before the next step is displayed while this node is registered.<br />
<br />
<div style="width:90%%">%s</div>
<div style="text-align:center;">
<input type="button" value="Perform New Scan" onclick="wizardRefreshBackhaul();" />
</div>
""" % html
        
        content += """
<div class="wizard" id="step4"> 
<h2>Rural Link CPE Setup Wizard - Configure Uplink</h2><br />
<div class="progressbar">
    <div class="past">
        <span class="stepno">1</span><br />
        <span class="stepdesc">Introduction</span>
    </div>
    <div class="past">
        <span class="stepno">2</span><br />
        <span class="stepdesc">Set Hostname</span>
    </div>
    <div class="past">
        <span class="stepno">3</span><br />
        <span class="stepdesc">Set Password</span>
    </div>
    <div>
        <span class="stepno">4</span><br />
        <span class="stepdesc">Configure Uplink</span>
    </div>
    <div class="future">
        <span class="stepno">5</span><br />
        <span class="stepdesc">Configuration Complete</span>
    </div>
</div>
<br clear="all" />
%s
%s
<br />
<a href="javascript:prevStep()" class="prev">&lt;&lt;&nbsp;&nbsp;Prev&nbsp;Step</a>
<a href="javascript:nextStep()" class="next">Next&nbsp;Step&nbsp;&nbsp;&gt;&gt;</a>
<br clear="all" />
</div>
""" % (statustxt, uplinkdetails)

    if step==5 or ajaxWizard:
        finalinstructions = ""
        if rl_isptype == ISP_ETH or ajaxWizard:
            finalinstructions += """<span id="eth-note">
As you have choosen to use the Ethernet backhaul configuration you will need to
unplug the device from the computer you used to configure it and connect it to
your network at this point.</span><br /><br />"""

        content += """
<div class="wizard" id="step5"> 
<h2>Rural Link CPE Setup Wizard - Complete</h2><br />
<div class="progressbar">
    <div class="past">
        <span class="stepno">1</span><br />
        <span class="stepdesc">Introduction</span>
    </div>
    <div class="past">
        <span class="stepno">2</span><br />
        <span class="stepdesc">Set Hostname</span>
    </div>
    <div class="past">
        <span class="stepno">3</span><br />
        <span class="stepdesc">Set Password</span>
    </div>
    <div class="past">
        <span class="stepno">4</span><br />
        <span class="stepdesc">Configure Uplink</span>
    </div>
    <div>
        <span class="stepno">5</span><br />
        <span class="stepdesc">Configuration Complete</span>
    </div>
</div>
<br clear="all" />
%s
Thank you. Your Rural Link device is nearly ready to use. 
<br /><br />
%s
<span id="home-note">To finalise your settings and complete this wizard please
click the button below.</span>
<br /><br />
<div style="text-align:center;">
<a href="/disablewizard" class="disablewizard">Finalise Settings &gt;&gt;</a>
</div>
<br />
</div>
<div id="updatewindow">
</div>
""" % (statustxt, finalinstructions)

    if not ajaxWizard:
        content += """</form>"""

    # Substitute as necessary
    title = "Rural Link CPE Setup Wizard"
    menustr = stylestr = ""
    scriptstr = """<script type="text/javascript" src="%s"></script>\n""" % \
            "/resources/rurallink.js"
    footer = "Page generated at: %s" % time.ctime()
    output = template.replace("%SCRIPTS%", scriptstr).replace("%STYLES%", \
            stylestr).replace("%TITLE%", title).replace("%MENU%", \
            menustr).replace("%CONTENT%", content).replace("%FOOTER%", \
            footer)
            
    # Send it away
    request.send_response(200)
    request.end_headers()
    request.wfile.write(output)
    request.finish()

@registerPage("/rladmin", requireAuth=True, realm=CPE_ADMIN_REALM)
def rladmin(request, method, returnDirect=True):
    """Returns the HTML for RuralLink administration page"""
    global rl_serialno, rl_password
    global backhaul_ifname, ap0_ifname, int_ifname, channels, rl_isptype
    
    isperr = ""
    etherr = ""
    
    if method == "POST":
        data = request.getPostData()
        # Incoming data
        invalid=True
        if "password" in data.keys():
            try:
                if data["password"] == "":
                    raise ccs_rurallink_error("Cannot set blank password!")
                if len(data["password"]) < 8:
                    raise ccs_rurallink_error("Password must be at " \
                            "least 8 characters!")
                # Now change the password
                rl_password = data["password"]
                admin_pass = crypt.crypt(rl_password, createSalt())
                pref_set("rurallink", "password", rl_password, \
                        getMonitorPrefs())
                # Change the CPE administration password as well
                pref_set(None, "admin_password", admin_pass, getMonitorPrefs())
                realm = getRealm()
                realm["users"][ADMIN_USERNAME] = admin_pass
                registerRealm(CPE_ADMIN_REALM, realm, overwrite=True)
                # Reconfigure interfaces as WEP key will have changed
                ifaces = debian_interfaces()
                if backhaul_ifname is not None:
                    ifaces[backhaul_ifname] = \
                            createBackhaulConfig(ifaces[backhaul_ifname])
                    log_command("/sbin/iwconfig %s key s:%s" % \
                            (backhaul_ifname, getWEPKey()))
                if ap0_ifname is not None:
                    ifaces[ap0_ifname] = \
                            createAP0Config(ifaces[ap0_ifname])
                    log_command("/sbin/iwconfig %s key s:%s" % \
                            (ap0_ifname, getWEPKey()))
                try:
                    remountrw("rladmin-password")
                    ifaces.write()
                finally:
                    remountro("rladmin-password")
            except ccs_rurallink_error:
                (type, value, tb) = sys.exc_info()
                request.send_error(400, value)
                request.end_headers()
                request.finish()
                return
            except:
                log_error("Failed to change rurallink password!", \
                        sys.exc_info())
                request.send_error(400, "Unexpected Error")
                request.end_headers()
                request.finish()
                return
            request.send_response(200, "Password updated")
            request.end_headers()
            rval = "%s:%s:%s" % (rl_password, getWEPKey(True), getWEPKey())
            request.wfile.write(rval)
            request.finish()
            return
        elif "ap0_channel" in data.keys() and ap0_ifname is not None:
            channel = int(data["ap0_channel"])
            if channel not in channels.keys():
                request.send_error(400, "Invalid channel value!")
                request.end_headers()
                request.finish()
                return
            rv = -1
            try:
                interfaces = debian_interfaces()
                t = interfaces[ap0_ifname]
                t["wireless_channel"] = channel
                interfaces[ap0_ifname] = t
                try:
                    remountrw("rladmin-ap0channel")
                    interfaces.write()
                finally:
                    remountro("rladmin-ap0channel")
                if log_command("/sbin/iwconfig %s channel %s 2>&1" % \
                        (ap0_ifname, channel)) != None:
                    raise Exception("Failed to set new interface channel!")
            except:
                log_error("Failed to change ap channel!", sys.exc_info())
                request.send_error(400, "Unable to update channel")
                request.end_headers()
                request.finish()
                return
            request.send_response(200, "Channel changed")
            request.end_headers()
            request.wfile.write(channel)
            request.finish()
            return
        elif "username" in data.keys():
            try:
                if "pass" not in data.keys():
                    raise ccs_rurallink_error("Missing post variables!")
                username = urllib.unquote(data["username"]).strip()
                password = urllib.unquote(data["pass"]).strip()
                updateISP(username, password)
            except:
                log_error("Exception setting ISP password", sys.exc_info())
                isperr = "Failed to update username and password"
            invalid = False
        elif "isptype" in data.keys():
            try:
                changeISP(data["isptype"])
            except:
                log_error("Exception setting ISP type", sys.exc_info())
                isperr = "Failed to update isp type"
            invalid = False
        elif "ethmode" in data.keys():
            elems = {"ethip":"IP", "ethnetmask":"netmask", "ethgw":"gateway"}
            try:
                # Validate incoming data
                if data["ethmode"] not in ["dhcp", "static"]:
                    raise ccs_rurallink_error("Invalid Ethernet mode!")
                if data["ethmode"] == "static":
                    for e in elems:
                        if e not in data.keys():
                            raise ccs_rurallink_error("Ethernet %s not " \
                                    "specified!" % elems[e])
                        if not isValidIP(data[e]):
                            raise ccs_rurallink_error("Invalid Ethernet " \
                                    "%s" % elems[e])
                    network = ipnetwork(ipnum(data["ethip"]), \
                            ipnum(data["ethnetmask"]))                    
                    if not inNetwork(ipnum(data["ethgw"]), network, \
                            ipnum(data["ethnetmask"])):
                        raise ccs_rurallink_error("Invalid gateway address!")
                # Set the mode
                pref_set("rurallink", "ethmode", data["ethmode"], \
                        getMonitorPrefs())
                # Set static IP details if necessary
                if data["ethmode"] == "static":
                    for e in elems:
                        pref_set("rurallink", e, data[e], getMonitorPrefs())
                # Regenerate the interface configuration
                checkMasterInterfaces()
                # Don't reload configuration automatically...
                # Let the user explicitly do that, seeing as it might break
                # their connectivity...
            except ccs_rurallink_error:
                type, value, tb = sys.exc_info()
                log_error("Error setting Ethernet backhaul parameters: %s" % \
                        value)
                etherr = value
            except:
                log_error("Exception setting Ethernet backhaul parameters", \
                        sys.exc_info())
                etherr = "Failed to update Ethernet backhaul parameters"
            invalid = False
        elif "reset" in data.keys():
            try:
                # Try and return the device to a "factory default" config
                remountrw("factory-reset")
                # Delete preferences
                os.system("rm -f %s" % config_get("www", "preferences", 
                    DEFAULT_PREF_FILE))
                # Delete associations
                os.system("rm -f %s/*.assoc" % ASSOC_STORE_DIR)
                # Delete traffic management passwords
                os.system("rm -f %s" % config_get("traffic", "passwd_file", \
                        DEFAULT_TRAFFIC_PASSWD_FILE))
                # Reset hostname
                os.system("echo 'rl-%s' > /etc/hostname" % rl_serialno)
                log_command("/bin/hostname -F /etc/hostname 2>&1")
                # Reset Resolvers
                os.system("echo 'search rurallink.co.nz\n" \
                        "nameserver 127.0.0.1\n' > /etc/resolv.conf")
                # Reset interfaces
                ifaces = debian_interfaces()
                for ifname in ifaces.keys():
                    if ifname in \
                            [ap0_ifname, backhaul_ifname, int_ifname]:
                        del ifaces[ifname]
                ifaces.write()
                # Reset DHCP
                dhcp = dhcpd_conf()
                for name in dhcp.keys():
                    del dhcp[name]
                dhcp.write()
                remountro("factory-reset")
            except:
                remountro("factory-reset")
                log_error("Exception resetting device", sys.exc_info())
                request.send_error(400, "Failed to reset device")
                request.end_headers()
                request.finish()
                return
            log_info("Device reset complete. Factory configuration restored")
            request.send_response(200, "Device reset")
            request.end_headers()
            request.finish()
            return
        elif "restart" in data.keys():
            # Device config has been reset, restart crcnet-monitor
            log_info("Received restart request from %s. Restarting..." % \
                    request.client_address[0])
            os.system("/etc/init.d/rurallink-monitor restart & 2>&1")
            request.send_response(200, "Device restarted")
            request.end_headers()
            request.finish()
            return
        
        if invalid:
            log_warn("Invalid POST request to /rladmin from %s" %
                    request.client_address[0]) 
            request.send_error(400, "Invalid method for this page!")
            request.end_headers()
            request.finish()
            return

    # Work out the WEP key
    wep = getWEPKey()
    wep_hex = getWEPKey(True)
    
    # Normal page GET
    output = """<div id="rladmin" class="content">
<h2>RuralLink CPE Administration</h2><br />
<style>
TH:first-child {
    width: 14em;
}
</style>

<table>
<tr>
    <th>CPE Serial no:</th>
    <td>%s</td>
</tr>
<tr>
    <th valign="top">Password:</th>
    <td><input id="password" value="%s"><br /><small>This password is used to
    control access to your wireless network.<br>It <b>must not</b> be the same
    as your Internet password. The password must be at least 8 characters long.
    </small></td> 
</tr>
<tr>
    <th valign="top">WEP Key:</th>
    <td>
<table>
<tr><th>Hexadecimal</th><td id="wephex">%s</td></tr>
<tr><th>ASCII</th><td id="wep">%s</td></tr>
</table>
    <small>The WEP key is derived from your network password and cannot be 
    changed separately.</small>
    </td>
</tr>
<tr>
    <th>Reset Device:</th>
    <td><input type="button" value="Reset to Default Settings" id="factory_reset"></td>
</tr>
</table>
<br />
""" % (rl_serialno, rl_password, wep_hex, wep)

    # Configure an ISP interface
    #################################
    if isMasterNode():
        if request.path.endswith("isp-connect"):
            gwstatus, gwtext, ispstatus, isptext, ispaction = ISPConnect()
        elif request.path.endswith("isp-disconnect"):
            gwstatus, gwtext, ispstatus, isptext, ispaction = ISPDisconnect()
        else:
            gwstatus, gwtext, ispstatus, isptext, ispaction = getISPStatus()
        ispuser = getISPUser()
        if isperr != "":
            isperr = """<br /><span class="error">%s</span><br /><br />""" % \
                isperr
        fwstatus, fwtext, fwaction = checkFirewall()
        output += """
<h2>Internet Connection Settings</h2><br />
<table>
<tr>
    <th>Connection Type:</th>
    <td><form action="/rladmin" method="post">%s</form></td>
</tr>
<tr>
    <th>Connection Status:</th>
    <td><span class="status%s">%s</span>&nbsp;&nbsp;%s</td>
</tr>
<tr>
    <th>Default Gateway</th>
    <td class="status%s">%s</td>
</tr>
<tr>
    <th>Firewall Status:</th>
    <td><span class="status%s">%s</span>&nbsp;&nbsp;%s</td>
</tr>""" % (generateSelect("isptype", rl_isptype, RL_ISPS), ispstatus, \
        isptext, ispaction, gwstatus, gwtext, fwstatus, fwtext, fwaction)

        # Retrieve ethernet details
        ethmode = pref_get("rurallink", "ethmode", getMonitorPrefs(), "dhcp")
        ethip = pref_get("rurallink", "ethip", getMonitorPrefs(), "")
        ethnetmask = pref_get("rurallink", "ethnetmask", getMonitorPrefs(), "")
        ethgw = pref_get("rurallink", "ethgw", getMonitorPrefs(), "")

        # Work out what should be displayed and hidden
        ispauth_class=""
        ethopts_class=""" style="display: none;" """
        ethstatic_class=""" style="display: none;" """
        if rl_isptype == ISP_ETH:
            ispauth_class=""" style="display: none;" """
            ethopts_class=""
            if ethmode == "static":
                ethstatic_class=""
        
        # Write out the ISP authentication block
        output += """
<tr id="username_row" %s>
    <th>Current Username</th>
    <td>%s</td>
</tr>
</table>
%s
<script language="javascript" type="text/javascript">
function displayauth() {
	$('ispauthdetails').style.display = 'block';
}
</script>
<a href="javascript:displayauth();" id="auth_link" %s>
Click here to change your ISP authentication details</a><br />
<div id="ispauthdetails" style="display: none;">
<form method="POST" action="/rladmin">
<table>
<tr>
<th width="20%%">Username</th>
<td><input type="input" value="" name="username"></td>
</tr>
<tr>
<th width="20%%">Password</th>
<td><input type="password" value="" name="pass"></td>
</tr>
<tr>
<td>&nbsp;</td>
<td><input type="submit" value="Update ISP Details"></td>
</tr>
</table>
</form>
</div>
""" % (ispauth_class, ispuser, isperr, ispauth_class)

        # Write out the ethernet options block
        display = """ style="display: none;" """
        if etherr != "":
            etherr = """<br /><span class="error">%s</span><br /><br />""" % \
                    etherr
            display = ""
        output += """
<script language="javascript" type="text/javascript">
function displayeth() {
	$('ethdetails').style.display = 'block';
}
</script>
<a href="javascript:displayeth();" id="auth_link" %s>
Click here to change your Ethernet settings</a><br />
<div id="ethdetails" %s>
%s
<form method="POST" action="/rladmin">
<table>
<tr id="ethmode_row">
<th width="20%%">Ethernet Mode</th>
<td>%s</td>
</tr>
<tr id="ethip_row" %s>
<th width="20%%">Ethernet IP</th>
<td>
<input type="text" value="%s" id="ethip" name="ethip">
</td>
</tr>
<tr id="ethnetmask_row" %s>
<th width="20%%">Ethernet Netmask</th>
<td>
<input type="text" value="%s" id="ethnetmask" name="ethnetmask">
</td>
</tr>
<tr id="ethgw_row" %s>
<th width="20%%">Ethernet Gateway</th>
<td>
<input type="text" value="%s" id="ethgw" name="ethgw">
</td>
</tr>
<tr>
<td>&nbsp;</td>
<td><input type="submit" value="Update Ethernet Details"></td>
</tr>
</table>
</form>
</div>
<br />
<a href="/traffic/admin">Edit Traffic Management Accounts&nbsp;&gt;&gt;</a>
<br /><br />
""" % (ethopts_class, display, etherr, \
        generateSelect("ethmode", ethmode, \
        {"dhcp":"DHCP", "static":"Static IP"}), ethstatic_class, ethip, \
        ethstatic_class, ethnetmask, ethstatic_class, ethgw)

    # Configure a backhaul interface
    #################################
    else:
        bhaul_status, bhaul_desc, stats = getBackhaulStatus()
        output += """
<h2>Backhaul Settings (using %s interface)</h2><br />
<table>
<tr>
    <th>Upstream Node:</th>
    <td><span class="status%s">%s</span>&nbsp;&nbsp;
    <a href="/rladmin/setup_backhaul">[change]</a>
    </td>
</tr>
<tr>
</table>
""" % (backhaul_ifname, bhaul_status, bhaul_desc)
        output += """<div id="ssmeter-%s" class="ssmeter">""" % backhaul_ifname
        output += getSSMeter(stats)
        output += "</div><br clear=\"all\" />"
        output += "<a href=\"/status/interfaces\">Click here for detailed " \
                "signal strength information</a><br /><br />"
                
    # Configure an AP interface
    #################################
    if ap0_ifname is not None:
        try:
            wiface = iwtools.get_interface(ap0_ifname)
            ap0_essid = wiface.get_essid()
            ap0_channel = wiface.get_channel()
        except:
            ap0_essid = "<span class=\"warning\">Unknown</span>"
            ap0_channel = -1
        ap0_channels = generateSelect("ap0_channel", ap0_channel, channels)
        ap0_policy = pref_get("traffic", "ap0_policy", getMonitorPrefs(), \
            DEFAULT_AP0_POLICY)
        ap0_firewall = generateSelect("ap0_policy", ap0_policy, \
                FIREWALL_NET_OPTIONS)
        output += """
<h2>Access Point Settings (using %s interface)</h2><br />
<table>
<tr>
    <th>ESSID:</th>
    <td>%s</td>
</tr>
<tr>
    <th>Channel:</th>
    <td>%s<br /><small>It is recommended that you select a channel marked
    with a <strong>*</strong>.</small>
    </td>
</tr>
""" % (ap0_ifname, ap0_essid, ap0_channels)
        if isMasterNode():
            output += """
<tr>
    <th>Access Policy:</th>
    <td>%s</td>
</tr>
<tr>
""" % ap0_firewall
        output += """
</table>
<a href="/status/interfaces">Click here for information on connected clients</a>
<br /><br />
"""

    # Configure an Internal interface
    #################################
    if isMasterNode() and int_ifname is not None:
        int_policy = pref_get("traffic", "internal_policy", getMonitorPrefs(), \
            DEFAULT_INTERNAL_POLICY)
        int_firewall = generateSelect("internal_policy", int_policy, \
                FIREWALL_NET_OPTIONS)
        output += """
<h2>Internal Network Settings (using %s interface)</h2><br />
<table>
<tr>
    <th>Access Policy:</th>
    <td>%s</td>
</tr>
<tr>
</table>
""" % (int_ifname, int_firewall)

    output += """
</div>
<div id="reset" class="content hidden">
<h2>Resetting Rural Link Device...</h2><br />
<br />
Please wait while your Rural Link device is reset to its factory configuration.
This process may take up to 2 minutes to complete successfully.<br />
<br />
<div id="resetstatus" style="font-weight:bold;"></div>
</div>
"""

        
    # Return the page
    if returnDirect:
        return returnPage(request, "RuralLink Administration", output, \
                scripts=["/resources/rurallink.js"])
    else:
        return output

def getBackhaulHTML(submitButtons=True, inputPrefix=""):
    global backhaul_ifname
    
    othernets = {}
    output = ""
    hostname = socket.gethostname()

    try:
        ensureBackhaulUp()
        wiface = iwtools.get_interface(backhaul_ifname)
        scanres = wiface.scanall()
    except:
        log_error("Could not complete scan on backhaul interface (%s)!" % \
                backhaul_ifname, sys.exc_info())
        scanres = []

    n=0
    for network in scanres:
        if not network.essid.startswith(RL_ESSID_PREFIX):
            # Skip non rurallink networks
            othernets[network.essid] = (network.channel, network.qual)
            continue
        # Get the node name from the ESSID
        parts = network.essid.split("-")
        if len(parts) < 3:
            othernets[network.essid] = (network.channel, network.qual)
            continue
        name = "-".join(parts[1:-1])
        iface = parts[-1]
        
        # Skip other interfaces on the same host
        if name == hostname:
            continue

        # Write the record
        output += """<h3>%s - (%s Interface)</h3>
        <div id="ssmeter-%s" class="ssmeter">%s</div>
        <div style="clear: all;">&nbsp;</div><br />
        """ % (name, iface, name, getSSMeter(network.qual))
        
        if submitButtons:
            output += """<form action="/rladmin/setup_backhaul" method="post">
            <input type="hidden" name="essid" value="%s" />
            <input type="submit" value="Connect to %s &gt;&gt;" />
            </form><br />""" % (network.essid, name)
        else:
            output += """Connect to <b>'%s'</b>&nbsp;<input type="radio" """ \
                    """id="%sessid" name="%sessid" value="%s" /><br />""" % \
                    (name, inputPrefix, inputPrefix, network.essid)
        output += "<br />"
        n+=1 

    if n==0:
        output += "<br /><b>No RuralLink devices found to connect to!</b>" \
                "<br /><br />"

    return (output, othernets)

@registerPage("/rladmin/setup_backhaul", requireAuth=True, \
        realm=CPE_ADMIN_REALM)
def rladmin_setupbackhaul(request, method):
    """Returns the HTML for RuralLink backhaul setup page"""
    global backhaul_ifname
    
    errmsg = ""

    if method == "POST":
        data = request.getPostData()
        # Incoming data
        if "essid" in data.keys():
            if configureBhaulInterface(data["essid"]):
                # Success - back to admin page
                return rladmin(request, "GET")
            # Failed
            parts = data["essid"].split("-")
            peer = "-".join(parts[1:-1])
            errmsg = "Failed to associate with %s" % peer
        
    # Normal page GET
    output = """<div class="content">
<h2>RuralLink CPE Administration - Configure Backhaul Interface</h2><br />
Please select the node to connect to from the following list.
<br /><br />
"""
    if errmsg != "":
        output += """<span class="error">%s</span><br /><br />""" % errmsg
        
    (toutput, othernets) = getBackhaulHTML()
    output += toutput

    if len(othernets.keys()) > 0:
        output += """<h2>Other networks</h2><br />
        The following other networks were detected. The RuralLink CPE is not
        able to automatically connect to these networks. You may need to
        co-ordinate channel usage with the operators of the listed 
        networks to minimise the chance of interference.<br /><br />
        """
        for essid, (channel,qual) in othernets.items():
            output += """<h3>%s on Channel %s</h3>
            <div id="ssmeter-%s" class="ssmeter">%s</div>
            <div style="clear: all;">&nbsp;</div><br /><br />
            """ % (essid, channel, essid, getSSMeter(qual))

    output += """<a href="/rladmin">&lt;&lt;&nbsp;Return to CPE 
    Administration page</a><br />"""

    return returnPage(request, "RuralLink Administration", output, \
                scripts=["/resources/rurallink.js"])

@registerPage("/masterip")
def masterip(request, method):
    """Outputs the IP address of the master node"""
    global rl_masterip
    
    request.send_response(200)
    request.end_headers()

    if isMasterNode():
        # Output the IP that the client is connected via
        masterip = getIfaceIPForIP(request.client_address[0])
        request.wfile.write(masterip)
    else:
        if rl_masterip is not None:
            request.wfile.write(rl_masterip)
        else:
            request.wfile.write("")

    request.finish()

@registerPage("/rlname")
def nodename(request, method):
    """Outputs the name of the client"""
    request.send_response(200)
    request.end_headers()
    request.wfile.write(socket.gethostname())
    request.finish()

@registerPage("/nodemap")
def serveNodemap(request, method):

    if not isMasterNode():
        request.send_error(400, "Only the master node can server a nodemap!")
        request.end_headers()
        request.finish()
        return
        
    nm_filename = "%s/nodemap" % config_get(None, "tmpdir", DEFAULT_TMPDIR)
    if not os.path.exists(nm_filename):
        buildNodemapFile(nm_filename)
    try:
        fp = open(nm_filename, "r")
        data = fp.read()
        fp.close()
    except:
        request.send_error(404, "The specified resource does not exist!")
        request.end_headers()
        request.finish()
        return
    request.send_response(200)
    request.send_header("Length", len(data))
    request.end_headers()
    request.wfile.write(data)
    request.finish()

@registerPage("/register_client")
def registerClient(request, method):
    """Called by a client to authenticate themselves to the access point"""
    
    parts = request.path.split("/")
    client_name = parts[len(parts)-1]
    log_info("Got register client request for %s" % client_name)
    
    # Check IP is directly connected
    in_iface = getIfaceForIP(request.client_address[0])
    ifaces = getInterfaces(returnOne=in_iface)
    if len(ifaces) != 1:
        # Cannot verify that this is a directly connected client
        log_error("Could not verify connection status for %s" % client_name)
        request.send_error(400, "Could not verify connection status for %s" % \
                client_name)
        request.end_headers()
        request.finish()
        return
    iface = ifaces[0]
    network = cidrToNetwork(iface["address"])
    netmask = cidrToNetmask(iface["address"])
    if not inNetwork(ipnum(request.client_address[0]), network, netmask):
        # Not a directly connected client
        log_error("%s is not directly connected" % client_name)
        request.send_error(401, "%s is not directly connected." % client_name)
        request.end_headers()
        request.finish()
        return
    
    # Get password / serial no.
    data = request.getPostData()
    if "password" not in data.keys() or "serialno" not in data.keys():
        log_error("Client registration request from %s is missing " \
                "required fields" % client_name)
        request.send_error(400, "Client registration request is missing " \
                "required fields.")
        request.end_headers()
        request.finish()
        return
        
    # Check password
    if data["password"] != rl_password:
        log_error("Invalid password in client registration from %s" % \
                client_name)
        request.send_error(400, "Invalid password in client registration " \
                "from %s" % client_name)
        request.end_headers()
        request.finish()
        return
    
    # Check serial 
    if not isValidRLSerialNo(data["serialno"]) or \
            data["serialno"]==rl_serialno:
        log_error("Invalid serial no in client registration from %s" % \
                client_name)
        request.send_error(400, "Invalid serial no in client registration " \
                "from %s" % client_name)
        request.end_headers()
        request.finish()
        return
        
    # Check for current registration status
    status = isClientAssociated(data["serialno"], client_name, \
            request.client_address[0])
    if status == client_name:
        log_info("Client (%s) already associated" % client_name)
        doSubClientRegistration(client_name, data["serialno"], \
                request.client_address[0])
        request.send_response(200, "Client already associated")
        request.end_headers()
        request.finish()
        return
    
    if status != "":
        # Registration does not match
        if status.find(".") == -1:
            # The device appears to have changed name
            updateClientAssociation(data["serialno"], client_name, \
                    request.client_address[0])    
            request.send_response(200, "Association updated successfully")
            request.end_headers()
            request.finish()
            return
        else:
            # The device has changed IP or is now registering on a different 
            # interface... Remove the old registration
            removeClientAssociation(data["serialno"])

    if not setupClientAssociation(data["serialno"], client_name, \
            request.client_address[0]):
        log_error("Failed to associate client: %s" % client_name)
        request.send_error(400, "Failed to associate client")
        request.end_headers()
        request.finish()
        return
        
    log_info("Client (%s) associated successfully" % client_name)
    request.send_response(200, "Client associated successfully")
    request.end_headers()
    request.finish()
    return

@registerPage("/unregister_client")
def unregisterClient(request, method):
    """Called by a client to unauthenticate themselves to the access point"""
    
    parts = request.path.split("/")
    client_name = parts[len(parts)-1]
    
    # Check IP is directly connected
    in_iface = getIfaceForIP(request.client_address[0])
    ifaces = getInterfaces(returnOne=in_iface)
    if len(ifaces) != 1:
        # Cannot verify that this is a directly connected client
        request.send_error(400, "Could not verify connection status for %s" % \
                client_name)
        request.end_headers()
        request.finish()
        return
    iface = ifaces[0]
    network = cidrToNetwork(iface["address"])
    netmask = cidrToNetmask(iface["address"])
    if not inNetwork(ipnum(request.client_address[0]), network, netmask):
        # Not a directly connected client
        request.send_error(401, "%s is not directly connected." % client_name)
        request.end_headers()
        request.finish()
        return
    
    # Get password / serial no.
    data = request.getPostData()
    if "password" not in data.keys() or "serialno" not in data.keys():
        request.send_error(400, "Request is missing required fields.")
        request.end_headers()
        request.finish()
        return
        
    # Check password
    if data["password"] != rl_password:
        request.send_error(400, "Invalid password.")
        request.end_headers()
        request.finish()
        return
    
    # Check serial 
    if not isValidRLSerialNo(data["serialno"]) or \
            data["serialno"]==rl_serialno:
        request.send_error(400, "Invalid serial no.")
        request.end_headers()
        request.finish()
        return
        
    removeClientAssociation(data["serialno"])
        
    request.send_response(200, "Client successfully unassociated")
    request.end_headers()
    request.finish()
    return

@registerPage("/register_subclient")
def registerSubclient(request, method):
    """Called by a client to tell us they have registered a client"""
    
    parts = request.path.split("/")
    client_name = parts[len(parts)-1]
    ip = request.client_address[0]
    log_info("Received a subclient registration for (%s) from %s" % \
            (client_name, ip))
    
    # Check IP is directly connected
    in_iface = getIfaceForIP(ip)
    ifaces = getInterfaces(returnOne=in_iface)
    if len(ifaces) != 1:
        # Cannot verify that this is a directly connected client
        log_error("Could not register subclient (%s) from %s, unable " \
                "to get iface object" % (client_name, ip))
        request.send_error(400, "Could not verify connection status for %s" % \
                client_name)
        request.end_headers()
        request.finish()
        return
    iface = ifaces[0]
    network = cidrToNetwork(iface["address"])
    netmask = cidrToNetmask(iface["address"])
    if not inNetwork(ipnum(ip), network, netmask):
        # Not a directly connected client
        log_error("Cannot register subclient (%s) of non-connected node %s" % \
                (client_name, ip))
        request.send_error(401, "Only directly connected clients can " \
                "register subclients.")
        request.end_headers()
        request.finish()
        return
    
    # Get password / serial no.
    data = request.getPostData()
    if "password" not in data.keys() or "serialno" not in data.keys() or \
            "client_name" not in data.keys() or "client_serialno" not in \
            data.keys() or "client_ip" not in data.keys():
        log_error("Subclient registration for (%s) from %s missing fields " \
                "(%s)!" % (client_name, ip, data.keys()))                
        request.send_error(400, "Request is missing required fields.")
        request.end_headers()
        request.finish()
        return
        
    # Check password
    if data["password"] != rl_password:
        log_error("Could not register subclient (%s) of %s. " \
                "Invalid password!" % (client_name, ip))
        request.send_error(400, "Invalid password.")
        request.end_headers()
        request.finish()
        return
    
    # Check serials
    if not isValidRLSerialNo(data["serialno"]) or \
            data["serialno"]==rl_serialno:
        log_error("Could not register subclient (%s) of %s. " \
                "Invalid serial no (%s)!" % \
                (client_name, ip, data["serialno"]))
        request.send_error(400, "Invalid serial no.")
        request.end_headers()
        request.finish()
        return
    if not isValidRLSerialNo(data["client_serialno"]) or \
            data["client_serialno"]==rl_serialno:
        log_error("Could not register subclient (%s) of %s. " \
                "Invalid client serial no (%s)!" % \
                (client_name, ip, data["client_serialno"]))
        request.send_error(400, "Invalid serial no.")
        request.end_headers()
        request.finish()
        return
        
    # Check that the registering node is associated
    status = isClientAssociated(data["serialno"], client_name, \
            request.client_address[0])
    if status != client_name:
        log_error("Could not register subclient (%s) of non-associated " \
                "node %s" % (client_name, ip))
        request.send_error(400, "You must associate before registering " \
                "sub clients!")
        request.end_headers()
        request.finish()
        return
    
    # Check if the subclient is registered
    status = isSubClientAssociated(request.client_address[0], \
            data["client_serialno"], data["client_name"], data["client_ip"])
    if status == data["client_name"]:
        log_info("Subclient (%s) of %s already registered" % \
                (client_name, ip))
        doSubClientRegistration(data["client_name"], data["client_serialno"], \
                data["client_ip"])
        request.send_response(200, "Subclient already registered")
        request.end_headers()
        request.finish()
        return
    
    if status != "":
        # Registration does not match
        if status.find(".") == -1:
            # The device appears to have changed name
            updateSubClientAssociation(request.client_address[0], \
                    data["client_serialno"], data["client_name"], \
                    data["client_ip"])
            log_info("Updated subclient registration for (%s) of %s" % \
                    (client_name, ip))
            request.send_response(200, "Association updated successfully")
            request.end_headers()
            request.finish()
            return
        else:
            # The device has changed IP or is now registering on a different 
            # interface... Remove the old registration
            removeSubClientAssociation(request.client_address[0], \
                    data["client_serialno"])
 
    if not setupSubClientAssociation(request.client_address[0], \
            data["client_serialno"], data["client_name"], data["client_ip"]):
        request.send_error(400, "Failed to associate client")
        request.end_headers()
        request.finish()
        return
        
    request.send_response(200, "Client associated successfully")
    request.end_headers()
    request.finish()
    return

@registerPage("/unregister_subclient")
def unregisterSubclient(request, method):
    """Called by a client to tell us they nolonger server a subclient"""
    
    parts = request.path.split("/")
    client_name = parts[len(parts)-1]
    
    # Check IP is directly connected
    in_iface = getIfaceForIP(request.client_address[0])
    ifaces = getInterfaces(returnOne=in_iface)
    if len(ifaces) != 1:
        # Cannot verify that this is a directly connected client
        request.send_error(400, "Could not verify connection status for %s" % \
                client_name)
        request.end_headers()
        request.finish()
        return
    iface = ifaces[0]
    network = cidrToNetwork(iface["address"])
    netmask = cidrToNetmask(iface["address"])
    if not inNetwork(ipnum(request.client_address[0]), network, netmask):
        # Not a directly connected client
        request.send_error(401, "Only directly connected clients can " \
                "register subclients.")
        request.end_headers()
        request.finish()
        return
    
    # Get password / serial no.
    data = request.getPostData()
    if "password" not in data.keys() or "serialno" not in data.keys() or \
            "client_serialno" not in data.keys():
        request.send_error(400, "Request is missing required fields.")
        request.end_headers()
        request.finish()
        return
        
    # Check password
    if data["password"] != rl_password:
        request.send_error(400, "Invalid password.")
        request.end_headers()
        request.finish()
        return
    
    # Check serials
    if not isValidRLSerialNo(data["serialno"]) or \
            data["serialno"]==rl_serialno:
        request.send_error(400, "Invalid serial no.")
        request.end_headers()
        request.finish()
        return
    if not isValidRLSerialNo(data["client_serialno"]) or \
            data["client_serialno"]==rl_serialno:
        request.send_error(400, "Invalid serial no.")
        request.end_headers()
        request.finish()
        return

    removeSubClientAssociation(request.client_address[0], \
            data["client_serialno"])
    
    request.send_response(200, "Subclientsuccessfully unassociated")
    request.end_headers()
    request.finish()
    return

@registerPage("/traffic/logout")
def toggleaccount(request, method):
    """Logs the user out"""
    
    request.logoutRealm(CPE_ADMIN_REALM)
    
    output = """<div class="content"><h2>Logged Out</h2>
<br />
You have been successfully logged out.<br />
"""
    returnPage(request, "Logged Out", output)

@registerPage("/traffic/toggle", requireAuth=True, realm=CPE_ADMIN_REALM)
def toggleaccount(request, method):
    """Toggles the state of the specified user
    
    Where the user is specified in the URL e.g:
        /traffic/toggle/<username>
    """
    global rl_trafficusers
    
    parts = request.path.split("/")
    username = parts[len(parts)-1]
    errMsg = ""
    
    if username not in rl_trafficusers.keys():
        returnErrorPage(request, "Invalid username!")
        return

    rl_trafficusers[username]["enabled"] = \
            not rl_trafficusers[username]["enabled"]
    writeTrafficUsers()
    return trafficadmin(request, "GET")

@registerPage("/traffic/remove", requireAuth=True, realm=CPE_ADMIN_REALM)
def removeaccount(request, method):
    """Removes the specified user
    
    Where the user is specified in the URL e.g:
        /traffic/remove/<username>
    """
    global rl_trafficusers
    
    parts = request.path.split("/")
    username = parts[len(parts)-1]
    
    if username not in rl_trafficusers.keys():
        returnErrorPage(request, "Invalid username!")
        return

    if method == "POST":
        # Assume the form has been filled in, validate and try to change pass
        vars = request.getPostData()
        if "confirm" in vars.keys() and vars["confirm"]=="yes":
            del rl_trafficusers[username]
            writeTrafficUsers()
        # No confirmation, no action
        return trafficadmin(request, "GET")

    # Display the form to confirm the remove
    output = """<div class="content"><h2>IP Traffic Administration</h2>
<br />
Are you sure you want to remove the account '%s'?<br />
<br />
<style>
FORM {
    display: inline;
    margin-right: 10px;
}
FORM INPUT {
    background-color: transparent;
    border: 0px;
    color: #225599;
	text-decoration: none;
    cursor: pointer;
}
FORM INPUT:hover {
    color:  #0044FF;
}
</style>
""" % username
    if rl_trafficusers[username]["enabled"]:
        output += """
You may wish to disable this account (which will prevent it from being used
to access the Internet until it is re-enabled) instead of completely removing
it.<br />
<br />
<form action="/traffic/toggle/%s" method="POST">
<input type="submit" value="&lt;&lt; No - Disable Account" />
</form>
""" % username
    output += """
<form action="/traffic/remove/%s" method="POST">
<input type="hidden" value="yes" name="confirm" />
<input type="submit" value="Yes - Remove Account &gt;&gt;" />
</form>

""" % username

    returnPage(request, "Remove User", output)

@registerPage("/traffic/chpass", requireAuth=True, realm=CPE_ADMIN_REALM)
def chpass(request, method):
    """Changes the password for the specified user
    
    Where the user is specified in the URL e.g:
        /traffic/chpass/<username>
    """
    global rl_trafficusers
    
    parts = request.path.split("/")
    username = parts[len(parts)-1]
    errMsg = ""
    
    if username not in rl_trafficusers.keys():
        returnErrorPage(request, "Invalid username!")
        return

    if method == "POST":
        # Assume the form has been filled in, validate and try to change pass
        vars = request.getPostData()
        if "pass1" not in vars.keys() or "pass2" not in vars.keys():
            returnErrorPage(request, "Missing post variables!")
            return
        if vars["pass1"] == vars["pass2"]:
            rl_trafficusers[username]["passwd"] = crypt.crypt(vars["pass1"], \
                    createSalt())
            writeTrafficUsers()
            return trafficadmin(request, "GET")
        # Passwords did not match, display an error
        errMsg = """<br /><span class="error">Passwords did not match""" \
                """</span><br />"""

    # Display the form to get a new password
    output = """<div class="content"><h2>IP Traffic Administration</h2>
<br />%s
Please enter a new password for '%s'<br />
<br />
<form method="POST" action="/traffic/chpass/%s">
<table>
<tr>
<th width="20%%">Password</th>
<td><input type="password" value="" name="pass1"></td>
</tr>
<tr>
<th width="20%%">Password Again</th>
<td><input type="password" value="" name="pass2"></td>
</tr>
<tr>
<td>&nbsp;</td>
<td><input type="submit" value="Change Password"></td>
</tr>
</table>
""" % (errMsg, username, username)

    returnPage(request, "Change Password", output)
    
@registerPage("/traffic/add", requireAuth=True, realm=CPE_ADMIN_REALM)
def create_account(request, method):
    """Adds a new user"""
    global rl_trafficusers

    errMsg = ""
    if method == "POST":
        # Assume the form has been filled in, validate and try to add
        vars = request.getPostData()
        if "pass" not in vars.keys() or "username" not in vars.keys():
            returnErrorPage(request, "Missing post variables!")
            return
        username = vars["username"]
        if re.match(USERNAME_CHAR_RE, username) is None:
            errMsg = "<span class=\"error\">Invalid characters in username!" \
                    "</span>"
        else:
            password = vars["pass"]
            rl_trafficusers[username] = \
                {"username":username, "enabled":True, "traffic":0, "ip":None}
            rl_trafficusers[username]["passwd"] = \
                    crypt.crypt(password, createSalt())
            writeTrafficUsers()
            return trafficadmin(request, "GET")

    # Display the form to get a new password
    output = """<div class="content"><h2>IP Traffic Administration</h2>
<br />%s
Please enter the details for the new user below<br />
<br />
<form method="POST" action="/traffic/add">
<table>
<tr>
<th width="20%%">Username</th>
<td><input type="input" value="" name="username"></td>
</tr>
<tr>
<th width="20%%">Password</th>
<td><input type="password" value="" name="pass"></td>
</tr>
<tr>
<td>&nbsp;</td>
<td><input type="submit" value="Create User"></td>
</tr>
</table>
""" % (errMsg)

    returnPage(request, "Change Password", output)

@registerPage("/traffic/policy", requireAuth=True, realm=CPE_ADMIN_REALM)
def trafficpolicy(request, method):
    """Changes the access policy for the specified network
    
    The network is specified in the URL e.g:
        /traffic/policy/<network>
    The policy for the network should be specified in the post vars.
    """
    global int_ifname, ap0_ifname
    
    if method != "POST":
        # Require changes to be POSTed
        request.send_header("Allow", "POST")
        request.send_error(405, "This URL only handles POST requests")
        request.end_headers()
        request.finish()
        return

    parts = request.path.split("/")
    network = parts[len(parts)-1]
    
    if network not in ["internal", "ap0"]:
        # Unknown network
        request.send_error(404, "Cannot set policy for unknown network!")
        request.end_headers()
        request.finish()
        return
    
    vars = request.getPostData()
    if "policy" not in vars.keys():
        # No policy specified
        request.send_error(400, "No policy specified!")
        request.end_headers()
        request.finish()
        return
        
    policy = vars["policy"]
    if policy not in FIREWALL_NET_OPTIONS.keys():
        # Invalid policy
        request.send_error(400, "Invalid policy specified! Options are: %s" \
                % ", ".join(FIREWALL_NET_OPTIONS.keys()))
        request.end_headers()
        request.finish()
        return
    
    # Update the policy
    pref_set("traffic", "%s_policy" % network, policy, getMonitorPrefs())
    
    # Now update the actual firewall
    request.send_response(200, "Policy updated")
    request.end_headers()
    request.finish()

    doFirewall("start")

@registerPage("/traffic/firewall", requireAuth=True, realm=CPE_ADMIN_REALM)
def trafficfirewall(request, method):
    """Manipulates the firewall"""

    parts = request.path.split("/")
    mode = parts[len(parts)-1]

    try:
        doFirewall(mode)
    except:
        (type, value, tb) = sys.exc_info()
        log_debug("Firewall manipulation request failed!", (type, value, tb))
    
    # Redirect the admin page
    request.send_response(302, "Firewall updated")
    request.send_header("Location", "/rladmin")
    request.end_headers()
    request.wfile.write(rladmin(request, method, False))
    request.finish()

@registerPage("/traffic/admin", requireAuth=True, realm=CPE_ADMIN_REALM)
def trafficadmin(request, method):
    """Returns the HTML for the network traffic administration page"""
    global rl_trafficusers
    
    output = """<div class="content"><h2>IP Traffic Administration</h2>"""
    output += "<br />"
    
    # Setup actions and status fields
    tusers = []
    for username,user in rl_trafficusers.items():
        tuser = {}
        if not user["enabled"]:
            tuser["status"] = "critical"
            tuser["statusdesc"] = "Disabled"
            toggle_state = "enable"
        else:
            tuser["status"] = "ok"
            if user["ip"] is None:
                tuser["statusdesc"] = "Enabled"
            else:
                tuser["statusdesc"] = "<span title=\"Logged in from %s\">" \
                        "Logged In</span>" % user["ip"]
            toggle_state = "disable"
        actions = """<a href="/traffic/chpass/%s">[change password]</a>""" \
                """<a href="/traffic/toggle/%s">[%s account]</a>""" \
                """<a href="/traffic/remove/%s">[remove account]</a>""" % \
                (username, username, toggle_state, username)
        tuser["actions"] = actions
        tuser["traffic"] = formatBytes(user["traffic"])
        tuser["username"] = user["username"]
        tusers.append(tuser)
    tusers.sort(trafficuser_sort)
    
    output += HTable(tusers, ["username", "status", "traffic", "actions"], \
            ["Username", "Status", "Traffic", "Actions"])
    
    output += "<br />"
    output += "<a href=\"/traffic/add\">Add New User &gt;&gt;</a><br />"
    output += "</div>"

    returnPage(request, "Traffic Administration", output)
    
def trafficuser_sort(a, b):
    return cmp(a["username"], b["username"])
