# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# CFengine Configuration Setup
#
# Manages the cfengine configuration for the configuration system. The two
# primary tasks involved in this are:
# - Configuration file generation from templates
# - Controling cfengine runs and collecting output on demand
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
import shutil
from stat import *
import svn.core as core
import svn.client as client
import svn.wc as wc
import svn.fs as fs
import svn.repos as repos
import imp
import time
import threading
from twisted.web import resource, server
from tempfile import mkdtemp
from Cheetah.Template import Template

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_config import config_get, config_get_required, \
        config_getint
from crcnetd._utils.ccsd_session import getSession, getSessionE, ccsd_session
from crcnetd._utils.ccsd_server import registerResource, exportViaXMLRPC, \
        initThread, registerRecurring, suggestThreadpoolSize
from crcnetd._utils.ccsd_service import getServiceInstance, ccs_service_error

DEFAULT_MAX_TEMPLATE_THREADS = 10

KIND_DIR = core.svn_node_dir
KIND_FILE = core.svn_node_file
KIND_NONE = core.svn_node_none
KIND_UNKNOWN = core.svn_node_unknown
KIND_MAP = {KIND_DIR:"dir", KIND_FILE:"file", KIND_NONE:"none", \
        KIND_UNKNOWN:"unknown"}

class ccs_template_error(ccsd_error):
    pass
class ccs_cfengine_error(ccsd_error):
    pass

#####################################################################
# General Cfengine Integration Helper Functions
#####################################################################
def initTemplates():
    global _templateDir, _templateModDir
    
    # Ensure output template module directories exist and are empty
    removeDir("%s/host" % _templateModDir)
    ensureDirExists("%s/host" % _templateModDir)
    removeDir("%s/network" % _templateModDir)
    ensureDirExists("%s/network" % _templateModDir)

    # Ensure templates are compiled
    rv = log_command("/usr/bin/cheetah compile -R --idir %s/host --odir " \
            "%s/host --nobackup 2>&1" % (_templateDir, _templateModDir))
    if rv != None:
        log_error("Unable to compile all host templates!")
    rv = log_command("/usr/bin/cheetah compile -R --idir %s/network --odir " \
            "%s/network --nobackup 2>&1" % \
            (_templateDir, _templateModDir))
    if rv != None:
        log_error("Unable to compile all network templates!")
    
    # Load template files
    hostTemplates = loadTemplates("%s/host" % _templateModDir)
    log_info("Loaded %s host templates for cfengine." % len(hostTemplates))
    networkTemplates = loadTemplates("%s/network" % _templateModDir)
    log_info("Loaded %s network templates for cfengine." % \
            len(networkTemplates))

    return networkTemplates, hostTemplates

def loadTemplates(moduleDir, baseStrip=""):
    """Creates a dictionary of template modules from the specified dir"""
    
    # Dictionary of template objects
    templates = {}
    
    if baseStrip == "":
        baseStrip = moduleDir
        
    # Get a list of possible templates
    if os.access(moduleDir, os.R_OK) != 1:
        raise ccs_template_exception("Unable to access directory! - %s" % \
                moduleDir)
    ptempls = os.listdir(moduleDir)
    
    # Scan through the list and load valid modules
    for tfile in ptempls:
        # Ignore hidden files
        if tfile.startswith("."):
            continue
        tfilename = "%s/%s" % (moduleDir, tfile)
        # Recurse into directories
        if os.path.isdir(tfilename):
            templates.update(loadTemplates(tfilename, baseStrip))
            continue
        # Ignore non module files
        if not tfile.endswith(".py"):
            continue
        # Load the template module
        tname = os.path.basename(tfilename)[:-3]
        if tname == "__init__":
            # Ignore python framework stuff
            continue
        m = None
        try:
            m = imp.load_source(tname, tfilename)
            # Don't want the module in the system module list
            if tname in sys.modules.keys():
                del sys.modules[tname]
        except:
            log_debug("Module import failed for %s template" % tname, \
                    sys.exc_info())
            pass
        if not m:
            log_error("Failed to import template: %s" % tname)
            continue
        # If an explicit output filename was specified use that, otherwise
        # prepend path information and store the template filename.
        path = "%s/" % os.path.dirname(tfilename[len(baseStrip)+1:])
        if len(path) == 1:
            path = ""
        tclass = eval("m.%s" % tname)
        m.fileName = "%s%s" % (path, getattr(tclass, "fileName", tname))
        m.multiFile = getattr(tclass, "multiFile", False)
        m.templateName = tname
        # Store the template for future use, prepend path for uniqueness
        templateID = "%s%s" % (path, tname)
        if templateID in templates.keys():
            log_error("Could not import duplicate template: %s" % tname)
            continue
        templates[templateID] = m
    
    # Return the templates
    return templates
    
@registerRecurring(60*10)
def cleanTemplateStatus():
    """Runs every ten minutes to clean up expired template status info"""
    global _templateStats, _statsLock
    
    # If generation is not finished by this many minutes after initiation
    # there is an error, stats are removed in hope of causing a Key error 
    # that will kill the errant threads
    err_time = 60*60
    # Statistics for finished generation runs are removed this many minutes
    # after the run completes
    expire_time = 60*30
    
    _statsLock.acquire()
    try:
        for key,stats in _templateStats.items():
            if (time.time()-stats["initiated"]) > err_time:
                # Still processing after one hour!?
                log_error("Template generation (%s) was still active after " \
                        "%d seconds!" % (key, err_time))
                del _templateStats[key]
                continue
            if stats["finished"] == 0:
                # Still in progress
                continue
            if (time.time()-stats["finished"]) > expire_time:
                log_info("Removing template generation status (%s)" % key)
                del _templateStats[key]
    finally:
        _statsLock.release()

    return True
    
@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR)
def getTemplateStatus(session_id, statsKey, asynchronous=True):
    """Returns the status of a specified template generation run"""
    global _templateStats, _statsLock

    stats = None
    
    _statsLock.acquire()
    try:
        if statsKey not in _templateStats.keys():
            raise ccs_cfengine_error("Invalid key: %s" % statsKey)
        stats = dict(_templateStats[statsKey])
    finally:
        _statsLock.release()

    return stats

@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def generateTemplate(session_id, requested_templates={}):
    """Generates the specified configuration templates

    The requested_templates parameter should be a dictionary indexed by 
    host_name each entry should contain a list of the template ids that 
    should be generated for that host. 
    
    If the template list for a host is empty all available templates will be 
    regenerated. 
    If the dictionary is completely empty then all hosts will have their 
    templates regenerated.

    If an entry in the dictionary contains the key "network" it will be
    interpreted as a list of network wide templates to regenerate. If this key
    is absent then the network wide templates will be regenerated if the number
    of host templates being regenerated is greater than one.
    
    All template processing is shunted off to another thread and the user is
    returned a token that can be passed to future calls to getTemplateStatus
    to retrieve the current status of template generation. Generation results
    are stored for 30 minutes after the end of template generation.
    """
    global _templateStats, _statsLock
    from crcnetd.modules.ccs_host import getHostList

    # Load the templates
    networkTemplates, hostTemplates = initTemplates()

    # Setup the basic set of statistics about template generation
    stats = {}
    stats["planned"] = {}
    stats["generated"] = {}
    stats["skipped"] = {}
    stats["initiated"] = time.time()
    stats["setupprogress"] = 10
    stats["generating"] = 0
    stats["finished"] = 0
    stats["error"] = None

    # Work out what the user has requested us to generate
    hosts = {}
    host_names = requested_templates.keys()
    if len(host_names) == 0:
        host_names = [host["host_name"] for host in getHostList(session_id)]
    for host in host_names:
        if host == "network": continue
        templates = []
        if host in requested_templates.keys():
            templates = requested_templates[host]
        if len(templates) == 0:
            templates = hostTemplates.keys()
        hosts[host] = templates
    stats["planned"]["hosts"] = hosts
    stats["generated"]["hosts"] = {}
    stats["skipped"]["hosts"] = {}

    # Work out how many host templates we're going to be generating
    total = 0
    for tlist in hosts.values():
        total += len(tlist)
    stats["planned"]["total"] = total
    
    # Add network level templates if more than one host template is requested
    # or they have been explicitly specified
    if "network" in host_names:
        stats["planned"]["network"] = requested_templates["network"]
    elif total > 1:
        stats["planned"]["network"] = networkTemplates.keys()
    else:
        stats["planned"]["network"] = []
    stats["planned"]["total"] += len(stats["planned"]["network"])
    stats["generated"]["network"] = {}
    stats["skipped"]["network"] = {}

    # Aquire the lock to deal with statistics
    statsKey = token = createPassword(8)
    _statsLock.acquire()
    try:
        _templateStats[statsKey] = stats
    finally:
        _statsLock.release()

    # Fire off the new thread
    initThread(processTemplates, session_id, statsKey, networkTemplates, 
            hostTemplates)

    # Return back to the user
    return statsKey
    
