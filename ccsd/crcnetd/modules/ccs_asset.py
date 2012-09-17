# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Asset Module - Provides classes to manipulate assets in the system
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
from OpenSSL import crypto
from md5 import md5

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC, registerResource
from crcnetd._utils.ccsd_ca import ccs_ca, getCertificateParameters, \
        CERT_PARAM_NAMES, REVOKE_SUPERSEDED
from ccs_site import getSiteName

ccs_mod_type = CCSD_SERVER
DEFAULT_CURRENCY = "NZD"

class ccs_asset_error(ccsd_error):
    pass

#####################################################################
# Assets 
#####################################################################
class ccs_asset(ccs_class):
    """Provides an abstract interface to an asset in the CRCnet Configuration
    System.
    
    The members of this class loosely map to the fields of the asset table
    in the database.
    """
    
    def __init__(self, session_id, asset_id):
        """Initialises a new class for a specified asset.
        
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
            raise ccs_asset_error("Invalid session id")
        self._session_id = session_id
        
        # See if the specified asset id makes sense
        sql = "SELECT * FROM asset WHERE asset_id=%s"
        res = session.query(sql, (asset_id))
        if len(res) < 1:
            raise ccs_asset_error("Invalid asset. Unable to retrieve " 
                "details")
        
        # Store details 
        self.asset_id = asset_id
        self._properties = res[0]

    @registerEvent("assetDetailsUpdated")
    @exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER, True)
    def updateAssetDetail(self, data_name, value):
        """Updates an asset in the database"""
        session = getSessionE(self._session_id)
        
        # Check it is a valid value
        if data_name not in ["description", "serial_no", "date_purchased", \
                "currency", "price", "supplier", "enabled", "notes"]:
            raise ccs_asset_error("Invalid asset data value!")
        # Check the value of the data being updated
        asset = {}
        asset[data_name] = value
        res =  _validateAsset(self._session_id, asset, False)
        
        # If a changeset is not already active, start one for this batch
        self._forceChangeset("Updated details of asset #%s" % self.asset_id, \
                "asset")

        # Do the update
        sql = "UPDATE asset SET %s=%%s WHERE asset_id=%%s" % data_name
        session.execute(sql, (value, self.asset_id))
            
        # Record the change
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1, data2) VALUES (%s, %s, %s, %s, %s)"
        p = (self.asset_id, ASSET_EVENT_DETAILS_UPDATED, session.username, \
                data_name, value)
        session.execute(sql, p)

        # Raise the event
        triggerEvent(self._session_id, "assetDetailsUpdated", \
                asset_id=self.asset_id)
        
        return self.returnSuccess()

    @registerEvent("assetLocationChanged")
    @exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER, True, "moveAssetToSite")
    def moveToSite(self, site_id):
        """Updates the asset's location to the specified site"""

        session = getSessionE(self._session_id)
        
        # Ensure the following changes are grouped together
        self._forceChangeset("Moving asset #%s to site %s" % \
                (self.asset_id, getSiteName(self._session_id, site_id)), \
                "asset")
    
        # Update the asset location table
        sql = "UPDATE asset_location SET site_id=%s, attached_to=NULL, " \
                "location_updated=NOW() WHERE asset_id=%s"
        p = (site_id, self.asset_id)
        session.execute(sql, p)

        # Record the event
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1) VALUES (%s, %s, %s, %s)"
        p = (self.asset_id, ASSET_EVENT_LOCATION_CHANGED, session.username, \
                site_id)
        session.execute(sql, p)
    
        # Raise the event
        triggerEvent(session.session_id, "assetLocationChanged", \
                asset_id=self.asset_id)
        
        return self.returnSuccess()
    
    @registerEvent("assetLocationChanged")
    @exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER, True, "attachAssetTo")
    def attachTo(self, asset_id):
        """Attaches this asset to the specified asset"""
        
        session = getSessionE(self._session_id)
        
        # Ensure the following changes are grouped together
        self._forceChangeset("Attaching asset #%s to asset #%s" % \
                (self.asset_id, asset_id), "asset")
    
        # Update the asset location table
        sql = "UPDATE asset_location SET site_id=NULL, attached_to=%s, " \
                "location_updated=NOW() WHERE asset_id=%s"
        p = (asset_id, self.asset_id)
        session.execute(sql, p)

        # Record the event
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1) VALUES (%s, %s, %s, %s)"
        p = (self.asset_id, ASSET_EVENT_ATTACHED, session.username, \
                asset_id)
        session.execute(sql, p)
    
        # Raise the event
        triggerEvent(session.session_id, "assetLocationChanged", \
                asset_id=self.asset_id)
        
        return self.returnSuccess()
    
    @registerEvent("assetLocationChanged")
    @exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER, True, "assignAssetTo")
    def assignTo(self, thing_name):
        """Attaches this asset to a named thing (usually a person)"""
        
        session = getSessionE(self._session_id)
        
        # Check that we have a site called "Assigned Assets"
        sql = "SELECT site_id FROM site WHERE location='" \
                "Assigned Assets'"
        assigned_site = session.getCountOf(sql, ())
        if assigned_site <= 0 :
            raise ccs_asset_error("Cannot assign asset! " \
                    "No 'Assigned Assets' location")
        if len(thing_name.strip()) <= 0:
            raise ccs_asset_error("You must specify the name of what the " \
                    "asset is being assigned to")

        # Ensure the following changes are grouped together
        self._forceChangeset("Assigning asset #%s to %s" % \
                (self.asset_id, thing_name), "asset")
    
        # Update the asset location table
        sql = "UPDATE asset_location SET site_id=%s, attached_to=NULL, " \
                "location_updated=NOW() WHERE asset_id=%s"
        p = (assigned_site, self.asset_id)
        session.execute(sql, p)

        # Record the event
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1) VALUES (%s, %s, %s, %s)"
        p = (self.asset_id, ASSET_EVENT_ASSIGNED, session.username, \
                thing_name)
        session.execute(sql, p)
    
        # Raise the event
        triggerEvent(session.session_id, "assetLocationChanged", \
                asset_id=self.asset_id)
        
        return self.returnSuccess()
        
    def moveToStock(self):
        """Updates the asset's location to the default stock site"""
 
        session = getSessionE(self._session_id)
        
        # Ensure the following changes are grouped together
        self._forceChangeset("Moving asset #%s to stock" % (self.asset_id), \
                "asset")
    
        # Update the asset location table
        sql = "UPDATE asset_location SET site_id=(SELECT site_id FROM " \
                "asset_stock_location WHERE default_location='t'), " \
                "attached_to=NULL, location_updated=NOW() WHERE asset_id=%s"
        p = (self.asset_id)
        session.execute(sql, p)

        # Get the stock location
        sql = "SELECT site_id FROM asset_stock_location WHERE " \
                "default_location='t'"
        default_site = session.getCountOf(sql, ())
        
        # Record the event
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1) VALUES (%s, %s, %s, %s)"
        p = (self.asset_id, ASSET_EVENT_LOCATION_CHANGED, session.username, \
                default_site)
        session.execute(sql, p)
    
        # Raise the event
        triggerEvent(session.session_id, "assetLocationChanged", \
                asset_id=self.asset_id)
        
        return self.returnSuccess()
   
    def supportsFunction(self, function):
        """Returns true if this asset supports the specified function"""

        session = getSessionE(self._session_id)
        
        return session.getCountOf("SELECT count(*) FROM asset a, " \
            "asset_type_map am WHERE a.asset_type_id=" \
            "am.asset_type_id AND am.asset_function=%s AND " \
            "a.asset_id=%s", (function, self.asset_id))

    def availableForHost(self, site_id):
        """Returns true if this asset can be a host at the specified site
        
        If site_id is -1 then Stock is assumed.
        """
        session = getSessionE(self._session_id)

        # Check if specified asset is availale for use at a host
        res = session.getCountOf("SELECT count(*) FROM assets_avail WHERE " \
                "asset_id=%s", (self.asset_id))
        if res == 1:
            return True

        # Check site specific availability
        if site_id!=-1:
            res = session.getCountOf("SELECT count(*) FROM " \
                    "site_host_assets_avail " \
                    "WHERE site_id=%s AND asset_id=%s", \
                    (site_id, self.asset_id))
        if res == 1:
            return True
        
        # Not available, must be in use
        return False
   
    @registerEvent("subassetAdded")
    @exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER, True)
    def addSubasset(self, at_subasset_id, sadata):
        """Adds a new subasset to an asset"""
        session = getSessionE(self._session_id)

        # Validate parameters
        res = _isValidAssetTypeSubassetId(self._session_id, at_subasset_id)
        
        # Check this asset is:
        # - allowed this subasset
        # - doesn't have it already
        sql = "SELECT ats.asset_type_subasset_id, ats.subasset_type_id " \
                "FROM asset_type_subasset ats, asset a WHERE " \
                "a.asset_type_id=ats.asset_type_id AND a.asset_id=%s " \
                "AND ats.asset_type_subasset_id not in (SELECT " \
                "asset_type_subasset_id FROM subasset WHERE asset_id=%s)"
        res = session.query(sql, (self.asset_id, self.asset_id))
        subasset_type_id = -1
        for row in res:
            if int(row["asset_type_subasset_id"]) == int(at_subasset_id):
                subasset_type_id = row["subasset_type_id"]
                break
        if subasset_type_id == -1:
            raise ccs_asset_error("Cannot add subasset of specified type " \
                    "to this asset!")
            
        # Check all the properties
        properties = getLinkedProperties(self._session_id, subasset_type_id)
        schema = {}
        schema["properties"] = {}
        props = {}
        for prop in properties:
            subasset_property_id = prop["subasset_property_id"]
            props[subasset_property_id] = prop
        schema["properties"] = props
        _validateSubassetProperties(sadata["properties"], schema)
        
        # If a changeset is not already active, start one for this batch
        self._forceChangeset("Added subasset to asset #%s" % self.asset_id, \
                "asset")

        # Add the subasset
        sql = "INSERT INTO subasset (asset_id, asset_type_subasset_id, " \
                    "enabled) VALUES (%s, %s, %s)"
        p = (self.asset_id, at_subasset_id, sadata["enabled"])
        session.execute(sql, p)

        # Get the new subasset_id
        sql = "SELECT currval('subasset_subasset_id_seq') as subasset_id"
        res = session.query(sql, ())
        subasset_id = res[0]["subasset_id"]
        
        # Add the property data
        for subasset_property_id,value in sadata["properties"].items():
            sql = "INSERT INTO asset_data (subasset_property_id, " \
                    "subasset_id, value) VALUES (%s, %s, %s)"
            p = (subasset_property_id, subasset_id, str(value))
            session.execute(sql, p)
        
        # Add event
        # XXX: This should probably be functionalised
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1) VALUES (%s, %s, %s, %s)"
        session.execute(sql, (self.asset_id, ASSET_EVENT_SUBASSET_ADDED, \
                session.username, subasset_id))
        
        # Raise the event
        triggerEvent(self._session_id, "subassetAdded", \
                asset_id=self.asset_id, subasset_id=subasset_id)

        return subasset_id

    @exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER, True)
    def getAttachedAssets(self):
        """Returns a list of assets that are attached to this asset"""
        session = getSessionE(self._session_id)

        return session.query("SELECT a.* FROM asset a, asset_location al " \
                "WHERE a.asset_id=al.asset_id AND al.attached_to=%s", \
                (self.asset_id))
        
    def getTemplateVariables(self):
        
        variables = {}
        
        for key,value in filter_keys(self._properties).items():
            if key.startswith("asset"):
                variables[key] = value
            else:
                variables["asset_%s" % key] = value

        return variables

    @exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER, True, "getAssetMac")
    def getMAC(self):
        """Returns the MAC address of the asset

        This method is only available for assets that may be used as a host. 
        We simply return the MAC address of the eth0 interface as the device's
        MAC address

        This is used by many modules as a unique key for the asset that will
        not change irrespective of its asset ID. It is also easily discoverable
        via the network.
        """
        
        # Check this asset can be used as a host
        if not self.supportsFunction("host"):
            raise ccs_asset_error("Cannot retrieve eth0 MAC address for a " \
                    "non host asset")
        
        # Look for the MAC address
        mac = None
        asset = getAsset(self._session_id, self.asset_id)
        for id,subasset in asset["subassets"].items():
            if subasset["name"] != "eth0":
                continue
            for pid, prop in subasset["properties"].items():
                if prop["description"] == "MAC Address":
                    mac = prop["value"]
                    break
            break    
        if mac is None or mac == "":
            raise ccs_asset_error("No eth0 MAC address found!")
        
        return mac.lower()

    def _getPassword(self):
        """Helper function for getPassword

        Determines the root password for the device
        """
        asset = getAsset(self._session_id, self.asset_id)
        for id,subasset in asset["subassets"].items():
            if subasset["description"] != "Motherboard":
                continue
            for pid, prop in subasset["properties"].items():
                if prop["description"] == "Root Password":
                    if prop["value"] != "":
                        return prop["value"]
                    if prop["default_value"] != "":
                        return prop["default_value"]
                    break
            break    

        return ""

    @exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER, True, "getAssetPassword")
    def getPassword(self):
        """Returns the device's password

        This password is generated by looking for a property called "Root
        Password" on the device. If this property is not set on the device the
        default value for the asset type is used instead. If both these
        properties a missing the blank string "" is used. 

        Once the root password has been determined it is concatenated with the
        first MAC address belonging to the device (eg. eth0) and the last 8
        characters of the md5sum of this string is returned as the password.
        """

        # Check this asset can be used as a host
        if not self.supportsFunction("host"):
            raise ccs_asset_error("Cannot get password for a non host asset")

        # Get the root password
        password = self._getPassword()
        # Get the MAC address of the specified device
        mac = self.getMAC()
        
        # Calculate and return the password
        sum = md5("%s%s" % (password, mac)).hexdigest()
        return sum[-8:]
    
    @exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER, True, "getAssetCert")
    def getCert(self, csr, force_mac=False):
        """Signs the specified request to generate a certificate for the asset

        The request is only signed if
        * The asset in question is able to be used as a host asset
        * The certificate parameters match the certificate authority
        * The CN parameter must be entirely in lower case
        * The CN parameter matches the eth0 mac address of the asset (unless
		  forced_mac is specified, used for build as X installs)
        
        If any previous certificate has been allocated to the asset it is first
        revoked and a new CRL is generated before the new asset certificate is
        issued.
        """
        
        # Check this asset can be used as a host
        if not self.supportsFunction("host"):
            raise ccs_asset_error("Cannot allocate certificate to a " \
                    "non host asset")

        # Check the certificate parameters
        params = getCertificateParameters()
        try:
            req = crypto.load_certificate_request(crypto.FILETYPE_PEM, csr)
            subj = req.get_subject()
            for p in CERT_PARAM_NAMES:
                if p == "CN" or p == "emailAddress":
                    # Don't need to verify these
                    continue
                if getattr(subj, p) != params[p]:
                    raise ccs_asset_error("Certificate Request does not " \
                            "match CA parameter: %s (%s)" % (p, params[p]))
        except ccs_asset_error: raise
        except:
            log_error("Unexpected error validating asset certificate " \
                    "parameters", sys.exc_info())
            raise ccs_asset_error("Could not validate certificate parameters")

        # Check the CN parameter matches the lowercase eth0 mac address
        if not force_mac:
    			mac = self.getMAC()
    			if getattr(subj, "CN") != mac:
    				raise ccs_asset_error("Certificate Request CN parameter " \
    						"does not match asset MAC address!")

        # Checks all pass, grab a CA instance
        try:
            ca = ccs_ca(self._session_id)
        except:
            log_error("Unexpected error initialising CA instance", \
                    sys.exc_info())
            raise ccs_asset_error("Could not obtain CA instance")
        
        # revoke any previous key
        try:
            # Check any certificates with matching CN's are in the revoked 
            # state
            ocerts = ca.findByCN(getattr(subj,"CN"))
            for cert in ocerts:
                if cert["state"] != "R":
                    ca.revoke(cert["serial"], REVOKE_SUPERSEDED, \
                            "new asset certificate requested")
        except:
            log_error("Unexpected error dealing with old asset certificate", \
                    sys.exc_info())
            raise ccs_asset_error("Could not deal with old asset certificate")
        
        # Get the CA and sign the request
        try:
            cert = ca.signReq(csr)
            cobj = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
            serial = cobj.get_serial_number()
            log_info("Certificate %s assigned to asset #%s" % \
                    (serial, self.asset_id))
        except:
            log_error("Unexpected error signing asset certificate", \
                    sys.exc_info())
            raise ccs_asset_error("Could not sign certificate")

        return cert

