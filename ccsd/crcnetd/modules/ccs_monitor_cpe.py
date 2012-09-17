# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# CPE configuration and management
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
import crypt
import re
import iwtools
import time

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_clientserver import registerPage, registerRealm, \
        registerDir, AsyncHTTPServer, CCSDHandler, registerRecurring
from crcnetd._utils.ccsd_config import config_getboolean, pref_get, pref_set, \
        pref_getboolean
from crcnetd._utils.ccsd_events import catchEvent
from crcnetd._utils.interfaces import debian_interfaces

from ccs_monitor_web import registerMenu, registerMenuItem, returnPage, \
        MENU_TOP, MENU_BOTTOM, MENU_GROUP_GENERAL, MENU_GROUP_HOME, \
        CPE_ADMIN_REALM, getMonitorPrefs, getRealm, ADMIN_USERNAME, \
        generateSelect, HTable, DEFAULT_RESOURCE_DIR, homepage, \
        DEFAULT_PREF_FILE

from ccs_monitor_status import getSSMeter, initialiseNetworkMap

class ccs_cpe_error(ccsd_error):
    pass

ccs_mod_type = CCSD_CLIENT

BACKHAUL_IFNAME = "bhaul"
UPSTREAM_CHECK_INTERVAL = 60
ESSID_PREFIX = "CRCap-"

##############################################################################
# Utility Functions
##############################################################################
def getBackhaulStatus():
    """Returns the status of the backhaul interface"""

    nopeer = {"snr":0,"signal":0,"noise":0}
    
    ifaces = getInterfaces(returnOne=BACKHAUL_IFNAME)
    if len(ifaces) != 1:
        return ("critical", "Backhaul interface not found", nopeer)
    iface = ifaces[0]
    wiface = iwtools.get_interface(BACKHAUL_IFNAME)

    if not iface["up"]:
        ifaces = debian_interfaces()
        apname = ifaces[BACKHAUL_IFNAME]["wpa-ssid"].replace(ESSID_PREFIX, "")
        return ("critical", "%s - Not associated" % apname, nopeer)
    
    essid = wiface.get_essid()
    if not essid.startswith(ESSID_PREFIX) and essid != "Any":
        log_warn("Associated to invalid AP: %s" % essid)
        return ("warning", "Not associated to correct Access Point", nopeer)
    parts = essid.split("-")

    stats = wiface.get_stats()
    if getActiveUsername() != getISPUsername():
        return ("warning", "Connected as '%s' not '%s'" % \
                (getActiveUsername(), getISPUsername()), stats)

    return ("ok", "%s" % "-".join(parts[1:]), stats)
    
def configureBhaulInterface(essid):
    """Configure an interface to talk to an access point"""

    try:
        log_info("Configuring backhaul interface onto AP: %s" % essid)
        # Take interface down
        log_command("/sbin/ifdown %s 2>&1" % BACKHAUL_IFNAME)

        # Write /etc/network/interfaces stanza
        ifaces = debian_interfaces()
        iface = ifaces[BACKHAUL_IFNAME]
        iface["wpa-ssid"] = essid
        ifaces[BACKHAUL_IFNAME] = iface
        try:
            remountrw("configureBhaulInterface")
            ifaces.write()
        finally:
            remountro("configureBhaulInterface")

        # Bring Up
        log_command("/sbin/ifup %s 2>&1" % BACKHAUL_IFNAME)
        ifaces = getInterfaces(returnOne=BACKHAUL_IFNAME)
        if len(ifaces) != 1 or not ifaces[0]["up"]:
            # Failed
            log_error("Failed to configure and bring up backhaul " \
                    "interface (%s)" % BACKHAUL_IFNAME)
            return False
        return True
    except:
        log_error("Unexpected exception while configuring backhaul!", 
                sys.exc_info())
        return False

def ensureBackhaulUp():
    """Ensures that the backhaul interface is up"""

    ifaces = getInterfaces(returnOne=BACKHAUL_IFNAME)
    if len(ifaces) == 1:
        iface = ifaces[0]        
        # Exit now if the interface is already up
        if iface["up"]:
            return True
        
    # Try ifup 
    log_info("Attempting to bring up backhaul interface")
    log_command("/sbin/ifup --force %s 2>&1" % BACKHAUL_IFNAME)

    # Assume it came up ok
    return True