@registerEvent("revisionPrepared")
def processTemplates(session_id, statsKey, networkTemplates, hostTemplates):
    """Does the hardwork of generating templates in a thread"""
    global _templateStats, _statsLock, _threadLimit
    from crcnetd.modules.ccs_host import getHostList, ccs_host, \
            getDistributions
    from crcnetd._utils.ccsd_service import getServiceTemplateVars
    from crcnetd.modules.ccs_asset import getAssetTypeTemplateVariables
    from crcnetd.modules.ccs_link import getLinkClassTemplateVariables, \
            getLinkTemplateVariables
    try:
        session = getSessionE(session_id)
        log_info("Entered template processing thread (%s)" % statsKey)
        ct = threading.currentThread()
        ct.setName("%s: processTemplates" % session.username)
        
        # Make sure we have a revision to insert files into
        # Check session to see if a revision is active
        commit=0
        if session.revision == None:
            session.begin("Updated host configuration files", initiator="cfengine")
            commit=1
        outputDir = session.revision.getConfigBase()
        
        # More progress
        _statsLock.acquire()
        try:
            _templateStats[statsKey]["setupProgress"] = 15
        finally:
            _statsLock.release()
            
        # Load all the data that we need to pass to the templates
        variables = {}
        hlist = {}
        id2name = {}
        for host in getHostList(session_id):
            host = ccs_host(session_id, host["host_id"])
            hostDetails = host.getTemplateVariables()
            hlist[host["host_name"]] =  hostDetails
            _statsLock.acquire()
            try:
                if _templateStats[statsKey]["setupProgress"] < 70:
                    _templateStats[statsKey]["setupProgress"] += 2
            finally:
                _statsLock.release()
        variables["hosts"] = hlist
        dlist = {}
        for distrib in getDistributions(session_id):
            dlist[distrib["distribution_id"]] = distrib
        variables["distributions"] = dlist
        variables["services"] = getServiceTemplateVars(session_id)
        _statsLock.acquire()
        try:
            _templateStats[statsKey]["setupProgress"] = 80
        finally:
            _statsLock.release()
        variables["date"] = time.ctime()
        variables["domain"] = config_get_required("network", "domain")
        variables["site_name"] = config_get_required("network", "site_name")
        variables["port"] = int(config_get(None, "https_port", DEFAULT_HTTPS_SERVER_PORT))
        variables["server_name"] = config_get_required("network", "server_name")
        ip = getIP(variables["server_name"])
        variables["policy_ip"] = ip
        variables["policy_ip_class"] = ip.replace(".", "_")
        variables["smtp_server"] = config_get_required("network", "smtp_server")
        variables["admin_email"] = config_get_required("network", "admin_email")
        variables["dbhost"] = ccsd_session.dhost
        variables["dbuser"] = ccsd_session.duser
        variables["dbpass"] = ccsd_session.dpass
        variables["dbname"] = ccsd_session.database
        _statsLock.acquire()
        try:
            _templateStats[statsKey]["setupProgress"] = 90
        finally:
            _statsLock.release()

        variables["asset_types"] = getAssetTypeTemplateVariables(session_id)
        variables["link_classes"] = getLinkClassTemplateVariables(session_id)
        variables["links"] = getLinkTemplateVariables(session_id)
        variables["session_id"] = session_id

        # Update the stats and get the list of hosts
        _statsLock.acquire()
        try:
            planned = _templateStats[statsKey]["planned"]
            _templateStats[statsKey]["generating"] = time.time()
            _templateStats[statsKey]["setupProgress"] = 100
        finally:
            # Release the lock before proceeding
            _statsLock.release()
        
        # Now generate each hosts template in a separate thread
        for host,template_ids in planned["hosts"].items():
            # See if we can start a new thread
            _threadLimit.acquire()
            try:
                # Extract the host specific data for this template
                hostData = variables["hosts"][host]
                # Fire off the thread to process this host, the thread will release
                # the semaphore as it is about to exit
                # XXX: This relies on the thread behaving nicely, need to find a
                # way to find out if it's been bad and exited without releasing 
                # the semaphore
                initThread(processHostTemplates, statsKey, outputDir, \
                        hostTemplates, hostData, variables)
            except:
                log_error("Failed to start thread to process templates for " \
                        "host: %s!" % host, sys.exc_info())
                _threadLimit.release()
                
        # Wait until all the configuration files have been generated
        hosts = list(planned["hosts"].keys())
        hasError = False
        hasTemplateError = False
        while len(hosts) > 0:
            # Wait a bit before trying again
            time.sleep(1)
            _statsLock.acquire()
            try:
                generated = _templateStats[statsKey]["generated"]["hosts"]
                for host in hosts:
                    if not host in generated.keys():
                        continue
                    # Check if it finished successfully
                    if generated[host]["finished"] > 0:
                        # Remove from list
                        hosts.remove(host)
                        # Check if any of the templates failed to be output
                        if generated[host]["error"] == "template":
                            # Set the flag so we don't commit the revision
                            hasTemplateError = True
                    else:
                        # Check for fatal errors
                        if generated[host]["error"] != "":
                            # Set the flag and remove the host from processing
                            hosts.remove(host)
                            hasError = True
                            continue
            finally:
                _statsLock.release()
        
        # Hosts are done, network templates now
        for template_id in planned["network"]:
            # See if we can start a new thread
            _threadLimit.acquire()
            try:
                # Fire off the thread to process this template, the thread will
                # release the semaphore as it is about to exit
                # XXX: This relies on the thread behaving nicely, need to find a
                # way to find out if it's been bad and exited without releasing 
                # the semaphore
                initThread(processNetworkTemplate, statsKey, outputDir, \
                        networkTemplates, template_id, variables)
            except:
                log_error("Failed to start thread to process network template: " \
                        "%s!" % template_id, sys.exc_info())
                _threadLimit.release()

        # Wait until all network templates are done
        network = list(planned["network"])
        while len(network) > 0:
            # Wait a bit before trying again
            time.sleep(1)
            _statsLock.acquire()
            try:
                generated = _templateStats[statsKey]["generated"]["network"]
                skipped = _templateStats[statsKey]["skipped"]["network"]
                for template in network:
                    if template in generated.keys():
                        # Check for errors
                        if generated[template]["error"] != "":
                            hasTemplateError = True
                    else:
                        if template not in skipped.keys():
                            continue
                    # Remove from the list
                    network.remove(template)
            finally:
                _statsLock.release()        
        
        # Trigger an event to allow other modules to perform final config setup
        triggerEvent(session_id, "revisionPrepared", outputDir=outputDir)

        # Commit if neceesary and no template/host errors occured
        rv = {"revision":None}
        if commit and not (hasError or hasTemplateError):
            rv = session.commit()
        # All done
        _statsLock.acquire()
        try:
            _templateStats[statsKey]["finished"] = time.time()
            _templateStats[statsKey]["revision"] = rv["revision"]
            d = _templateStats[statsKey]["finished"] - \
                    _templateStats[statsKey]["initiated"]
            if hasError:
                _templateStats[statsKey]["error"] = "host"
            elif hasTemplateError:
                _templateStats[statsKey]["error"] = "template"
        finally:
            _statsLock.release()
            log_info("Template generation completed in %0.3f seconds for %s" % \
                (d, statsKey))  
    except:
        info = sys.exc_info()
        log_error("Error processing templates", info)
        _statsLock.acquire()
        _templateStats[statsKey]["error"] = ''.join(traceback.format_exception( \
            *info)[-1:]).strip().replace('\n',': ')
        _templateStats[statsKey]["finished"] = 1
        _templateStats[statsKey]["generating"] = 0
        _statsLock.release()
        session.rollback()
    
    return True

def processHostTemplates(statsKey, outputDir, hostTemplates, hostData, 
        networkData):
    """Runs in a thread and generates the output files for the template"""
    global _templateStats, _statsLock, _threadLimit
    host_id = -1
    host = "unknown"
    
    # It is imperative that we release the semaphore before returning from
    # this function or we could potentially starve the calling thread of 
    # workers and we'd end up in a deadlock situation!
    try:
        # Work out the host_id and host_name of this host
        host_id = hostData["host_id"]
        host = hostData["host_name"]
        hostPath = "%s/hosts/%s" % (outputDir, host)
        start = time.time()
        log_debug("Started host generation thread for %s" % host)
        session = getSessionE(networkData["session_id"])
        ct = threading.currentThread()
        ct.setName("%s: processHostTemplates %s" % (session.username, host))
        
        # Retrieve the list of templates to generate and flag the start 
        _statsLock.acquire()
        try:
            planned = _templateStats[statsKey]["planned"]
            generated = _templateStats[statsKey]["generated"]["hosts"]
            generated[host] = {}
            generated[host]["initiated"] = start
            generated[host]["finished"] = 0
            generated[host]["error"] = ""
        finally:
            _statsLock.release()

        # Now that we have a set of templates to use do the actual generation
        hadError = False
        for tname in planned["hosts"][host]:
            try:
                tstart = time.time()
                # Instantiate a template
                template = hostTemplates[tname]
                t = eval("template.%s()" % template.templateName)
                # Is it enabled on this host?
                if not t.enabledOnHost(networkData["session_id"], host_id):
                    continue
                # Set up the variables we want to substitute in
                t._searchList = [hostData, networkData]
                # Generate the file
                filename = "%s/%s" % (hostPath, template.fileName)
                files = t.writeTemplate(filename, template.multiFile)
                tend = time.time()
                # Set properties
                format = getattr(t, "highlightFormat", "")
                if format != "":
                    for file in files:
                        session.revision.propset(file, "ccs:format", format)
                # Record how long the file took to generate
                _statsLock.acquire()
                try:
                    info = {"time":tend-tstart, "error":""}
                    generated[host][tname] = info
                finally:
                    _statsLock.release()
            except:
                (type, value, tb) = sys.exc_info()
                # Single template errors can be skipped over, nothing will
                # get committed unless the user explicitly approves
                _statsLock.acquire()
                try:
                    
                    info = {"time":0, "error":value}
                    generated[host][tname] = info
                finally:
                    _statsLock.release()
                hadError = True
                log_error("Failed to process template (%s) for host: %s" % \
                        (tname, host), (type, value, tb))
        
        # Clean up
        end = time.time()
        log_debug("Completed host generation for %s in %0.3f seconds" % \
                (host, (end-start)))
        _statsLock.acquire()
        try:
            generated[host]["finished"] = end
            # If a template failed make a note of it here
            if hadError:
                generated[host]["error"] = "template"
        finally:
            _statsLock.release()
    except:
        (type, value, tb) = sys.exc_info()
        # Record the error for display to the user
        _statsLock.acquire()
        try:
            generated = _templateStats[statsKey]["generated"]["hosts"]
            if host not in generated.keys():
                generated[host] = {}
                generated[host]["initiated"] = 0
            generated[host]["finished"] = time.time()
            generated[host]["error"] = value
        finally:
            _statsLock.release()
        # Log the error for the administrators record
        log_error("Exception while processing host templates (%s)!" % \
                host, (type, value, tb))
    
    # Release the semaphore
    _threadLimit.release()
    return

def processNetworkTemplate(statsKey, outputDir, networkTemplates, 
        template_id, networkData):
    """Runs in a thread and generates the output files for the template"""
    global _templateStats, _statsLock, _threadLimit
    
    # It is imperative that we release the semaphore before returning from
    # this function or we could potentially starve the calling thread of 
    # workers and we'd end up in a deadlock situation!
    try:
        log_debug("Started template generation thread for %s" % template_id)
        tstart = time.time()
        session = getSessionE(networkData["session_id"])
        ct = threading.currentThread()
        ct.setName("%s: processNetworkTemplates %s" % \
                (session.username, template_id))
        # Instantiate a template
        template = networkTemplates[template_id]
        t = eval("template.%s()" % template.templateName)
        # Is it enabled?
        if not t.enabledOnNetwork(networkData["session_id"]):
            _statsLock.acquire()
            try:
                skipped = _templateStats[statsKey]["skipped"]["network"]
                skipped[template_id] = True
            finally:
                _statsLock.release()
            _threadLimit.release()
            return
        # Set up the variables we want to substitute in
        t._searchList = [networkData]
        # Generate the file
        filename = "%s/%s" % (outputDir, template.fileName)
        files = t.writeTemplate(filename, template.multiFile)
        tend = time.time()
        # Set properties
        format = getattr(template, "highlightFormat", "")
        if format != "":
            for file in files:
                session.revision.propset(file, "ccs:format", format)
        # Record how long the file took to generate
        _statsLock.acquire()
        try:
            generated = _templateStats[statsKey]["generated"]["network"]
            info = {"time":tend-tstart, "error":""}
            generated[template_id] = info
        finally:
            _statsLock.release()
        log_debug("Completed template generation for %s in %0.3f seconds" \
                % (template_id, (tend-tstart)))
    except:
        (type, value, tb) = sys.exc_info()
        # Skip over the error, nothing will get committed unless the user
        # explicitly approves
        _statsLock.acquire()
        try:
            generated = _templateStats[statsKey]["generated"]["network"]
            info = {"time":0, "error":value}
            generated[template_id] = info
        finally:
            _statsLock.release()
        log_error("Failed to process network template (%s)" % template_id, \
                (type, value, tb))
    
    # Release the semaphore
    _threadLimit.release()
    return

