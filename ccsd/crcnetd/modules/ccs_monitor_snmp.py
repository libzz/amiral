# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# CRCnet Monitor Base SNMP Functionality
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
import sys, os
import time
import socket
import fcntl
import asyncore
import sslasn1

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_clientserver import registerPage, registerDir, \
        registerRealm
from crcnetd._utils.ccsd_config import config_get, config_getboolean
from crcnetd.version import ccsd_version, ccsd_revision

class ccs_monitor_error(ccsd_error):
    pass

ccs_mod_type = CCSD_CLIENT

# Default Port
DEFAULT_SNMP_PORT = 161

UPTIME_START = 0

# SNMP Packet Types
SNMP_GETREQUEST = 0
SNMP_GETNEXTREQUEST = 1
SNMP_GETRESPONSE = 2
SNMP_SETREQUEST = 3
SNMP_TRAP = 4

#####################################################################
# SNMP Server Helper Functions
#####################################################################

# Keep a list of registered OIDs, must be kept sorted for snmp getNext to work
oidList = []
oidData = {}

# The following classes define types of OIDs that objects can return
#
# Static - Single OID -> value, value static during program execution
# Dynamic - OID -> value, value determined dynamically when requested, may
#           handle multiple oids if requested.
# Table - Multiple OIDs as a table, values determined dynamically
#
# Each class must define a __cmp__, __call__ and getNext method. 
#
# The __call__ method should always return a value for the explicit OID it
# is passed, regardless of what the base oid of the handler is. 
#
# getNext should return the OID immediately following it in this handler, or
# None if this handler does not handle any further oids.
#
# Hence Single OID classes always return the same value for __call__ and None
# from getNext
class ccsdStaticOidItem:
    types = ["Integer", "OctetString", "IpAddress", "Counter", "Guage", 
        "TimeTicks", "Opaque" ]
    def __init__(self, oid, value, vtype):
        """Initialises a static oid value"""
        self.name = oid
        self.value = value
        if vtype not in self.types:
            raise ccsd_server_error("Invalid type (%s) for oid!" % vtype)
        self.type = vtype
    def __cmp__(self, other): return cmp(self.name, other)    
    def __call__(self, oid):
        vtype = eval("%s" % self.type)
        if oid is None: oid = self.name
        return (oid, vtype(self.value))
    def getNext(self, oid): return None

class ccsdDynamicOidItem:
    def __init__(self, oid, function):
        """Initialises a static oid value"""
        self.name = oid
        self.function = function
    def __cmp__(self, other): return cmp(self.name, other)    
    def __call__(self, oid):
        if oid is None: oid = self.name
        return self.function(oid, False)
    def getNext(self, oid):
        if oid is None: oid = self.name
        return self.function(oid, True)
        
    
