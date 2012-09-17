# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Status Module - Keeps track of the status of hosts in the system
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
import os.path
import threading
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from time import time
import random
import threading

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_config import config_get, config_getboolean
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC, initThread
from crcnetd._utils.ccsd_cfengine import getCfengineHostStatus, \
        getActiveRevision, getGeneratedRevision
from crcnetd.modules.ccs_host import ccs_host, getHostList, getHostName

ccs_mod_type = CCSD_SERVER

DEFAULT_CHECK_INTERVAL = 3*60

CCS_REVISION_OID = (1,3,6,1,4,1,15120,1,3,1)
LOAD_AVG1_OID = (1,3,6,1,4,1,15120,1,3,1)
LOAD_AVG5_OID = (1,3,6,1,4,1,15120,1,3,1)
LOAD_AVG15_OID = (1,3,6,1,4,1,15120,1,3,1)
UPTIME_OID = (1,3,6,1,4,1,15120,1,3,1)

class ccs_status_error(ccsd_error):
    pass

class ccs_host_status(ccs_class):
    """Monitors the status of a host in the system"""
    
    # Check list. Queue of which status class to check next. Each entry in the 
    # queue is a tuple (time, class), time specifies when the check is to be run
    # and class specifies an instance of this class that will perform the check.
    # The queue method of the class should be used to add new tests to the queue.
    update_queue = []

    def __init__(self, session_id, host_id, interval=-1):
        """Initialises a new class for a specified host.

        The specified session must be valid and have appropriate access to
        the database.
        """
        
        self.lock = threading.RLock()

        session = getSession(session_id)
        if session is None:
            raise ccs_host_error("Invalid session id")
        self._session_id = session_id
        
        # See if the specified host id makes sense
        self.host = ccs_host(session_id, host_id)
        self._hostname = self.host["host_name"]
        self._ip = self.host["ip_address"]
        
        # Initialise the status information
        self.reachable = False
        self.operatingRevision = -1
        self.operatingRevisionStatus = STATUS_UNKNOWN
        self.operatingRevisionText = "Unknown"
        self.operatingRevisionHint = "Status not yet fetched"
        self.currentLoad = (-1,-1,-1)
        self.uptime = 0
        self.infoUpdatedAt = 0
        self.lastCheckedAt = time.time()
        self.interval = interval
        self.attempt = 0
        # Retrieve locally available information
        self.activeRevision = getActiveRevision(self._hostname)
        self.generatedRevision = getGeneratedRevision(self._hostname)

        # Will this object be updated?
        if interval != -1:
            ccs_host_status.queue(time.time(), self)
        log_info("Initialised host status monitor for %s" % self._hostname)

    @staticmethod
    def queue(runat, instance):
        """Class method that adds the instance to the end of the queue"""
        # Jitter the interval by up to half of itself to avoid checking
        # everything at once!
        jitter = random.randint(0, instance.interval/2)
        dir = random.randint(0, 1) == 1 and 1 or -1
        runat += jitter*dir

        ccs_host_status.update_queue.append((runat, instance))
        ccs_host_status.update_queue.sort(queue_sort)

    def requeue(self):
        """Called by an instance to add itself to the queue after a run.

        Implements an exponential type backoff to reduce update frequency if a 
        host is not responding.
        """
        # Backoff can be up to three times the original interval
        attempt = self.attempt > 3 and 3 or self.attempt
        attempt = attempt > 0 and attempt or 1
        interval = self.interval * attempt
        ccs_host_status.queue(time.time()+interval, self)

    def update(self):
        """Called by the processing thread to trigger an update of the data"""
        ip = self._ip
        hostname = self._hostname
        
        # Grab the lock
        lock = self.lock
        lock.acquire()
        try:
            # Retrieve locally available information
            self.activeRevision = getActiveRevision(hostname)
            self.generatedRevision = getGeneratedRevision(self._hostname)
            # Check that the host is reachable
            if not isHostUp(ip):
                self.reachable = False
                self.lastCheckedAt = time.time()
                self.attempt+=1
                return
            self.reachable = True
            # Retrieve host status information
            pMod = api.protoModules[api.protoVersion1]
            reqPDU =  pMod.GetRequestPDU()
            pMod.apiPDU.setDefaults(reqPDU)
            pMod.apiPDU.setVarBinds(
                    reqPDU, ((CCS_REVISION_OID, pMod.Null()),
                        (LOAD_AVG1_OID, pMod.Null()),
                        (LOAD_AVG5_OID, pMod.Null()),
                        (LOAD_AVG15_OID, pMod.Null()),
                        (UPTIME_OID, pMod.Null())
                        )
                    )
            # Build message
            reqMsg = pMod.Message()
            pMod.apiMessage.setDefaults(reqMsg)
            pMod.apiMessage.setCommunity(reqMsg, 'public')
            pMod.apiMessage.setPDU(reqMsg, reqPDU)
            # Dispatch Request
            transportDispatcher = AsynsockDispatcher()
            transportDispatcher.registerTransport(
                    udp.domainName, udp.UdpSocketTransport().openClientMode()
            )

            startedAt = time.time()
            def cbTimerFun(timeNow):
                if timeNow - startedAt > 3:
                    transportDispatcher.jobFinished(1)
                    transportDispatcher.closeDispatcher()
                    self.attempt+=1
                    log_warn("Timeout fetching status from %s. Attempt #%s" % 
                        (hostname, self.attempt))

            def cbRecvFun(transportDispatcher, transportDomain, \
                    transportAddress, wholeMsg, reqPDU=reqPDU):
                while wholeMsg:
                    rspMsg, wholeMsg = decoder.decode(wholeMsg, \
                            asn1Spec=pMod.Message())
                    rspPDU = pMod.apiMessage.getPDU(rspMsg)
                    # Match response to request
                    if pMod.apiPDU.getRequestID(reqPDU) == \
                            pMod.apiPDU.getRequestID(rspPDU):
                        # Check for SNMP errors reported
                        errorStatus = pMod.apiPDU.getErrorStatus(rspPDU)
                        if errorStatus:
                            transportDispatcher.jobFinished(1)
                            transportDispatcher.closeDispatcher()
                            raise ccs_status_error(errorStatus.prettyPrint())
                        else:
                            la1 = 0
                            la5 = 0
                            la15 = 0
                            for oid, val in pMod.apiPDU.getVarBinds(rspPDU):
                                if oid == CCS_REVISION_OID:
                                    self.operatingRevision = str(val)
                                    self._parseOperatingRevision()
                                elif oid == LOAD_AVG1_OID:
                                    la1 = val
                                elif oid == LOAD_AVG5_OID:
                                    la5 = val
                                elif oid == LOAD_AVG15_OID:
                                    la15 = val
                                elif oid == UPTIME_OID:
                                    self.uptime = val
                            self.currentLoad = (la1, la5, la15)
                        transportDispatcher.jobFinished(1)
                self.attempt = 0
                return wholeMsg

            transportDispatcher.registerRecvCbFun(cbRecvFun)
            transportDispatcher.registerTimerCbFun(cbTimerFun)
            transportDispatcher.sendMessage(
                    encoder.encode(reqMsg), udp.domainName, (ip, 161)
            )
            transportDispatcher.jobStarted(1)
            transportDispatcher.runDispatcher()
            transportDispatcher.closeDispatcher()
            # Record that the details were updated
            self.infoUpdatedAt = time.time()
            self.lastCheckedAt = time.time()
        finally:
            lock.release()

    def _parseOperatingRevision(self):
        """Parsing the incoming operating revision and discerns what it means
        about the status of the host"""

        if self.operatingRevision == -1 or self.operatingRevision=="":
            # Host doesn't know it's own revision!
            self.operatingRevisionStatus = STATUS_CRITICAL
            self.operatingRevisionText = "Invalid State"
            self.operatingRevisionHint = "The host is in an invalid state"
            self.operatingRevision = ""
            return

        if self.operatingRevision.find("M") != -1:
            self.operatingRevisionStatus = STATUS_WARNING
            self.operatingRevisionText = "Has manual changes!"
            self.operatingRevisionHint = "Manual changes risk being overwritten"
            self.operatingRevision = self.operatingRevision[:-1]
            return

        if self.operatingRevision.find(":") != -1:
            parts = self.operatingRevision.split(":")
            self.operatingRevisionStatus = STATUS_WARNING
            self.operatingRevisionText = "Mixed with r%s" % parts[1]
            self.operatingRevisionHint = "There are configuration files on " \
                    "the host that do not come from the active revision"
            self.operatingRevision = parts[0]
            return

        self.operatingRevisionStatus = STATUS_OK
        self.operatingRevisionText = ""
        self.operatingRevisionHint = "The host configuration is up to date"
        return

    def __getattribute__(self, name):
        """Override the default accessor to put a lock around all accesses"""

        lock = object.__getattribute__(self, "lock")
        lock.acquire()
        try:
            val = object.__getattribute__(self, name)
            return val
        finally:
            lock.release()
    