@registerRecurring(UPSTREAM_CHECK_INTERVAL)
def checkUpstream():
    
    ifaces = debian_interfaces()
    diface = ifaces[BACKHAUL_IFNAME]
    if diface["wpa-ssid"] == "default":
        # Not configured, scan for valid APs
        try:
            log_command("/sbin/ip link set up dev %s 2>&1" % BACKHAUL_IFNAME)
            wiface = iwtools.get_interface(BACKHAUL_IFNAME)
            scanres = wiface.scanall()
        except:
            log_error("Could not complete scan on backhaul interface (%s)!" % \
                    BACKHAUL_IFNAME, sys.exc_info())
            scanres = []
        # Exclude networks that don't match our ESSID
        aps = [ n for n in scanres if n.essid.startswith(ESSID_PREFIX)]
        # Pick the one with the highest SNR
        best = None
        for ap in aps:
            if best is None or ap.qual["snr"] > best.qual["snr"]:
                best = ap
        # Select it
        if best is not None:
            log_info("Selecting Access Point '%s' based on SNR strength" % \
                    best.essid)
            configureBhaulInterface(best.essid)

        # Hope for the best
        return

    # Check that the backhaul is up
    doUp = False
    ifaces = getInterfaces(returnOne=BACKHAUL_IFNAME)
    if len(ifaces) != 1:
        ensureBackhaulUp()
        return

    iface = ifaces[0]        
    if not iface["up"]:
        ensureBackhaulUp()
        return
    
    # Check credentials are up to date
    if diface["wpa-identity"] != getActiveUsername() or \
            diface["wpa-password"] != getActivePassword():
        # Take down so that we re-authenticate
        log_info("Triggering reassociation to update credentials")
        log_command("/sbin/ifdown %s 2>&1" % BACKHAUL_IFNAME)
        ensureBackhaulUp()
        return

    # Check IP layer is OK
    dg = getGatewayIP()
    if dg == "":
        log_info("Triggering reassociation to acquire gateway")
        log_command("/sbin/ifdown %s 2>&1" % BACKHAUL_IFNAME)
        ensureBackhaulUp()
        return
       
    # Done

def getActiveUsername():
    """Returns the username wpa-cli is currently using"""
    return _wpacli_get_network("identity")

def getActivePassword():
    """Returns the password wpa-cli is currently using"""
    return _wpacli_get_network("password")

def _wpacli_get_network(value, network=0):
    """Helper function to read and parse network values from wpa_cli"""
    (fdi, fdo) = os.popen2("wpa_cli get_network %s %s 2>&1" % \
            (network, value))
    fdi.close()
    output = fdo.readlines()
    fdo.close()
        
    if len(output) < 2:
        return ""
    if not output[0].startswith("Selected interface"):
        return ""
    if not output[1].startswith('"') or not output[1].strip().endswith('"'):
        return ""
    
    return output[1].strip().strip('"')

def setCPEPassword(newpass):
                
    admin_pass = crypt.crypt(newpass, createSalt())
    pref_set(None, "admin_password", admin_pass, getMonitorPrefs())
    realm = getRealm()
    realm["users"][ADMIN_USERNAME] = admin_pass
    registerRealm(CPE_ADMIN_REALM, realm, overwrite=True)
            

def setISPDetails(username, password):

    try:
        # Write /etc/network/interfaces stanza
        ifaces = debian_interfaces()
        iface = ifaces[BACKHAUL_IFNAME]
        iface["wpa-identity"] = username
        iface["wpa-password"] = password
        ifaces[BACKHAUL_IFNAME] = iface
        try:
            remountrw("setISPDetails")
            ifaces.write()
        finally:
            remountro("setISPDetails")
        
        return True
    except:
        log_error("Unexpected exception while configuring ISP details!", 
                sys.exc_info())
        return False

def getISPUsername():
    """Returns the currently configured ISP Username"""
    ifaces = debian_interfaces()
    return ifaces[BACKHAUL_IFNAME]["wpa-identity"]

def getISPPassword():
    """Returns the currently configured ISP Password"""
    ifaces = debian_interfaces()
    return ifaces[BACKHAUL_IFNAME]["wpa-password"]

def getCPESerial():

    fp = open("/sys/class/net/int/address", "r")
    serial = fp.read()
    fp.close()
    return serial.strip().strip(":")