#####################################################################
# Template Mixin
#####################################################################
class ccs_template(Template):
    """Config System Template Processor
    
    All templates that expect to be processed by the configuration system
    must derive from this class. It provides helper functions that are required
    to determine where and when each template should be generated and how to
    store it to disk. 
    """

    def __init__(self):
        """Initialise the class

        You must call this method from your subclass
        """
        # Call Cheetah's init
        Template.__init__(self)

    def writeTemplate(self, filename, multiFile):
        """Writes the template output to the specified file"""
       
        files = []
        
        # Ensure the output directory exists
        ensureDirExists(os.path.dirname(filename))

        # Get the template contents
        self._CHEETAH__searchList += self._searchList
        template = self.writeBody().strip()
        if not template.endswith("\n"): template += "\n"

        # Write it out to a file
        if not multiFile:
            f = open(filename, "w")
            f.write(template)
            f.close()
            files.append(filename)
        else:
            # Handle templates that generate multiple output files
            lines = template.split("\n")
            f = None
            for line in lines:
                if line.startswith(".newfile"):
                    # New file starting, close previous file
                    if f is not None: f.close()
                    # Open new file
                    parts = line.split(" ")
                    if len(parts) != 2:
                        raise ccs_template_error("Invalid multifile template!")
                    fname = "%s%s" % (filename, parts[1])
                    f = open(fname, "w")
                    files.append(fname)
                    continue
                elif f is not None:
                    # Write the line out
                    f.write("%s\n" % line)
            # Close the file
            if f is not None: f.close()  

        return files

    def __str__(self):
        return self.writeBody()
    
    def enabledOnHost(self, session_id, host_id):
        """Returns true if the template is applicable to the specified host

        By default this method looks to see if the template has defined a 
        serviceName parameter. If it has then the function checks to see if
        that service is enabled on the specified host. If it is not the 
        function returns False. 
        
        This function may be overriden by other classes/templates if you want
        to implement more logic than the default implementation provides.
        """
        serviceName = getattr(self, "serviceName", None)
        if serviceName is None:
            return True

        from crcnetd.modules.ccs_host import ccs_host
        host = ccs_host(session_id, host_id)
        return host.hasServiceEnabledByName(serviceName)

    def enabledOnNetwork(self, session_id):
        """Returns true if the template is able to be processed

        By default this method looks to see if the template has defined a 
        serviceName parameter. If it has then the function checks to see if
        that service is enabled. If it is not the function returns False. 
        
        This function may be overriden by other classes/templates if you want
        to implement more logic than the default implementation provides.
        """
        serviceName = getattr(self, "serviceName", None)
        if serviceName is None:
            return True

        try:
            service = getServiceInstance(session_id, serviceName)
        except ccs_service_error:
            # Named service not known
            return False
        return service.getState()

    def getTemplateVariables(self):
        """Returns a dictionary of variables that can be used by the template

        The dictionary is passed to Cheetah's searchList so that it's entries
        can be used as placeholders in the template.

        This function retains an empty list. You should override this in your
        implementing class.
        """
        return []

#####################################################################
# Functions to maintain / deal with hosts
#####################################################################
def getCfengineHostStatus(session_id, host):
    """Returns a dictionary describing the state of the host configuration"""

    status = {}
    
    # Check keys exist
    revision = ccs_revision(checkout=False)
    
    sshkeydir = "inputs/sshkeys/%s" % host["host_name"]
    cfkeydir = "ppkeys"
    
    # SSH keys
    status["ssh_key_status"] = STATUS_OK
    status["ssh_key_text"] = ""
    for key in ["dsa", "rsa"]:
        if not revision.fileExists("%s/ssh_host_%s_key" % (sshkeydir, key)):
            status["ssh_key_status"] = STATUS_CRITICAL
            status["ssh_key_text"] += "%s private key missing, " % \
                    key.upper()
        if not revision.fileExists("%s/ssh_host_%s_key.pub" % \
                (sshkeydir, key)):
            status["ssh_key_status"] = STATUS_CRITICAL
            status["ssh_key_text"] += "%s private key missing, " % \
                    key.upper()
    if status["ssh_key_text"]!="":
        status["ssh_key_text"]  = status["ssh_key_text"][:-2]
    
    # Cfengine keys
    status["cfengine_key_status"] = STATUS_OK
    status["cfengine_key_text"] = ""
    if not revision.fileExists("%s/root-%s.priv" % \
            (cfkeydir, host["ip_address"])):
        status["cfengine_key_status"] = STATUS_CRITICAL
        status["cfengine_key_text"] += "CFengine private key missing"
    if not revision.fileExists("%s/root-%s.pub" % \
            (cfkeydir, host["ip_address"])):
        status["cfengine_key_status"] = STATUS_CRITICAL
        if status["cfengine_key_text"]!="": status["cfengine_key_text"]+=", "
        status["cfengine_key_text"] += "CFengine public key missing"

    return status
    
@catchEvent("hostAdded")
def hostAddedCB(eventName, host_id, session_id, **params):
    """Callback function to setup host configuration upon host creation"""

    session = getSession(session_id)
    if session is None:
        return

    # Create keys for the host
    createSSHHostKeys(session_id, host_id)
    createCfengineHostKeys(session_id, host_id)

@catchEvent("hostRemoved")
def hostRemovedCB(eventName, host_id, session_id, **params):
    """Callback function to remoce host configuration upon host deletion"""
    from crcnetd.modules.ccs_host import ccs_host 
    session = getSessionE(session_id)
    host = ccs_host(session_id, host_id)
    
    # Check for existing changeset
    commit = 0
    if session.changeset == 0:
        session.begin("Removing configuration and keys for deleted host: %s" %
                (host["host_name"]))
        commit = 1

    try:
        # Remove SSH Keys
        base = "%s/sshkeys" % session.revision.getConfigBase()
        client.svn_client_delete(["%s/%s" % (base, host["host_name"])], True, 
                session.revision.ctx, session.revision.pool)
        
        # Remove CFengine Keys
        base = "%s/ppkeys" % session.revision.getWorkingDir()
        client.svn_client_delete(["%s/root-%s.priv" % 
            (base, host["ip_address"])], True, session.revision.ctx, 
            session.revision.pool)
        client.svn_client_delete(["%s/root-%s.pub" % 
            (base, host["ip_address"])], True, session.revision.ctx, 
            session.revision.pool)
        
        # Remove Configuration
        base = "%s/hosts" % session.revision.getConfigBase()
        client.svn_client_delete(["%s/%s" % (base, host["host_name"])], True,
                session.revision.ctx, session.revision.pool)
    except:
        log_error("Failed to remove all configuration/keys for %s!" % 
                host["host_name"], sys.exc_info())
    
    # Commit changeset if necessary
    if commit==1:
        session.commit()
        
    return True

catchEvent("hostnameChanged")
def hostnameChangedCB(eventName, host_id, session_id, **params):
    from crcnetd.modules.ccs_host import ccs_host 
    session = getSessionE(session_id)
    host = ccs_host(session_id, host_id)

    old_name = params["old_name"]
    
    # Check for existing changeset
    commit = 0
    if session.changeset == 0:
        session.begin("Moved SSH keys due to host rename from %s => %s" % 
                (old_name, host["host_name"]))
        commit = 1

    try:
        base = "%s/sshkeys" % session.revision.getConfigBase()
        ensureDirExists("%s/%s" % (base, host["host_name"]))
        session.revision._checkForModified(base)
        for key in ["dsa", "rsa"]:
            session.revision.copy("%s/%s/ssh_host_%s_key" % 
                    (base, old_name, key), "%s/%s/ssh_host_%s_key" %
                    (base, host["host_name"], key))
            session.revision.copy("%s/%s/ssh_host_%s_key.pub" % 
                    (base, old_name, key), "%s/%s/ssh_host_%s_key.pub" % 
                    (base, host["host_name"], key))
        client.svn_client_delete(["%s/%s" % (base, old_name)], True, 
                session.revision.ctx, session.revision.pool)
    except:
        (type, value, tb) = sys.exc_info()
        log_error("Failed to move SSH keys for %s! - %s" % \
                (host["host_name"], value))
        # Rollback any changes
        if commit == 1:
            session.rollback()
        return False
    
    # Commit changeset if necessary
    if commit==1:
        session.commit()
        
    return True

@catchEvent("hostIPChanged")
def hostIPChangedCB(eventName, host_id, session_id, **params):
    from crcnetd.modules.ccs_host import ccs_host 
    session = getSessionE(session_id)
    host = ccs_host(session_id, host_id)

    old_ip = params["old_ip"]
    
    # Check for existing changeset
    commit = 0
    if session.changeset == 0:
        session.begin("Moved CFengine keys due to host ip change %s => %s" % 
                (old_ip, host["ip_address"]))
        commit = 1

    try:
        base = session.revision.getWorkingDir()
        session.revision.copy("%s/ppkeys/root-%s.priv" % (base, old_ip), 
                "%s/ppkeys/root-%s.priv" % (base, host["ip_address"]))
        session.revision.copy("%s/ppkeys/root-%s.pub" % (base, old_ip), 
                "%s/ppkeys/root-%s.pub" % (base, host["ip_address"]))
        client.svn_client_delete(["%s/ppkeys/root-%s.priv" % (base, old_ip), \
                "%s/ppkeys/root-%s.pub" % (base, old_ip)], True, 
                session.revision.ctx, session.revision.pool)
    except:
        (type, value, tb) = sys.exc_info()
        log_error("Failed to move CFengine keys for %s! - %s" % \
                (host["host_name"], value))
        # Rollback any changes
        if commit == 1:
            session.rollback()
        return False
    
    # Commit changeset if necessary
    if commit==1:
        session.commit()
        
    return True

