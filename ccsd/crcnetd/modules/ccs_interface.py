# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Interface Module - Provides classes for manipulating interfaces
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

from ccs_link import validateLinkId, ccs_link
from ccs_asset import ccs_subasset

INTERFACE_TYPE_MIN=0
INTERFACE_TYPE_PHYSICAL=1
INTERFACE_TYPE_VAP=2
INTERFACE_TYPE_VLAN=3
INTERFACE_TYPE_ALIAS=4
INTERFACE_TYPE_MAX=5

ccs_mod_type = CCSD_SERVER

class ccs_interface_error(ccsd_error):
    pass

class ccs_interface(ccs_class):
    """Provides an abstraction of an interface in the Configuration System.
    
    The members of this class loosely map to the fields of the interface table
    in the database.
    """
    
    def __init__(self, session_id, interface_id):
        """Initialises a new class for a specified interface.
        
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
        
        # See if the specified interface id makes sense
        sql = "SELECT * FROM interface WHERE interface_id=%s"
        res = session.query(sql, (interface_id))
        if len(res) != 1:
            raise ccs_interface_error("Invalid interface. Unable to " \
                    "retrieve details")
        
        # Store details 
        self.interface_id = interface_id
        self._properties = res[0]
                
    @registerEvent("interfaceModified")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, \
            "updateInterfaceDetails")
    def updateDetails(self, details):
        """Updates the details of the interface.

        details should be a dictionary containing only those parameters
        that have changed and need to be updated in the database.

        Returns ccs_interface.SUCCESS,
        """
        session = getSessionE(self._session_id)

        # Check the data
        validateInterface(self._session_id, details)
       
        # Extract values for ease of use.
        host_id = "host_id" in details.keys() and \
                int(details["host_id"]) or self["host_id"]
        link_id = "link_id" in details.keys() and \
                int(details["link_id"]) or self["link_id"]
        subasset_id = "subasset_id" in details.keys() and \
                int(details["subasset_id"]) or self["subasset_id"]
        interface_type =  "interface_type" in details.keys() and \
                int(details["interface_type"]) or self["interface_type"]
        bridge_interface = "bridge_interface" in details.keys() and \
                int(details["bridge_interface"]) or self["bridge_interface"]
        monitor_interface = "monitor_interface" in details.keys() and \
                details["monitor_interface"] or self["monitor_interface"]
    
        # Check subasset is valid if it is specified
        if subasset_id != self["subasset_id"] and subasset_id != -1:
            subasset = ccs_subasset(self._session_id, subasset_id)
            if not subasset.supportsFunction("interface"):
                raise ccs_interface_error("Invalid subasset type!")
            if not subasset.availableForInterface(host_id):
                raise ccs_interface_error("Subasset already in use!")
        
        # Check this host doesn't already have an interface on the new link
        if link_id != self["link_id"] and \
                (bridge_interface=="" or bridge_interface==-1):
            link = ccs_link(self._session_id, link_id)
            if link.connectsHost(host_id, self.interface_id):
                raise ccs_interface_error("Host already has an interface on " \
                        "the specified link!")
            if "ip_address" not in details.keys():
                raise ccs_interface_error("IP Address must change when " \
                        "modifing the link!")
                
        # Check interface type
        if interface_type != self["interface_type"]:
            if interface_type <= INTERFACE_TYPE_MIN or \
                    interface_type >= INTERFACE_TYPE_MAX:
                raise ccs_interface_error("Invalid interface type!")
    
        # Check IP is specified and is correct for the link
        if "ip_address" in details.keys() and \
                (bridge_interface=="" or bridge_interface==-1):
            link = ccs_link(self._session_id, link_id)
            if details["ip_address"] == "":
                details["ip_address"] = link.allocateIP(host_id, False)
            elif not link.isValidIP(details["ip_address"]):
                raise ccs_interface_error("Invalid IP address for link!")
        
        # Check interface is in master mode if a channel was specified
        if "master_channel" in details.keys() or \
                "master_mode" in details.keys():
            if "master_interface" not in details.keys():
                if not self._properties["master_interface"]:
                    log_warn("Interface channel may only " \
                            "be set for Master mode interfaces!")
                del details["master_channel"]
                del details["master_mode"]
            else:
                if details["master_interface"]!="t":
                    log_warn("Interface channel may only " \
                            "be set for Master mode interfaces!")
                    del details["master_channel"]
                    del details["master_mode"]

        # Check VLAN properties
        if interface_type == INTERFACE_TYPE_VLAN:
            # Check the vid is valid if specified
            if "vid" in interface.keys() and \
                    interface["vid"] != "":
                try:
                    vid = int(interface["vid"])
                except:
                    raise ccs_interface_error("Alias VLAN ID must be an integer")
            # VLAN interfaces have a name derived from their parent interface
            parent_iface = ccs_interface(session_id, interface["raw_interface"])
            interface["name"] = "%s.%s" % \
                    (parent_iface["name"], interface["vid"])

        # Check alias properties
        if interface_type == INTERFACE_TYPE_ALIAS:
            # Check the netmask is valid if specified
            if "alias_netmask" in details.keys() and \
                    details["alias_netmask"] != "":
                if details["alias_netmask"].startswith("/"):
                    details["alias_netmask"] = details["alias_netmask"][1:]
                try:
                    details["alias_netmask"] = int(details["alias_netmask"])
                except:
                    raise ccs_interface_error("Alias netmask must be an integer")
            # Alias interfaces have a name derived from their parent interface
            parent_iface = ccs_interface(self._session_id, 
                    details["raw_interface"])
            details["name"] = "%s-alias-%s" % (parent_iface["name"], link_id)
            details["ifname"] = details["name"]

        # Deal with ifname/name dictionary entries
        if "ifname" in details.keys():
            details["name"] = details["ifname"]
        
        # Wrap changes into a changeset
        self._forceChangeset("Interface details updated")     

        # Deal with subasset changes
        if subasset_id != self["subasset_id"] and \
                interface_type != INTERFACE_TYPE_VAP:
            if self.hasSubasset():
                self.detachSubasset()
            subasset = ccs_subasset(self._session_id, subasset_id)
            from ccs_host import ccs_host
            host = ccs_host(self._session_id, host_id)
            if host.hasAsset():
                subasset.attachTo(host["asset_id"])
            elif host.hasSite():
                subasset.moveToSite(host["site_id"])
            
        # Build list of properties for the interface type
        props = [ "interface_id", "interface_type", "host_id", "link_id", \
                "name", "use_gateway", "interface_active", "master_mode", \
                "master_interface", "master_channel", "module_id", \
                "monitor_interface" ]
        nProps = []
        if interface_type == INTERFACE_TYPE_PHYSICAL or \
                interface_type == INTERFACE_TYPE_VAP:
            props.extend(["subasset_id"])
            nProps.extend(["raw_interface", "alias_netmask"])
        elif interface_type == INTERFACE_TYPE_VLAN:
            props.extend(["raw_interface", "vid"])
            nProps.extend(["subasset_id", "alias_netmask"])            
        elif interface_type == INTERFACE_TYPE_ALIAS:
            props.extend(["raw_interface",])
            nProps.extend(["subasset_id"])
            if "alias_netmask" in details.keys() and \
                    details["alias_netmask"] != "":
                props.extend(["alias_netmask"])
        if monitor_interface=="t":
            nProps.extend(["ip_address", "bridge_interface"])
        elif bridge_interface != "" and bridge_interface!=-1:
            props.extend(["bridge_interface"])
            nProps.extend(["ip_address"])
        else:
            props.extend(["ip_address"])
            nProps.extend(["bridge_interface"])
        
        # Build update string
        (sql, values) = buildUpdateFromDict("interface", props, details, \
                "interface_id", self.interface_id, True, nProps)                
        if values is None:
            # No changes made... ?
            return self.returnSuccess()
        
        # Run the query
        session.execute(sql, values)
        
        # Fire the trigger
        triggerHostEvent(self._session_id, "interfaceModified", host_id, \
                interface_id=self.interface_id);
        
        return self.returnSuccess()
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getInterfaceDetails")
    def getDetails(self):
        """Returns a detailed object describing the interface"""
        session = getSessionE(self._session_id)

        sql = "SELECT * FROM interface WHERE interface_id=%s"
        res = session.query(sql, (self.interface_id))
        return res[0]
    
    def getTemplateVariables(self):
        """Returns a dictionary containing template variables.

        Template variables contain information about this host that may be
        used in templates. This function attempts to be as comprehensive as
        possible in returning information about the host.

        WARNING: The returned dictionary could be very large!
        """

        variables = {}
        
        # Include basic properties
        variables.update(filter_keys(self._properties))
        
        # Get link information
        link = ccs_link(self._session_id, self["link_id"])
        variables.update(filter_keys(link))
        # Allow master interfaces to override link settings
        if variables["master_interface"]:
            if variables["master_mode"] != "":
                variables["mode"] = variables["master_mode"]
            if variables["master_channel"] != "":
                variables["channel"] = variables["master_channel"]
        # Output some other helper information
        variables["mode_adhoc"] = link.isAdHoc()
        variables["mode_managed"] = link.isManaged()
        variables["link_length"] = self.getInterfaceDistance()
        variables["gateway"] = link.getDefaultGateway(self["host_id"])
        if link["network_address"] != "":
            variables["netmask"] = cidrToNetmaskS(link["network_address"])
            variables["cidr_netmask"] = cidrToLength(link["network_address"])
            variables["network"] = cidrToNetworkS(link["network_address"])
            variables["broadcast"] = cidrToBroadcastS(link["network_address"])
            if variables["alias_netmask"] == "":
                variables["alias_netmask"] = variables["cidr_netmask"]
        try:
            variables["mac"] = self.getMACAddress()
        except:
            variables["mac"] = ""
        if "subasset_id" in self.keys() and self["subasset_id"]!="" and \
                int(self["subasset_id"])!=-1:
            sa = ccs_subasset(self._session_id, self["subasset_id"])
            if sa.supportsFunction("wireless_interface"):
                variables["wireless_interface"] = True
            else:
                variables["wireless_interface"] = False
            variables.update(sa.getTemplateVariables())
        else:
            variables["wireless_interface"] = False

        return variables
    
    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "getInterfaceMAC")
    def getMACAddress(self):
        """Returns the MAC address of this interface."""
        session = getSessionE(self._session_id)
        
        if self["subasset_id"] == "" or self["subasset_id"] == None:
            raise ccs_interface_error("No subasset_assigned")

        sql = "SELECT * FROM asset_macs WHERE subasset_id=%s"
        res = session.query(sql, (self["subasset_id"]))
        if len(res)!=1:
            raise ccs_interface_error("No MAC address found")
        
        return res[0]["mac"].lower()
    
    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "isInterfaceActive")    
    def interfaceActive(self):

        if "interface_active" not in self._properties.keys():
            return False
        if str(self["interface_active"]) == "t":
            return True

        return False
    
    @registerEvent("interfaceRemoved")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def removeInterface(self):
        """Removes the interface from the database."""
        session = getSessionE(self._session_id)
        
        # Raise the event
        triggerHostEvent(self._session_id, "interfaceRemoved", \
                self["host_id"], interface_id=self.interface_id)
    
        # Delete the site, will cause cascaded deletes
        sql = "DELETE FROM interface WHERE interface_id=%s"
        session.execute(sql, (self.interface_id))

        return self.returnSuccess()

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "interfaceHasSubasset")
    def hasSubasset(self):

        if "subasset_id" not in self._properties.keys():
            return False
        if self["subasset_id"] == -1 or self["subasset_id"]=="":
            return False
        
        return True

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, \
            "detachInterfaceSubasset") 
    def detachSubasset(self):
        """Detaches the specified subasset from the interface host
        
        Asset is only detached if it is not a subasset of the host asset
        """
        subasset = ccs_subasset(self._session_id, self["subasset_id"])
        if subasset["asset_id"] == host["asset_id"]:
            return
        subasset.moveToStock()

    def getInterfaceDistance(self):
        """Finds the distance of the largest link for a VAP.
           This is because setting a distance is global to a card
           and not specific to a VAP"""
        session = getSessionE(self._session_id)
        
        #If no subasset_id, then not a VAP
        if self['subasset_id'] == "":
            return 20000
        
        sql = "SELECT interface_id FROM interface WHERE subasset_id=%s"
        res = session.query(sql, (self['subasset_id']))
        distance = 0
        for iface in res:
            iface = ccs_interface(self._session_id, iface['interface_id'])
            link = ccs_link(self._session_id, iface['link_id'])
            distance = max(distance, link.getLength(iface.interface_id))

        return distance

@registerEvent("interfaceAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def addInterface(session_id, interface):
    """Creates a new interface on a host
    
    Throws an exception on error or returns the new interface ID
    """
    session = getSessionE(session_id)
    from ccs_host import ccs_host, getHostName
    
    print interface["vid"]
    # Check interface details
    validateInterface(session_id, interface)

    # Check interface type
    if "interface_type" in interface.keys():
        try:
            it = int(interface["interface_type"])
        except:
            ccs_interface_error("Invalid interface type! Must be an integer.")
        if it <= INTERFACE_TYPE_MIN or it >= INTERFACE_TYPE_MAX:
            raise ccs_interface_error("Invalid interface type! - %s" % \
                    interface["interface_type"])
    else:
        raise ccs_interface_error("Interface type must be specified!")
    
    # Check subasset is valid if it is specified
    if "subasset_id" in interface.keys() and interface["subasset_id"]!="" \
            and int(interface["subasset_id"])!=-1:
        subasset = ccs_subasset(session_id, interface["subasset_id"])
        if not subasset.supportsFunction("interface"):
            raise ccs_interface_error("Invalid subasset type for interface!")
        if it == INTERFACE_TYPE_VAP:
            # Check specified subasset supports virtual APs
            if not subasset.supportsFunction("vap"):
                raise ccs_interface_error("Invalid subasset type for VAP " \
                        "interface")
            # XXX: Check we're not over the maximum number of vaps...
        elif not subasset.availableForInterface(interface["host_id"]):
            raise ccs_interface_error("Subasset already in use!")
    else:
        try:
            del interface["subasset_id"]
        except KeyError: pass

    # If interface is active check subasset_id is specified
    if "interface_active" in interface.keys() and \
            interface["interface_active"]=="t":
        if it == INTERFACE_TYPE_PHYSICAL or it == INTERFACE_TYPE_VAP:
            if "subasset_id" not in interface.keys():
                raise ccs_interface_error("Cannot create active " \
                        "interface without specifying a subasset!")
        elif it == INTERFACE_TYPE_VLAN or it == INTERFACE_TYPE_ALIAS:
            if "raw_interface" not in interface.keys():
                raise ccs_interface_error("Cannot create active " \
                        "interface without specifying a raw interface!")
    
    # Check VLAN properties
    if it == INTERFACE_TYPE_VLAN:
        # Check the vid is valid if specified
        if "vid" in interface.keys() and \
                interface["vid"] != "":
            print interface["vid"]
            try:
                print interface["vid"]
                vid = int(interface["vid"])
            except:
                raise ccs_interface_error("VLAN ID must be an integer")
        # VLAN interfaces have a name derived from their parent interface
        parent_iface = ccs_interface(session_id, interface["raw_interface"])
        interface["name"] = "%s.%s" % \
                (parent_iface["name"], interface["vid"])

    # Check alias properties
    if it == INTERFACE_TYPE_ALIAS:
        # Check the netmask is valid if specified
        if "alias_netmask" in interface.keys() and \
                interface["alias_netmask"] != "":
            if interface["alias_netmask"].startswith("/"):
                interface["alias_netmask"] = interface["alias_netmask"][1:]
            try:
                interface["alias_netmask"] = int(interface["alias_netmask"])
            except:
                raise ccs_interface_error("Alias netmask must be an integer")
        # Alias interfaces have a name derived from their parent interface
        parent_iface = ccs_interface(session_id, interface["raw_interface"])
        interface["name"] = "%s-alias-%s" % \
                (parent_iface["name"], interface["link_id"])

    # XXX: Check raw interface is valid if specified
           
    # Ensure boolean values are specified correctly
    for f in ["use_gateway", "interface_active", "master_interface", \
            "monitor_interface"]:
        if f not in interface.keys():
            interface[f] = "f"
        else:
            if interface[f]!="t" and interface[f]!="f":
                raise ccs_interface_error("Invalid value for " \
                        "%s parameter" % f)
    
    link = ccs_link(session_id, interface["link_id"])

    # Check IP Parameters if applicable
    if interface["monitor_interface"]=="f" and \
            (interface["bridge_interface"]=="" or \
            int(interface["bridge_interface"])==-1):
        # Check this host doesn't already have an interface on this link
        if link.connectsHost(interface["host_id"]):
            raise ccs_interface_error("Host already has an interface on the " \
                    "specified link!")
    
        # Check IP specified is correct for the link, or allocate an IP
        if "ip_address" not in interface.keys():
            interface["ip_address"] = ""
        if interface["ip_address"] == "":
            interface["ip_address"] = \
                    link.allocateIP(interface["host_id"], \
                    interface["master_interface"])
        elif not link.isValidIP(interface["ip_address"]):
            raise ccs_interface_error("Invalid IP address for link!")
    elif interface["monitor_interface"]=="f":
            # XXX: Check bridge parameters are valid
            pass
                
    # Create changeset to wrap all of this
    commit = 0
    if session.changeset == 0:
        session.begin("Created interface (%s) on host %s" % \
                (interface["name"], \
                getHostName(session_id, interface["host_id"])))
        commit = 1

    # Make sure the subasset is attached to the host
    try:
        if "subasset_id" in interface.keys():
            subasset = ccs_subasset(session_id, interface["subasset_id"])
            host = ccs_host(session_id, interface["host_id"])
            if subasset["asset_id"] != host["asset_id"]:
                subasset.attachTo(host["asset_id"])
    except:
        log_warn("Could not attach subasset (%s) to host (%s)! Interface " \
                "creation may fail!" % \
                (interface["subasset_id"], interface["host_id"]), \
                sys.exc_info())
    
    # Build list of properties for the interface type
    props = [ "interface_id", "interface_type", "host_id", "link_id", \
            "name", "use_gateway", "interface_active", "master_interface", \
            "master_mode", "master_channel", "module_id", "monitor_interface"]
    nProps = []
    if it == INTERFACE_TYPE_PHYSICAL or it == INTERFACE_TYPE_VAP :
        props.extend(["subasset_id"])
        nProps.extend(["raw_interface"])
        nProps.extend(["raw_interface", "alias_netmask"])
    elif it == INTERFACE_TYPE_VLAN:
        props.extend(["raw_interface", "vid"])
        nProps.extend(["subasset_id", "alias_netmask"])            
    elif it == INTERFACE_TYPE_ALIAS:
        props.extend(["raw_interface"])
        nProps.extend(["subasset_id"])
        if "alias_netmask" in interface.keys() and \
                interface["alias_netmask"] != "":
            props.extend(["alias_netmask"])

    if interface["monitor_interface"]=="t":
        nProps.extend(["ip_address", "bridge_interface"])
    elif interface["bridge_interface"] != "" and \
            int(interface["bridge_interface"])!=-1:
        props.extend(["bridge_interface"])
        nProps.extend(["ip_address"])
    elif interface["ip_address"] == "":
        nProps.extend(["ip_address"])
    else:
        props.extend(["ip_address"])
        nProps.extend(["bridge_interface"])
        
    # Create the interface in the database
    (sql, values) = buildInsertFromDict("interface", props, interface, True, \
            nProps)
    session.execute(sql, values)
    
    # Get the new interface id
    sql = "SELECT currval('interface_interface_id_seq') as interface_id"
    res = session.query(sql, ())
    if len(res) != 1:
        raise ccs_interface_error("Could not retrieve new interface ID!")
    interface_id = res[0]["interface_id"]
    
    # If we started a changeset, then finish it off
    if commit == 1:
        session.commit()
    
    # Fire the trigger
    triggerHostEvent(session_id, "interfaceAdded", interface["host_id"], \
            interface_id=interface_id)
    
    return interface_id

@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR)
def getIfaceSuggestedIP(session_id, link_id, host_id, master_if):
    """Retrieves the suggested IP address for a specified interface"""  
    session = getSessionE(session_id)
    
    link = ccs_link(session.session_id, link_id)
    ip = link.allocateIP(host_id, master_if)
    return ip

@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR)
def getModules(session_id):
    """Returns a list of the wireless modules available"""
    session = getSessionE(session_id)

    # Retrieve the list of modules
    sql = "SELECT * FROM module"
    res = session.query(sql, ())
    return res

def validateInterface(session_id, details):
    """Validates the details are valid.

    This routine does not check for the existance of required data, it 
    only verifies that the fields in the supplied dictionary are valid.
    """
    from ccs_host import validateHostId
    
    # Check for required fields
    if "host_id" in details.keys():
        validateHostId(session_id, details["host_id"])
        
    if "link_id" in details.keys():
        validateLinkId(session_id, details["link_id"])
        
    if "name" in details.keys():
        if len(details["name"])>16:
            raise ccs_interface_error("Interface name must not be more " \
                    "than 16 characters")
        if details["name"].find(" ") != -1:
            raise ccs_interface_error("Interface name must not contain " \
                    "spaces")
    
    return

def validateInterfaceId(session_id, interface_id):
    """Checks that the specified interfaceID is valid (ie in the DB)"""
    session = getSessionE(session_id)

    rv = session.getCountOf("SELECT count(*) FROM interface WHERE " \
            "interface_id=%s", (site_id))
    if rv != 1:
        raise ccs_interface_error("Invalid Interface ID! Interface not found!")

    return
    
    
