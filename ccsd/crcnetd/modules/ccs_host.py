# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Host Module - Provides classes for manipulating hosts in the system
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
from twisted.web import resource, server
import os.path
import re

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC, registerResource
from crcnetd._utils.ccsd_service import getServiceInstance, getServiceID, \
        ccsd_service , ccs_service_error
from ccs_asset import validateAssetId, getSubassetName, getAssetDescription, \
        ccs_asset
from ccs_site import validateSiteId
import ccs_interface

ccs_mod_type = CCSD_SERVER
_kernels = {}

class ccs_host_error(ccsd_error):
    pass

class ccs_host(ccs_class):
    """Provides an abstract interface to a host in the CRCnet Configuration
    System.
    
    The members of this class loosely map to the fields of the host table
    in the database.
    """
    
    def __init__(self, session_id, host_id):
        """Initialises a new class for a specified host.

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
            raise ccs_host_error("Invalid session id")
        self._session_id = session_id
        
        # See if the specified host id makes sense
        sql = "SELECT * FROM host WHERE host_id=%s"
        res = session.query(sql, (host_id))
        if len(res) < 1:
            raise ccs_host_error("Invalid host. Unable to retrieve " 
                "details")
        
        # Store details 
        self.host_id = host_id
        self._properties = res[0]

    @registerEvent("hostRemoved")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def removeHost(self):
        """Removes the host from the database."""
        session = getSessionE(self._session_id)
        
        # Raise an event
        triggerHostEvent(self._session_id, "hostRemoved", self.host_id)
    
        # Delete the host, will cause cascaded deletes
        sql = "DELETE FROM host WHERE host_id=%s"
        res = session.execute(sql, (self.host_id))

        return self.returnSuccess()

    @registerEvent("hostModified")
    @registerEvent("hostnameChanged")
    @registerEvent("hostActiveChanged")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, "updateHostDetails")
    def updateDetails(self, newDetails):
        """Updates the details of the host.

        newDetails should be a dictionary containing only these host paramters
        that have changed and need to be updated in the database.

        Returns ccs_host.SUCCESS.
        """
        session = getSessionE(self._session_id)
        
        ################## Validate incoming data ##################

        validateHost(self._session_id, newDetails)
    
        # XXX: Check if the host can be moved to this site
        # XXX: Check if the asset can be added to this host/site
        
        ################## Update the database ##################
        
        # Wrap all changes into a single changeset if one is not already active
        self._forceChangeset("Updated host details", "host")

        # Build SQL
        props = ["host_name", "distribution_id", "kernel_id", "asset_id", \
                "ip_address", "site_id", "host_active", "is_gateway"]
        (sql, values) = buildUpdateFromDict("host", props, newDetails, \
                "host_id", self.host_id, True)
        
        if values == None:
            # No changes made... ?
            return self.returnSuccess()
        
        # Run the query
        session.execute(sql, values)

        # Raise the event
        triggerHostEvent(self._session_id, "hostModified", self.host_id)

        ################## Update associated information ##################
        
        # If site or asset changed, update asset location
        if "asset_id" in newDetails.keys():
            if int(newDetails["asset_id"]) == -1 and self.hasAsset():
                # Asset removed, Update interface configurations
                self.removeInterfaceSubassetLinks()
                # Move old asset back to stock
                self.removeAssetToStock()
            elif int(newDetails["asset_id"]) != -1:
                # Asset changed, update interface subassets
                self.updateInterfaceSubassetLinks(newDetails["asset_id"])
                # Move old asset to stock
                if self.hasAsset():
                    self.removeAssetToStock()
                # Possibly set new asset location
                if "site_id" in newDetails.keys():
                    sid = int(newDetails["site_id"])
                else:
                    sid = self._properties["site_id"]
                if sid != -1 and sid != None:
                    self.setAssetLocation(newDetails["asset_id"], sid)
        
        if "site_id" in newDetails.keys():
            if int(newDetails["site_id"]) == -1 and self.hasSite() and \
                    self.hasAsset():
                # Removed from a site, move asset back to stock
                self.moveAssetToStock()
            elif int(newDetails["site_id"]) != -1:
                # Site changed, possibly set new asset location
                if "asset_id" in newDetails.keys():
                    aid = int(newDetails["asset_id"])
                else:
                    aid = self._properties["asset_id"]
                if aid != -1 and aid != None:
                    self.setAssetLocation(aid, newDetails["site_id"])
        
        # Trigger an event if the hostname changes
        if "host_name" in newDetails.keys():
            if newDetails["host_name"] != self._properties["host_name"]:
                triggerHostEvent(self._session_id, "hostnameChanged", 
                        self.host_id, old_name=self._properties["host_name"])
        if "host_active" in newDetails.keys():
            if newDetails["host_active"] != self._properties["host_active"]:
                triggerHostEvent(self._session_id, "hostActiveChanged", 
                        self.host_id, host_active=newDetails["host_active"])
                
        # Update our internal state
        for prop in props:
            if prop in newDetails.keys():
                self._properties[prop] = newDetails[prop]
            
        ################## Clean Up and Return ##################
        return self.returnSuccess()

    @registerEvent("hostIPChanged")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, "updateHostIP")
    def updateHostIP(self, new_ip):
        """Allows the user to change the loopback IP of the host.

        Care is needed when using this function as it will allow you to set the
        IP to anything you choose, provided it is not currently in use elsewhere
        on the network. In particular, using this function you can select an IP
        that is not in the standard range of host loopback addressess.
        """
        session = getSessionE(self._session_id)

        # Validate IP address
        try:
            ip = ipnum(new_ip)
            if ip < 0 or ip > 4294967295:
                raise ccs_host_error("Invalid Host IP!")
            n = session.getCountOf("SELECT count(*) FROM host WHERE " \
                    "ip_address=%s AND host_id!=%s", (new_ip, self.host_id))
            n2 = session.getCountOf("SELECT count(*) FROM interface WHERE " \
                    "ip_address=%s", (new_ip))
            if (n+n2) > 0:
                raise ccs_host_error("Specified Host IP is already in use!")
        except:
            log_error("Exception while validating Host IP!", sys.exc_info())
            raise ccs_host_error("Could not validate Host IP")

        # Wrap all changes into a single changeset if one is not already active
        self._forceChangeset("Updated host IP", "host")

        # Update details
        session.execute("UPDATE host SET ip_address=%s WHERE host_id=%s", 
                (new_ip, self.host_id))

        # Trigger events
        triggerHostEvent(self._session_id, "hostIPChanged", self.host_id,
                old_ip=self._properties["ip_address"])

        # Update internal state
        self._properties["ip_address"] = new_ip

        # Return success
        return self.returnSuccess()

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, "getHost")
    def getDetails(self):
        """Returns a detailed object describing the host"""
        session = getSessionE(self._session_id)

        sql = "SELECT * FROM host_detail WHERE host_id=%s"
        res = session.query(sql, (self.host_id))
        return res[0]
        
    def getTemplateVariables(self):
        """Returns a dictionary containing template variables.

        Template variables contain information about this host that may be
        used in templates. This function attempts to be as comprehensive as
        possible in returning information about the host.

        WARNING: The returned dictionary could be very large!
        """
        global _kernels
        from ccs_interface import ccs_interface, INTERFACE_TYPE_ALIAS
        variables = {}
        
        # Include basic properties
        variables.update(filter_keys(self._properties))
        
        # Get interface information
        interfaces = self.getInterfaces()
        ilist = {}
        btargets = {}
        aliases = {}
        for n,iface in interfaces.items():
            if iface["interface_id"] == "" or iface["interface_id"] is None:
                continue
            niface = ccs_interface(self._session_id, \
                    iface["interface_id"])
            ifacevars = niface.getTemplateVariables()
            # Catch aliased interfaces here and store for later processing
            if iface["interface_type"] == INTERFACE_TYPE_ALIAS:
                if iface["raw_interface"] not in aliases.keys():
                    aliases[iface["raw_interface"]] = []
                aliases[iface["raw_interface"]].append(ifacevars)
                continue
            ifacevars["aliases"] = []
            # Handle bridge interface name resolution
            ifacevars["bridge_with"] = []
            ifacevars["bridge_interface_name"] = ""
            if ifacevars["bridge_interface"]!="" and \
                    ifacevars["bridge_interface"]!=-1:
                bi = ifacevars["bridge_interface"]
                bt = ccs_interface(self._session_id, bi)
                bn = bt["name"]
                ifacevars["bridge_interface_name"] = bn                        
                if bn in btargets.keys():
                    btargets[bn].append(iface["name"])
                else:
                    btargets[bn] = [iface["name"]]
            # Store interface
            ilist[iface["name"]] = ifacevars

        # Setup bridge targets
        for ifn,iflist in btargets.items():
            ilist[ifn]["bridge_with"] = iflist
            ilist[ifn]["bridge_interface_name"] = ifn
        
        # Setup aliases
        for n,iface in interfaces.items():
            if iface["interface_id"] not in aliases.keys():
                continue
            ilist[iface["name"]]["aliases"].extend( \
                    aliases[iface["interface_id"]])
        
        variables["interfaces"] = ilist

        # Output kernel name information
        kid = variables["kernel_id"]
        variables["kernel_name"] = "%s%s" % \
                (_kernels[kid]["upstream_release"], \
                _kernels[kid]["local_version"])

        # Get service information
        services = self.getServices()
        slist = {}
        for service in services:
            nservice = getServiceInstance(self._session_id, \
                    service["service_name"])
            slist[service["service_name"]] = \
                    nservice.getTemplateVariables(self.host_id)
        variables["service"] = slist
          
        return variables
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, "getHostInterfaces")
    def getInterfaces(self):
        """Returns a list of interfaces related to the host
        
        This list includes both defined and configured interfaces and also 
        hardware related to the host that may be used to create an interface
        but is not currently configured. 

        Result Sources:
        1. interface subassets that are part of the host asset
        2. interface assets attached to the host asset
        3. interface records with no asset assigned but configured on the host
        4. interface assets at the same site and configured on this host.
        """
        session = getSessionE(self._session_id)
        
        # Phew! Select all the physical interfaces of a host and their data
        # and then join that (via UNION) with any interfaces that do not have
        # a physical asset defined.
        sql = "SELECT i.host_id, hi.asset_id, hi.subasset_id, hi.name AS " \
                "sa_name, hi.description, i.interface_id, i.link_id, " \
                "i.module_id, i.ip_address, i.alias_netmask, i.name, " \
                "i.use_gateway, i.interface_active, i.master_interface, " \
                "i.master_mode, i.monitor_interface, i.interface_type, " \
                "i.master_channel, i.raw_interface, i.link_desc, " \
                "i.bridge_interface, m.mac " \
                "FROM asset_macs m, host_asset_interfaces hi LEFT JOIN " \
                "interface_linkdescs i ON hi.host_id=i.host_id AND " \
                "hi.subasset_id=i.subasset_id WHERE hi.subasset_id=" \
                "m.subasset_id AND hi.host_id=%s UNION SELECT i.host_id, " \
                "i.asset_id, i.subasset_id, NULL, NULL, i.interface_id, " \
                "i.link_id, i.module_id, i.ip_address, i.alias_netmask, " \
                "i.name, i.use_gateway, i.interface_active, " \
                "i.master_interface, i.master_mode, i.monitor_interface, " \
                "i.interface_type, i.master_channel, i.raw_interface, " \
                "i.link_desc, i.bridge_interface, NULL FROM " \
                "interface_linkdescs i WHERE " \
                "i.host_id=%s AND (i.subasset_id IS NULL OR " \
                "(i.subasset_id IS NOT NULL AND i.subasset_id NOT IN " \
                "(SELECT subasset_id FROM host_asset_interfaces WHERE " \
                "host_id=%s)))";
        res = session.query(sql, (self.host_id, self.host_id, self.host_id))
        
        res2 = {}
        i=0
        for iface in map(filter_keys, res):
            if iface["subasset_id"] != "":
                iface["sa_name"] = getSubassetName(self._session_id, \
                        iface["subasset_id"])
                iface["sa_desc"] = getAssetDescription(self._session_id, \
                        iface["asset_id"])
            res2[i] = iface
            i+=1
                
        return res2

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, "getHostServices")
    def getServices(self):
        """Returns a list of services defined on the host"""
        session = getSessionE(self._session_id)
        
        sql = "SELECT hs.service_id, hs.enabled, s.enabled AS " \
                "service_enabled, s.service_name FROM service_host hs, " \
                "service s WHERE s.service_id=hs.service_id AND hs.host_id=%s"
        res = session.query(sql, (self.host_id))
        return res
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getHostUnconfiguredServices")
    def getUnconfiguredServices(self):
        """Returns a list of services not configured for the host"""
        session = getSessionE(self._session_id)
        
        sql = "SELECT * FROM service WHERE service_id NOT IN (SELECT " \
                "service_id FROM service_host WHERE host_id=%s)"
        res = session.query(sql, (self.host_id))
        return res
     
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True)
    def getRawInterfaces(self, interface_type):
        """Retrieves a list of interfaces that can be used as a raw device.

        Raw devices can have virtual interfaces or IP addresses, added to them.
        Eg. VLANs, VAPs and Aliases.
        """
        from ccs_interface import INTERFACE_TYPE_VAP, \
                INTERFACE_TYPE_VLAN, INTERFACE_TYPE_PHYSICAL, \
                INTERFACE_TYPE_ALIAS
        session = getSessionE(self._session_id)
        
        res = {}
    
        try:
            interface_type = int(interface_type)
        except:
            raise ccs_host_error("Invalid interface type!")

        p = []
        if interface_type == INTERFACE_TYPE_VAP:
            # User wants to create a VAP interface, return all interfaces
            # that are based on Atheros cards
            sql = "SELECT i.interface_id, i.name FROM interface i, " \
                    "subasset sa, asset a WHERE i.interface_type=%s AND " \
                    "i.subasset_id=sa.subasset_id AND sa.asset_id=" \
                    "a.asset_id AND a.asset_type_id IN (SELECT " \
                    "asset_type_id FROM asset_type_map WHERE " \
                    "asset_function='vap_interface') AND i.host_id=%s"
            p = [INTERFACE_TYPE_PHYSICAL, self.host_id]
        elif interface_type == INTERFACE_TYPE_VLAN:
            # User wants to create a VLAN interface, return all interfaces
            # capable of creating VLANs
            # XXX: Currently we assume any physical interface can create a
            # VLAN... may need to look at this further
            sql = "SELECT i.interface_id, i.name FROM interface i WHERE " \
                    "i.interface_type=%s AND i.host_id=%s"
            p = [INTERFACE_TYPE_PHYSICAL, self.host_id]
        elif interface_type == INTERFACE_TYPE_ALIAS:
            # Any interface at all can receive an aliased IP, except for 
            # existing aliased interfaces
            sql = "SELECT i.interface_id, i.name FROM interface i WHERE " \
                    "i.interface_type!=%s AND i.host_id=%s"
            p = [INTERFACE_TYPE_ALIAS, self.host_id]
        else:
            raise ccs_host_error("Invalid interface type!")

        # Run the query
        res1 = session.query(sql, p)
        idx = 0
        for iface in res1:
            temp = {}
            temp["interface_id"] = iface["interface_id"]
            temp["description"] = "%s Interface" % iface["name"]
            res[idx] = temp
            idx+=1
            
        return res

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True)
    def getInterfaceSubassets(self, link_id=-1, interface_id=-1, \
            interface_type=-1):
        """Retrieves a list of subassets that could be used for an interface"""
        from ccs_link import ccs_link
        session = getSessionE(self._session_id)

        res = {}
        p = []

        ## Step 1, select subassets that are part of the host, or are already
        ## directly attached

        # If we're creating a VAP interface select only VAP capable assets
        if int(interface_type) == ccs_interface.INTERFACE_TYPE_VAP:
            # No need to worry about whether they're in use as a VAP capable
            # asset can support multiple virtual interfaces
            sql = "SELECT hai.* FROM host_asset_interfaces hai, " \
                    "subasset s, asset_type_subasset ats, " \
                    "subasset_type_map stm WHERE ((hai.subasset_id=" \
                    "s.subasset_id AND s.asset_type_subasset_id=" \
                    "ats.asset_type_subasset_id AND " \
                    "ats.subasset_type_id=stm.subasset_type_id AND " \
                    "stm.asset_function='vap')"
        else:
            # Normal interface, Retrieve the list of interface subassets that
            # are part of the host asset and are not currently in use
            sql = "SELECT * FROM host_asset_interfaces WHERE (subasset_id " \
                    "NOT IN (SELECT subasset_id FROM interface WHERE " \
                    "subasset_id IS NOT NULL)"

        # If an existing interface has been specified, make sure its currently
        # uses asset is in the list returned
        if interface_id != -1 and interface_id != "":
            sql += " OR subasset_id in (SELECT subasset_id FROM interface " \
                    "WHERE interface_id=%s)"
            p.append(interface_id)

        # And finally restrict results to the current host only
        sql += ") AND host_id=%s"
        p.append(self.host_id)

        # Get the results
        results = session.query(sql, p)

        ## Step 2, if a link has been specified, select "in stock" subassets
        ## that could be attached to the host. If no link has been specified
        ## we don't know what type of assets could be used so skip this step.
        if link_id != -1:
            link = ccs_link(self._session_id, link_id)
            tmp = link.getAvailableHardware(interface_type)
            results.extend(tmp)

        ## Step 3, if the host is at a site, find any assets that have been
        ## allocated to the site but are not yet in use.
        if self.hasSite():
            sql = "SELECT * FROM site_interface_subassets WHERE site_id=%s " \
                    "AND subasset_id NOT IN (SELECT subasset_id FROM " \
                    "interface WHERE subasset_id IS NOT NULL)"
            p = [self._properties["site_id"]]
            if self.hasAsset():
                sql += " AND asset_id!=%s"
                p.append(self._properties["asset_id"])
            tmp = session.query(sql, p)
            results.extend(tmp)

        ## Step 4, calculate a description for each asset
        idx = 0
        for subasset in results:
            temp = {}
            temp["subasset_id"] = subasset["subasset_id"]
            if subasset["asset_id"] == self._properties["asset_id"]:
                temp["description"] = "Host's %s" % subasset["name"]
            else:
                temp["description"] = "[%3s] %s" % \
                    (subasset["asset_id"], subasset["description"])
            res[idx] = temp
            idx+=1
               
        return res
    
    def removeInterfaceSubassetLinks(self):
        """Removes the subasset associated with each interface on the host

        This function is called when the host's asset is removed, for each
        subasset that was part of the host's asset the associated interface is
        disabled and set to have no associated hardware. 

        Assets that are attached to the hosts's asset and are configured as an 
        interface are relocated to the site the host is present at.

        This needs to be called before the internal properties are updated so 
        that self._properties["asset_id"] contains the ID of the asset that is
        being removed.
        """
        session = getSessionE(self._session_id)

        # Disable the interfaces that used subassets of the host asset
        session.execute("UPDATE interface SET subasset_id=NULL, " \
                "interface_active='f' WHERE host_id=%s AND subasset_id IN " \
                "(SELECT subasset_id FROM interface_subassets WHERE " \
                "asset_id=%s)", (self.host_id, self._properties["asset_id"]))

        # Move attached assets configured as an interface to the hosts site
        res = session.query("SELECT a.asset_id FROM interface i, subasset s, " \
                "asset a WHERE i.subasset_id=s.subasset_id AND " \
                "s.asset_id=a.asset_id AND i.host_id=%s AND " \
                "i.subasset_id NOT IN (SELECT subasset_id FROM " \
                "interface_subassets WHERE asset_id=%s)", 
                (self.host_id, self._properties["asset_id"]))
        for iface in res:
            asset = ccs_asset(self._session_id, iface["asset_id"])
            if self.hasSite():
                asset.moveToSite(self._properties["site_id"])
            else:
                asset.moveToStock()
        
    def updateInterfaceSubassetLinks(self, new_asset_id):
        """Updates the subasset associated with each interface on the host

        This function is called when a hosts asset is changed. For each
        subasset that was part of the old host asset, the new asset is search
        for a subasset that matches the type and name, if one is found the 
        interface is updated to use it. Any remaining subassets on the original
        host asset after this step are matched with any free subassets of the
        appropriate type on the new asset. Any remaining subassets on the 
        original host after both these steps are disabled.

        Assets that are attached to hosts asset and are configured as an 
        interface are reattached to the new host asset.

        This needs to be called before the internal properties are updated so 
        that self._properties["asset_id"] contains the ID of the asset that is
        being removed.
        """
        session = getSessionE(self._session_id)
        used = []
        remaining = False

        # Exit now if the host did not have an asset assigned previously
        if self._properties["asset_id"] == "":
            return

        # Get a list of configured interface subassets on the old host and
        # their matching pair (based on name) on the new host
        res = session.query("SELECT a.name, a.asset_id AS old_asset_id, " \
                "a.subasset_id AS old_subasset_id, b.asset_id AS " \
                "new_asset_id, b.subasset_id AS new_subasset_id FROM " \
                "interface_subassets a LEFT JOIN interface_subassets b ON " \
                "a.name=b.name AND b.asset_id=%s WHERE a.asset_id=%s", 
                (new_asset_id, self._properties["asset_id"]))
        for match in res:
            if match["new_subasset_id"] == "":
                remaining = True
                continue
            session.execute("UPDATE interface SET subasset_id=%s WHERE " \
                    "host_id=%s AND subasset_id=%s", 
                    (match["new_subasset_id"], self.host_id, \
                            match["old_subasset_id"]))
            used.append(match["new_subasset_id"])

        # Now deal with the remainders, don't both matching names
        if remaining:
            # Fetch a list of interface subassets on the new asset
            idx = 0
            res2 = session.query("SELECT * FROM interface_subassets WHERE " \
                    "asset_id=%s", new_asset_id)
            # Loop through each remaining subasset from the old asset
            for match in res:
                if match["new_subasset_id"] != "":
                    continue
                fixed = False
                while idx < len(res2):
                    # Check this subasset wasn't used above
                    if res2[idx]["subasset_id"] in used:
                        idx += 1
                        continue
                    # Use it
                    session.execute("UPDATE interface SET subasset_id=%s " \
                            "WHERE host_id=%s AND subasset_id=%s", 
                            (res2[idx]["subasset_id"], self.host_id, \
                                    match["old_subasset_id"]))
                    used.append(res2[idx]["new_subasset_id"])
                    idx += 1
                    fixed = True
                    break
                # Disable if not fixed
                if not fixed:
                    session.execute("UPDATE interface SET subasset_id=NULL, " \
                            "interface_active='f' WHERE host_id=%s AND " \
                            "subasset_id=%s", (self.host_id, \
                            match["old_subasset_id"]))
                            
        # Move attached assets configured as an interface to the hosts site
        res = session.query("SELECT a.asset_id FROM interface i, subasset s, " \
                "asset a WHERE i.subasset_id=s.subasset_id AND " \
                "s.asset_id=a.asset_id AND i.host_id=%s AND " \
                "i.subasset_id NOT IN (SELECT subasset_id FROM " \
                "interface_subassets WHERE asset_id=%s OR asset_id=%s)", 
                (self.host_id, self._properties["asset_id"], new_asset_id))
        for iface in res:
            asset = ccs_asset(self._session_id, iface["asset_id"])
            asset.attachTo(new_asset_id)

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, "hostHasService")
    def hasService(self, service_id):
        session = getSessionE(self._session_id)
        n = session.getCountOf("SELECT count(*) FROM service s, " \
                "service_host sh WHERE sh.host_id=%s AND s.service_id=" \
                "sh.service_id AND s.service_id=%s", \
                (self.host_id, service_id))
        if n == 1:
            return True
        else:
            return False
    def hasServiceByName(self, service_name):
        service_id = getServiceID(self._session_id, service_name)
        return self.hasService(service_id)
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "hostHasServiceEnabled")
    def hasServiceEnabled(self, service_id):
        """Returns true if the specified service is enabled on the host"""
        service = ccsd_service(self._session_id, service_id)
        return service.getHostState(self.host_id)
    def hasServiceEnabledByName(self, service_name):
        service_id = getServiceID(self._session_id, service_name)
        return self.hasServiceEnabled(service_id)
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, "hostHasSite")
    def hasSite(self):

        if "site_id" not in self._properties.keys():
            return False
        if self["site_id"] == -1 or self["site_id"] == "":
            return False

        return True
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, "hostHasAsset")
    def hasAsset(self):

        if "asset_id" not in self._properties.keys():
            return False
        if self["asset_id"] == -1 or self["asset_id"] == "":
            return False

        return True
    
    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, "hostEnabled")
    def hostEnabled(self):

        if "host_active" not in self._properties.keys():
            return False
        if str(self["host_active"]) == "t":
            return True

        return False

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def removeAssetToStock(self):
        """Removes the host asset and shifts it to stock"""
        asset = ccs_asset(self._session_id, self["asset_id"])
        asset.moveToStock()
        self._properties["asset_id"] = -1
        
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def moveAssetToStock(self):
        """Moves the host asset to stock, leaving it attached to the host"""
        asset = ccs_asset(self._sesion_id, self["asset_id"])
        asset.moveToStock()

    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def setAssetLocation(self, newAsset=-1, newSite=-1):
        """Moves the host asset to a new location

        If newAsset or newSite are present and are not -1 they override 
        the values stored in our current properties.
        """

        # Process overrides
        if newAsset != -1:
            asset_id = newAsset
        else:
            asset_id = self["asset_id"]
        if newSite != -1:
            site_id = newSite
        else:
            site_id = self["site_id"]
            
        # Check asset and site are specified
        if site_id == -1 or asset_id == -1:
            return
        
        # Move to site
        asset = ccs_asset(self._session_id, asset_id)
        asset.moveToSite(site_id)
  
@registerEvent("hostAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def addHost(session_id, host):
    """Adds a new host to the database"""
    session = getSessionE(session_id)
    
    # Check host details
    validateHost(session_id, host, True)

    # Get loopback IP if not specified
    if "ip_address" not in host.keys() or host["ip_address"] == "":
        link_class_id = None
        if "link_class_id" in host.keys():
            link_class_id = host["link_class_id"]
        host["ip_address"] = allocateLoopbackIP(session_id, link_class_id)
    
    # Build query
    props = ["host_id", "host_name", "distribution_id", "kernel_id", \
            "ip_address", "asset_id", "site_id", "host_active", "is_gateway"]
    (sql, values) = buildInsertFromDict("host", props, host)
    
    # Run query
    session.execute(sql, values)

    # Get new host id
    res = session.query("SELECT currval('host_host_id_seq') " \
            "AS host_id", ())
    if len(res) != 1 or res[0]["host_id"]<1:
        return xmlrpclib.Fault(CCSD_BADPARAM, "Could not retrieve host ID")
    host_id = res[0]["host_id"]
    
    # Update asset location if required
    if "site_id" in host.keys() and "asset_id" in host.keys() and \
            int(host["site_id"])!=-1 and int(host["asset_id"])!=-1:
        asset = ccs_asset(session_id, host["asset_id"])
        asset.moveToSite(host["site_id"])

    # Fire trigger
    triggerHostEvent(session_id, "hostAdded", host_id)

    return host_id

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getHostList(session_id):
    """Returns a list of hosts"""
    from crcnetd.modules.ccs_status import getHostStatusSummary
    session = getSessionE(session_id)
    
    # Retrieve the hosts
    sql = "SELECT * FROM host_list"
    res = session.query(sql, ())
    for host in res:
        host.update(getHostStatusSummary(session_id, host["host_name"]))
        host.update({"host_key":re.sub("[^\w]", "_", host["host_name"])})

    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getHostName(session_id, host_id):
    """Returns the name for the specified host"""
    session = getSessionE(session_id)

    res = session.query("SELECT host_name FROM host WHERE host_id=%s", \
            (host_id))
    if len(res) != 1:
        raise ccs_host_error("Unable to retrieve hostname!")
    return res[0]["host_name"]

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getHostID(session_id, host_name):
    """Returns the ID for the specified host"""
    session = getSessionE(session_id)

    res = session.query("SELECT host_id FROM host WHERE host_name=%s", \
            (host_name))
    if len(res) != 1:
        raise ccs_host_error("Unable to retrieve host ID!")
    return res[0]["host_id"]

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getAvailHostAssets(session_id, site_id=-1):
    """Returns a list of assets that could be used for a new host

    Returns a list of assets that are assigned to a site and could be used
    for a new host. If the site_id is -1 then a list of assets in stock that
    could be used for a new host are returned.
    """
    session = getSessionE(session_id)

    if site_id==-1:
        # Return generic list of available host assets at site 'stock'
        sql = "SELECT s.asset_id, s.description FROM site_host_assets_avail " \
                "s, asset a WHERE a.asset_id=s.asset_id AND s.site_id IN " \
                "(SELECT site_id FROM asset_stock_location) " \
                "AND s.asset_id NOT IN (SELECT asset_id FROM host WHERE " \
                "asset_id IS NOT NULL) AND a.asset_type_id IN " \
                "(SELECT asset_type_id FROM asset_type_map WHERE " \
                "asset_function='host')"
        p = ()
    else:
        # Verify site_id is OK
        validateSiteId(session_id, site_id)
        # Return list of host assets assigned to site but not yet to a host
        sql = "SELECT asset_id, description FROM site_host_assets_avail " \
                "WHERE site_id=%s"
        p = (site_id)
        
    res = session.query(sql, p)
    return res

@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def allocateLoopbackIP(session_id, class_id=None):
    """Allocates a new loopback IP address for a host

    Loopback IPs are allocated out of a pool identified from the link_class
    table.
    """
    session = getSessionE(session_id)
    
    # Get the loopback range
    if class_id != None:
        prop = (class_id)
        sql = "SELECT * FROM link_class WHERE link_class_id=%s"
    else:
        prop = ()
        sql = "SELECT * FROM link_class WHERE description LIKE 'Loopback%%'"
    res = session.query(sql, prop)
    if len(res)<1:
        raise ccs_host_error("No loopback link class available!")
    
    # XXX: Just use the first loopback range returned atm
    loopback = res[0]
    
    # Check it is valid
    if int(loopback["allocsize"]) != 32:
        raise ccs_host_error("Invalid loopback address range. Cannot " \
                "allocate address!")
    
    # Set the initial IP to loopback range network + 1
    network = cidrToNetwork(loopback["netblock"])
    ip = network + 1
    netmask = cidrToNetmask(loopback["netblock"])

    # Find current highest loopback IP allocated
    sql = "SELECT ip_address FROM host ORDER BY ip_address DESC"
    res = session.query(sql, ())
    
    for host in res:
        # Check ip is same netblock as we are allocating from
        addr = ipnum(host["ip_address"])
        if not inNetwork(addr, network, netmask):
            continue
        # Select next highest IP
        ip = addr+1
        break

    return formatIP(ip)

def validateHost(session_id, details, required=False):
    """Validates the details are valid.
    
    This routine does not check for the existance of required data, it 
    only verifies that the fields in the supplied dictionary are valid.
    """
    session = getSessionE(session_id)
    
    if "host_name" in details.keys():
        if len(details["host_name"])<=0:
            raise ccs_host_error("Hostname must be greater than 0 " \
                    "characters long!")
        if len(details["host_name"]) > 64:
            raise ccs_host_error("Hostname must be less than 64 " \
                    "characters long!")
        if details["host_name"].find(" ") != -1:
            raise ccs_host_error("Hostname must not contain spaces")
    elif required:
        raise ccs_host_error("Hostname is a required field")
        
    if "distribution_id" in details.keys():
        validateDistributionId(session_id, details["distribution_id"])
    elif required:
        raise ccs_host_error("Distribution is a required field")
    
    if "kernel_id" in details.keys():
        validateKernelId(session_id, details["kernel_id"])
    elif required:
        raise ccs_host_error("Kernel is a required field")
        
    if "host_active" in details.keys():
        if details["host_active"] != "t" and details["host_active"] != "f":
            raise ccs_host_error("Invalid host status value. Must be 't' " \
                    "or 'f'")
    elif required:
        raise ccs_host_error("Host status is a required field")
        
    if "is_gateway" in details.keys():
        if details["is_gateway"] != "t" and details["is_gateway"] != "f":
            raise ccs_host_error("Invalid is gateway value. Must be 't' " \
                    "or 'f'")
    elif required:
        raise ccs_host_error("Gateway is a required field")
            
    # XXX: Check ip_address field
    
    # Site
    if "site_id" in details.keys() and int(details["site_id"])!=-1:
        validateSiteId(session_id, details["site_id"])
        
    # Asset
    if "asset_id" in details.keys() and int(details["asset_id"])!=-1:
        asset = ccs_asset(session_id, details["asset_id"])

        # Check asset is of the correct type
        if not asset.supportsFunction("host"):
            raise ccs_host_error("Specified asset is not of the " \
                    "appropriate type to use as a host!")
                    
        # Check asset isn't assigned elsewhere
        if "site_id" in details.keys():
            site_id = details["site_id"]
        else:
            site_id = -1
        if not asset.availableForHost(site_id):
            raise ccs_host_error("Specified asset already in use or " \
                    "not available!")
    
    return

def validateHostId(session_id, host_id):
    """Checks that the specified hostID is valid (ie in the DB)"""
    session = getSessionE(session_id)

    rv = session.getCountOf("SELECT count(*) FROM host WHERE host_id=%s", \
                (host_id))
    if rv != 1:
        raise ccs_host_error("Invalid Host ID! Host not found!")

    return

#####################################################################
# Loopbacks
#####################################################################
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getLoopbackRanges(session_id):
    """Returns a list of the distributions"""
    session = getSessionE(session_id)

    # Retrieve the distributions
    sql = "SELECT * FROM link_class where description ~ 'Loopback'";
    res = session.query(sql, ())
    return res

def validateLinkClassId(session_id, link_class_id):
    """Checks if the specified distribution is valid"""
    session = getSessionE(session_id)

    rv = session.getCountOf("SELECT count(*) FROM link_class " \
            "WHERE link_class_id=%s", (link_class_id))
    
    if rv != 1:
        raise ccs_host_error("Invalid Link Class! Specified " \
                "Loopback range not found!")
    
    return

#####################################################################
# Distributions
#####################################################################
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getDistributions(session_id):
    """Returns a list of the distributions"""
    session = getSessionE(session_id)

    # Retrieve the distributions
    sql = "SELECT * FROM distribution"
    res = session.query(sql, ())
    return res

def validateDistributionId(session_id, distribution_id):
    """Checks if the specified distribution is valid"""
    session = getSessionE(session_id)

    rv = session.getCountOf("SELECT count(*) FROM distribution " \
            "WHERE distribution_id=%s", (distribution_id))
    
    if rv != 1:
        raise ccs_host_error("Invalid Distribution! Specified " \
                "distribution not found!")
    
    return

#####################################################################
# Kernels
#####################################################################
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getKernels(session_id):
    """Returns a list of the kernels"""
    session = getSessionE(session_id)
    
    # Retrieve the kernels
    sql = "SELECT * FROM kernel"
    res = session.query(sql, ())
    return res

def validateKernelId(session_id, kernel_id):
    """Checks if the specified kernel is valid"""
    session = getSessionE(session_id)
    
    rv = session.getCountOf("SELECT count(*) FROM kernel WHERE " \
            "kernel_id=%s", (kernel_id))
    if rv != 1:
        raise ccs_host_error("Invalid Kernel! Specified kernel not found!")
 
    return

#####################################################################
# Webserver Portion to resolve hostnames to Asset Details
#####################################################################
class ccs_hostlookup(resource.Resource):
    """Implements a simple Hostname lookup resource

    Called when the main server receives a query for /hostlookup/*
    """
    
    # Name for the resource
    resourceName = "Hostname Lookup Server"
    
    # Mark as leaf so that render gets called
    isLeaf = 1
        
    def render(self, request):

        session = getSession(ADMIN_SESSION_ID)
        
        host_name = os.path.basename(request.path)
        
        #XXX: Verify MAC format here
        
        log_debug("Received hostlookup request for %s" % host_name)

        # Lookup mac
        sql = "SELECT h.host_name, h.ip_address, am.asset_id, am.mac FROM " \
                "host h LEFT JOIN asset_macs am ON h.asset_id=" \
                "am.asset_id WHERE h.host_name=%s LIMIT 1"
        try:
            res = session.query(sql, (host_name.strip()))
        except:
            (type, value, tb) = sys.exc_info()
            log_warn("Could not lookup host!", sys.exc_info())
            request.setResponseCode(500, "Database query failed - %s" % \
                    value)
            request.finish()
            return server.NOT_DONE_YET
        
        if len(res)!=1:
            request.setResponseCode(404, "Specified Host not found!")
            request.finish()
            return server.NOT_DONE_YET
        
        # Write out info about the host
        rs = "FOUND=1\nASSET_ID=%s\nHOST_NAME=%s\nHOST_IP=%s\nMAC=%s\n" % \
                (res[0]["asset_id"], res[0]["host_name"], \
                res[0]["ip_address"], res[0]["mac"])
        return rs
    
def ccs_init():
    global _kernels
    
    # Register Hostname Lookup Handler
    registerResource("hostlookup", ccs_hostlookup)

    # Cache a list of kernels
    for kernel in getKernels(ADMIN_SESSION_ID):
        _kernels[kernel["kernel_id"]] = kernel

    