@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def createSSHHostKeys(session_id, host_id):
    """Creates a set of SSH keys for the specified host"""
    from crcnetd.modules.ccs_host import ccs_host 
    session = getSessionE(session_id)
    
    host = ccs_host(session_id, host_id)
    
    # Check for existing changeset
    commit = 0
    if session.changeset == 0:
        session.begin("Created SSH keys for %s" % host["host_name"])
        commit = 1
   
    try:
        # Determine directories to store things in
        revdir = session.revision.getConfigBase()
        sshkeydir = "%s/sshkeys/%s" % (revdir, host["host_name"])
        ensureDirExists(sshkeydir)
        
        # Generate the keys
        genSSHKey(sshkeydir, "rsa")
        genSSHKey(sshkeydir, "dsa")    
    except:
        (type, value, tb) = sys.exc_info()
        log_error("Failed to generate SSH keys for %s! - %s" % \
                (host["host_name"], value))
        # Rollback any changes
        if commit == 1:
            session.rollback()
        return False

    # Commit changeset if necessary
    if commit==1:
        session.commit()
        
    return True

@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def createCfengineHostKeys(session_id, host_id):
    """Creates a set of Cfengine keys for the specified host"""
    from crcnetd.modules.ccs_host import ccs_host 
    session = getSessionE(session_id)
    
    host = ccs_host(session_id, host_id)
    
    # Check for existing changeset
    commit = 0
    if session.changeset == 0:
        session.begin("Created CFengine keys for %s" % host["host_name"])
        commit = 1
   
    try:
        # Determine directories to store things in
        workdir = session.revision.getWorkingDir()
        cfkeydir = "%s/ppkeys" % (workdir)
        ensureDirExists(cfkeydir)
        
        # Generate the keys
        genCfKey(cfkeydir, host["ip_address"])
    except:
        (type, value, tb) = sys.exc_info()
        log_error("Failed to generate CFengine keys for %s! - %s" % \
                (host["host_name"], value))
        # Rollback any changes
        if commit == 1:
            session.rollback()
        return False

    # Commit changeset if necessary
    if commit==1:
        session.commit()
        
    return True

def genSSHKey(dir, type):
    """Generates a SSH host key of the specified type

    dir specifies the directory to place the key in
    """
    filename = "ssh_host_%s_key" % type
    key = "%s/%s" % (dir, filename)
    pubkey = "%s.pub" % key
    
    # Try and avoid needless recreating keys
    if os.path.exists(key) and os.path.exists(pubkey):
        log_debug("Skipping SSH key creation in %s. " \
                "Keys already exist!" % dir)
        return
    try:
        os.remove(key)
        os.remove(pubkey)
    except:
        pass
        
    fh = os.popen("cd %s &>/dev/null && /usr/bin/ssh-keygen -q -f %s " \
            "-N '' -t %s || echo \"unable to access %s\"" % \
            (dir, filename, type, dir))
    output = fh.readlines()
    rv = fh.close()
    if rv != None or (len(output)>0 and output[0].startswith("unable")):
        raise ccs_cfengine_error("Could not create SSH %s host key: %s" % \
                (type, "".join(output)))
    
def genCfKey(dir, host_ip):
    """Generates a Cfengine host key pair

    dir specifies the directory to place the key in
    """
    filename = "root-%s" % host_ip
    key = "%s/%s.priv" % (dir, filename)
    pubkey = "%s/%s.pub" % (dir, filename)

    # Try and avoid needless recreating keys
    if os.path.exists(key) and os.path.exists(pubkey):
        log_debug("Skipping Cfengine key creation in %s. " \
                "Keys already exist!" % dir)
        return
    try:
        os.remove(key)
        os.remove(pubkey)
    except:
        pass

    fh = os.popen("cd %s &>/dev/null && /usr/sbin/cfkey -f %s || echo " \
            "\"unable to access %s\"" % (dir, filename, dir))
    output = fh.readlines()
    rv = fh.close()
    if rv != None or (len(output)>0 and output[0].startswith("unable")):
        raise ccs_cfengine_error("Could not create CFengine host key: %s" % \
                "".join(output))
    
def checkCfengineKeys():
    """Ensures that CFengine keys for the server exist"""
    session = getSessionE(ADMIN_SESSION_ID)
    
    # Check for existing changeset
    commit = 0
    if session.changeset == 0:
        session.begin("Creating CFengine policy server keys")
        commit = 1
   
    policy_ip = getIP(config_get_required("network", "server_name"))

    try:
        # Determine directories to store things in
        workdir = session.revision.getWorkingDir()
        cfkeydir = "%s/ppkeys" % (workdir)
        ensureDirExists(cfkeydir)
        
        # Check if the policy server keys exist
        key = "%s/root-%s" % (cfkeydir, policy_ip)
        if not os.path.exists("%s.pub" % key) or \
                not os.path.exists("%s.priv" % key):
            # Generate the keys
            genCfKey(cfkeydir, policy_ip)
            log_info("Created CFengine keys for policy server (%s)" % \
                    policy_ip)

        # Check if the policy server keys are linked to localhost
        if not os.path.exists("%s/localhost.pub" % cfkeydir) or \
                not os.path.exists("%s/localhost.priv" % cfkeydir):
            # Copy policy server keys to here, using shutil rather than 
            # svn as the policy server keys may have been created above
            # and not checked in yet.
            shutil.copy("%s.pub" % key, 
                    "%s/localhost.pub" % cfkeydir)
            shutil.copy("%s.priv" % key, 
                    "%s/localhost.priv" % cfkeydir)
            log_info("Copied CFengine policy server keys for localhost")

    except:
        log_error("Failed to setup CFengine keys for policy server", 
                sys.exc_info())
        # Rollback any changes
        if commit == 1:
            session.rollback()
        return False

    # Commit changeset if necessary
    if commit==1:
        session.commit()
        
    return True

def getActiveRevision(hostname=None):
    """Returns the active revision for the cfengine input directory 

    If a hostname is specified it looks in the hosts/<hostname> directory 
    specifically
    """
    global _cfInputDir

    if hostname is None:
        dir = _cfInputDir
    else:
        dir = "%s/hosts/%s" % (_cfInputDir, hostname)

    # Get the revision number of the checked out revision
    try:
        contents = open("%s/ccs-revision" % dir, "r").read()
        return int(contents.strip())
    except: 
        log_debug("Could not read ccs-revision", sys.exc_info())
        pass
    
    # No checked out revision
    return -1

def getGeneratedRevision(hostname=None):
    """Returns the latest revision that has been generated

    If a hostname is specified it looks in the hosts/<hostname> directory
    specifically
    """
    
    if hostname is None:
        dir = ""
    else:
        dir = "inputs/hosts/%s" % hostname
    
    revision = ccs_revision(checkout=False)
    return revision.getYoungestRevision(dir)

@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR)
def getCfRunLogs(session_id):
    """Returns the output of the last cfrun execution for all active hosts"""
    from crcnetd.modules.ccs_host import getHostList, getHostID
    from crcnetd.modules.ccs_status import getHostStatus, ccs_status_error, \
            ccs_host_status
    global _cfBaseDir, _cfrunStatus
    
    hosts = {}
    
    outputDir = "%s/outputs" % _cfBaseDir
    domain = config_get_required("network", "domain")

    # Get a list of active hosts
    for host in getHostList(session_id):
        # Skip hosts that are disabled
        if not host["host_active"]:
            continue
        # Store enabled hosts
        hostname = host["host_name"]
        hosts[hostname] = host
        # Retrieve the information about it
        filename = "%s/%s.%s" % (outputDir, host["host_name"], domain)
        hosts[hostname]["last_run"] = -1
        hosts[hostname]["age"] = ""
        hosts[hostname]["age_rounded"] = ""
        hosts[hostname]["contents"] = []
        hosts[hostname]["no_lines"] = 0
        try:
            hostStatus = getHostStatus(hostname)
        except ccs_status_error:
            # Create a blank status entry
            host_id = getHostID(ADMIN_SESSION_ID, hostname)
            hostStatus = ccs_host_status(ADMIN_SESSION_ID, host_id)
        hosts[hostname]["active_rev"] = hostStatus.activeRevision
        hosts[hostname]["generated_rev"] = hostStatus.generatedRevision
        hosts[hostname]["operating_rev_status"] = \
                hostStatus.operatingRevisionStatus
        hosts[hostname]["operating_rev_text"] = \
                hostStatus.operatingRevisionText
        hosts[hostname]["operating_rev_hint"] = \
                hostStatus.operatingRevisionHint
        if hostStatus.infoUpdatedAt > 0:
            hosts[hostname]["operating_rev"] = int(hostStatus.operatingRevision)
            try:
                o = int(hosts[hostname]["operating_rev"])
                a = int(hosts[hostname]["active_rev"])
                g = int(hosts[hostname]["generated_rev"])
                if o > g:
                    hosts[hostname]["operating_rev_status"] = "critical"
                    hosts[hostname]["operating_rev_text"] = "Invalid Revision"
                    hosts[hostname]["operating_rev_hint"] = "The operating " \
                            "revision is greater than the newest generated " \
                            "revision!"
                elif o != a:
                    hosts[hostname]["operating_rev_status"] = "warning"
                    hosts[hostname]["operating_rev_text"] = ""
                    hosts[hostname]["operating_rev_hint"] = "The operating " \
                            "revision does not match the desired active " \
                            "revision!"                   
            except: pass
        else:
            hosts[hostname]["operating_rev"] = ""
        if hostname in _cfrunStatus.keys():
            hosts[hostname]["run_status"] = _cfrunStatus[hostname]["status"]
            hosts[hostname]["run_age"] = time.strftime("%d/%m/%Y %H:%M:%S", \
                    time.localtime(_cfrunStatus[hostname]["time"]))
            hosts[hostname]["run_age_rounded"] = roundTime(time.time() - \
                    _cfrunStatus[hostname]["time"])
        else:
            hosts[hostname]["run_status"] = ""
            hosts[hostname]["run_age"] = ""
            hosts[hostname]["run_age_rounded"] = ""
        hosts[hostname]["error"] = ""
        if not os.path.exists(filename):
            # No cfrun output for this host
            continue
        try:
            stat = os.stat("%s/%s.%s" % (outputDir, host["host_name"], domain))
            hosts[hostname]["age"] = time.strftime("%d/%m/%Y %H:%M:%S", \
                    time.localtime(stat[ST_MTIME]))
            hosts[hostname]["age_rounded"] = roundTime(time.time() - \
                    stat[ST_MTIME])
            hosts[hostname]["last_run"] = stat[ST_MTIME]
            hosts[hostname]["contents"] = open(filename).read()
            hosts[hostname]["no_lines"] = \
                    len(hosts[hostname]["contents"].split("\n"))
        except:
            (type, value, tb) = sys.exc_info()
            log_error("Failed to retrieve CfRun log for %s" % hostname, \
                    (type, value, tb))
            hosts[hostname]["error"] = value
            continue

    # Return it
    return hosts