def queue_sort(a, b):
    return cmp(a[0], b[0])

@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, False, "getHostStatus")
def getStatus(session_id, host_id):
    """Returns a dictionary describing the status of the host"""
    
    # Get some basic info
    hostname = getHostName(session_id, host_id)
    hoststatus = getHostStatus(hostname)
    
    # Get the host's CFengine status
    status = getCfengineHostStatus(session_id, hoststatus.host._properties)
    
    # Get state information
    status["reachable"] = hoststatus.reachable
    status["operating_rev"] = hoststatus.operatingRevision
    status["operating_rev_status"] = hoststatus.operatingRevisionStatus
    status["operating_rev_text"] = hoststatus.operatingRevisionText
    status["operating_rev_hint"] = hoststatus.operatingRevisionHint
    status["active_rev"] = hoststatus.activeRevision
    status["generated_rev"] = hoststatus.generatedRevision
    status["current_load"] = hoststatus.currentLoad
    status["uptime"] = hoststatus.uptime
    status["infoUpdatedAt"] = time.strftime("%d/%m/%Y %H:%M:%S", \
                    time.localtime(hoststatus.infoUpdatedAt))
    status["lastCheckedAt"] = time.strftime("%d/%m/%Y %H:%M:%S", \
                    time.localtime(hoststatus.lastCheckedAt))
    
    return status