def resetCPE():
    # Try and return the device to a "factory default" config
    remountrw("factory-reset")
    # Delete preferences
    os.system("rm -f %s" % config_get("www", "preferences", 
        DEFAULT_PREF_FILE))
    # Reset interfaces
    configureBhaulInterface("default")
    setISPDetails("default", "default")
    log_command("/sbin/ifdown %s 2>&1" % BACKHAUL_IFNAME)
    remountro("factory-reset")

##############################################################################
# Initialisation
##############################################################################
def ccs_init():
    
    registerMenuItem(MENU_TOP, MENU_GROUP_GENERAL, \
            "/admin", "CPE Administration")

##############################################################################
# Content Pages
##############################################################################

@registerPage("/admin", requireAuth=True, realm=CPE_ADMIN_REALM)
def admin(request, method, returnDirect=True):
    """Returns the HTML for administration page"""
    
    isperr = ""
    reconnect = False

    if method == "POST":
        data = request.getPostData()
        # Incoming data
        invalid=True
        if "password" in data.keys():
            try:
                if data["password"] == "":
                    raise ccs_cpe_error("Cannot set blank password!")
                if len(data["password"]) < 8:
                    raise ccs_cpe_error("Password must be at " \
                            "least 8 characters!")
                # Now change the password
                setCPEPassword(data["password"])
            except ccs_cpe_error:
                (type, value, tb) = sys.exc_info()
                request.send_error(400, value)
                request.end_headers()
                request.finish()
                return
            except:
                log_error("Failed to change password!", \
                        sys.exc_info())
                request.send_error(400, "Unexpected Error")
                request.end_headers()
                request.finish()
                return
            request.send_response(200, "Password updated")
            request.end_headers()
            request.finish()
            return
        if "isppassword" in data.keys():
            try:
                # Now change the details
                setISPDetails(data["ispusername"], data["isppassword"])
            except ccs_cpe_error:
                (type, value, tb) = sys.exc_info()
                isperr = value
            except:
                log_error("Failed to change password!", \
                        sys.exc_info())
                isperr = "Could not change password!"
            if isperr == "":
                reconnect = True
            invalid = False
        elif "reconnect" in data.keys():
            log_info("User Triggered reassociation to update credentials")
            log_command("/sbin/ifdown %s 2>&1" % BACKHAUL_IFNAME)
            ensureBackhaulUp()
            request.send_response(200, "Reconnected")
            request.end_headers()
            request.finish()
            return
        elif "reset" in data.keys():
            try:
                resetCPE()
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
            os.system("/etc/init.d/crcnet-monitor restart & 2>&1")
            request.send_response(200, "Device restarted")
            request.end_headers()
            request.finish()
            return
        
        if invalid:
            log_warn("Invalid POST request to /admin from %s" %
                    request.client_address[0]) 
            request.send_error(400, "Invalid method for this page!")
            request.end_headers()
            request.finish()
            return
    
    # Normal page GET
    output = """<div id="admin" class="content">
<h2>CPE Administration</h2><br />
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
    <th valign="top">CPE Password:</th>
    <td><input id="password" value="*****"><br />
    <small>Enter the new admin password in the box above.</small></td>
</tr>
<tr>
    <th>Reset Device:</th>
    <td><input type="button" value="Reset to Default Settings" id="factory_reset"></td>
</tr>
</table>
<br />
""" % getCPESerial()

    # Configure the backhaul interface
    #################################
    if reconnect:
        bhaul_status = "warning"
        bhaul_desc = """<script language="javascript" type="text/javascript">
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
    document.location = l;
}
id = window.setInterval(progress, 1000);
pars="reconnect=true";
myAjax = new Ajax.Request("/admin", {method: 'post', postBody: pars});
</script>
Details updated. Reconnecting... <span id="rem">30</span> seconds left
"""
        change = ""
    else:
        bhaul_status, bhaul_desc, stats = getBackhaulStatus()
        change = """<a href="/admin/setup_backhaul">[change]</a>"""
    if isperr != "":
        isperr = "<div class=\"statuserror\">%s</div>" % isperr

    output += """
<h2>Backhaul Settings (using %s interface)</h2><br />
<form method="post" action="/admin">
%s
<table>
<tr>
<th>Access Point:</th>
<td><span class="status%s">%s</span>&nbsp;&nbsp;%s
</td>
</tr>
<tr>
<th>Username:</th>
<td><input name="ispusername" value="%s"></td>
</tr>
<tr>
<th>Password:</th>
<td><input name="isppassword" value="%s"></td>
</tr>
<tr>
<tr>
<th>Save Details:</th>
<td><input type="submit" value="Save Username &amp; Password"></td>
</tr>
<tr>
</table>
""" % (BACKHAUL_IFNAME, isperr, bhaul_status, bhaul_desc, change, 
        getISPUsername(), getISPPassword())
    if not reconnect:
        output += """<div id="ssmeter-%s" class="ssmeter">""" % BACKHAUL_IFNAME
        output += getSSMeter(stats)
        output += "</div><br clear=\"all\" />"
        output += "<a href=\"/status/interfaces\">Click here for detailed " \
                "signal strength information</a><br /><br />"

    output += """
</div>
<div id="reset" class="content hidden">
<h2>Resetting Device...</h2><br />
<br />
Please wait while your device is reset to its factory configuration.
This process may take up to 30 seconds to complete successfully.<br />
<br />
<div id="resetstatus" style="font-weight:bold;"></div>
</div>
"""
        
    # Return the page
    if returnDirect:
        return returnPage(request, "CPE Administration", output, \
                scripts=["/resources/admin.js"])
    else:
        return output