class ccsdOidTableItem:
    """A table is registered with a base oid. there are two suboids from this

    base.1      Number of records in table
    base.2      Base of table

    Under the table the records are in the form 1.item.index , where the 1
    represents the entry item. eg.

    base.2.1.item.index
    
    The values used for item and index are completely up to the caller. All
    of the item values must be specified when constructing the table object.
    """
    
    def __init__(self, oid, function, parameters):
        """Initialises an oid that acts as the base of a table"""
        self.name = oid
        self.function = function
        self.NO_ENTRIES = oid + (1,)
        self.TABLE = oid + (2,1)
        
        if type(parameters) != type([]):
            raise ccs_server_error("Parameters must be a list!")
        if len(parameters)==0:
            raise ccs_server_error("Cannot create a table with no parameters!")
        self.parameters = parameters
        
    def __cmp__(self, other): return cmp(self.name, other)    
    def __call__(self, oid):
        # Get the list of entries in the table
        entries = self.function()

        if oid == self.name or oid == self.NO_ENTRIES or oid is None:
            # number of entries
            return (self.NO_ENTRIES, Integer(len(entries)))
        
        # Check validity
        if not self.isValidOID(oid, entries):
            return None

        # Get and return the value
        parts = oid[len(self.TABLE):]
        if len(parts)<2:
            # Invalid OID
            return None
        val = self.function(parts[0], parts[1])
        return (oid, val)

    def getNext(self, oid):
        # Get the list of entries in the table
        entries = self.function()
        
        if oid == self.name or oid is None:
            # number of entries
            return (self.NO_ENTRIES, Integer(len(entries)))
            
        if oid == self.NO_ENTRIES:
            if len(entries)==0: return None
            # Return first table entry
            nextIdx = entries[0]
            nextParam = self.parameters[0]
            val = self.function(nextParam, nextIdx)
            newOid = self.TABLE + (nextParam, nextIdx)
            return (newOid, val)

        # Check validity
        if not self.isValidOID(oid, entries):
            return None
        
        # Increment
        parts = oid[len(self.TABLE):]
        if len(parts)<2:
            nextIdx=0
        else:
            nextIdx = bisect(entries, parts[1])
        if nextIdx == len(entries):
            nextParam = bisect(self.parameters, parts[0])
            if nextParam == len(self.parameters):
                ## End of table
                return None
            else:
                # Next parameter
                nextParam = self.parameters[nextParam]
                # Back to first index
                nextIdx = entries[0]
        else:
            nextIdx = entries[nextIdx]
            nextParam = parts[0]
    
        # Get and return the value
        val = self.function(nextParam, nextIdx)
        newOid = self.TABLE + (nextParam, nextIdx)
        return (newOid, val)
      
    def isValidOID(self, oid, entries):
        try:
            # Strip off the base oid
            parts = oid[len(self.name):]
            if (parts[0] != 2 and parts[1] != 1) or \
                (len(parts)<3 and len(parts)>4):
                # Invalid oid. 
                log_warn("Request for invalid table OID: %s" % str(oid))
                return False
    
            # Check the parameter is valid
            if parts[2] not in self.parameters:
                # Invalid oid. 
                log_warn("Request for invalid table parameter: %s" % str(oid))
                return False
           
            # Check the index is valid
            if len(parts)==4 and parts[3] not in entries:
                # Invalid oid.
                log_warn("Request for invalid table index: %s" % str(oid))
                return False
       
            return True
        except:
            log_error("Request for table OID (%s) caused exception" % \
                    str(oid), sys.exc_info())
            return False
    
def registerStaticOID(oid, value, type):
    """Registers an OID with a static value"""
    global oidList, oidData
    oidData[oid] = ccsdStaticOidItem(oid, value, type)
    nextIdx = bisect(oidList, oid)
    oidList.insert(nextIdx, oidData[oid])
    
def registerDynamicOID(oid):
    """Decorator to register a function that provides values for an OID"""
    global oidList, oidData
    
    def decorator(func):
        oidData[oid] = ccsdDynamicOidItem(oid, func)
        nextIdx = bisect(oidList, oid)
        oidList.insert(nextIdx, oidData[oid])
        return func
    return decorator

def registerTableOID(oid, parameters):
    """Decorator to register a function that provides values for a table"""
    global oidList, oidData
    
    def decorator(func):
        oidData[oid] = ccsdOidTableItem(oid, func, parameters)
        nextIdx = bisect(oidList, oid)
        oidList.insert(nextIdx, oidData[oid])
        return func
    return decorator

def findOidHandler(toid):
    """Returns an object that can handle this oid or None

    This function first checks for an oid handler that mateches the requested
    oid exactly. If found it is returned. If an exact match is not found, a
    recursive search is performed for "higher" level handlers by stripping the
    rightmost oid component and then looking for a match. 
    """
    global oidList, oidData
    
    # Convert from the ASN1 OID representation to a tuple of integers
    #toid = tuple(map(int, str(oid).strip("( )").split(",")))
    # Search for the OID in the list
    while len(toid)>0:
        if oidData.has_key(toid):
            return oidData[toid]
        toid = toid[:-1]

    # Not found
    return None

def getNextOidHandler(oid):
    """Returns an object that can handle the next oid or None

    This function first checks for an oid handler that mateches the requested
    oid exactly. If found it is returned. If an exact match is not found, a
    recursive search is performed for "higher" level handlers by stripping the
    rightmost oid component and then looking for a match. 

    The recursive search terminates when the base of the SNMPv2-MIB is found
    (ie. .1.3.6.1.2.1.1)
    """
    
    # Search next OID to report
    handler = findOidHandler(oid)
    if handler is None:
        return None

    # Get the next value from the handler
    return handler.getNext(oid)