@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def pushConfig(session_id, hosts, params=[]):
    """Initiates a cfrun instance to push a new config out to a host"""
    global _threadLimit, _cfrunStatus, _cfrunLock

    # PHP sends in an associative array we want the values only
    hosts = hosts.values()

    # Loop through the specified hosts and mark them as pending
    _cfrunLock.acquire()
    try:
        try:
            for host in hosts:
                _cfrunStatus[host] = {"status":"pending","time":time.time()}
        except:
            log_error("Exception setting up config push!", sys.exc_info())
            raise ccs_cfengine_error("Could not initiate config push!")
    finally:
        _cfrunLock.release()
    
    # Start the threads
    initThread(startCfRunThreads, hosts, params)
    return True

def startCfRunThreads(hosts, params):

    # Loop through the hosts and start threads to do the cfrun stuff
    for host in hosts:
        _threadLimit.acquire()
        try:
            initThread(doCfrun, host, params)
        except:
            log_error("Failed to start cfrun instance for host: %s!" % \
                    host, sys.exc_info())
            _threadLimit.release()
    return True

def doCfrun(host_name, params=[]):
    """Executes a cfrun instance to update the specified host

    This function expects to be called in a thread and will take care of 
    releasing the semaphore when it finishes.
    """
    global _threadLimit, _cfrunStatus, _cfrunLock, _cfBaseDir
    
    outputDir = "%s/outputs" % _cfBaseDir
    domain = config_get_required("network", "domain")
    cmdline = ""
    filename = ""
    
    # Make sure that any errors are captured so that we can't exit without 
    # releasing the semaphore
    try:
        # Record that this host is being processed
        _cfrunLock.acquire()
        try:
            if host_name in _cfrunStatus.keys():
                if _cfrunStatus[host_name]["status"] != "pending":
                    # This host is already being processed!
                    _threadLimit.release()
                    return
            _cfrunStatus[host_name] = {"status":"running","time":time.time()}
        finally:
            _cfrunLock.release()
        # Ouput filename
        filename = "%s/%s.%s" % (outputDir, host_name, domain)
        try:
            os.unlink(filename)
        except:
            log_warn("Could not remove old logfile before cfrun! - %s" % \
                    filename, sys.exc_info())
        # Build the command line 
        cmdline = "/usr/sbin/cfrun %s" % host_name
        if len(params) > 0:
            cmdline += " -- "
            for i,param in params.items(): cmdline += "%s " % param
        # Execute the command
        fp = os.popen(cmdline, "r")
        output = fp.read().strip()
        rv = fp.close()
        if rv is not None:
            code="failed"
        else:
            code="succeeded"
        # Retrieve the actual cfrun output
        try:
            contents = open(filename, "r").read()
        except:
            log_warn("Could not read logfile from cfrun! - %s" % filename, \
                    sys.exc_info())
            contents = ""
        # Prepend the output from the execution to the log
        fp = open(filename, "w")
        fp.write("%s\n" % ("*"*80))
        fp.write("Command execution %s!\n" % code)
        fp.write("Cmdline: %s\n" % cmdline)
        if len(output) > 0:
                fp.write("\n%s\n" % output)
        fp.write("%s\n\n" % ("*"*80))
        fp.write(contents)
        fp.close()
        # Record that this host is no longer being processed
        _cfrunLock.acquire()
        try:
            del _cfrunStatus[host_name]
        finally:
            _cfrunLock.release()
    except:
        (type, value, tb) = sys.exc_info()
        # Record that this host is no longer being processed
        _cfrunLock.acquire()
        try:
            del _cfrunStatus[host_name]
        finally:
            _cfrunLock.release()
        # Record an error in the log file
        if filename != "":
            try:
                try:
                    contents = open(filename, "r").read()
                except:
                    log_warn("Could not read logfile from cfrun! - %s" % \
                            filename, sys.exc_info())
                    contents = ""
                fp = open(filename, "w")
                fp.write("%s\n" % ("*"*80))
                fp.write("Command execution failed!\n")
                fp.write("Cmdline: %s\n" % cmdline)
                fp.write("Error: %s\n" % value)
                fp.write("%s\n\n" % ("*"*80))
                fp.write(contents)
                fp.close()
            except: pass
        log_error("Failed to initiate cfrun for host: %s" % host_name, \
                (type, value, tb))
    
    # Release the semaphore
    _threadLimit.release()
    return

#####################################################################
# Functions to maintain / deal with checked out Cfengine configs
#####################################################################
@catchEvent("revisionCreated")
def updateCfInputsCB(eventName, host_id, session_id, **kwargs):
    """Callback function to trigger updates when revisions are created"""
    
    autoupdate = int(config_get("cfengine", "autoupdate", "0"))
    if autoupdate:
        updateCfInputs(session_id)
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def updateCfInputs(session_id, revNum=-1):
    """Updates the cfengine input directory.

    Triggered explicitly by user or on the revisionCreated hook.
    """
    global _cfBaseDir
    
    # Update the inputs directory
    irev = updateSVNDirectory("%s/inputs" % ccs_revision.svnroot, 
            "%s/inputs" % _cfBaseDir, revNum)
    # Update the ppkeys directory
    prev = updateSVNDirectory("%s/ppkeys" % ccs_revision.svnroot, 
            "%s/ppkeys" % _cfBaseDir, revNum)
    if irev != prev:
        status = "%s/%s" % (irev, prev)
    else:
        status = irev

    # Update the revision information files
    log_command("%(b)s/inputs/update-revisioninfo \"%(b)s/inputs\"" % \
            {"b":_cfBaseDir})

    log_info("Updated cfengine configuration to revision %s" % status)

    return True

def updateSVNDirectory(svnroot, path, revNum=-1):
    """Ensures that the specified path contains the specified revision from 
    svnroot checked out in it
    """
    
    # Get a python memory pool and context to use
    pool = core.svn_pool_create(None)
    ctx = client.svn_client_ctx_t()
    ctx.config = core.svn_config_get_config(None, pool)
    
    # Work out which revision to update to
    rev = core.svn_opt_revision_t()
    if revNum == -1:
        rev.kind = core.svn_opt_revision_head
    else:
        rev.kind = core.svn_opt_revision_number
        rev.value.number = int(revNum)

    # See if there is a checked out revision 
    gotrev = 0
    try:
        list = client.svn_client_ls(path, rev, False, ctx, pool)
        gotrev = 1
    except:
        log_error("Unable to access cfengine base checkout!")
        raise ccs_cfengine_error("Cannot access cfengine base checkout!")
    
    if gotrev:
        # Update the directory
        nrev = client.svn_client_update(path, rev, True, ctx, pool)
    else:
        # Checkout the directory
        nrev = client.svn_client_checkout(svnroot, path, rev, True, ctx, pool)
    
    # Get rid of the pool
    core.svn_pool_destroy(pool)
    del pool
    del ctx

    return nrev

#####################################################################
# Functions to support the web based configuration browser
#####################################################################
@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR)
def viewConfigAtPath(session_id, path, revno=None, order=None, direction=0, \
        doMarkup=True):
    """Returns the configurations present at the specified path in the repo
    
    If the path is a directory you get a directory listing back
    If the path is a file you get the file contents back along with other 
    metadata.

    If the revno parameter is set the configuration is shown as it existed
    in the specified revision. If the revno parameter is None then the 
    current (HEAD) revision is shown. 
    
    The order parameter may be used to specify a parameter and order to sort
    the list that is returned. Valid parameters are name, size and date. Order
    may be 1 for descending or 0 for ascending.
    
    Unless the markup parameter is set to false the contents of the file will
    be processed through enscript and HTML will be returned. 
    """

    items = {}
    
    revision = ccs_revision(checkout=False)
    path = path.replace("//","/")
    
    (revno, entries) = revision.ls(path, revno)
    if revno == -1:
        # An error occured
        raise ccs_cfengine_error("Could not retrieve config at path: %s" % \
                path)
    for entry in entries:
        entry["path"] = entry["name"]
        entry["name"] = os.path.basename(entry["name"])
        # python-subversion bindings don't seem to have this bug
        #if entry["path"].find("%s/" % entry["name"]) != -1:
        #    # psyvn bug, filename is duplicated 
        #    entry["path"] = entry["path"][:-(len(entry["name"])+1)]
        if entry["path"].startswith(revision.svnroot):
            entry["path"] = entry["path"][len(revision.svnroot)+1:]
        entry["age"] = time.strftime("%d/%m/%Y %H:%M:%S", \
                time.localtime(entry["time"]))
        entry["age_rounded"] = roundTime(time.time() - entry["time"])
        entry["kind_desc"] = KIND_MAP[entry["kind"]]

    # Sort if necessary
    if order is not None and order != "":
        direction = int(direction)
        if order not in ["name", "size", "date"]:
            raise ccs_cfengine_error("Invalid order parameter: %s" % order)
        if direction != 0 and direction != 1:
            raise ccs_cfengine_error("Invalid direction parameter: %s" % \
                    direction)
        if order == "date": 
            order="time"
            direction += 1
        if direction == 1:
            entries.sort(lambda x,y: cmp(x[order], y[order])*-1)
        else:
            entries.sort(lambda x,y: cmp(x[order], y[order]))

    # Return now if there are multiple files or no files
    if len(entries) == 0 or len(entries) > 1:
        return [revno, entries]
    # or a single directory
    if entries[0]["kind"] == KIND_DIR:
        return [revno, entries]

    # Single file, does it match the path we were given?
    if entries[0]["path"] == path:
        # Get the contents
        file = revision.getFile(path)
        props = revision.getProps(path)
        entries[0]["props"] = props
        if doMarkup:
            if "ccs:format" in props.keys():
                entries[0]["contents"] = markup(file, props["ccs:format"])
            else:
                entries[0]["contents"] = markup(file)

    return [revno, entries]

def markup(file, format="sh"):
    """Passes the file through enscript for syntax highlighting"""
    
    # Generate the command line to pass to enscript
    cmdline = config_get("cfengine", "enscript_path", "enscript")
    cmdline += ' --color -h -q --language=html -p - -E' + format
    log_debug("Enscript command line: %s" % cmdline)
    
    # Run enscript
    (fdi, fdo) = os.popen2(cmdline)
    fdi.write(file)
    fdi.close()
    odata = fdo.read()
    rv = fdo.close()
    if rv is not None:
        log_warn("Could not run enscript to markup file!")
        log_debug(odata)
        return file.split("\n")

    # Strip header and footer
    i = odata.find('<PRE>')
    beg = i > 0 and i + 6
    i = odata.rfind('</PRE>')
    end = i > 0 and i or len(odata)
    odata = EnscriptDeuglifier().format(odata[beg:end])
    return odata.splitlines()