@registerEvent("assetAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def addAsset(session_id, asset):
    """Adds a new asset to the database"""
    session = getSessionE(session_id)

    # Validate asset parameters
    _validateAsset(session_id, asset)
    
    # Set defaults
    if "serial_no" not in asset:
        asset["serial_no"] = ""
    if "currency" not in asset:
        asset["currency"] = DEFAULT_CURRENCY
    if "price" not in asset:
        asset["price"] = float(0)
    else:
        asset["price"] = float(asset["price"])
    if "supplier" not in asset:
        asset["supplier"] = ""
    if "notes" not in asset:
        asset["notes"] = ""
        
    # Check the appropriate subasset data is present
    res = _validateAssetSubasset(session_id, asset)
    
    # If a changeset is not already active, start one for this batch
    commit = 0
    if session.changeset == 0:
        session.begin("Created Subasset", "add_asset", 1)
        commit = 1
    
    # Insert the primary asset record
    sql = "INSERT INTO asset (asset_type_id, description, serial_no, " \
            "date_purchased, currency, price, supplier, enabled, notes) " \
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    p = (asset["asset_type"], asset["description"], str(asset["serial_no"]), \
            asset["date_purchased"], asset["currency"], asset["price"], 
            asset["supplier"], asset["enabled"], asset["notes"])  
    session.execute(sql, p)

    # Get the new asset_id
    sql = "SELECT currval('asset_asset_id_seq') as asset_id"
    res = session.query(sql, ())
    asset_id = res[0]["asset_id"]
    
    # Create the subassets
    for asset_type_subasset_id,subasset in asset["subassets"].items():
        sql = "INSERT INTO subasset (asset_id, asset_type_subasset_id, " \
                "enabled) VALUES (%s, %s, %s)"
        p = (asset_id, asset_type_subasset_id, subasset["enabled"])
        session.execute(sql, p)
        # Get the new subasset_id
        sql = "SELECT currval('subasset_subasset_id_seq') as subasset_id"
        res = session.query(sql, ())
        subasset_id = res[0]["subasset_id"]
        # Add the property data
        for subasset_property_id,value in subasset["properties"].items():
            sql = "INSERT INTO asset_data (subasset_property_id, " \
                    "subasset_id, value) VALUES (%s, %s, %s)"
            p = (subasset_property_id, subasset_id, str(value))
            session.execute(sql, p)
    
    # Setup add record and initial location
    # XXX: This should probably be functionalised
    sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
            "data1) VALUES (%s, %s, %s, %s)"
    session.execute(sql, (asset_id, ASSET_EVENT_CREATED, \
            session.username, ""))
    
    sql = "SELECT site_id FROM asset_stock_location WHERE default_location='t'"
    default_site = session.getCountOf(sql, ())     
    sql = "INSERT INTO asset_location (asset_id, site_id) VALUES (%s, %s)"
    session.execute(sql, (asset_id, default_site))

    # If we started a changeset, then finish it off
    if commit == 1:
        session.commit()
    
    # Raise the event
    triggerEvent(session_id, "assetAdded", asset_id=asset_id)

    return asset_id
    
@registerEvent("assetAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def addSoekris(session_id, asset):
    """Adds one or more soekris assets to the database
    
    Soekris details should be passed in as a dictionary containing the 
    normal asset details and another dictionary called isoekris with the
    invidual soekris details. The soekris are inserted into the asset database
    in numerical order based on their key in the isoekris dictionary.
    """
    session = getSessionE(session_id)

    # Validate asset parameters
    _validateAsset(session_id, asset)
    
    # Set defaults
    if "currency" not in asset:
        asset["currency"] = DEFAULT_CURRENCY
    if "price" not in asset:
        asset["price"] = float(0)
    else:
        asset["price"] = float(asset["price"])
    if "supplier" not in asset:
        asset["supplier"] = ""
    if "notes" not in asset:
        asset["notes"] = ""
        
    # If a changeset is not already active, start one for this batch
    commit = 0
    if session.changeset == 0:
        session.begin("Creating Soekris Assets", "addSoekris",1)
        commit = 1
        
    sql = "SELECT site_id FROM asset_stock_location WHERE " \
            "default_location='t'"
    default_site = session.getCountOf(sql, ())      

    # Insert each asset, try and keep them in order
    keys = asset["isoekris"].keys()
    keys.sort(key=int)
    n=0
    for idx in keys:
        isoekris = asset["isoekris"][idx]

        # Calculate mac address and serial number details
        if isoekris["serial"] != "":
            isoekris["eth0mac"] = getSoekrisMac(isoekris["serial"], 0);
        elif isoekris["mac"] != "":
            isoekris["serial"] = getSoekrisSerial(isoekris["mac"])
            isoekris["eth0mac"] = isoekris["mac"]
        else:
            # Invalid data, skip this record
            continue
        
        # Calculate a few more macs incase we need them
        isoekris["eth1mac"] = getSoekrisMac(isoekris["serial"], 1);
        isoekris["eth2mac"] = getSoekrisMac(isoekris["serial"], 2);
        isoekris["eth3mac"] = getSoekrisMac(isoekris["serial"], 3);
        
        # Insert the primary asset record
        sql = "INSERT INTO asset (asset_type_id, description, serial_no, " \
                "date_purchased, currency, price, supplier, enabled, notes) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        p = (asset["asset_type"], asset["description"], \
                str(isoekris["serial"]), asset["date_purchased"], \
                asset["currency"], asset["price"], asset["supplier"], \
                asset["enabled"], asset["notes"])  
        session.execute(sql, p)
        
        # Get the new asset_id
        sql = "SELECT currval('asset_asset_id_seq') as asset_id"
        res = session.query(sql, ())
        asset_id = res[0]["asset_id"]
        
        # Create the subassets
        schema = getAssetSchema(session_id, asset["asset_type"])
        for asset_type_subasset_id,subasset in schema.items():
            sql = "INSERT INTO subasset (asset_id, asset_type_subasset_id, " \
                    "enabled) VALUES (%s, %s, 't')"
            p = (asset_id, asset_type_subasset_id)
            session.execute(sql, p)
            # Get the new subasset_id
            sql = "SELECT currval('subasset_subasset_id_seq') as subasset_id"
            res = session.query(sql, ())
            subasset_id = res[0]["subasset_id"]
            # Add the property data
            for subasset_property_id,data in subasset["properties"].items():
                value = ""
                if subasset["name"].startswith("eth") and \
                        data["description"].startswith("MAC"):
                    # If this is a MAC address property, look up the mac
                    # address
                    kname = "%smac" % subasset["name"]
                    if kname in isoekris.keys():
                        value = isoekris[kname]
                if value == "":
                    # If we haven't got a value already use the default
                    value = data["default_value"]
                sql = "INSERT INTO asset_data (subasset_property_id, " \
                        "subasset_id, value) VALUES (%s, %s, %s)"
                p = (subasset_property_id, subasset_id, str(value))
                session.execute(sql, p)
    
        # Setup add record and initial location
        # XXX: This should probably be functionalised
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1) VALUES (%s, %s, %s, %s)"
        session.execute(sql, (asset_id, ASSET_EVENT_CREATED, \
                session.username, ""))
       
        sql = "INSERT INTO asset_location (asset_id, site_id) VALUES (%s, %s)"
        session.execute(sql, (asset_id, default_site))
        
        # Raise the event
        triggerEvent(session_id, "assetAdded", asset_id=asset_id)

        n+=1
        
    # If we started a changeset, then finish it off
    if commit == 1:
        session.commit()

    if n == 0:
        raise ccs_asset_error("No soekris were able to be created!")

    return n

@registerEvent("assetAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def addWirelessCards(session_id, asset):
    """Adds one or more wireless card assets to the database
    
    Card details should be passed in as a dictionary containing the 
    normal asset details and another dictionary called icards with the
    invidual card details. The cards are inserted into the asset database
    in numerical order based on their key in the icards dictionary.
    """
    session = getSessionE(session_id)

    # Validate asset parameters
    _validateAsset(session_id, asset)
    
    # Set defaults
    if "currency" not in asset:
        asset["currency"] = DEFAULT_CURRENCY
    if "price" not in asset:
        asset["price"] = float(0)
    else:
        asset["price"] = float(asset["price"])
    if "supplier" not in asset:
        asset["supplier"] = ""
    if "notes" not in asset:
        asset["notes"] = ""
        
    # If a changeset is not already active, start one for this batch
    commit = 0
    if session.changeset == 0:
        session.begin("Creating Wireless Card Assets", "addWirelessCard", 1)
        commit = 1
        
    sql = "SELECT site_id FROM asset_stock_location WHERE " \
            "default_location='t'"
    default_site = session.getCountOf(sql, ())      

    # Insert each asset, try and keep them in order
    keys = asset["icards"].keys()
    keys.sort(key=int)
    n=0
    for idx in keys:
        icard = asset["icards"][idx]
        
        # Insert the primary asset record
        sql = "INSERT INTO asset (asset_type_id, description, serial_no, " \
                "date_purchased, currency, price, supplier, enabled, notes) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        p = (asset["asset_type"], asset["description"], \
                str(icard["serial"]), asset["date_purchased"], \
                asset["currency"], asset["price"], asset["supplier"], \
                asset["enabled"], asset["notes"])  
        session.execute(sql, p)
        
        # Get the new asset_id
        sql = "SELECT currval('asset_asset_id_seq') as asset_id"
        res = session.query(sql, ())
        asset_id = res[0]["asset_id"]
        
        # Create the subassets
        schema = getAssetSchema(session_id, asset["asset_type"])
        for asset_type_subasset_id,subasset in schema.items():
            sql = "INSERT INTO subasset (asset_id, asset_type_subasset_id, " \
                    "enabled) VALUES (%s, %s, 't')"
            p = (asset_id, asset_type_subasset_id)
            session.execute(sql, p)
            # Get the new subasset_id
            sql = "SELECT currval('subasset_subasset_id_seq') as subasset_id"
            res = session.query(sql, ())
            subasset_id = res[0]["subasset_id"]
            # Add the property data
            for subasset_property_id,data in subasset["properties"].items():
                value = ""
                if subasset["name"].startswith("wireless") and \
                        data["description"].startswith("MAC"):
                    # If this is a MAC address property, look up the mac
                    # address
                    value = icard["mac"]
                if value == "":
                    # If we haven't got a value already use the default
                    value = data["default_value"]
                sql = "INSERT INTO asset_data (subasset_property_id, " \
                        "subasset_id, value) VALUES (%s, %s, %s)"
                p = (subasset_property_id, subasset_id, str(value))
                session.execute(sql, p)
    
        # Setup add record and initial location
        # XXX: This should probably be functionalised
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1) VALUES (%s, %s, %s, %s)"
        session.execute(sql, (asset_id, ASSET_EVENT_CREATED, \
                session.username, ""))
       
        sql = "INSERT INTO asset_location (asset_id, site_id) VALUES (%s, %s)"
        session.execute(sql, (asset_id, default_site))
        
        # Raise the event
        triggerEvent(session_id, "assetAdded", asset_id=asset_id)

        n+=1
        
    # If we started a changeset, then finish it off
    if commit == 1:
        session.commit()

    if n == 0:
        raise ccs_asset_error("No wireless cards were able to be created!")

    return n
    
@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getAssetList(session_id, asset_type_id=-1, site_id=-1):
    """Returns a list of assets"""
    session = getSessionE(session_id)
    
    params = []
    sql = "SELECT a.asset_id, a.description, a.asset_type_id, a.enabled, " \
            "al.site_id, al.attached_to, date_part('epoch', " \
            "al.location_updated) as location_updated, " \
            "COALESCE(s.location, 'Attached to Asset #' || " \
            "al.attached_to) AS location FROM asset a, " \
            "asset_location al LEFT JOIN site s ON " \
            "al.site_id=s.site_id WHERE a.asset_id=al.asset_id"
    if asset_type_id != -1:
        sql = "%s AND a.asset_type_id=%%s" % sql
        params.append(asset_type_id)
    if site_id != -1:
        sql = "%s AND al.site_id=%%s" % sql
        params.append(site_id)
    sql = "%s ORDER BY asset_type_id, asset_id" % sql
    res = session.query(sql, params)
    if len(res) < 1:
        return {}

    return res

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getAssetSchema(session_id, asset_type_id):
    """Returns the schema to be used for assets of this type."""
    session = getSessionE(session_id)
    
    schema = {}
    
    subassets = getLinkedSubassets(session_id, asset_type_id)
    for subasset in subassets:
        asset_type_subasset_id = subasset["asset_type_subasset_id"]
        schema[asset_type_subasset_id] = subasset
        properties = getLinkedProperties(session_id, \
                subasset["subasset_type_id"])
        props = {}
        for prop in properties:
           subasset_property_id = prop["subasset_property_id"]
           props[subasset_property_id] = prop
        schema[asset_type_subasset_id]["properties"] = props

    return schema

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getAssetLocation(session_id, asset_id):
    session = getSessionE(session_id)

    sql = "SELECT asset_id, site_id, attached_to, " \
            "date_part('epoch', location_updated) AS location_updated FROM " \
            "asset_location WHERE asset_id=%s"
    res = session.query(sql, (asset_id))

    if len(res) != 1:
        raise ccs_asset_error("No location information available!")
    
    # Check that we have a site called "Assigned Assets"
    sql = "SELECT site_id FROM site WHERE location='" \
            "Assigned Assets'"
    assigned_site = session.getCountOf(sql, ())

    if res[0]["site_id"] != "":
        if assigned_site > 0 and res[0]["site_id"] == assigned_site:
            sql = "SELECT data1 FROM asset_event WHERE event_type=%s " \
                    "AND asset_id=%s ORDER BY timestamp DESC LIMIT 1"
            thing_name = session.getCountOf(sql, \
                    (ASSET_EVENT_ASSIGNED, asset_id))
            res[0]["description"] = "Assigned to %s" % thing_name
        else:
            res[0]["description"] = getSiteName(session_id, res[0]["site_id"])
    else:
        res[0]["description"] = "Attached to asset #%s" % res[0]["attached_to"]
    
    return res[0]

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getAssetHistory(session_id, asset_id):
    """Retrieves all the history information about this asset"""
    session = getSessionE(session_id)

    sql = "SELECT ae.asset_event_id, ae.asset_id, date_part('epoch', " \
            "ae.timestamp) as timestamp, et.description, ae.username, " \
            "ae.data1, ae.data2, ae.event_type FROM asset_event ae, " \
            "event_type et WHERE ae.event_type=et.event_type_id AND " \
            "ae.asset_id=%s ORDER BY timestamp DESC"
    res = session.query(sql, (asset_id))
    
    # Turn the data fields into something readable
    res2 = []
    for event in res:
        if event["event_type"] == ASSET_EVENT_LOCATION_CHANGED:
            event["event_desc"] = "To '%s'" % (getSiteName(session_id, \
                    event["data1"]))
        elif event["event_type"] == ASSET_EVENT_ATTACHED:
            event["event_desc"] = "To asset #%s" % event["data1"]
        elif event["event_type"] == ASSET_EVENT_ASSIGNED:
            event["event_desc"] = "To %s" % event["data1"]
        elif event["event_type"] == ASSET_EVENT_DETAILS_UPDATED:
            event["event_desc"] = "%s set to '%s'" % \
                    (event["data1"], event["data2"])
        elif event["event_type"] == ASSET_EVENT_PROPERTY_UPDATED:
            parts = event["data1"].split(":")
            subasset_id = parts[0]
            subasset_property_id = parts[1]
            if subasset_property_id == "enabled":
                event["event_desc"] = "%s enabled set to '%s'" % \
                    (getSubassetName(session_id, subasset_id), \
                    event["data2"])
            else:
                event["event_desc"] = "%s %s set to '%s'" % \
                    (getSubassetName(session_id, subasset_id), \
                    _getSubassetPropertyDescription(session_id, \
                    subasset_property_id), event["data2"])
        elif event["event_type"] == ASSET_EVENT_SUBASSET_ADDED:
            event["event_desc"] = getSubassetName(session_id, event["data1"])
        else:
            event["event_desc"] = "&nbsp;"
        res2.append(event)
        
    return res2

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getAssetByMac(session_id, mac):
    """Retrieves all the information about an asset based on a MAC address"""
    session = getSessionE(session_id)

    # Validate MAC address 
    if not isValidMAC(mac):
        raise ccs_asset_error("Invalid MAC address!")
    
    sql = "SELECT asset_id FROM asset_macs WHERE mac=upper(%s)"
    res = session.query(sql, (mac.strip()))
    if len(res) < 1:
        raise ccs_asset_error("Specified MAC address not known!")

    asset_id = res[0]["asset_id"]

    return getAsset(session_id, asset_id)

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getAssetDescription(session_id, asset_id):
    """Retrieves the description of the specified asset"""
    session = getSessionE(session_id)
    
    validateAssetId(session_id, asset_id)
    
    res = session.query("SELECT description FROM asset WHERE asset_id=%s", \
            (asset_id))
    if len(res)<1:
        return ""
    return res[0]["description"]

@exportViaXMLRPC(SESSION_RO, AUTH_AUTHENTICATED)
def getAsset(session_id, asset_id):
    """Retrieves all the information about this asset from the database"""
    session = getSessionE(session_id)

    # Get the basic asset data 
    sql = "SELECT a.*, date_part('epoch', a.date_purchased) AS " \
            "date_purchased_ts, at.description AS " \
            "asset_type_description FROM asset a, " \
            "asset_type at WHERE a.asset_type_id=at.asset_type_id AND " \
            "a.asset_id=%s"
    res = session.query(sql, (asset_id))
    
    if len(res) != 1:
        raise ccs_asset_error("Invalid asset result returned!")
    
    asset = res[0]
    
    # Get some location data
    ldata = getAssetLocation(session_id, asset_id)
    asset["site_id"] = ldata["site_id"]
    asset["attached_to"] = ldata["attached_to"]
    asset["location"] = ldata["description"]
    asset["location_updated"] = ldata["location_updated"]

    # Now get the required subassets (and optional subassets with data)
    sql = "SELECT sat.description, ats.name, ats.required, " \
            "ats.asset_type_subasset_id, sa.subasset_id, sa.enabled " \
            "FROM asset_type_subasset ats " \
            "LEFT JOIN subasset sa ON sa.asset_type_subasset_id=" \
            "ats.asset_type_subasset_id, subasset_type sat WHERE " \
            "ats.subasset_type_id=sat.subasset_type_id AND " \
            "sa.asset_id=%s"
    res = session.query(sql, (asset_id))
    subassets = {}
    subasset_list = ""
    for subasset in res:
        # Get the properties for this subasset
        sql = "SELECT sap.subasset_id, sap.description, sap.required, " \
            "sap.default_value, sap.subasset_property_id, ad.value FROM " \
            "subasset_properties sap LEFT JOIN asset_data ad USING " \
            "(subasset_id, subasset_property_id) WHERE sap.subasset_id=%s"
        res2 = session.query(sql, (subasset["subasset_id"]))
        properties = {}
        proplist = ""
        for data in res2:
            properties[data["subasset_property_id"]] = data
            proplist = "%s %s" % (proplist, data["subasset_property_id"])
        subasset["properties"] = properties
        subasset["property_list"] = proplist
        subassets[subasset["subasset_id"]] = subasset
        subasset_list = "%s %s" % (subasset_list, subasset["subasset_id"])
        
    asset["subassets"] = subassets
    asset["subasset_list"] = subasset_list

    # Other available optional subassets
    sql = "SELECT ats.asset_type_subasset_id, sat.description, ats.name, " \
            "ats.subasset_type_id FROM asset_type_subasset ats, asset a, " \
            "asset_type at, subasset_type sat WHERE " \
            "a.asset_id=%s AND a.asset_type_id=at.asset_type_id AND " \
            "ats.asset_type_id=at.asset_type_id AND ats.subasset_type_id=" \
            "sat.subasset_type_id AND ats.asset_type_subasset_id NOT IN " \
            "(SELECT asset_type_subasset_id FROM subasset WHERE " \
            "asset_id=%s) AND ats.required='f'"
    p = (asset_id, asset_id)
    res = session.query(sql, p)

    subassets = {}
    for subasset in res:
        # Get the properties for this optional subasset
        sql = "SELECT sap.subasset_property_id, sap.asset_property_id, " \
                "sap.required, sap.default_value, sat.description FROM " \
                "subasset_property sap, subasset_type sat WHERE " \
                "sap.subasset_type_id=%s AND " \
                "sap.subasset_type_id=sat.subasset_type_id"
        res2 = session.query(sql, (subasset["subasset_type_id"]))
        properties = {}
        for data in res2:
            properties[data["subasset_property_id"]] = data          
        subasset["properties"] = properties
        subassets[subasset["asset_type_subasset_id"]] = subasset
              
    asset["optionalsubassets"] = subassets

    return asset

def validateAssetId(session_id, asset_id):
    """Checks the specified asset_id is OK"""
    session = getSessionE(session_id)

    res = session.getCountOf("SELECT count(*) FROM asset " \
            "WHERE asset_id=%s", (asset_id))
    if res == 1:
        return

    raise ccs_asset_error("Invalid Asset ID: Not Found")

def _validateAsset(session_id, asset, required=True):
    """Validates the asset parameters"""
    
    # Check the parameters for the main asset
    if "asset_type" in asset:
        res = _isValidAssetType(session_id, asset["asset_type"])
    if "serialno" in asset:
        if len(str(asset["serialno"]))>32:
            raise ccs_asset_error("Serial No. must be less than 32 " \
                    "characters!")
    if ("description" not in asset or len(asset["description"])==0):
        if required:
            raise ccs_asset_error("Description not specified!")
    else:
        if len(asset["description"])>64:
            raise ccs_asset_error("Description must be less than 64 " \
                    "characters!")
    if "date_purchased" not in asset:
        if required:
            raise ccs_asset_error("Date Purchased not specified!")
    else:
        mpat = re.compile("\d{4}-\d{1,2}-\d{1,2}")
        m = mpat.match(asset["date_purchased"])
        if m is None:
            raise ccs_asset_error("Invalid date format!")
    if "currency" in asset:
        if len(asset["currency"])!=3:
            raise ccs_asset_error("Invalid currency parameter!")
    if "price" in asset:
        try:
            v = float(asset["price"])
        except:
            (et, value, tb) = sys.exc_info()
            raise ccs_asset_error("Invalid price value! - %s" % value)
    if "supplier" in asset:
        if len(asset["supplier"]) > 64:
            raise ccs_asset_error("Supplier must be less than 64 characters")
    if "enabled" in asset:
        if asset["enabled"] != "t" and asset["enabled"] != "f":
            raise ccs_asset_error("Invalid enabled value!")

    return

#####################################################################
# Asset Types 
#####################################################################
@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getTypes(session_id):
    """Returns a list of asset types"""
    session = getSessionE(session_id)
    
    sql = "SELECT at.asset_type_id, at.description, " \
            "coalesce(na.no_assets,0) AS no_assets, " \
            "coalesce(nsat.no_subasset_types, 0) AS no_subasset_types, " \
            "coalesce(nh.usage_count, 0) AS host_count " \
            "FROM asset_type at LEFT JOIN  n_subasset_types_by_asset_type " \
            "nsat ON at.asset_type_id=nsat.asset_type_id LEFT JOIN " \
            "n_assets_by_asset_type na ON at.asset_type_id=na.asset_type_id " \
            "LEFT JOIN n_hosts_by_asset_type nh ON " \
            "at.asset_type_id=nh.asset_type_id"
    res = session.query(sql, ())
    return res

def getAssetTypeTemplateVariables(session_id):
    """Returns a list of asset types for use in templates"""
    session = getSessionE(session_id)

    types = {}
    for type in getTypes(session_id):
        type["mangled_description"] = re.sub("[ \.\-]", "_", type["description"])
        if type["host_count"] > 0:
            sql = "SELECT DISTINCT h.host_name FROM host h, asset a, " \
                    "asset_location al, asset_type at WHERE " \
                    "a.asset_id=al.asset_id AND (h.asset_id=a.asset_id OR " \
                    "h.asset_id=al.attached_to) AND " \
                    "a.asset_type_id=at.asset_type_id AND at.asset_type_id=%s"
            res = session.query(sql, (type["asset_type_id"]))
            type["hosts"] = [ t["host_name"] for t in res ]
        else:
            type["hosts"] = []
        types[type["asset_type_id"]] = type
    return types
    
@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getNoSubassetTypes(session_id, asset_type_id):
    """Return the number of subasset types linked to the specified type"""
    session = getSessionE(session_id)

    return session.getCountOf("SELECT count(*) FROM asset_type_subasset " \
            "WHERE asset_type_id=%s", (asset_type_id))

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getNoAssetsOfType(session_id, asset_type_id):
    """Return the number of assets linked to the specified type"""
    session = getSessionE(session_id)

    return session.getCountOf("SELECT count(*) FROM asset " \
            "WHERE asset_type_id=%s", (asset_type_id))
    
@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getAssetType(session_id, asset_type_id):
    """Returns the description of the specified asset type"""
    session = getSessionE(session_id)

    sql = "SELECT * FROM asset_type WHERE asset_type_id=%s"
    res = session.query(sql, (asset_type_id))

    if len(res) != 1:
        return ""

    return res[0]["description"]

@registerEvent("assetTypeAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def addAssetType(session_id, asset_type_id, description):
    """Adds a new asset type to the database. The asset_type_id parameter is
    ignored and is simply present to allow the add/edit functions to have 
    the same prototype.
    """
    session = getSessionE(session_id)
    
    sql = "INSERT INTO asset_type (asset_type_id, description) VALUES " \
            "(DEFAULT, %s)"
    session.execute(sql, (description))

    # Retrieve the allocated ID
    sql = "SELECT currval('asset_type_asset_type_id_seq') as asset_type_id"
    res = session.query(sql, ())
    
    # Raise the event
    triggerEvent(session_id, "assetTypeAdded", \
            asset_type_id=res[0]["asset_type_id"])
    
    return res[0]["asset_type_id"]

@registerEvent("assetTypeModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def editAssetType(session_id, asset_type_id, description):
    """Updates the asset type"""
    session = getSessionE(session_id)

    sql = "UPDATE asset_type SET description=%s WHERE asset_type_id=%s"
    res = session.execute(sql, (description, asset_type_id))
    
    # Raise the event
    triggerEvent(session_id, "assetTypeModified", asset_type_id=asset_type_id)
    
    return asset_type_id

@registerEvent("assetTypeRemoved")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def delAssetType(session_id, asset_type_id):
    """Removes the asset type"""
    session = getSessionE(session_id)
    
    # Raise the event
    triggerEvent(session_id, "assetTypeRemoved", asset_type_id=asset_type_id)

    sql = "DELETE FROM asset_type WHERE asset_type_id=%s"
    session.execute(sql, (asset_type_id))
    
    return 0

def _isValidAssetType(session_id, asset_type_id):
    session = getSessionE(session_id)

    res = session.getCountOf("SELECT count(*) FROM asset_type " \
            "WHERE asset_type_id=%s", (asset_type_id))
    if res == 1:
        return True

    raise ccs_asset_error("Invalid Asset Type ID: Not Found")

#####################################################################
# Subasset Type Functions 
#####################################################################

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getSubassetTypes(session_id):
    """Returns a list of Subasset types"""
    session = getSessionE(session_id)
    
    sql = "SELECT * FROM subasset_type"
    res = session.query(sql, ())

    if len(res) < 1:
        return {}

    # Grab some extra info
    sats= {}
    for at in res:
        satid = at["subasset_type_id"]
        data = {}
        data["subasset_type_id"] = satid
        data["description"] = at["description"]
        data["no_asset_types"] = getNoAssetTypes(session_id, satid)
        data["no_properties"] = getNoProperties(session_id, satid)
        sats["%s" % satid] = data
    
    return sats

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getNoAssetTypes(session_id, subasset_type_id):
    """Return the number of asset types that use the specified subasset type"""
    session = getSessionE(session_id)

    return session.getCountOf("SELECT count(*) FROM asset_type_subasset " \
            "WHERE subasset_type_id=%s", (subasset_type_id))

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getNoProperties(session_id, subasset_type_id):
    """Return the number of properties linked to the specified subasset type"""
    session = getSessionE(session_id)

    return session.getCountOf("SELECT count(*) FROM subasset_property " \
            "WHERE subasset_type_id=%s", (subasset_type_id))
    
@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getNoSubassetsOfType(session_id, subasset_type_id):
    """Return the number of subassets linked to the specified type"""
    session = getSessionE(session_id)

    return session.getCountOf("SELECT count(*) FROM subasset sa, " \
            "asset_type_subasset ats WHERE sa.asset_type_subasset_id=" \
            "ats.asset_type_subasset_id AND ats.subasset_type_id=%s", \
            (subasset_type_id))
    
@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getSubassetType(session_id, subasset_type_id):
    """Returns the description of the specified subasset type"""
    session = getSessionE(session_id)

    sql = "SELECT * FROM subasset_type WHERE subasset_type_id=%s"
    res = session.query(sql, (subasset_type_id))

    if len(res) != 1:
        return ""

    return res[0]["description"]

@registerEvent("subassetTypeAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def addSubassetType(session_id, subasset_type_id, description):
    """Adds a new subasset type to the database. The subasset_type_id 
    parameter is ignored and is simply present to allow the add/edit 
    functions to have the same prototype.
    """
    session = getSessionE(session_id)

    sql = "INSERT INTO subasset_type (subasset_type_id, description) " \
            "VALUES (DEFAULT, %s)"
    session.execute(sql, (description))

    # Retrieve the allocated ID
    sql = "SELECT currval('subasset_type_subasset_type_id_seq') as " \
            "subasset_type_id"
    res = session.query(sql, ())
                
    # Raise the event
    triggerEvent(session_id, "subassetTypeAdded", \
            subasset_type_id=res[0]["subasset_type_id"])
    
    return res[0]["subasset_type_id"]

@registerEvent("subassetTypeModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def editSubassetType(session_id, subasset_type_id, description):
    """Updates the subasset type"""
    session = getSessionE(session_id)
    
    sql = "UPDATE subasset_type SET description=%s WHERE subasset_type_id=%s"
    session.execute(sql, (description, subasset_type_id))
    
    # Raise the event
    triggerEvent(session_id, "subassetTypeModified", \
            subasset_type_id=subasset_type_id)
    
    return subasset_type_id

@registerEvent("subassetTypeRemoved")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def delSubassetType(session_id, subasset_type_id):
    """Removes the subasset type"""
    session = getSessionE(session_id)
    
    # Raise the event
    triggerEvent(session_id, "subassetTypeRemoved", \
            subasset_type_id=subasset_type_id)

    sql = "DELETE FROM subasset_type WHERE subasset_type_id=%s"
    res = session.execute(sql, (subasset_type_id))
    
    return 0

def _isValidSubassetType(session_id, subasset_type_id):
    session = getSessionE(session_id)

    res = session.getCountOf("SELECT count(*) FROM subasset_type " \
            "WHERE subasset_type_id=%s", (subasset_type_id))
    if res == 1:
        return

    raise ccs_asset_error("Invalid Subasset Type ID: Not Found")

#####################################################################
# Asset / Subasset Type Relationship 
#####################################################################

@registerEvent("subassetLinkAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def addSubassetLink(session_id, asset_type_id, subasset_type_id, name, required):
    """Adds a subasset type to the specified asset type"""
    session = getSessionE(session_id)

    # Validate parameters
    _isValidAssetType(session_id, asset_type_id)
    _isValidSubassetType(session_id, subasset_type_id)
    if int(required) != 1 and int(required) !=0:
        return ccs_asset_error("Required must be 1 or 0!")
    if getNoAssetsOfType(session_id, asset_type_id)>0 and int(required)==1:
        return ccs_asset_error("Cannot add required " \
                "subasset types to an asset type with child assets!")
    
    if int(required) == 1:
        reqstr = "t"
    else:
        reqstr = "f"
    
    sql = "INSERT INTO asset_type_subasset (asset_type_id, " \
            "subasset_type_id, name, required) VALUES (%s, %s, %s, %s)"
    session.execute(sql, (asset_type_id, subasset_type_id, name, reqstr))
    
    # Retrieve the allocated ID
    sql = "SELECT currval('asset_type_subasset_asset_type_subasset_id_seq') " \
            "as asset_type_subasset_id"
    res = session.query(sql, ())
                
    # Raise the event
    triggerEvent(session_id, "subassetLinkAdded", \
            asset_type_subasset_id=res[0]["asset_type_subasset_id"])
    
    return res[0]["asset_type_subasset_id"]

@registerEvent("subassetLinkRemoved")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def removeSubassetLink(session_id, asset_type_subasset_id):
    """Removes a subasset type from the specified asset type"""
    session = getSessionE(session_id)
    
    # Raise the event
    triggerEvent(session_id, "subassetLinkRemoved", \
            asset_type_subasset_id=asset_type_subasset_id)

    sql = "DELETE FROM asset_type_subasset WHERE asset_type_subasset_id=%s"
    session.execute(sql, (asset_type_subasset_id))
    
    return asset_type_subasset_id

@registerEvent("subassetLinkModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def updateSubassetLink(session_id, asset_type_subasset_id, required):
    """Update  a subasset type from the specified asset type"""
    session = getSessionE(session_id)

    if int(required) != 1 and int(required) !=0:
        return ccs_asset_error("Required must be 1 or 0!")

    # Check for linked assets
    if int(required)==1:
        sql = "SELECT asset_type_id FROM asset_type_subasset WHERE " \
                "asset_type_subasset_id=%s"
        res = session.query(sql, (asset_type_subasset_id))
        asset_type_id = res[0]["asset_type_id"]
        if getNoAssetsOfType(session_id, asset_type_id)>0:
            return ccs_asset_error("Cannot make subasset type required on " \
                    "an asset type with child assets!")
    
    # Update the status
    if int(required) == 1:
        reqstr = "t"
    else:
        reqstr = "f"
    sql = "UPDATE asset_type_subasset SET required=%s WHERE " \
            "asset_type_subasset_id=%s"
    session.execute(sql, (reqstr, asset_type_subasset_id))
    
    # Raise the event
    triggerEvent(session_id, "subassetLinkModified", \
            asset_type_subasset_id=asset_type_subasset_id)
    
    return asset_type_subasset_id

@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def getLinkedSubassets(session_id, asset_type_id):
    """Returns a list of subasset types that are linked to this asset type"""
    session = getSessionE(session_id)
    
    sql = "SELECT ats.asset_type_subasset_id, sat.subasset_type_id, " \
            "sat.description, ats.name, ats.required FROM subasset_type " \
            "sat, asset_type_subasset ats WHERE " \
            "sat.subasset_type_id=ats.subasset_type_id AND " \
            "ats.asset_type_id=%s ORDER BY name"
    res = session.query(sql, (asset_type_id))

    return res

def _validateAssetSubasset(session_id, asset):
    """Checks that the required subassets / properties are present"""

    # Get the schema
    schema = getAssetSchema(session_id, asset["asset_type"])

    # Check for invalid subasset types
    for asset_type_subasset_id,subasset in asset["subassets"].items():
        if int(asset_type_subasset_id) not in schema.keys():
            raise ccs_asset_error("Invalid subasset (%s) not in schema!" % \
                    asset_type_subasset_id)
        # Check subasset parameters
        if "enabled" in subasset:
            if subasset["enabled"] != "t" and subasset["enabled"] != "f":
                raise ccs_asset_error("Invalid enabled status for " \
                        "subasset (%s)" % asset_type_subasset_id)
        # Check the properties of this subasset
        _validateSubassetProperties(subasset["properties"], \
                schema[int(asset_type_subasset_id)])

    # Check required subassets are present
    for asset_type_subasset_id,subasset in schema.items():
        if subasset["required"] != "t":
            continue
        if str(asset_type_subasset_id) not in asset["subassets"].keys():
            raise ccs_asset_error("Required subasset (%s - %s) not " \
                    "present!" % (subasset["description"], subasset["name"]))

    return
    
def _isValidAssetTypeSubassetId(session_id, asset_type_subasset_id):
    """Checks the specified asset_type_subasset_id is OK"""
    session = getSessionE(session_id)

    res = session.getCountOf("SELECT count(*) FROM asset_type_subasset " \
            "WHERE asset_type_subasset_id=%s", (asset_type_subasset_id))
    if res == 1:
        return

    raise ccs_asset_error("Invalid Asset Type Subasset ID: Not Found")

#####################################################################
# Asset Properties
#####################################################################

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getProperties(session_id):
    """Returns a list of asset properties"""
    session = getSessionE(session_id)
    
    sql = "SELECT * FROM asset_property"
    res = session.query(sql, ())

    if len(res) < 1:
        return {}

    # Grab some extra info
    aps = {}
    for ap in res:
        apid = ap["asset_property_id"]
        data = {}
        data["asset_property_id"] = apid
        data["description"] = ap["description"]
        data["no_subasset_properties"] = getNoSubassetProperties(session_id, \
                apid)
        aps["%s" % apid] = data
    
    return aps

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getNoSubassetProperties(session_id, asset_property_id):
    """Return the number of subasset types that use this property"""
    session = getSessionE(session_id)

    return session.getCountOf("SELECT count(*) FROM subasset_property " \
            "WHERE asset_property_id=%s", (asset_property_id))

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getAssetProperty(session_id, asset_property_id):
    """Returns the description of the specified asset property"""
    session = getSessionE(session_id)

    sql = "SELECT * FROM asset_property WHERE asset_property_id=%s"
    res = session.query(sql, (asset_property_id))

    if len(res) != 1:
        return ""

    return res[0]["description"]

@registerEvent("assetPropertyAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def addAssetProperty(session_id, asset_property_id, description):
    """Adds a new asset property to the database. The asset_property_id 
    parameter is ignored and is simply present to allow the add/edit 
    functions to have the same prototype.
    """
    session = getSessionE(session_id)

    sql = "INSERT INTO asset_property (asset_property_id, description) " \
            "VALUES (DEFAULT, %s)"
    session.execute(sql, (description))

    # Retrieve the allocated ID
    sql = "SELECT currval('asset_property_asset_property_id_seq') as " \
            "asset_property_id"
    res = session.query(sql, ())
                
    # Raise the event
    triggerEvent(session_id, "assetPropertyAdded", \
            asset_property_id=res[0]["asset_property_id"])
    
    return asset_property_id

@registerEvent("assetPropertyModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def editAssetProperty(session_id, asset_property_id, description):
    """Updates the asset property"""
    session = getSessionE(session_id)
    
    sql = "UPDATE asset_property SET description=%s WHERE asset_property_id=%s"
    session.execute(sql, (description, asset_property_id))
    
    # Raise the event
    triggerEvent(session_id, "assetPropertyModified", \
            asset_property_id=asset_property_id)
    
    return asset_property_id

@registerEvent("assetPropertyRemoved")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def delAssetProperty(session_id, asset_property_id):
    """Removes the asset property"""
    session = getSessionE(session_id)
    
    # Raise the event
    triggerEvent(session_id, "assetPropertyRemoved", \
            asset_property_id=asset_property_id)

    sql = "DELETE FROM asset_property WHERE asset_property_id=%s"
    session.execute(sql, (asset_property_id))
    
    return 0

def _isValidAssetProperty(session_id, asset_property_id):
    session = getSessionE(session_id)
    
    res = session.getCountOf("SELECT count(*) FROM asset_property " \
            "WHERE asset_property_id=%s", (asset_property_id))
    if res == 1:
        return ""

    raise ccs_asset_error("Invalid Asset Type ID: Not Found")

def _validateSubassetProperties(properties, schema):
    
    # Check for invalid properties
    for subasset_property_id,value in properties.items():
        if int(subasset_property_id) not in schema["properties"].keys():
            raise ccs_asset_error("Invalid property (%s) not in schema!" % \
                    subasset_property_id)
        if len(str(value)) > 64:
            raise ccs_asset_error("Property value must be less than 64 " \
                    "characters!")
        
    # Check the required properties are present
    for subasset_property_id,prop in schema["properties"].items():
        if prop["required"] != "t":
            continue
        if str(subasset_property_id) not in properties.keys():
            raise ccs_asset_error("Required property (%s) not present!" % \
                    (prop["description"]))
    
    return

def _isSubassetPropertyRequired(session_id, subasset_property_id):
    """Checks if the specified subasset_property is required"""
    session = getSessionE(session_id)

    return session.getCountOf("SELECT count(*) FROM subasset_property " \
            "WHERE subasset_property_id=%s AND required='t'", \
            (subasset_property_id))

#####################################################################
# Asset Property / Subasset Links
#####################################################################

@registerEvent("subassetPropertyAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def addSubassetProperty(session_id, subasset_type_id, asset_property_id, \
        default_value, required):
    """Adds a property to the specified subasset type"""
    session = getSessionE(session_id)

    # Validate parameters
    required = int(required)
    _isValidSubassetType(session_id, subasset_type_id)
    _isValidAssetProperty(session_id, asset_property_id)
    if required != 1 and required !=0:
        raise ccs_asset_error("Required must be 1 or 0!")
    if getNoSubassetsOfType(session_id, subasset_type_id)>0 and required:
        raise ccs_asset_error("Cannot add required property to a " \
                "subasset type with child assets!")
    
    if required:
        reqstr = "t"
    else:
        reqstr = "f"
    
    sql = "INSERT INTO subasset_property (subasset_type_id, " \
            "asset_property_id, default_value, required) " \
            "VALUES (%s, %s, %s, %s)"
    session.execute( sql, (subasset_type_id, asset_property_id, \
            default_value, reqstr))
    
    # Retrieve the allocated ID
    sql = "SELECT currval('subasset_property_subasset_property_id_seq') " \
            "as subasset_property_id"
    res = session.query(sql, ())
                
    # Raise the event
    triggerEvent(session_id, "subassetPropertyAdded", \
            subasset_property_id=res[0]["subasset_property_id"])
    
    return res[0]["subasset_property_id"]

@registerEvent("subassetPropertyModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def updateSubassetProperty(session_id, subasset_property_id, default_value, \
        required):
    """Update a subasset properties details"""
    session = getSessionE(session_id)

    if int(required) != 1 and int(required) !=0:
        raise ccs_asset_error("Required must be 1 or 0!")
    if subasset_property_id == "":
        raise ccs_asset_error("Missing subasset property id!")

    # Check for linked subassets
    if int(required)==1:
        sql = "SELECT subasset_type_id FROM subasset_property WHERE " \
                "subasset_property_id=%s"
        res = session.query(sql, (subasset_property_id))
        subasset_type_id = res[0]["subasset_type_id"]
        if getNoSubassetsOfType(session_id, subasset_type_id)>0:
            raise ccs_asset_error("Cannot make property required on an " \
                    "subasset type with child assets!")
    
    # Update the status
    if int(required) == 1:
        reqstr = "t"
    else:
        reqstr = "f"
    sql = "UPDATE subasset_property SET required=%s, default_value=%s WHERE " \
            "subasset_property_id=%s"
    session.execute(sql, (reqstr, default_value, subasset_property_id))
    
    # Raise the event
    triggerEvent(session_id, "subassetPropertyModified", \
            subasset_property_id=subasset_property_id)
    
    return subasset_property_id

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getNoDataOfSubassetProperty(session_id, subasset_property_id):
    """Return the number of peices of data for this property in the database"""
    session = getSessionE(session_id)

    return session.getCountOf("SELECT * FROM asset_data ad, " \
            "subasset_property sp WHERE ad.subasset_property_id=" \
            "sp.subasset_property_id AND sp.subasset_property_id=%s", \
            (subasset_property_id))
    
@registerEvent("subassetPropertyRemoved")
@exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER)
def removeSubassetProperty(session_id, subasset_property_id):
    """Removes a property from the specified subasset type"""
    session = getSessionE(session_id)

    if getNoDataOfSubassetProperty(session_id, subasset_property_id)>0:
        raise ccs_asset_error("Cannot remove subasset property which has " \
                "asset data attached!")
        
    # Raise the event
    triggerEvent(session_id, "subassetPropertyRemoved", \
            subasset_property_id=subasset_property_id)
            
    sql = "DELETE FROM subasset_property WHERE subasset_property_id=%s"
    session.execute(sql, (subasset_property_id))
    
    return 0

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getLinkedProperties(session_id, subasset_type_id):
    """Returns a list of properties that are linked to this subasset type"""
    session = getSessionE(session_id)

    if subasset_type_id == "":
        raise ccs_asset_error("Missing subasset type id!")
    
    sql = "SELECT sap.subasset_property_id, sap.subasset_type_id, " \
            "sap.asset_property_id, sap.required, sap.default_value, " \
            "ap.description FROM subasset_property sap, asset_property ap " \
            "WHERE sap.asset_property_id=ap.asset_property_id AND " \
            "sap.subasset_type_id=%s ORDER BY ap.description"
    res = session.query(sql, (subasset_type_id))

    return res

def _isValidSubassetPropertyId(session_id, subasset_property_id):
    """Checks the specified subasset_property_id is OK"""
    session = getSessionE(session_id)

    res = session.getCountOf("SELECT count(*) FROM subasset_property " \
            "WHERE subasset_property_id=%s", (subasset_property_id))
    if res == 1:
        return

    raise ccs_asset_error("Invalid Subasset Property ID: Not Found")


#####################################################################
# Subassets 
#####################################################################
class ccs_subasset(ccs_class):
    """Provides an abstract interface to a subasset in the CRCnet Configuration
    System.
    
    The members of this class loosely map to the fields of the subasset table
    in the database.
    """
    
    def __init__(self, session_id, subasset_id):
        """Initialises a new class for a specified subasset.

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
            raise ccs_asset_error("Invalid session id")
        self._session_id = session_id
        
        # See if the specified subasset id makes sense
        sql = "SELECT * FROM subasset WHERE subasset_id=%s"
        res = session.query(sql, (subasset_id))
        if len(res) < 1:
            # DB Query failed
            raise ccs_asset_error("Invalid subasset. Unable to retrieve " 
                "details")
        
        # Store details 
        self.subasset_id = subasset_id
        self._properties = res[0]


    def moveToSite(self, site_id):
        """Updates the subasset's location to the specified site"""
        session = getSessionE(self._session_id)
        
        asset = ccs_asset(session.session_id, self["asset_id"])
        return asset.moveToSite(site_id)
    
    def attachTo(self, asset_id):
        """Attaches this subasset to the specified asset"""
        session = getSessionE(self._session_id)
        
        # No-op if someone tries to attach us to ourself...
        if self["asset_id"] == asset_id:
            return True

        asset = ccs_asset(session.session_id, self["asset_id"])
        return asset.attachTo(asset_id)
        
    def moveToStock(self):
        """Updates the subasset's location to the default stock site"""
        session = getSessionE(self._session_id) 
        
        asset = ccs_asset(session.session_id, self["asset_id"])
        return asset.moveToStock()
   
    def supportsFunction(self, function):
        """Returns true if this subasset supports the specified function"""
        session = getSessionE(self._session_id)
        
        return session.getCountOf("SELECT count(*) FROM subasset sa, " \
            "asset_type_subasset ats, subasset_type_map stm WHERE " \
            "sa.asset_type_subasset_id=ats.asset_type_subasset_id AND " \
            "ats.subasset_type_id=stm.subasset_type_id AND " \
            "stm.asset_function=%s AND sa.subasset_id=%s", \
            (function, self.subasset_id))

    @exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER, True)
    def getSubassetFunctions(self):
        session = getSessionE(self._session_id)
        
        funcs = []
        res = session.query("SELECT stm.asset_function FROM " \
                "subasset_type_map stm, asset_type_subasset ats, " \
                "subasset s WHERE stm.subasset_type_id=" \
                "ats.subasset_type_id AND ats.asset_type_subasset_id=" \
                "s.asset_type_subasset_id AND s.subasset_id=%s", \
                (self.subasset_id))
        for row in res:
            funcs.append(row["asset_function"])
        return funcs

    def attachedToHost(self, host_id):
        """Returns true if this subasset is attached to the specified host"""
        session = getSessionE(self._session_id)
    
        return session.getCountOf("SELECT * FROM interface_subassets isa, " \
                "asset_location al, host h WHERE isa.subasset_id=%s AND " \
                "isa.asset_id=al.asset_id AND al.attached_to=h.asset_id", \
                self.subasset_id)
        
    def availableForInterface(self, host_id):
        """Returns true if this asset can be an interface on the specified host
        """
        session = getSessionE(self._session_id)
        
        if self.attachedToHost(host_id):
            return True
 
        return session.getCountOf("SELECT COUNT(*) FROM  asset_location " \
                "al, interface_subassets isa LEFT JOIN host h ON " \
                "isa.asset_id=h.asset_id WHERE isa.asset_id=al.asset_id AND " \
                "((al.site_id IN (SELECT site_id FROM asset_stock_location) " \
                "OR al.site_id IN (SELECT site_id FROM host WHERE host_id=%s) " \
                ")OR h.host_id=%s) AND subasset_id=%s", \
                (host_id, host_id, self.subasset_id))

    @registerEvent("subassetStateChanged")
    @exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER, True)
    def updateSubassetEnabled(self, value):
        """Updates the enabled status of the subasset"""
        session = getSessionE(self._session_id)
        
        # Validate
        if value != "t" and value != "f":
            raise ccs_asset_error("Enabled must be t or f!")
        
        # If a changeset is not already active, start one for this batch
        self._forceChangeset("Updated status of subasset #%s" % \
                self.subasset_id, "subasset")
        
        asset_id = self._properties["asset_id"]

        # Do the update
        sql = "UPDATE subasset SET enabled=%s WHERE subasset_id=%s"
        res = session.execute(sql, (value, self.subasset_id))
            
        # Record the change
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1, data2) VALUES (%%s, %%s, %%s, '%s:enabled', %%s)" % \
                (self.subasset_id)
        p = (asset_id, ASSET_EVENT_PROPERTY_UPDATED, session.username, value)
        res = session.execute(sql, p)
        
        # Raise the event
        triggerEvent(session_id, "subassetStateChanged", \
                subasset_id=self.subasset_id)
                    
        return self.returnSuccess()
    
    @registerEvent("subassetPropertyUpdated")
    @exportViaXMLRPC(SESSION_RW, AUTH_ASSET_MANAGER, True)
    def updateSubassetPropertyData(self, subasset_property_id, value):
        """Updates an asset property in the database"""
        session = getSessionE(self._session_id)
        
        # Validate id
        _isValidSubassetPropertyId(self._session_id, subasset_property_id)
        # Validate data
        if len(value) > 64:
            raise ccs_asset_error("Property value must be less than 64 " \
                    "characters!")
        if _isSubassetPropertyRequired(self._session_id, \
                subasset_property_id) and len(value)==0:
            raise ccs_asset_error("Cannot set blank value on required " \
                    "property")
        
        # If a changeset is not already active, start one for this batch
        self._forceChangeset("Updated property of subasset #%s" % \
                self.subasset_id, "subasset")
            
        asset_id = self._properties["asset_id"]
        
        # Check if the data exists currently
        res = session.getCountOf("SELECT count(*) FROM asset_data " \
                "WHERE subasset_id=%s AND subasset_property_id=%s", \
                (self.subasset_id, subasset_property_id))
        if res == 1:
            # Do the update
            sql = "UPDATE asset_data SET value=%s WHERE subasset_id=%s AND " \
                    "subasset_property_id=%s"
            session.execute(sql, (value, self.subasset_id, \
                    subasset_property_id))
        else:
            # Do the insert
            sql = "INSERT INTO asset_data (subasset_id, subasset_property_id, " \
                    "value) VALUES (%s, %s, %s)"
            session.execute(sql, (self.subasset_id, subasset_property_id, \
                    value))
            
        # Record the change
        sql = "INSERT INTO asset_event (asset_id, event_type, username, " \
                "data1, data2) VALUES (%%s, %%s, %%s, '%s:%s', %%s)" % \
                (self.subasset_id, subasset_property_id)
        p = (asset_id, ASSET_EVENT_PROPERTY_UPDATED, session.username, value)
        session.execute(sql, p)
        
        # Raise the event
        triggerEvent(self._session_id, "subassetPropertyUpdated", \
                subasset_id=self.subasset_id, \
                subasset_property_id=subasset_property_id)
                    
        return self.returnSuccess()
    
    def getTemplateVariables(self):
        
        asset = ccs_asset(self._session_id, self["asset_id"])
        return asset.getTemplateVariables()

@exportViaXMLRPC(SESSION_RO, AUTH_ASSET_MANAGER)
def getSubassetName(session_id, subasset_id):
    """Returns the name of the specified subasset"""
    session = getSessionE(session_id)

    sql = "SELECT ats.name FROM subasset sa, asset_type_subasset ats WHERE " \
            "sa.asset_type_subasset_id=ats.asset_type_subasset_id AND " \
            "sa.subasset_id=%s"
    res = session.query(sql, (subasset_id))
    if len(res)!=1:
        raise ccs_asset_error("Invalid result returned in getSubassetName")
    
    return res[0]["name"]

def _getSubassetPropertyDescription(session_id, subasset_property_id):
    """Returns the description of the specified subasset property"""
    session = getSessionE(session_id)

    sql = "SELECT ap.description FROM subasset_property sap, " \
            "asset_property ap WHERE sap.asset_property_id=" \
            "ap.asset_property_id AND sap.subasset_property_id=%s"
    res = session.query(sql, (subasset_property_id))
    if len(res)!=1:
       raise ccs_asset_error("Invalid result returned in " \
               "getSubassetPropertyDescription")
    
    return res[0]["description"]

def _isValidSubasset(session_id, subasset_id):
    """Checks the specified subasset_id is OK"""
    session = getSessionE(session_id)

    res = session.getCountOf("SELECT count(*) FROM subasset " \
            "WHERE subasset_id=%s", (subasset_id))
    if res == 1:
        return

    raise ccs_asset_error("Invalid Subsset ID: Not Found")

#####################################################################
# Webserver Portion to resolve MAC addresses to Asset details
#####################################################################
class ccs_maclookup(resource.Resource):
    """Implements a simple MAC lookup resource

    Called when the main server receives a query for /maclookup/*
    """

    # Name for the resource
    resourceName = "MAC Lookup Server"
    
    # Mark as leaf so that render gets called
    isLeaf = 1
        
    def render(self, request):
        session = getSession(ADMIN_SESSION_ID)
        
        mac = os.path.basename(request.path)
        
        # Verify MAC address format
        if not isValidMAC(mac):
            request.setResponseCode(400, "Invalid MAC address format!")
            request.finish
            return server.NOT_DONE_YET
        
        log_debug("Received maclookup request for %s" % mac)

        # Lookup mac
        sql = "SELECT h.host_name, h.ip_address, a.asset_id, am.mac FROM " \
                "asset_macs am, asset a LEFT JOIN host h ON a.asset_id=" \
                "h.asset_id WHERE am.asset_id=a.asset_id AND upper(am.mac)" \
                "=upper(%s)"
        try:
            res = session.query(sql, (mac.strip()))
        except:
            (type, value, tb) = sys.exc_info()
            request.setResponseCode(500, "Database query failed - %s" % \
                    value)
            request.finish()
            return server.NOT_DONE_YET
        
        if len(res)!=1:
            request.setResponseCode(404, "Specified MAC address not found!")
            request.finish()
            return server.NOT_DONE_YET
        
        host_name = res[0]["host_name"]
        ip_address = res[0]["ip_address"]
        
        # Check if this asset is attached to another asset that is a host
        if host_name == "":
            sql = "SELECT h.host_name, h.ip_address FROM asset_location al " \
                    "LEFT JOIN host h ON al.attached_to=h.asset_id WHERE " \
                    "al.asset_id=%s AND al.attached_to IS NOT NULL"
            try:
                res2 = session.query(sql, res[0]["asset_id"])
            except:
                (type, value, tb) = sys.exc_info()
                request.setResponseCode(500, "Database query failed - %s" % \
                        value)
                request.finish()
                return server.NOT_DONE_YET
            
            if len(res2)==1:
                host_name = res2[0]["host_name"]
                ip_address = res2[0]["ip_address"]
            
        # Write out info about the host
        rs = "FOUND=1\nASSET_ID=%s\nHOST_NAME=%s\nHOST_IP=%s\nMAC=%s\n" % \
                (res[0]["asset_id"], host_name, ip_address, res[0]["mac"])
        return rs
    
def ccs_init():
    # Register MAC Address Handler
    registerResource("maclookup", ccs_maclookup)