#####################################################################
# SNMP / ASN1 Encoding / Decoding
#####################################################################
def parseSNMP(msg):
    """Parses an incoming SNMP message and returns its components

    This function uses the OpenSSL ASN1 parser via the Pysslasn module
    to parse the SNMP request. 

    It is optimised for speed, not protocol compliance, only the bare
    minimum information that is required to respond to the request is
    extracted out of the ASN1 block.
    """
    lines = sslasn1.parse(msg).rstrip().split("\n")
    try:
        # Get version from line 2
        version = int(lines[1].split(":")[3], 16)

        # Get request type from line 4
        type = int(lines[3].split("[")[1].strip().split()[0])

        # Request ID 
        id = int(lines[4].split(":")[3], 16)

        # Variables
        oids = []
        for line in lines[9:-1]:
            if line.find("OBJECT") == -1:
                continue
            oids.append(StrToOID(line.split(":")[3]))
    except:
        log_error("Unable to parse incoming SNMP packet", sys.exc_info())
        return (-1, -1, -1, -1)

    return (version, type, id, oids)

def StrToOID(val):
    """Convert an OID in str format to a tuple of ints"""
    return tuple(map(int, val.split(".")))

def ASN1encodeLength(length):
    """Return the ASN1 encoding for the specified length"""
    if length < 0x80:
        return chr(length)
    elif length < 0xFF:
        return "\x81%c" % (length)
    elif length < 0xFFFF:
        return "\x82%c%c" % ((length >> 8)&0xFF, length&0xFF)
    elif length < 0xFFFFFF:
        return "\x83%c%c%c" % \
                ((length >> 16)&0xFF, (length >> 8)&0xFF, length&0xFF)
    else:
        ccs_snmp_error("ASN1 encoding overflow!")

def ASN1encodeString(val, subtype="\x04"):
    """Return the ASN1 encoding for the specified string
    
    Optionally a different subtype can be specified to allow encoding of
    ASN1 values that have the same encoded semantics as a String.
    """
    return subtype + ASN1encodeLength(len(val)) + str(val)

def ASN1encodeInteger(val, subtype="\x02"):
    """Return the ASN1 encoding for the specified integer

    Optionally a different subtype can be specified to allow encoding of
    ASN1 values that have the same encoded semantics as an Integer.
    """
    val = int(val)
    t = ""
    if val == 0:
        return subtype + "\x01\x00"
    elif val ==-1:
        return subtype + "\x01\xff"
    elif val < 0:
        while val <> -1:
            t = chr(val & 0xff) + t
            val >>= 8
        if ord(t[0]) & 0x80 == 0:
            t = "\xff" + t
    else:
        while val > 0:
            t = chr(val & 0xff) + t
            val >>= 8
        if ord(t[0]) & 0x80 <> 0:
            t = "\x00" + t
    return subtype + ASN1encodeLength(len(t)) + t

def ASN1encodeBytes(val, subtype):
    """Return the ASN1 encoding for the specified input integer

    The integer is encoded as raw bytes, ignoring the ASN1 semantics for 
    how an integer would typically be encoded. A subtype must be specified.
    """
    val = int(val)
    t = ""
    while val > 0:
        t = chr(val & 0xff) + t
        val >>= 8
    return subtype + ASN1encodeLength(len(t)) + t

def ASN1encodeOID(oid):
    """Returns the ASN1 encoding of the specified OID"""
    t = ""

    if type(oid) == type(""):
        oid = StrToOID(oid)
    if type(oid) != type(()) or len(oid) < 2:
        raise ccs_snmp_error('Invalid OID %s' % (oid))
    
    # Pack first two components into the first byte
    t += chr((oid[0] * 40) + oid[1])
    
    # Encode the remaining components
    for item in oid[2:]:
        if item > -1 and item < 128:
            # Single byte encoding
            t += chr(item & 0x7F)
        elif item < 0 or item > 0xFFFFFFFFL:
            raise ccs_snmp_error("OID is too big (%s in %s)!" % (item, oid))
        else:
            # Multi-byte enocding
            os = chr(item & 0x7f)
            item >>= 7
            while item > 0:
                os = chr(0x80 | (item & 0x7f)) + os
                item >>= 7
            t += os
    return "\x06" + ASN1encodeLength(len(t)) + t

# Map the ASN1 encoding functions from above into "Type" names that external
# modules can use
Integer = ASN1encodeInteger
OctetString = ASN1encodeString
ObjectIdentifier = ASN1encodeOID
IpAddress = lambda x: ASN1encodeBytes(ipnum(x), "\x40")
Counter = lambda x: ASN1encodeInteger(x, "\x41")
Gauge = lambda x: ASN1encodeInteger(x, "\x42")
TimeTicks = lambda x: ASN1encodeInteger(x, "\x43")
Null = lambda x: "\x05"