# Enscript Deuglifier code from Trac
# 
# Copyright (C) 2003-2006 Edgewall Software
# All rights reserved.
#
# Licensed using the Modified BSD license
class EnscriptDeuglifier(object):
    def __new__(cls):
        self = object.__new__(cls)
        if not hasattr(cls, '_compiled_rules'):
            cls._compiled_rules = re.compile('(?:'+'|'.join(cls.rules())+')')
        self._compiled_rules = cls._compiled_rules
        return self
    
    def format(self, indata):
        return re.sub(self._compiled_rules, self.replace, indata)

    def replace(self, fullmatch):
        for mtype, match in fullmatch.groupdict().items():
            if match:
                if mtype == 'font':
                    return '<span>'
                elif mtype == 'endfont':
                    return '</span>'
                return '<span class="code-%s">' % mtype
    
    def rules(cls):
        return [
            r'(?P<comment><FONT COLOR="#B22222">)',
            r'(?P<keyword><FONT COLOR="#5F9EA0">)',
            r'(?P<type><FONT COLOR="#228B22">)',
            r'(?P<string><FONT COLOR="#BC8F8F">)',
            r'(?P<func><FONT COLOR="#0000FF">)',
            r'(?P<prep><FONT COLOR="#B8860B">)',
            r'(?P<lang><FONT COLOR="#A020F0">)',
            r'(?P<var><FONT COLOR="#DA70D6">)',
            r'(?P<font><FONT.*?>)',
            r'(?P<endfont></FONT>)'
        ]
    rules = classmethod(rules)

#####################################################################
# Cfengine Resource Server 
#####################################################################
class cfserver(resource.Resource):
    """Implements a simple webserver to retrieve resources related to cfengine

    Called when the main server receives a query for /cfengine/*

    Currently supports the following resources
    /cfengine/update.conf/<host_name>
        Retrieves an update.conf file for the specified host
    /cfkey/keyname
        Retrieves the specified cfengine key
        
    Requests to this resource are restricted to the IP address ranges
    specified in the allow_requests_from configuration directive.
    """
    
    resourceName = "CFengine Resource Server"

    # Mark as leaf so that render gets called
    isLeaf = 1
    
    def render(self, request):

        # XXX: Verify request IP
        
        log_debug("Received cfengine request for %s" % request.path)
        
        parts = request.path.split("/")
        path = "/".join(parts[2:])
        
        # Process request
        if path.startswith("update.conf"):
            return self.getUpdateConf(path, request)
        elif path.startswith("cfkey"):
            return self.getCfkey(path, request)
        elif path.startswith("hostvars"):
            return self.getHostvars(path, request)
        else:
            request.setResponseCode(404, "Unknown cfengine resource requested!")
            request.finish()
            return server.NOT_DONE_YET

    def getCfkey(self, path, request):
        """Returns the contents of a cfengine key for the specified host."""
        
        parts = path.split("/")
        
        # Get a revision to grab the key from
        revision = ccs_revision()
        keydir = "%s/ppkeys" % revision.getWorkingDir()
        
        # Retrieve the requested key
        keyfile = "%s/%s" % (keydir, parts[1])

        try:
            fd = open(keyfile, "r")
            content = fd.readlines()
            fd.close()
        except:
            log_warn("Could not open Cfengine key file!", sys.exc_info())
            request.setResponseCode(404, "Unknown cfengine key requested!")
            request.finish()
            return server.NOT_DONE_YET

        return "".join(content)

    def getUpdateConf(self, path, request):
        """Returns the contents of an update.conf file for the specified host.

        Currently the host parameter is ignored.
        """
        
        # Get a revision to grab the update.conf from
        revision = ccs_revision()
        revdir = revision.getConfigBase()
        
        try:
            fd = open("%s/cfconf/update.conf" % revdir, "r")
        except:
            request.setResponseCode(503, "update.conf unavailable. Please " \
                    "try again later")
            request.finish()
            return server.NOT_DONE_YET
        
        contents = fd.readlines()
        fd.close()
        
        return "".join(contents)
    
    def getHostvars(self, path, request):
        """Returns the contents of an update.conf file for the specified host.

        Currently the host parameter is ignored.
        """
        
        parts = path.split("/")
        if len(parts)<2:
            request.setResponseCode(404, "Hostname not specified" % host)
            request.finish()
            return server.NOT_DONE_YET
        host = parts[1]
        
        # Get a revision to grab the hostvars file from
        revision = ccs_revision()
        revdir = revision.getConfigBase()
        
        try:
            fd = open("%s/hosts/%s/cf.hostvars" % (revdir, host), "r")
        except:
            request.setResponseCode(404, "%s hostvars not found!" % host)
            request.finish()
            return server.NOT_DONE_YET
        
        contents = fd.readlines()
        fd.close()
        
        return "".join(contents)
    
