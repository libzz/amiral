# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# RuralLink Module - Provides support for installing and maintaining RuralLink
#                    farm CPEs
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# No usage or redistribution rights are granted for this file unless
# otherwise confirmed in writing by the copyright holder.
import time
from md5 import md5

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC, registerResource
from crcnetd._utils.ccsd_service import ccsd_service, ccs_service_error, \
        registerService
        
from ccs_asset import getAssetByMac, ccs_asset_error, addAsset, \
        getLinkedSubassets, getLinkedProperties, getAsset, ccs_asset, \
        getAssetLocation

ccs_mod_type = CCSD_SERVER

class ccs_rurallink_error(ccsd_error):
    pass

TYPE_SOEKRIS = 0
TYPE_WRAP = 1

AUTH_RURALLINK = "Rural Link"

RURALLINK_SERIAL_DESCRIPTION = "Rurallink Serial No"
ROOTPASS_PROPERTY = "rl_root_pw"

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

# Partition the serial number space in half, bottom=soekris, top=wrap
SOEKRIS_MAXSERIAL = int((2**SERIAL_BITS)/2)

# Keep track of rurallink devices as they phone home
devices = {}

##############################################################################
# Asset / Serial Number Support
##############################################################################
def allocateRurallinkSerial(session_id, type):
    """Allocates a new serial no. for the rurallink device"""

    # Retrieve the next available serial number
    if type == TYPE_SOEKRIS:
        sql = "SELECT nextval('rurallink_soekris_serial') AS serialno"
    else:
        sql = "SELECT nextval('rurallink_wrap_serial') AS serialno"

    session = getSessionE(session_id)
    res = session.query(sql, ())
    if res[0]["serialno"] == "":
        raise ccs_rurallink_error("No RuralLink serial numbers available!")
    else:
        current = int(res[0]["serialno"])

    return current

def getRurallinkAssetType(session_id, type):
    """Returns the asset_type_id that a new rurallink asset should be given"""
    session = getSessionE(session_id)
    
    sql = "SELECT asset_type_id FROM asset_type WHERE description LIKE "
    if type == TYPE_SOEKRIS:
        sql += "'%%net4526%%'"
    else:
        sql += "'%%WRAP%%'"
    return session.getCountOf(sql, ())

def getRurallinkWirelessType(session_id, mac):
    """Returns the asset_type_id that a new wireless card should be given"""
    session = getSessionE(session_id)
    
    sql = "SELECT asset_type_id FROM asset_type WHERE description LIKE '" \
            "%%miniPCI Card%%' LIMIT 1"
    return session.getCountOf(sql, ())
    
def addRurallinkWirelessAsset(session_id, mac):
    """Creates a new RuralLink wireless card asset"""
    
    setmac = False
    
    asset = {}
    asset["asset_type"] = getRurallinkWirelessType(session_id, mac)
    asset["description"] = "miniPCI 802.11abg card"
    asset["date_purchased"] = time.strftime("%Y-%m-%d")
    asset["enabled"] = "t"
    asset["subassets"] = {}
    
    # Now setup the subassets
    for subasset in getLinkedSubassets(session_id, asset["asset_type"]):
        sadata = {}
        # Skip optional subassets
        if not subasset["required"]:
            continue
        sadata["enabled"] = "t"
        sadata["properties"] = {}
        for prop in getLinkedProperties(session_id, \
                subasset["subasset_type_id"]):
            # Look for eth0 mac to set
            if subasset["name"] == "wireless" and \
                    prop["description"] == "MAC Address":
                val = mac
                setmac = True
            else:
                # Skip optional properties
                if not prop["required"]:
                    continue
                val = prop["default_value"]
            sadata["properties"][prop["subasset_property_id"]] = val
        asset["subassets"][subasset["asset_type_subasset_id"]] = sadata
        
    # Check the MAC addres and Serial properties were set
    if not setmac:
        raise ccs_rurallink_error("Unable to create wireless asset. Asset " \
                "type %d lacks necessary properties!" % (asset["asset_type"]))
    
    # Add the asset and return the newly created object
    asset_id = addAsset(session_id, asset)
    return getAsset(session_id, asset_id)

