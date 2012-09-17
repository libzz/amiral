# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Link Module - Provides classes for manipulating links in the system
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
import re
import nav
from math import ceil

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_config import config_getint
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC

import ccs_asset
import ccs_interface

ccs_mod_type = CCSD_SERVER

DEFAULT_LINK_LENGTH = 20000
MIN_DEFAULT_LINK_LENGTH = 3000
# XXX: This is a bit of a hack
WIRELESS_LINK_TYPES = [ "Managed", "Ad-Hoc" ]

class ccs_link_error(ccsd_error):
    pass

class ccs_link(ccs_class):
    """Provides an abstraction of a link in the Configuration System.
    
    The members of this class loosely map to the fields of the link table
    in the database.
    """
    
    def __init__(self, session_id, link_id):
        """Initialises a new class for a specified link.

        Parent must be a reference to the core crcnetd class.
        
        The specified session must be valid and have appropriate access to
        the database for the tasks you intend to perform with the class. All
        database access / configuration manipulation triggered by this
        instance will pass through the specified session.
        """

        self._errMsg = ""
        self._commit = 0
        self._csInit = ""
        
        session = getSession(session_id)
        if session is None:
            raise ccs_interface_error("Invalid session id")
        self._session_id = session_id
        
        # See if the specified link id makes sense
        sql = "SELECT * FROM link WHERE link_id=%s"
        res = session.query(sql, (link_id))
        if len(res) != 1:
            # DB Query failed
            raise ccs_link_error("Invalid link. Unable to retrieve " 
                "details")
        
        # Store details 
        self._properties = res[0]
        self.link_id = link_id
                
    @registerEvent("linkModified")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, "updateLinkDetails")
    def updateDetails(self, newDetails):
        """Updates the details of the link.

        newDetails should be a dictionary containing only those link parameters
        that have changed and need to be updated in the database.

        Returns ccs_site.SUCCESS
        """
        
        session = getSessionE(self._session_id)

        # Check the data
        if "link_id" not in newDetails:
            newDetails["link_id"] = self.link_id
        validateLink(self._session_id, newDetails)

        # If a changeset is not already active, start one for this batch
        self._forceChangeset("Updated details of link #%s" % self.link_id, \
            "link")
        
        # Build SQL Update string
        props = ["description", "type", "mode", "class_id", "essid", \
                "channel", "key", "network_address", "shared_network" ]

        if "network_address" in newDetails.keys() and len(newDetails["network_address"]) == 0:
            newDetails["network_address"] = -1
            
        if "type" in newDetails.keys():
            if newDetails["type"] not in WIRELESS_LINK_TYPES:
                newDetails["essid"] = -1
                newDetails["channel"] = -1
                newDetails["key"] = -1
        (sql, values) = buildUpdateFromDict("link", props, newDetails, \
                "link_id", self.link_id, True)
        
        # Run the query
        res = session.execute(sql, values)
         

        # Check that AP isn't set for an ad-hoc network
        if "type" in newDetails.keys() and newDetails["type"] == "Ad-Hoc":
            sql = "SELECT * FROM interface WHERE link_id=%s"
            res = session.query(sql, (self.link_id))
            for iface in res:
                session.execute("UPDATE interface SET master_channel = NULL, \
                master_interface = 'f' WHERE interface_id = %s", (iface["interface_id"]))
	
        # Trigger an Event
        triggerEvent(self._session_id, "linkModified", link_id=self.link_id)

        return self.returnSuccess()
    
    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "getLink")
    def getDetails(self):
        """Returns a detailed object describing the link"""
        
        session = getSessionE(self._session_id)

        sql = "SELECT l.*, lm.description AS mode_desc FROM link l, " \
                "link_mode lm WHERE l.mode=lm.mode AND l.link_id=%s"
        res = session.query(sql, (self.link_id))
        return res[0]
    
    @registerEvent("linkRemoved")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def removeLink(self):
        """Removes the link from the database."""
        session = getSessionE(self._session_id)
        
        # Trigger an Event
        triggerEvent(self._session_id, "linkRemoved", link_id=self.link_id)
    
        # Delete the link, will cause cascaded deletes
        sql = "DELETE FROM link WHERE link_id=%s"
        res = session.execute(sql, (self.link_id))
        return self.returnSuccess()

    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "linkIsAdHoc")
    def isAdHoc(self):

        if self["type"] == "AdHoc":
            return True
        
        return False
        
    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "linkIsManaged")
    def isManaged(self):

        if self["type"] == "Managed":
            return True
        
        return False

    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "linkIsShared")
    def isShared(self):

        if self["shared_network"] == "t":
            return True

        return False

    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "linkLength")
    def getLength(self, from_interface):
        """Returns the length in metres of the link from the named interface

        If there are multiple peer interfaces on the link, the length returned
        is the length to the most distance interface.

        The length is calculated using the great circle distance based on the
        GPS co-ordinates of the two sites where the host containing the
        interface is located. If GPS information is not available for either
        end the link is set to a default value of 20000m. The default value
        can be modified via the default_link_length configuration file 
        parameter
        """
        session = getSessionE(self._session_id)
        orig = None
        orig_lat = 0
        orig_long = 0
        peers = []
        length = 0
        
        # Get the default link length
        default_link_length = config_getint("network", \
                "default_link_length", DEFAULT_LINK_LENGTH)
        if default_link_length < MIN_DEFAULT_LINK_LENGTH:
            log_error("Invalid default link length! Must be > %sm" % \
                    MIN_DEFAULT_LINK_LENGTH)
            default_link_length = DEFAULT_LINK_LENGTH

        # Select the interface co-ordinates for all interfaces on this link
        res = session.query("SELECT * FROM interface_gpslocation WHERE " \
                "link_id=%s", (self.link_id))
        if len(res) < 2:
            return default_link_length
        
        for iface in res:
            # No GPS co-ords available
            if iface["gps_lat"] <= 0 or iface["gps_long"] <= 0:
                return default_link_length
            this_lat = iface["gps_lat"]
            this_long = iface["gps_long"]
            if iface["interface_id"] == from_interface:
                try:
                    orig = nav.GeoPoint()
                    orig.set_latitude_dec(this_lat)
                    orig.set_longitude_dec(this_long)
                except:
                    log_warn("Invalid co-ordinates for interface %s" % \
                            from_interface, sys.exc_info())
                    return default_link_length
            else:
                peers.append((this_lat, this_long))
            if orig is not None:
                # Calculate distance 
                while peers != []:
                    lat, long = peers.pop()
                    try:
                        peer = nav.GeoPoint()
                        peer.set_latitude_dec(lat)
                        peer.set_longitude_dec(long)
                    except:
                        log_warn("Invalid co-ordinates for interface", \
                            sys.exc_info())
                        return default_link_length
                    # Round the length up to the nearest integer and convert
                    # to metres
                    plength = int(ceil(orig.get_distance_to(peer) * 1000))
                    if plength > length: length = plength

        # Check that at least one distance was calculated
        if length == 0: length = default_link_length
        return length
    
    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "getLinkDefaultGateway")
    def getDefaultGateway(self, host_id):
        """Returns the default gateway for the link for traffic from host_id

        Checks each host with an interface on the link to see if that host is
        marked as being an internet gateway. If it is it's IP address is
        returned. 
        
        If there are no explicit gateways the link is checked for an interface
        acting in master mode. If one is found it is used as the gateway.
        
        If the previous two steps fail the lowest numbered IP address on the
        link that is not the specified host is returned.

        As a last resort a default route of 0.0.0.0 is returned.
        """
        session = getSessionE(self._session_id)

        # Look for an explicit gateway interface
        sql = "SELECT i.interface_id, h.host_id, i.ip_address FROM " \
                "interface i, host h WHERE i.host_id=h.host_id AND " \
                "i.use_gateway='f' AND h.is_gateway='t' AND i.link_id=%s"
        res = session.query(sql, (self.link_id))
        if len(res)>1:
            log_warn("Multiple gateways detected on link %s" % self.link_id)
        if len(res)>0:
            return res[0]["ip_address"]

        # Look for an interface acting as an access point
        sql = "SELECT i.interface_id, h.host_id, i.ip_address FROM " \
                "interface i, host h WHERE i.host_id=h.host_id AND " \
                "i.use_gateway='f' AND i.master_interface='t' AND " \
                "i.link_id=%s"
        res = session.query(sql, (self.link_id))
        if len(res)>1:
            log_warn("Multiple gateways detected on link %s" % self.link_id)
        if len(res)>0:
            return res[0]["ip_address"]

        # Use lowest IP on another host which isn't explicit set to use a 
        # gateway itself
        sql = "SELECT i.interface_id, i.ip_address FROM interface i " \
                "WHERE i.link_id=%s AND i.use_gateway='f' AND i.host_id!=%s " \
                "ORDER BY ip_address"
        res = session.query(sql, (self.link_id, host_id))
        if len(res)>0:
            return res[0]["ip_address"]

        # Last Resort
        return "0.0.0.0"

    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "linkGetAvailableHardware")
    def getAvailableHardware(self, interface_type):
        """Returns a list of subassets that could be attached to this link
        
        This list does not include physical ethernet interfaces
        """
        session = getSessionE(self._session_id)
        
        sql =  "SELECT * FROM link_wireless_interfaces_avail"
        if interface_type == ccs_interface.INTERFACE_TYPE_VAP:
            sql = "SELECT * FROM link_vap_interfaces_avail"
        res = session.query(sql, ())
        return res
  
    def isValidIP(self, ip_address, checkUsage=False):
        """Returns true if the specified IP is valid on this link.

        If checkUsage is True then the IP is only valid if it is not currently
        assigned to an interface.

        Returns True if the IP address is valid
        """

        lnetwork = cidrToNetwork(self["network_address"])
        lnetmask = cidrToNetmask(self["network_address"])
        ip = ipnum(ip_address)
        
        # Determine the network of the specified ip
        network = ipnetwork(ip, lnetmask)

        if lnetwork != network:
            # link network and IP network differ
            return False

        # Check IP usage if required
        if checkUsage:
            if self.ipInUse(ip):
                return False

        return True
    
    def connectsHost(self, host_id, interface_id=-1):
        """Returns true if the specified host is connected to this link by
        an interface other than the specified one."""
        session = getSessionE(self._session_id)
        
        if interface_id != -1:
            return session.getCountOf("SELECT count(*) FROM interface " \
                    "WHERE host_id=%s AND link_id=%s AND interface_id!=%s " \
                    "AND bridge_interface IS NULL AND monitor_interface " \
                    "IS NULL", (host_id, self.link_id, interface_id))
        else:
            return session.getCountOf("SELECT count(*) FROM interface " \
                    "WHERE host_id=%s AND link_id=%s AND bridge_interface " \
                    "IS NULL AND monitor_interface IS NULL", \
                    (host_id, self.link_id))

    def allocateIP(self, host_id, master_if=False):
        """Allocates an IP address for use on the link 

        Uses a heuristic to try and determine the appropriate IP for the
        interface given the IP allocation scheme for the given link class.

        The two parameters host_id and master_if are not used at the present
        time but must be specified to allow a more sophisticated allocation
        algorithm to be easily implemented in future.
        """
        
        #First ensure that there is supposed to be an ip address
        if checkNoIp(self._session_id, self["class_id"]):
            return ""
        
        # Here we assume that networks that allocate upwards use "internal"
        # style addressing
        if getLinkClassAllocateUp(self._session_id, self["class_id"]):
            return self._allocateInternalIP(host_id, master_if)
        else:
            return self._allocateRoutingIP(host_id, master_if)

    def _allocateRoutingIP(self, host_id, master_if):
        """Allocates an IP address for use on a routing link

        We assume that if no other interfaces are yet allocated on this link
        then this interface is closest to the center of the network and should
        be the lowest IP in the network, otherwise assign downwards from the
        highest IP in the network for each successive interface.
        """

        nIfs = self._getNoInterfaces()

        if nIfs == 0:
            return self._minIP()

        return self._maxIP()

    def _allocateInternalIP(self, host_id, master_if):
        """Allocates an IP address for use on an internal link

        The gateway interface (which we assume is the first interface to be
        added to the link) gets the highest IP. Following interfaces get 
        assigned from the second to bottom IP up to the middle of the range. 

        The lowest IP is reserved for a server. 
        The range from the middle IP to the top is reserved for DHCP
        """

        nIfs = self._getNoInterfaces()

        if nIfs == 0:
            return self._maxIP()
        
        # Reserve the lowest IP for a server
        return self._minIP(True, 1)

    def _minIP(self, checkFree=True, skipN=0):
        """Returns the lowest IP on the link, optionally finding a free IP.

        If checkFree is True (the default) this function returns the lowest
        IP on the link that is not:
        a) The network address
        b) Already assigned to another interface.

        If checkFree is false, the second check from the above list is dropped
        and the return value from this function will be the lowest IP on the
        link that is not the network address regardless of whether it is
        already assigned to an interface or not.

        skipN allows the lowest N addresses in the link to be skipped from the
        check, so minIP + N will be the optimal return value, or minIP + N +1
        if minIP + N is not free, etc.
        """
            
        # Absolute Min IP == network_address + 1 + however many we are skipping
        min = cidrToNetwork(self["network_address"])+1+skipN
        if not checkFree:
            return formatIP(min)

        # Find the lowest free IP
        max = self._maxIP(False)
        while self._ipInUse(min):
            if min==max:
                raise ccs_link_error("No IPs available on link!")
            min += 1

        return formatIP(min)
    
    def _maxIP(self, checkFree=True, skipN=0):
        """Returns the highest IP on the link, optionally finding a free IP

        If checkFree is True (the default) this function returns the highest
        IP on the link that is not:
        a) The broadcast address
        b) Already assigned to another interface.

        If checkFree is false, the second check from the above list is dropped
        and the return value from this function will be the highest IP on the
        link that is not the broadcast address regardless of whether it is
        already assigned to an interface or not.
        
        skipN allows the highest N addresses in the link to be skipped from the
        check, so maxIP - N will be the optimal return value, or maxIP - N - 1
        if maxIP - N is not free, etc.
        """
  
        # Absolute Max IP == broadcast_address -1 - however many we skip
        max = ipbroadcast(cidrToNetwork(self["network_address"]), 
                cidrToNetmask(self["network_address"]))-1-skipN
        if not checkFree:
            return formatIP(max)

        # Find the highest free IP
        min = self._minIP(False)
        while self._ipInUse(max):
            if max==min:
                raise ccs_link_error("No IPs available on link!")
            max -= 1

        return formatIP(max)
    
    def _ipInUse(self, ip):
        """Checks if the specified IP address is in use anywhere"""
        session = getSessionE(self._session_id)
        ips = formatIP(ip)
        
        return session.getCountOf("SELECT count(*) FROM "
                "interface WHERE ip_address=%s", (ips))
        
    def _getNoInterfaces(self):
        """Returns the number of interfaces configured on this link"""
        session = getSessionE(self._session_id)

        return session.getCountOf("SELECT count(*) FROM interface WHERE " 
                "link_id=%s", (self["link_id"]))
        