#####################################################################
# Revision Class 
#####################################################################       
class ccs_revision:
    """Wrapper for a revision of files.
    
    This class wraps the generation of an entire revision of the configuration
    files managed by this system.
    
    It contains the methods needed to generate the files, insert them into
    version control (svn) and then update then pass the resulting revision 
    identifier back to it's caller. 
    """

    # Location of the svnroot
    svnroot = None
    
    def __init__(self, parentSession=None, changeset=None, checkout=True):
        """Creates a ccs_revision class.

        If parentSession or changeset are not specified or None, a read-only
        revision is created. This is only useful if you want to inspect the
        repository without making any changes.
        """
        
        self.mParentSession = parentSession
        self.mChangeset = changeset
        self.checkout = checkout
        self.pendingProps = {}
        self.lock = threading.RLock()
        self._revinfocache = {}
        self._needsCommit = False

        # Get a python memory pool and context to use
        self.pool = core.svn_pool_create(None)
        self.ctx = client.svn_client_ctx_t()
        self.ctx.config = core.svn_config_get_config(None, self.pool)
        
        if self.checkout:
            # Setup a working directory for this revision
            self.rDir = mkdtemp("", "ccsd")
        
            # Checkout the current configuration HEAD to this directory
            rev = core.svn_opt_revision_t()
            rev.kind = core.svn_opt_revision_head
            client.svn_client_checkout(self.svnroot, self.rDir, rev, \
                    True, self.ctx, self.pool)
            self.mCurRev = rev
            
            # Check basic repository structure
            if self.mParentSession is not None and self.mChangeset is not None:
                self.checkRepoStructure()
        else:
            self.rDir = None
            self.mCurRev = None

        # Start with no errors
        self.mErrors = {}
        
    def __del__(self):
        
        # Nothing to check if nothing was checked out
        if self.rDir is None:
            core.svn_pool_destroy(self.pool)
            self.pool = None
            self.ctx = None
            return

        # Don't check the status of a read-only revision
        if self.mParentSession is None or self.mChangeset is None:
            removeDir(self.rDir)
            core.svn_pool_destroy(self.pool)
            self.pool = None
            self.ctx = None
            return
        
        # Callback function to process status information
        def status_cb(epath, entry):
            try:
                if entry.text_status == wc.svn_wc_status_ignored:
                    pass
                elif entry.text_status != wc.svn_wc_status_normal:
                    log_debug("Changes (%s) to %s in changeset %s will " \
                            "be lost" % \
                            (entry.text_status, epath, self.mChangeset))
            except:
                log_error("Failed to check status of %s" % epath, \
                        sys.exc_info())
        
        # Check the status
        self.flag = False
        self.lock.acquire()
        try:
            client.svn_client_status(self.rDir, self.mCurRev, status_cb, \
                    True, True, False, False, self.ctx, self.pool)
        finally:
            self.lock.release()
        
        # Clean up the working directory
        removeDir(self.rDir)
        core.svn_pool_destroy(self.pool)
        self.pool = None
        self.ctx = None

    def getWorkingDir(self):
        """Returns the path that the repository is checked out into"""

        return self.rDir
    
    def getConfigBase(self):
        """Returns the path that cfengine config files should live in"""
        if self.rDir is None:
            return None
        return "%s/inputs" % self.rDir
    
    def _getFsPtr(self):
        # Strip scheme from URL
        path = self.svnroot[self.svnroot.find("://")+3:]
        rep = repos.svn_repos_open(path, self.pool)
        fs_ptr = repos.svn_repos_fs(rep)
        return fs_ptr
    
    def _checkForModified(self, cDir, recursed=False):
        """Performs svn actions on changed files in the specified directory"""
        # Nothing to check if no repository is checked out
        if self.rDir is None:
            return 
        
        # Don't check the status of a read-only revision
        if self.mParentSession is None or self.mChangeset is None:
            log_warn("Cannot check status on a read-only revision!")
            return
        
        if not recursed:
            self._needsCommit = False

        # Recurse through if we were passed a list
        if type(cDir) == type([]):
            for d in cDir:
                self._checkForModified(d)
            return

        self.lock.acquire()
        try:
            # Callback function to process status information
            def status_cb(epath, entry):
                # Check the text of the entry
                if entry.text_status == wc.svn_wc_status_unversioned:
                    if epath.startswith(self.rDir):
                        ename = epath[len(self.rDir)+1:]
                    log_debug("Added %s in changeset %s" % \
                            (ename, self.mChangeset))
                    client.svn_client_add(epath, False, self.ctx, self.pool)
                    self._needsCommit = True
                    # Recurse if we added a directory
                    if os.path.isdir(epath):
                        self._checkForModified(epath)
                    else:
                        # Ensure the date property is set on files
                        self.propset(epath, "svn:keywords", "Date")
                        # Check if there are any other pending properties to
                        # set
                        path = epath 
                        if path in self.pendingProps.keys():
                            for prop,value in self.pendingProps[path].items():
                                self.propset(path, prop, value, False)
                elif entry.text_status == wc.svn_wc_status_modified or \
                        entry.text_status == wc.svn_wc_status_added or \
                        entry.text_status == wc.svn_wc_status_deleted or \
                        entry.text_status == wc.svn_wc_status_replaced or \
                        entry.text_status == wc.svn_wc_status_merged:
                    self._needsCommit = True
                elif entry.text_status == wc.svn_wc_status_ignored:
                    # Ignore it!
                    pass
                elif entry.text_status != wc.svn_wc_status_normal:
                    log_debug("%s (%s) has bad state in changeset %s!" % \
                            (epath, entry.text_status, self.mChangeset))
                # Now look at the properties of the entry
                if entry.prop_status == wc.svn_wc_status_modified or \
                        entry.prop_status == wc.svn_wc_status_added or \
                        entry.prop_status == wc.svn_wc_status_deleted or \
                        entry.prop_status == wc.svn_wc_status_replaced or \
                        entry.prop_status == wc.svn_wc_status_merged:
                    self._needsCommit = True
                # Ensure that ccs-revision files are always ignored
                if os.path.isdir(epath):
                    if not self.hasIgnore(epath, "ccs-revision"):
                        self.propadd(epath, "svn:ignore", "ccs-revision")
                        self._needsCommit = True

            # Check the status
            client.svn_client_status(cDir, self.mCurRev, status_cb, \
                    True, True, False, False, self.ctx, self.pool)
        finally:
            self.lock.release()
        
    def propadd(self, path, prop, value, canDefer=True, sep="\n"):
        """Adds the specified value to the property on the specified path"""
        
        # Use the svn repo directly if nothing is checked out
        if self.rDir is None:
            base = self.svnroot
        else:
            base = self.rDir
                
        try:
            if not path.startswith(base):
                filename = "%s/%s" % (base, path)
            else:
                filename = path
            filename = filename.rstrip("/")
            self.lock.acquire()
            try:
                rev = core.svn_opt_revision_t()
                rev.kind = core.svn_opt_revision_head
                eprop = client.svn_client_propget(prop, filename, rev, False, \
                        self.ctx, self.pool)
                if eprop == {}:
                    # No existing property set
                    self.propset(path, prop, value, canDefer)
                else:
                    
                    existing = str(eprop.values()[0]).strip()
                    self.propset(path, prop, \
                            "%s%s%s" % (existing, sep, value), canDefer)
            finally:
                self.lock.release()
        except:
            log_error("Could not add '%s' to %s on %s" % \
                    (value, prop, filename), sys.exc_info())

    def propset(self, path, prop, value, canDefer=True):
        """Sets the specified property on the specified path"""
        
        if self.mParentSession is None or self.mChangeset is None:
            raise ccs_revision_error("Cannot set property on read-only " \
                    "revision")
        
        # Use the svn repo directly if nothing is checked out
        if self.rDir is None:
            base = self.svnroot
        else:
            base = self.rDir
                
        try:
            if not path.startswith(base):
                filename = "%s/%s" % (base, path)
            else:
                filename = path
            filename = filename.rstrip("/")
            self.lock.acquire()
            try:
                client.svn_client_propset(prop, value, filename, False, \
                        self.pool)
            finally:
                self.lock.release()
        except core.SubversionException:
            # Add to a list of pending properties that we'll try and set on
            # commit after adding the file. This covers the case where a
            # caller tries to set a property on an as yet unversioned file
            if filename in self.pendingProps.keys():
                self.pendingProps[filename][prop] = value
            else:
                self.pendingProps[filename] = {prop:value}
            log_debug("Deferred propset on %s" % filename, sys.exc_info())
        except:
            log_error("Could not set %s to '%s' on %s" % \
                    (prop, value, filename), sys.exc_info())

    @registerEvent("revisionCreated")
    def checkin(self, message, paths=None):
        """Checks in the changes to the repository with the specified message"""
        if self.rDir is None:
            raise ccs_revision_error("Cannot checkin. Not checked out!")
        
        if self.mParentSession is None or self.mChangeset is None:
            raise ccs_revision_error("Cannot checkin a read-only revision")
        
        # Default to the whole repository
        if paths is None:
            paths = [self.rDir]
        if type(paths) != type([]):
            paths = [paths]
        
        # Check status of working directory and add / del files etc
        self._checkForModified(paths)
        if not self._needsCommit:
            # Nothing changed
            return -1
        
        try:
            self.lock.acquire()
            try:
                # Run cleanup on any directories in the set to clear locks
                # Our lock above ensures that there should be no legitimate
                # WC locks at this point
                for path in paths:
                    if not os.path.isdir(path): continue
                    client.svn_client_cleanup(path, self.ctx, self.pool)
                # Commit
                i = client.svn_client_commit(paths, False, self.ctx, self.pool)
                if i.revision < 0:
                    return -1
                n = self.saveRevProps(i.revision, message)
            finally:
                self.lock.release()
        except:
            log_error("Could not commit revision", sys.exc_info())
            return -1

        if n<0:
            # Nothing changed
            return -1
        
        if self.mParentSession:
            triggerEvent(self.mParentSession.session_id, "revisionCreated", \
                    revision_no=n)
        log_info("Committed revision %s to version control" % i.revision)

        return n

    def saveRevProps(self, r, message=""):
        """Saves customised properties against each revision

        These properties are used to help keep track of how the database/svn 
        repository changes match up.
        """
        
        if r is None:
            # Nothing changed
            return -1
        
        rev = core.svn_opt_revision_t()
        rev.kind = core.svn_opt_revision_number
        rev.value.number = int(r)
        
        # Set the log message if specified
        if message != "":
            try:
                self.lock.acquire()
                try:
                    client.svn_client_revprop_set("svn:log", message, \
                            self.svnroot, rev, False, self.ctx, self.pool)
                finally:
                    self.lock.release()
            except:
                (type, value, tb) = sys.exc_info()
                log_warn("Could not set log property on revision %s - %s" % \
                        (r, value), (type, value, tb))
        
        # Set the author property on the checkin
        try:
            self.lock.acquire()
            try:
                client.svn_client_revprop_set("svn:author", \
                        str(self.mParentSession.username), self.svnroot, rev, \
                        False, self.ctx, self.pool)
            finally:
                self.lock.release()
        except:
            (type, value, tb) = sys.exc_info()
            log_warn("Could not set author property on revision %s - %s" % \
                    (r, value), (type, value, tb))
        
        # Record the changeset that triggered this revision
        try:
            self.lock.acquire()
            try:
                client.svn_client_revprop_set("ccs:changeset", "%s" % \
                        self.mChangeset, self.svnroot, rev, \
                        False, self.ctx, self.pool)
            finally:
                self.lock.release()
        except:
            (type, value, tb) = sys.exc_info()
            log_warn("Could not set changeset property on " \
                    "revision %s - %s" % (r, value), (type, value, tb))

        return r
    
    def fileExists(self, path):
        """Checks if the specified file exists in the repository"""
        
        # Use the svn repo directly if nothing is checked out
        if self.rDir is None:
            base = self.svnroot
        else:
            base = self.rDir
                
        try:
            if not path.startswith(base):
                filename = "%s/%s" % (base, path)
            else:
                filename = path
            filename = filename.rstrip("/")
            self.lock.acquire()
            try:
                rev = core.svn_opt_revision_t()
                rev.kind = core.svn_opt_revision_head
                e = client.svn_client_ls(filename, rev, False, \
                        self.ctx, self.pool)
            finally:
                self.lock.release()
            if len(e) > 0:
                return True
        except core.SubversionException:
            (type, value, tb) = sys.exc_info()
            if value[0].find("non-existent") == -1:
                log_warn("Failed to check existance of file: %s" % filename, \
                        (type, value, tb))
            return False
        except:
            log_warn("Failed to check existance of file: %s" % filename, \
                    sys.exc_info())
            return False
        
        return False
    
    def revinfo(self, revno):
        if revno in self._revinfocache.keys():
            return self._revinfocache[revno]
        
        self.lock.acquire()
        try:
            rev = core.svn_opt_revision_t()
            rev.kind = core.svn_opt_revision_number
            rev.value.number = int(revno)
            props = client.svn_client_revprop_list(self.svnroot, rev, \
                    self.ctx, self.pool)
        finally:
            self.lock.release()
        if len(props) != 2:
            return {}
        info = {}
        info["number"] = props[1]
        for prop,value in props[0].items():
            info[prop.strip("svn:")] = str(value)
        self._revinfocache[revno] = info
        return info
    
    def copy(self, oldpath, newpath):
        """Moves the specified file from the oldpath to the newpath"""

        # Use the svn repo directly if nothing is checked out
        if self.rDir is None:
            base = self.svnroot
        else:
            base = self.rDir
                
        try:
            if not oldpath.startswith(base):
                oldname = "%s/%s" % (base, oldpath)
            else:
                oldname = oldpath
            if not newpath.startswith(base):
                newname = "%s/%s" % (base, newpath)
            else:
                newname = newpath
            oldname = oldname.rstrip("/")
            newname = newname.rstrip("/")
            self.lock.acquire()
            try:
                rev = core.svn_opt_revision_t()
                rev.kind = core.svn_opt_revision_head
                e = client.svn_client_copy(oldname, rev, newname, \
                        self.ctx, self.pool)
            finally:
                self.lock.release()
            return True
        except:
            log_warn("Could not move file: %s => %s" % (oldpath, newpath), 
                    sys.exc_info())
        
        return False
        
    def ls(self, path, revno=None):
        """Returns a list of entries in the specified directory"""
        
        # Use the svn repo directly if nothing is checked out
        if self.rDir is None:
            base = self.svnroot
        else:
            base = self.rDir
                
        try:
            if not path.startswith(base):
                filename = "%s/%s" % (base, path)
            else:
                filename = path
            filename = filename.rstrip("/")
            self.lock.acquire()
            try:
                if revno is None or revno=="":
                    rev = core.svn_opt_revision_t()
                    rev.kind = core.svn_opt_revision_head
                else:
                    rev = core.svn_opt_revision_t()
                    rev.kind = core.svn_opt_revision_number
                    rev.value.number = int(revno)
                e = client.svn_client_ls(filename, rev, False, self.ctx, \
                        self.pool)
            finally:
                self.lock.release()
            if len(e) > 0:
                if revno is None:
                    revno = self.getYoungestRevision()
                entries = []
                for entry,details in e.items():
                    t = {}
                    if path.endswith(entry):
                        t["name"] = "%s/%s" % (os.path.dirname(path), entry)
                    else:
                        t["name"] = "%s/%s" % (path, entry)
                    t["created_rev"] = self.revinfo(details.created_rev)
                    t["kind"] = details.kind
                    t["last_author"] = details.last_author
                    t["size"] = details.size
                    t["time"] = details.time/1000000
                    entries.append(t)
                return (revno, entries)
        except:
            log_warn("Could not list directory: %s" % filename, sys.exc_info())
        
        return (-1, [])
        
    def getYoungestRevision(self, path=""):
        """Returns the number of the youngest revision in the repository"""
        revno = -1
        
        try:
            self.lock.acquire()
            try:
                # Strip scheme from URL
                fs_ptr = self._getFsPtr()
                revno = fs.youngest_rev(fs_ptr, self.pool)      
            finally:
                self.lock.release()
        except:
            log_warn("Could not determine youngest revision", sys.exc_info())

        return revno
    
    def getLog(self, revno):
        """Returns the log message for the specified revision"""
        log = ""
        
        def rcvMessage(a,b,c,d,msg,f):
            log = msg.strip()
        
        try:
            self.lock.acquire()
            try:
                rev = core.svn_opt_revision_t()
                rev.kind = core.svn_opt_revision_number
                rev.value.number = int(revno)
                client.svn_client_log([self.svnroot], rev, rev, False, \
                        False, nmsg, self.ctx, self.pool)
            finally:
                self.lock.release()
        except:
            log_warn("Could not retrieve log for revision %s" % revno, \
                    sys.exc_info())

        return log
    
    def getFile(self, path, revno=None):
        """Returns the contents of the file at the specified path and rev"""
        
        # Use the svn repo directly if nothing is checked out
        if self.rDir is None:
            base = self.svnroot
        else:
            base = self.rDir
                
        try:
            if path.startswith(base):
                filename = path[len(base)+1:]
            else:
                filename = path
            filename = filename.rstrip("/")
            self.lock.acquire()
            try:
                if revno is None or revno=="":
                    revno = self.getYoungestRevision()
                else:
                    revno = int(revno)
                fs_ptr = self._getFsPtr()
                root = fs.revision_root(fs_ptr, revno, self.pool)
                s = core.Stream(fs.file_contents(root, filename, self.pool))
                contents = s.read()
            finally:
                self.lock.release()
            return contents
        except:
            log_warn("Could not retrieve file: %s" % filename, sys.exc_info())
        
        return ""

    def getProps(self, path, revno=None):
        """Returns the properties set on the specified file"""
        
        # Use the svn repo directly if nothing is checked out
        if self.rDir is None:
            base = self.svnroot
        else:
            base = self.rDir
                
        try:
            if not path.startswith(base):
                filename = "%s/%s" % (base, path)
            else:
                filename = path
            filename = filename.rstrip("/")
            self.lock.acquire()
            try:
                if revno is None or revno=="":
                    rev = core.svn_opt_revision_t()
                    rev.kind = core.svn_opt_revision_head
                else:
                    rev = core.svn_opt_revision_t()
                    rev.kind = core.svn_opt_revision_number
                    rev.value.number = int(revno)
                contents = client.svn_client_proplist(filename, rev, \
                        False, self.ctx, self.pool)
            finally:
                self.lock.release()
            if len(contents) > 0:
                props = {}
                for prop,value in contents[0][1].items():
                    props[prop] = str(value)
                return props
        except:
            log_warn("Could not retrieve properties: %s" % \
                    filename, sys.exc_info())
        
        return {}

    def hasIgnore(self, path, value):
        """Checks whether the specified ignore value is set on the path"""
        try:
            props = client.svn_client_proplist(path, self.mCurRev, \
                    False, self.ctx, self.pool)
        except:
            return False
        if len(props)<1:
            return False
        
        (path, pdict) = props[0]
        if "svn:ignore" not in pdict.keys():
            return False
        if str(pdict["svn:ignore"]).find(value) == -1:
            return False
        
        return True

    def checkRepoStructure(self):
        """Checks the repository has all the required base directories. 

        If a base directory is not present it is created. The base directories
        are:
        inputs/        Host/Service configuration files

        Further hierarchy within each base directory is the responsibility of 
        other modules.
        """
        
        if self.rDir is None:
            raise ccs_revision_error("Cannot check repository structure. " \
                    "Not checked out!")
        
        if self.mParentSession is None or self.mChangeset is None:
            log_warn("Cannot check repository structure on a read-only " \
                    "revision")
            return
        
        flag = 0
        
        configsDir = self.getConfigBase()
        n = ensureDirExists(configsDir)
        self.lock.acquire()
        try:
            if n > 0:
                # Schedule Additions
                bDir = configsDir
                while n>1:
                    bDir = os.path.dirname(configsDir)
                    n-=1
                log_info("Created configuration directory (%s) within " \
                        "repository" % configsDir)
                client.svn_client_add(bDir, False, self.ctx, self.pool)
                flag = 1
            
            # Commit directory changes immediately
            if flag==1:
                self.checkin("checkRepoStructure created missing directories")
                #i = client.svn_client_commit([self.rDir], False, self.ctx, \
                #        self.pool)
                #self.saveRevProps(i.revision, \
                #        "checkRepoStructure created missing directories")
        finally:
            self.lock.release()

        # Check for the script that updates the ccs-revision files 
        filename = "%s/update-revisioninfo" % configsDir
        docreate=False
        doupdate=False
        if not os.path.exists(filename):
            docreate=True
        else:
            contents = file(filename, "r").read()
            if contents.find("svn info") == -1:
                doupdate = True
        if docreate or doupdate:
            self.lock.acquire()
            try:
                # Create the script
                fp = open(filename, "w")
                fp.write("""#!/bin/bash
echo "Updating version information"
for d in `find $1 -type d | grep -v ".svn" | xargs`; do
    version=`svn info $d/* | grep "Last Changed Rev" | awk '{print $4}' | sort -nr | head -n1`
    echo "  $d -> $version"
    echo "$version" > $d/ccs-revision
done
# vim:set sw=4 ts=4 sts=4 et:
""")
                fp.close()
                if docreate:
                    client.svn_client_add(filename, False, self.ctx, self.pool)
                    action = "Created"
                else:
                    action = "Updated"
                i = client.svn_client_commit([self.rDir], False, self.ctx, \
                        self.pool)
                self.saveRevProps(i.revision, \
                        "%s update-revisioninfo script" % action)
            finally:
                self.lock.release()