def getHostStatus(host_name):
    """Returns the host status object for the specified host"""
    global _statusInfo

    if host_name not in _statusInfo.keys():
        raise ccs_status_error("No status information for %s" % host_name)

    return _statusInfo[host_name]

def getHostStatusSummary(session_id, host_name):
    """Returns an overall status for the host"""

    status = {}
    try:
        hoststatus = getHostStatus(host_name)
    except:
        status = {"status":STATUS_UNKNOWN,"status_text":"UNKNOWN", \
                "status_hint":"No status information available"}
        return status

    status["infoUpdatedAt"] = time.strftime("%d/%m/%Y %H:%M:%S", \
                    time.localtime(hoststatus.infoUpdatedAt))
    status["lastCheckedAt"] = time.strftime("%d/%m/%Y %H:%M:%S", \
                    time.localtime(hoststatus.lastCheckedAt))
    status["status"] = STATUS_OK
    status["status_text"] = "UP"
    status["status_hint"] = "Last checked at %s" % status["lastCheckedAt"]

    if not hoststatus.reachable:
        status["status"] = STATUS_CRITICAL
        status["status_text"] = "Down"
        status["status_hint"] = "Not seen since %s" % status["infoUpdatedAt"]
        return status

    if hoststatus.operatingRevisionStatus != STATUS_OK:
        status["status"] = hoststatus.operatingRevisionStatus
        status["status_text"] = hoststatus.operatingRevisionText
        status["statux_hint"] = hoststatus.operatingRevisionHint
        return status
    
    cstatus = getCfengineHostStatus(session_id, hoststatus.host._properties)
    if cstatus["ssh_key_status"] != STATUS_OK:
        status["status"] = cstatus["ssh_key_status"]
        status["status_text"] = "SSH Key Error"
        status["status_hint"] = cstatus["ssh_key_text"]
        return status
    if cstatus["cfengine_key_status"] != STATUS_OK:
        status["status"] = cstatus["cfengine_key_status"]
        status["status_text"] = "CFengine Key Error"
        status["status_hint"] = cstatus["cfengine_key_text"]
        return status
    
    return status