@registerEvent("linkAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def addLink(session_id, link):
    """Adds the specified link to the database
    
    If the link was sucessfully added to the database the new link_id is
    returned.
    """
    session = getSessionE(session_id)
    
    # verify link details
    validateLink(session_id, link, True)
    
    # insert the site record
    props = [ "description", "type", "mode", "class_id", "network_address", \
            "shared_network" ]
    if link["type"] in WIRELESS_LINK_TYPES:
        props.extend(["essid", "channel", "key"])

    if "network_address" in link.keys() and len(link["network_address"]) == 0:
        link["network_address"] = -1

    (sql, values) = buildInsertFromDict("link", props, link, True)
    session.execute(sql, values)
    
    # Get the link_id that was created for the link
    sql = "SELECT currval('link_link_id_seq') as link_id"
    res = session.query(sql, ())
    link_id = res[0]["link_id"]
            
    # Raise the event
    triggerEvent(session_id, "linkAdded", link_id=link_id);
    
    return link_id

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getLinkList(session_id, subasset_id=-1):
    """Returns a list of links in the system"""
    session = getSessionE(session_id)

    typeq = ""
    if subasset_id != -1:
        subasset = ccs_asset.ccs_subasset(session_id, subasset_id)
        if subasset.supportsFunction("wireless_interface"):
            typeq = " AND l.type!='Ethernet'"
        else:
            typeq = " AND l.type='Ethernet'"
    
    sql = "SELECT l.link_id, l.description, l.type, l.mode, lc.description " \
            "AS class_desc, l.essid, l.channel, l.network_address, " \
            "l.shared_network, COALESCE(lic.no_interfaces, 0) AS " \
            "no_interfaces FROM link_class lc, link l LEFT JOIN " \
            "link_interface_count lic ON lic.link_id=l.link_id " \
            "WHERE lc.link_class_id=l.class_id%s ORDER BY l.network_address" \
            % typeq
    res = session.query(sql, ())
    res2 = []
    for row in res:
        nrow = row
        str = row["type"]
        str = "%s %s" % (str, \
                getModeDesc(session_id, row["type"], row["mode"]))
        if row["shared_network"] == "t":
            str = "%s (shared)" % str
        nrow["mode_desc"] = str
        res2.append(nrow)
        
    return res2

def getLinkTemplateVariables(session_id):
    links = {}
    for link in getLinkList(session_id):
        links[link["link_id"]] = link
    return links

def getModeDesc(session_id, type, mode):
    """Returns a description string describing the link's mode"""
    #XXX: This is a bit of a hack
    if type == "Ethernet":
        return "%sMbps" % mode
    elif type == "Managed" or type == "Ad-Hoc":
        return "802.11%s" % mode

    return ""

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getLinkTypes(session_id):
    """Returns a detailed object describing the available link types"""
    session = getSessionE(session_id)

    sql = "SELECT * FROM link_type"
    res = session.query(sql, ())
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getLinkModes(session_id, type_name=""):
    """Returns a dictionary describing the available link modes"""
    session = getSessionE(session_id)
    sql = "SELECT * FROM link_mode"
    params = []
    if type_name != "":
        sql = "%s WHERE type_name=%%s" % sql
        params.append(type_name)
    res = session.query(sql, params)
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getLinkClasses(session_id, includeHostAllocs=False):
    """Returns a dictionary describing the available link classes
    
    Link classes that can only support a single host (ie, allocsize 32) are
    excluded from this list.
    """
    session = getSessionE(session_id)

    sql = "SELECT * FROM link_class"
    if not includeHostAllocs:
        sql += " WHERE allocsize<32"
    res = session.query(sql, ())
    return res

def getInterfaceLink(session_id, interface_id):
    """Returns a link object for the link specified for the interface"""
    from crcnetd.modules.ccs_interface import ccs_interface

    interface = ccs_interface(session_id, interface_id)
    
    return ccs_link(session_id, interface["link_id"])
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getChannelList(session_id, mode=""):
    """Returns a dictionary describing the available channels for a mode"""
    session = getSessionE(session_id)
    sql = "SELECT * FROM mode_channels"
    params = []
    if mode != "":
        sql = "%s WHERE mode=%%s" % sql
        params.append(mode)
    res = session.query(sql, params)
    return res

def getLinkClassTemplateVariables(session_id):
    """Returns a list of link classes for use in templates"""
    session = getSessionE(session_id)

    classes = {}
    for lc in getLinkClasses(session_id, True):
        lc["mangled_description"] = re.sub("[ \.\-]", "_", lc["description"])
        classes[lc["link_class_id"]] = lc
    return classes
    
def checkNoIp(session_id, link_class_id):
    """Returns true if the specified link class does not allocate IP"""
    session = getSessionE(session_id)
    
    # Get link class details
    lcd = session.query("SELECT * FROM link_class WHERE link_class_id=%s", \
            (link_class_id))
    if len(lcd) != 1:
        raise ccs_link_error("Invalid link class ID!")

    if len(lcd[0]["netblock"]) > 0:
        return False
    else:
        return True

def getLinkClassAllocateUp(session_id, link_class_id):
    """Returns true if the specified link class allocates upwards"""
    session = getSessionE(session_id)
    
    # Get link class details
    lcd = session.query("SELECT * FROM link_class WHERE link_class_id=%s", \
            (link_class_id))
    if len(lcd) != 1:
        raise ccs_link_error("Invalid link class ID!")

    return lcd[0]["allocup"]

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def allocateNetwork(session_id, link_class_id):
    """Allocates a network address for use on a link"""
    session = getSessionE(session_id)

    # Get link class details
    lcd = session.query("SELECT * FROM link_class WHERE link_class_id=%s", \
            (link_class_id))
    if len(lcd) != 1:
        raise ccs_link_error("Invalid link class ID!")

    base = cidrToNetwork(lcd[0]["netblock"])
    baselen = cidrToLength(lcd[0]["netblock"])
    alloclen = lcd[0]["allocsize"]
    
    if lcd[0]["allocup"]:
        net = _getLowestAvailableNetwork(session_id, base, baselen, alloclen)
    else:
        net = _getHighestAvailableNetwork(session_id, base, baselen, alloclen)
    
    return net

def _getLowestAvailableNetwork(session_id, base, basesize, allocsize):
    """Returns the lowest network not in use in the specified base netblock.

    Uses basesize and allocsize to determine the bounds of each network.
    """
    allocmask = bitsToNetmask(allocsize)
    
    # Determine the top network 
    basemask = bitsToNetmask(basesize)   
    topnet = ipbroadcast(base, basemask)
        
    # Loop upwards until we find a free network
    while base <= topnet:
        net = ipnetwork(base, allocmask)
        netstr = "%s/%s" % (formatIP(net), allocsize)
        if not _networkInUse(session_id, netstr, basesize):
            # Found one, return it
            return netstr
        # In use, move up a network
        base += (2**(32-allocsize))
        
    # None available!
    raise ccs_link_error("No available networks!")

def _getHighestAvailableNetwork(session_id, base, basesize, allocsize):
    """Returns the lowest network not in use in the specified base netblock.

    Uses basesize and allocsize to determine the bounds of each network.
    """
    allocmask = bitsToNetmask(allocsize)
    
    # Determine the top network
    basemask = bitsToNetmask(basesize)   
    topnet = ipbroadcast(base, basemask)
    
    # Determine the bottom network
    botnet = ipnetwork(base, allocmask)
    
    # Start the the top
    base = topnet

    # Loop downwards until we find a free network
    while base >= botnet:
        net = ipnetwork(base, allocmask)
        netstr = "%s/%s" % (formatIP(net), allocsize)
        if not _networkInUse(session_id, netstr, basesize):
            # Found one, return it
            return netstr
        # In use, move up a network
        base -= (2**(32-allocsize))
        
    # None available
    raise ccs_link_error("No available networks!")

def _networkInUse(session_id, cidr_network, baselen):
    """Checks if the specified network is in use anywhere in the system"""

    session = getSessionE(session_id)
    
    # Check for this exact network
    n = session.getCountOf("SELECT count(*) FROM link WHERE " \
            "network_address=%s", (cidr_network))
    if n > 0:
        return True

    # Check for larger networks (smaller prefix lengths) that include this
    net = cidrToNetwork(cidr_network)
    len = cidrToLength(cidr_network)
    while len > baselen:
        len -= 1
        netmask = bitsToNetmask(len)
        newnw = ipnetwork(net, netmask)
        nwstr = "%s/%s" % (formatIP(newnw), len)
        n = session.getCountOf("SELECT count(*) FROM link WHERE " \
            "network_address=%s", (cidr_network))
        if n > 0:
            return True
    
    # Not in use
    return False

def validateLinkClassId(session_id, link_class_id):
    """Checks that the specified class_ID is valid (ie in the DB)"""
    session = getSessionE(session_id)

    rv = session.getCountOf("SELECT count(*) FROM link_class WHERE " \
            "link_class_id=%s", (link_class_id))
    if rv != 1:
        raise ccs_link_error("Invalid Link Class ID! Link class not found!")

    return

def validateLinkMode(session_id, type_name, mode):
    """Checks that the specified link type is valid"""
    session = getSessionE(session_id)

    rv = session.getCountOf("SELECT count(*) FROM link_type WHERE " \
            "type_name=%s", (type_name))
    if rv != 1:
        raise ccs_link_error("Invalid link type! Type not found!")

    rv = session.getCountOf("SELECT count(*) FROM link_mode WHERE " \
            "type_name=%s AND mode=%s", (type_name, mode))
    if rv != 1:
        raise ccs_link_error("Invalid link mode! Mode not found!")
    
    return

def validateLinkId(session_id, link_id):
    """Checks that the specified linkID is valid (ie in the DB)"""
    session = getSessionE(session_id)

    rv = session.getCountOf("SELECT count(*) FROM link WHERE link_id=%s", \
                (link_id))
    if rv != 1:
        raise ccs_link_error("Invalid Link ID! Link not found!")

    return

def validateLink(session_id, details, isAdd=False):
    """Validates that the specified link details are correct"""

    # Link ID
    if "link_id" in details.keys():
        validateLinkId(session_id, details["link_id"])
    elif not isAdd:
        raise ccs_link_error("Link ID must be specified!")
    
    # Required props
    if isAdd:
        rprops = [ "description", "type", "mode", "class_id", \
                "network_address", "shared_network" ]
        for prop in rprops:
            if prop not in details.keys():
                raise ccs_link_error("%s is a required link property!" % prop)

    # Check values
    if "description" in details.keys():
        if len(details["description"])<=0:
            raise ccs_link_error("Description must be specified!")
        if len(details["description"])>250:
            raise ccs_link_error("Description must be less than 250 chars!")
    
    if "mode" in details.keys() and "type" in details.keys():
        validateLinkMode(session_id, details["type"], details["mode"])
    if "class_id" in details.keys():
        validateLinkClassId(session_id, details["class_id"])
    if "type" in details.keys() and details["type"] in WIRELESS_LINK_TYPES:
        if "essid" in details.keys():
            if len(details["essid"])<=0:
                raise ccs_link_error("ESSID must be specified!")
            if len(details["essid"])>64:
                raise ccs_link_error("ESSID must be less than 64 chars!")
            essid_valid = re.compile("[a-zA-z0-9\-]*")
            if essid_valid.match(details["essid"]) == None:
                raise ccs_link_error("Invalid character in ESSID!")
        if "channel" in details.keys():
            try:
                c = int(details["channel"])
                if c == 0:
                    raise ccs_link_error("Channel must not be 0!")
            except:
                raise ccs_link_error("Invalid channel specified!")
        if "key" in details.keys() and details["key"] != "":
            if len(details["key"]) != 32:
                raise ccs_link_error("Key must be 32 characters!")
            key_valid = re.compile("[a-zA-z0-9]*")
            if key_valid.match(details["key"]) == None:
                raise ccs_link_error("Invalid character in key!")
    if "network_address" in details.keys() and len(details["network_address"]) > 0:
        validateCIDR(details["network_address"])
        
        session = getSession(session_id)
        if session is None:
            raise ccs_interface_error("Invalid session id")
       
        
        # Must ensure that no two links can have same ip range
        sql = "SELECT link_id FROM link WHERE network_address=%s"
        p = [details["network_address"]]
        if "link_id" in details.keys():
            sql += " AND link_id != %s"
            p.append(details["link_id"])
        res = session.query(sql, p)
        if len(res) != 0:
            raise ccs_link_error("Network address already in used!")
        
    if "shared_network" in details.keys():
        if details["shared_network"] not in ["t","f"]:
            raise ccs_link_error("Shared Network flag must be 't' or 'f'!")

    # All OK
    return