def validateRepository(svnroot):
    """Checks for the existance of a valid svn repository at svnroot"""

    # Extract the path from the URL
    svnpath = svnroot[svnroot.find("://")+3:]

    # Check directory exists
    if not os.path.exists(svnpath):
        log_debug("Specified repository path does not exist: %s" % svnpath)
        return False
   
    # Check it looks a bit like a subversion repository
    fp = open("%s/README.txt" % svnpath, "r")
    if not fp:
        log_debug("No README.txt inside repository: %s" % svnpath)
        return False
    tmp = fp.read().strip()
    fp.close()
    if not tmp.startswith("This is a Subversion repository"):
        log_debug("invalid README.txt in repository: %s" % svnpath)       
        return False

    # Final, master check, can we check it out, instantiate a revision class
    revision = ccs_revision(None, None, True)
    del revision

    # All OK
    return True

def createRepository(svnroot):
    """Initialises a blank repository and configures it for use by ccsd"""

    # Look for the svnadmin utility
    fd = os.popen("/usr/bin/which svnadmin 2>/dev/null")
    path = fd.read().strip()
    if fd.close() != None:
        log_error("Cannot find svnadmin utility.")
        return False
    
    # Check we can execute the svnadmin utilty
    if not os.access(path, os.X_OK):
        log_error("Cannot execute svnadmin utility.")
        return False

    # Try and create the repository
    svnpath = svnroot[svnroot.find("://")+3:]
    fd = os.popen("%s create --fs-type fsfs %s 2>&1" % (path, svnpath))
    result = fd.read().strip()
    if fd.close() != None:
        log_error("svnadmin create failed. See tb log for more details.")
        log_tb(None, result)
        return False
    
    # Add a pre-revprop-change hook to allow the daemon to set author
    # revision properties
    hook = "%s/hooks/pre-revprop-change" % svnpath
    fd = open(hook, "w")
    if not fd:
        log_warning("Unable to setup pre-revprop-change hook in new " \
                "repository!")
    else:
        fd.write("""#!/bin/bash

# PRE-REVPROP-CHANGE HOOK

# Created by the CRCnet Configuration System Daemon on
# %s

# Allow all changes at this time
exit 0
""" % time.ctime())
        fd.close()
        os.chmod(hook, 0755)

    # Success
    log_info("Subversion repository created at %s" % svnpath)
    return True

#####################################################################
# Cfengine Integration Initialisation
#####################################################################
# Base CFengine paths
_cfBaseDir = ""
_cfInputDir = ""
_svnroot = ""
# Global information about template generation
_templateDir = ""
_templateModDir = ""
_events = {}
_templateStats = {}
_statsLock = None
# Global information about cfrun instances
_cfrunStatus = {}
_cfrunLock = None
# Semaphore to control how many threads we initiate
_threadLimit = None

def initCFengine():
    global _templateDir, _templateModDir
    global _events, _cfBaseDir, _cfInputDir, _svnroot, _statsLock, _threadLimit
    global _cfrunLock

    # Retrieve template directory configuration
    _templateDir = config_get("cfengine", "template_dir")
    if _templateDir == None or _templateDir == "":
        log_fatal("Invalid template directory (%s)!" % _templateDir)
    _templateModDir = config_get("cfengine", "template_module_dir")
    if _templateModDir == None or _templateModDir == "":
        log_fatal("Invalid template module directory (%s)!" % _templateModDir)

    # Retrieve cfengine configuration file directory configuration
    _cfBaseDir = config_get("cfengine", "cfbase_dir")
    if _cfBaseDir == None or _cfBaseDir == "":
        log_fatal("Invalid cfengine base directory (%s)!" % _cfBaseDir)
    _cfInputDir = "%s/inputs" % _cfBaseDir

    # Decide where the svn root is 
    _svnroot = config_get("cfengine", "config_svnroot")     
    if _svnroot == None or _svnroot == "":
        log_fatal("Configuration Data subversion repository not specified!")
    # Check that the svnroot is a valid svn URL
    if _svnroot.find("://")==-1:
        log_fatal("Invalid svnroot URL: %s" % _svnroot)   
    # Let the revision class know where to get its data from
    ccs_revision.svnroot = _svnroot
    # Validate the repository and create it if it doesn't exist
    if not validateRepository(_svnroot):
        log_warn("No svn repository at specified path. Attempting " \
                "to create one.")
        if not createRepository(_svnroot):
            log_fatal("Could not create repository at %s" % _svnroot)
    
    # Initialise the statistics lock
    _statsLock = threading.Lock()

    # Initialise the cfrun lock
    _cfrunLock = threading.Lock()
    
    # How many template generation threads are we allowed to run at a time
    maxThreads = config_getint("cfengine", "max_template_threads", 
            DEFAULT_MAX_TEMPLATE_THREADS)
    _threadLimit = threading.Semaphore(maxThreads)
    
    # Ensure that CFengine keys exists for this server
    checkCfengineKeys()

    # Register Cfengine Resource Server
    registerResource("cfengine", cfserver)