def getBackhaulHTML(submitButtons=True, inputPrefix=""):
    
    othernets = {}
    output = ""

    try:
        ensureBackhaulUp()
        wiface = iwtools.get_interface(BACKHAUL_IFNAME)
        scanres = wiface.scanall()
    except:
        log_error("Could not complete scan on backhaul interface (%s)!" % \
                BACKHAUL_IFNAME, sys.exc_info())
        scanres = []

    n=0
    for network in scanres:
        if not network.essid.startswith(ESSID_PREFIX):
            # Skip non matching networks
            othernets[network.essid] = (network.channel, network.qual)
            continue
        # Get the AP name from the ESSID
        parts = network.essid.split("-")
        if len(parts) < 2:
            othernets[network.essid] = (network.channel, network.qual)
            continue
        name = "-".join(parts[1:])

        # Write the record
        output += """<h3>%s</h3>
        <div id="ssmeter-%s" class="ssmeter">%s</div>
        <div style="clear: all;">&nbsp;</div><br />
        """ % (name, name, getSSMeter(network.qual))
        
        if submitButtons:
            output += """<form action="/admin/setup_backhaul" method="post">
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
        output += "<br /><b>No access points found to connect to!</b>" \
                "<br /><br />"

    return (output, othernets)

@registerPage("/admin/setup_backhaul", requireAuth=True, \
        realm=CPE_ADMIN_REALM)
def admin_setupbackhaul(request, method):
    """Returns the HTML for backhaul setup page"""
   
    errmsg = ""

    if method == "POST":
        data = request.getPostData()
        # Incoming data
        if "essid" in data.keys():
            if configureBhaulInterface(data["essid"]):
                return admin(request, "GET")
            # Failed
            parts = data["essid"].split("-")
            ap = "-".join(parts[1:])
            errmsg = "Failed to associate with %s" % ap
        
    # Normal page GET
    output = """<div class="content">
<h2>CPE Administration - Select Access Point</h2><br />
Please select the access point to connect to from the following list.
<br /><br />
"""
    if errmsg != "":
        output += """<span class="error">%s</span><br /><br />""" % errmsg
        
    (toutput, othernets) = getBackhaulHTML()
    output += toutput

    if len(othernets.keys()) > 0:
        output += """<h2>Other networks</h2><br />
        The following other networks were detected. This CPE is not
        able to connect to these networks. You may need to
        co-ordinate channel usage with the operators of the listed 
        networks to minimise the chance of interference.<br /><br />
        """
        for essid, (channel,qual) in othernets.items():
            output += """<h3>%s on Channel %s</h3>
            <div id="ssmeter-%s" class="ssmeter">%s</div>
            <div style="clear: all;">&nbsp;</div><br /><br />
            """ % (essid, channel, essid, getSSMeter(qual))

    output += """<a href="/admin">&lt;&lt;&nbsp;Return to CPE 
    Administration page</a><br />"""

    return returnPage(request, "CPE Administration", output, \
                scripts=["/resources/admin.js"])