def addRurallinkAsset(session_id, eth0mac):
    """Creates a new RuralLink asset"""
    
    setmac = False
    setserial = False
    
    try:
        serial = getSoekrisSerial(eth0mac)
        type = TYPE_SOEKRIS
    except:
        type = TYPE_WRAP
    
    asset = {}
    asset["asset_type"] = getRurallinkAssetType(session_id, type)
    if type == TYPE_SOEKRIS:
        asset["serial_no"] = serial
    asset["description"] = "RuralLink Farm Device"
    asset["date_purchased"] = time.strftime("%Y-%m-%d")
    asset["enabled"] = "t"
    asset["subassets"] = {}
    
    # Now setup the subassets
    for subasset in getLinkedSubassets(session_id, asset["asset_type"]):
        sadata = {}
        # Skip optional subassets
        if not subasset["required"]:
            continue
        sadata["enabled"] = "t"
        sadata["properties"] = {}
        for prop in getLinkedProperties(session_id, \
                subasset["subasset_type_id"]):
            # Look for eth0 mac to set
            if subasset["name"] == "eth0" and \
                    prop["description"] == "MAC Address":
                val = eth0mac
                setmac = True
            elif prop["description"] == RURALLINK_SERIAL_DESCRIPTION:
                val = allocateRurallinkSerial(session_id, type)
                setserial = True
            else:
                # Skip optional properties
                if not prop["required"]:
                    continue
                val = prop["default_value"]
            sadata["properties"][prop["subasset_property_id"]] = val
        asset["subassets"][subasset["asset_type_subasset_id"]] = sadata
        
    # Check the MAC addres and Serial properties were set
    if not setmac or not setserial:
        raise ccs_rurallink_error("Unable to create device asset. Asset " \
                "type %d lacks necessary properties! (%s, %s)" % \
                (asset["asset_type"], setmac, setserial))
    
    # Add the asset and return the newly created object
    asset_id = addAsset(session_id, asset)
    return getAsset(session_id, asset_id)

@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def registerRurallinkDevice(session_id, eth0mac):
    """Called by pxe-scripts to register a new rurallink device"""
    
    # Validate MAC address 
    if not isValidMAC(eth0mac):
        raise ccs_asset_error("Invalid MAC address!")

    try:
        asset = getAssetByMac(session_id, eth0mac)
    except ccs_asset_error:
        # Asset does not exist
        asset = addRurallinkAsset(session_id, eth0mac)

    # Return the asset
    return asset

@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def registerRurallinkWirelessCard(session_id, host_asset_id, mac):
    """Called by pxe-scripts to register a new wireless card
    
    The card is also attached to the device that is used to PXE boot it
    """
    
    # Validate MAC address 
    if not isValidMAC(mac):
        raise ccs_asset_error("Invalid MAC address!")
    
    try:
        asset = getAssetByMac(session_id, mac)
    except ccs_asset_error:
        # Asset does not exist
        asset = addRurallinkWirelessAsset(session_id, mac)

    # Check current location
    location = getAssetLocation(session_id, asset["asset_id"])
    if location["attached_to"] == host_asset_id:
        # Up to date
        return asset
    
    # Get an asset object and attach it to the host asset
    assetobj = ccs_asset(session_id, asset["asset_id"])
    assetobj.attachTo(host_asset_id)
    
    # Return the asset
    return asset

@exportViaXMLRPC(SESSION_RW, AUTH_AUTHENTICATED)
def setRurallinkDeviceConfig(session_id, asset_id, type):
    """Updates the device asset record to reflect the configuration type"""
    session = getSessionE(session_id)

    if asset_id == -1:
        # Called by a device itself, use the CN of the certificate to 
        # lookup the mac address and find an asset ID
        mac = ":".join([session.username[(i*2)-2:i*2] for i in range(1,7)])
        if not isValidMAC(mac):
            raise ccs_rurallink_error("Asset not specified!")
        asset = getAssetByMac(session_id, mac) 
        asset_id = asset["asset_id"]
    
    asset = ccs_asset(session_id, asset_id)
    
    if type == "CPE":
        asset.updateAssetDetail("description", "RuralLink Farm Terminal")
    elif type == "Repeater":
        asset.updateAssetDetail("description", "RuralLink Farm Repeater")
    elif type == "Master":
        asset.updateAssetDetail("description", "Rurallink Farm AP (Master Node)")
    else:
        raise ccs_rurallink_error("Unknown configuration type!")

    return True

@exportViaXMLRPC(SESSION_RO, AUTH_RURALLINK)
def getDevicePassword(session_id, asset_id):
    """Returns the device's password

    This password is generated by taking the Rural Link root password, 
    concatenating it with the devices MAC address and returning the last 8
    characters of an md5sum of the two
    """

    # Get the master rurallink password
    s = rurallink_service(session_id, rurallink_service.service_id)
    d = s.getDetails()
    rl_pass = d["properties"][ROOTPASS_PROPERTY]["network_value"]
    
    # Get the MAC address of the specified device
    asset = ccs_asset(session_id, asset_id)
    mac = asset.getMAC()
    
    # Calculate and return the password
    sum = md5("%s%s" % (rl_pass, mac)).hexdigest()
    return sum[-8:]

##############################################################################
# Phone Home Support
##############################################################################