@catchEvent("shutdown")
def shutdownHandler(*args, **kwargs):
    global _runStatus
    _runStatus = False

_statusInfo = {}    
_runStatus = False

@catchEvent("hostAdded")
def addHostStatus(eventName, host_id, session_id, **params):
    """New host needs to be added to the monitor"""
    global _statusInfo, _runStatus

    #Only add if thread is running
    if _runStatus:
        host = ccs_host(session_id, host_id)
        name = host["host_name"]

        #Only add if host is active and not already in the list
        if host._properties["host_active"] and name not in _statusInfo:
            interval = config_get("status", "interval", DEFAULT_CHECK_INTERVAL)
            _statusInfo[name] = ccs_host_status(ADMIN_SESSION_ID, \
                host_id, interval)
    
@catchEvent("hostRemoved")
def delHostStatus(eventName, host_id, session_id, **params):
    """Host has been deleted so remove from the monitor"""
    global _statusInfo

    host_name = getHostName(session_id, host_id)

    #Only remove if it is in the list
    if host_name in _statusInfo.keys():
        del _statusInfo[host_name]
        log_debug("Removed host status monitor for %s" % (host_name))
        
@catchEvent("hostnameChanged")
def changeHostName(eventName, host_id, session_id, **params):
    """Hosts name changed so change the name in the monitor"""
    global _statusInfo
    
    old_name = params["old_name"]
    host_name = getHostName(session_id, host_id)
    log_debug("Changing host status monitor for %s to %s" % (old_name, host_name))
    if old_name not in _statusInfo.keys():
        raise ccs_status_error("Cannot rename %s as does not exist" % old_name)
    _statusInfo[host_name] = _statusInfo[old_name]
    del _statusInfo[old_name]
    
@catchEvent("hostActiveChanged")
def changeActive(eventName, host_id, session_id, **params):
    """New host needs to be added to the monitor"""
    global _statusInfo
    
    host_active = params["host_active"]
    if host_active == "t":
        addHostStatus(eventName, host_id, session_id, **params)
    else:
        delHostStatus(eventName, host_id, session_id, **params)
        
def statusThread():
    """Runs as a thread to keep the status information up to date"""
    global _statusInfo, _runStatus

    try:
        # Is status checking enabled
        enabled = config_getboolean("status", "enabled", True)
        if not enabled:
            log_info("Status checking disabled. Exiting status monitor thread")
            return
        _runStatus = True;

        # Setup the thread information 
        ct = threading.currentThread()
        ct.setName("CCSD Status Monitor")

        # What interval shall we check hosts at
        interval = config_get("status", "interval", DEFAULT_CHECK_INTERVAL)
        
        # Initialise the host status information
        hosts = getHostList(ADMIN_SESSION_ID)
        for host in getHostList(ADMIN_SESSION_ID):
            if not host["host_active"]:
                continue
            name = host["host_name"]
            _statusInfo[name] = ccs_host_status(ADMIN_SESSION_ID, \
                    host["host_id"], interval)
        
        # Loop forever reading status as appropriate
        while _runStatus:
            # wait a bit before checking
            time.sleep(2)
            # Does the queue have entries
            if len(ccs_host_status.update_queue) <= 0:
                continue
            # Is the first entry valid
            if len(ccs_host_status.update_queue[0]) != 2:
                log_error("Invalid entry in status update queue! - %s" %
                        ccs_host_status.update_queue[0])
                ccs_host_status.update_queue.pop(0)
                continue
            # Check if it's ready to run
            if ccs_host_status.update_queue[0][0] > time.time():
                continue
            # Read to run
            check = ccs_host_status.update_queue.pop(0)
            try:
                check[1].update()
            except:
                log_error("Failed to update status of %s" % \
                        check[1]._hostname, sys.exc_info())
            # Regardless of what happened, check again sometime soon if it
            # is still in the list of hosts to check
            if check[1]._hostname in _statusInfo.keys():
                check[1].requeue()
    except:
        log_error("Exception in status monitor thread!", sys.exc_info())

    log_info("Exiting status monitor thread")
        
def ccs_init():
    # Start the status information thread
    initThread(statusThread)