def buildResponse(version, sequence, err, results):
    """Builds the ASN1 response block for the given information"""

    # PDU Information
    pdu = ""
    pdu += ASN1encodeInteger(sequence)
    pdu += ASN1encodeInteger(err)
    pdu += ASN1encodeInteger(0)

    # Build the ASN1 for the values 
    t = ""
    for result in results:
        rs = ASN1encodeOID(result[0])
        rs += str(result[1])
        t += "\x30" + ASN1encodeLength(len(rs)) + rs
    pdu += "\x30" + ASN1encodeLength(len(t)) + t

    # Now the SNMP packet header
    header = ASN1encodeInteger(version)
    header += ASN1encodeString("public")
    header += "\xA2" + ASN1encodeLength(len(pdu)) + pdu

    # Final header and length
    return "\x30" + ASN1encodeLength(len(header)) + header

def handleSNMPRequest(server, data, remoteHost):
    """Handles an incoming SNMP request"""
    global oidList, debug_snmp
    start = time.time()
    
    (version, reqtype, sequence, oids) = parseSNMP(data)
    if version == -1:
        return
    parsed = time.time()-start
    results = []
    err = 0
    # GETNEXT PDU
    if reqtype == SNMP_GETNEXTREQUEST:
        for oid in oids:
            # Get the next variable
            vars = getNextOidHandler(oid)
            if vars is not None:
                results.append(vars)
                continue
            # No next variable - Try the next handler
            nextIdx = bisect(oidList, oid)
            if nextIdx == len(oidList):
                # Out of MIB
                err = 2
                continue
            # Retrieve the value from the next handler
            vars = oidList[nextIdx].getNext(None)
            if vars is None:
                # Fall back to just getting this if there is no getNext
                # handler
                vars = oidList[nextIdx](None)
            if vars is not None:
                results.append(vars)
            else:
                # Could not get more vars - end of MIB
                err = 2
    elif reqtype == SNMP_GETREQUEST:
        for oid in oids:
            handler = findOidHandler(oid)
            if handler is not None:
                vars = handler(oid)
                if vars is not None:
                    results.append(vars)
                    continue
            # No such instance
            err = 2
            break
    else:
        log_error("Ingoring Invalid SNMP Request from %s (%s)" % 
                (remoteHost[0], reqtype))
        return

    responded = time.time()-start
    response = buildResponse(version, sequence, err, results)
    server.sendMessage(response, remoteHost)
    if debug_snmp:
        log_debug("Replied to %s in (%.4f, %.4f, %.4f) seconds" % \
                (remoteHost[0], parsed, responded, time.time()-start))

##############################################################################
# Asynchronous SNMP Server using the asyncore framework
##############################################################################
class AsyncSNMPServer(asyncore.dispatcher):
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(address)
        fcntl.fcntl(self.socket, fcntl.F_SETFD, fcntl.FD_CLOEXEC)
    def handle_read(self):
        data, remoteHost = self.socket.recvfrom(65535)
        try:
            handleSNMPRequest(self, data, remoteHost)
        except:
            log_error("Exception while processing SNMP request!", 
                    sys.exc_info())
    def handle_connect(self): pass
    def handle_write(self): pass
    def sendMessage(self, data, toAddress):
        self.socket.sendto(data, toAddress)

    #Need this to prevent asyncore from returning
    #imeadiatly on poll and causing infinite loop
    def writable(self):
        return False

##############################################################################
# Initialisation
##############################################################################
def ccs_init():
    global debug_snmp
    # Default SNMP Content Helpers
    
    # Implement the basics of the SNMPv2-MIB
    SNMPv2_MIB = (1,3,6,1,2,1,1)
    registerStaticOID(SNMPv2_MIB+(1,0), "CRCnet Monitor v%s (r%s), %s" % \
            (ccsd_version, ccsd_revision, " ".join(os.uname())), "OctetString")

    # sysObjectID not implemented

    UPTIME_START = time.time()
    @registerDynamicOID(SNMPv2_MIB+(3,0))
    def uptime(oid, getNext):
        if getNext: return None
        uptime = (time.time()-UPTIME_START)*100
        return (oid, TimeTicks(uptime))

    # sysContact not implemented
    registerStaticOID(SNMPv2_MIB+(5,0), socket.gethostname(), "OctetString")
    # sysLocation not implemented
    # sysServices not implemented
    # sysOR not implemented
    
    # Start the actual SNMP server
    try:
        debug_snmp = config_getboolean("snmp", "debug", False)
        port = int(config_get("snmp", "port", DEFAULT_SNMP_PORT))
        AsyncSNMPServer(('', port))
        log_info("SNMP Server Started")
    except:
        log_fatal("Could not initialise the SNMP server!", sys.exc_info())