@exportViaXMLRPC(SESSION_RO, AUTH_AUTHENTICATED, clientAddress=True)
def phoneHome(session_id, address, info):
    global devices

    session = getSessionE(ADMIN_SESSION_ID)

    serialno = int(info["serialno"])

    if serialno in devices.keys():
        devices[serialno]["ip"] = address
        devices[serialno]["timestamp"] = time.time()
        return True

    # Phone home from unknown device, lookup asset id
    res = session.query("SELECT a.asset_id, a.description FROM " \
            "asset_data d, subasset s, asset a WHERE " \
            "d.subasset_id=s.subasset_id AND " \
            "s.asset_id=a.asset_id AND d.value=%s", (serialno)) 
    if len(res) <= 0 :
        log_info("Phone home from %s claiming to be unknown device #%s" % \
                (address, serialno))
        return False
    asset_id = res[0]["asset_id"]

    # Create a new phone home record
    data = {"serialno":serialno, "asset_id":asset_id, "ip":address,
            "timestamp":time.time(), "timestamp_str":"", "location":"",
            "description":res[0]["description"]}
    devices[serialno] = data
    log_info("Created phone home entry for device #%s from %s" % \
            (serialno, address))
    return True

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getPhoneHome(session_id):
    """Returns phone home status details"""
    global devices
    rv = devices.copy()

    session = getSessionE(session_id)

    sql = "SELECT a.asset_id, d.value AS serialno, " \
            "date_part('epoch', al.location_updated) AS location_updated, " \
            "COALESCE(s.location, 'Attached to Asset #' || " \
            "al.attached_to) AS location FROM asset_data d, " \
            "subasset sa, asset a, subasset_property sp, asset_property ap, " \
            "asset_location al LEFT JOIN site s ON " \
            "al.site_id=s.site_id WHERE d.subasset_id=sa.subasset_id AND " \
            "sa.asset_id=a.asset_id AND " \
            "d.subasset_property_id=sp.subasset_property_id AND " \
            "sp.asset_property_id=ap.asset_property_id AND " \
            "ap.description=%s AND a.description LIKE '%%AP%%' AND " \
            "a.asset_id=al.asset_id"
    for device in session.query(sql, (RURALLINK_SERIAL_DESCRIPTION)):
        serialno = int(device["serialno"])
        if serialno not in rv.keys(): continue
        rv[serialno]["location"] = device["location"]
        if rv[serialno]["timestamp"] is None:
            rv[serialno]["timestamp_str"] = "Never"
        else:
            rv[serialno]["timestamp_str"] = \
                    roundTime(time.time()-rv[serialno]["timestamp"])

    return rv

def initPhoneHome():
    """Initailises the phone home support."""
    global devices

    session = getSessionE(ADMIN_SESSION_ID)

    # Find every asset with a Rural Link serial number and add it ot the array
    sql = "SELECT a.asset_id, a.description, d.value AS serialno FROM " \
            "asset_data d, subasset s, asset a, subasset_property sp, " \
            "asset_property ap WHERE d.subasset_id=s.subasset_id AND " \
            "s.asset_id=a.asset_id AND d.subasset_property_id=" \
            "sp.subasset_property_id AND sp.asset_property_id=" \
            "ap.asset_property_id AND ap.description=%s AND " \
            "a.description LIKE '%%AP%%'"
    for device in session.query(sql, (RURALLINK_SERIAL_DESCRIPTION)):
        serialno = int(device["serialno"])
        data = {"serialno":serialno, "asset_id":device["asset_id"], "ip":None,
                "timestamp":None, "timestamp_str":"", "location":"",
                "description":device["description"]}
        devices[data["serialno"]] = data

##############################################################################
# Rural Link Service
##############################################################################
class rurallink_service(ccsd_service):
    """Configures the ruralink service on a host"""
    
    serviceName = "rurallink"
    allowNewProperties = True
    networkService = True

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("Initialising Rural Link service")        
        try:
            # Create the service entry
            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (rurallink_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS service_id", ())
            
            # Setup Properties
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, " \
                "required) VALUES (DEFAULT, %s, %s, 'string', %s, 't')", \
                (service_id, ROOTPASS_PROPERTY, ""))
            
            # Create the Auth group if it doesn't exist
            try:
                id = getGroupID(session.session_id, AUTH_RURALLINK)
                if id==-1:
                    addGroup(session.session_id, \
                            {"group_name":AUTH_RURALLINK})
            except:
                log_error("Could not initialise the Rurallink Auth group!", \
                        sys.exc_info())

            # Commit the changese
            session.commit()
            
            log_info("Created Rural Link service")
        except:
            session.rollback()
            log_error("Unable to initialise Rural Link service!", \
                    sys.exc_info())
            raise ccs_rurallink_error("Failed to setup Rural Link service!")

        return service_id

##############################################################################
# Initialisation
##############################################################################
def ccs_init():
    registerService(rurallink_service)
    initPhoneHome()
