#!/usr/bin/env python
#
# crcnetd - CRCnet Configuration System Daemon - Small Web Server
#
# Provides the server that forms the primary interface to the CRCnet
# Configuration System Daemon. This is a smaller version of the main server
# provided in ccsd_server.py. This version uses asyncore rather than twisted 
# and is intended for use on small installations like biscuit PCs.
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# Copyright (C) 2005  The University of Waikato 
#
# crcnetd is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# crcnetd is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more 
# details.
#
# You should have received a copy of the GNU General Public License along with
# crcnetd; if not, write to the Free Software Foundation, Inc., 59 Temple 
# Place, Suite 330, Boston, MA 02111-1307 USA 
import os
import os.path
import inspect
import base64
import crypt
from BaseHTTPServer import BaseHTTPRequestHandler
import asyncore
import socket
import thread

from ccsd_common import *
from ccsd_log import *
from ccsd_config import config_get
from ccsd_events import *

class ccs_server_error(ccsd_error):
    pass

# Is the server running?
server_running = False
recurring = {}

#####################################################################
# Webserver Helper Functions
#####################################################################
def registerResource(path, res_class, **kwargs):
    """Function to register a resource at the specified path
    
    """
    raise ccs_server_error("Cannot register resources with this server")

def registerRecurring(interval):
    """Decorator to register a function that is called at regular intervals
    
    interval should be specified in seconds
    """
    global recurring
    
    def decorator(func):
        # Store the recurrance interval as a function attribute
        func._interval = interval
        
        newTime = time.time() + interval
        recurring[newTime] = func
        return func
    
    return decorator

def registerPage(path, force=False, requireSSL=False, requireAuth=False, \
        realm=None):
    """Decorator to register a page to respond to a URL"""
   
    if not path.startswith("/"):
        raise ccs_server_error("Path must start with /!")
    
    if path in CCSDHandler.pages.keys() and not force:
        raise ccs_server_error("Handler already registered for path: %s" \
                % path)
   
    def decorator(func):
        func.requireSSL = requireSSL
        func.requireAuth = requireAuth
        func.realm = realm
        CCSDHandler.pages[path] = func
        return func

    return decorator
    
def registerDir(path, file, overwrite=False):
    """Register a directory to be sent in response to a URL
    
    Any files in this directory will be served
    """
    
    if not path.startswith("/"):
        raise ccs_server_error("Path must start with /!")
    
    if path in CCSDHandler.dirs.keys() and not overwrite:
        raise ccs_server_error("Directory already registered for path: %s" \
                % path)
    
    CCSDHandler.dirs[path] = file

    return lambda f:f
        
def registerRealm(name, data, overwrite=False):
    """Register an authentication realm containing user/passwords"""

    if name in CCSDHandler.realms.keys() and not overwrite:
        raise ccs_server_error("Realm '%s' already registered!" % name)

    data["cookies"] = {}
    CCSDHandler.realms[name] = data

    return lambda f:f

def initThread(func, *args, **kwargs):
    """Calls the specified function in a new thread"""
    thread.start_new_thread(func, *args, **kwargs)

# Create an asynchronous HTTP server based on the asyncore module
class AsyncHTTPServer(asyncore.dispatcher):
    def __init__(self, address, handler, *args, **kw):
        self.server = CCSHTTPServer(address, handler)
        asyncore.dispatcher.__init__(self, self.server.socket)
    def handle_read(self):
        self.server.handle_request()

class CCSDHandler(BaseHTTPRequestHandler):

    pages = {}
    dirs = {}
    realms = {}
    
    def __init__(self, request, client_address, server):
        self.cookies = {}
        self.cookie_names = []
        self.username = ""
        # Call base handler
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def hasAuthCookie(self, realm):
        """Checks whether this request specified an auth cookie"""

        cookiename = "cm-auth-%s" % realm
        if cookiename not in self.cookies.keys():
            return ""
        cookiekey = self.cookies[cookiename]
        
        if cookiekey in self.realms[realm]["cookies"].keys():
            cookie = self.realms[realm]["cookies"][cookiekey]
            if cookie["expires"] > time.time():
                self.username = cookie["username"]
                return cookiekey

        del self.cookies[cookiename]
        return ""
        
    def validateAuth(self, realm):
        """Checks whether this request has the necessary authentication"""
        
        # Check if auth data has been posted
        data = self.getPostData()
        if "username" not in data.keys() or "password" not in data.keys():
            # No auth data present
            return ""
        if realm not in self.realms.keys():
            # Invalid realm
            log_warn("Specified realm (%s) not registered" % realm)
            return ""
        
        # Lookup the user in the realm and check the password
        if data["username"] not in self.realms[realm]["users"].keys():
            # Invalid user
            log_info("Failing login to '%s' from invalid user '%s'" % \
                    (realm, data["username"]))
            return ""
        
        # Check the password
        passwd = self.realms[realm]["users"][data["username"]]
        if crypt.crypt(data["password"], passwd) != passwd:
            # Invalid password
            log_info("Failing login to '%s' with bad password for '%s'" % \
                    (realm, data["username"]))
            return ""
        
        # Create an auth cookie 
        cookie = {"username":data["username"], "expires":time.time()+(60*30)}
        cookiekey = base64.b64encode(createPassword(18))
        self.realms[realm]["cookies"][cookiekey] = cookie
        self.username = data["username"]
        
        # Return success
        return cookiekey
    
    def logoutRealm(self, realm):
        """Removes a login cookie from the realm and logs the user out"""

        cookiekey = self.hasAuthCookie(realm)
        if cookiekey == "":
            log_warn("logoutRealm(%s) called when not logged in!" % realm)
            return 

        # Remove cookie from the users browser
        del self.cookies["cm-auth-%s" % realm]
        # Remove our stored cookie
        del self.realms[realm]["cookies"][cookiekey]

    def callHandler(self, func, method):
        fstr = "func(self, method)"
        if func.requireSSL:
            # check for SSL
            pass
        if func.requireAuth:
            if func.realm is None:
                realm = func.func_name
            else:
                realm = func.realm
            if realm not in self.realms.keys():
                log_error("Request for %s unsatisifed. Requires auth from " \
                        "unknown realm '%s'" % (self.path, realm))
                self.send_response(500, "Server error")
                self.end_headers()
                return
            if self.hasAuthCookie(realm) == "":
                cookiestr = ""
                if method=="POST":
                    cookiestr = self.validateAuth(realm)
                if cookiestr != "":
                    # Authenticated OK, set cookie
                    self.cookies["cm-auth-%s" % realm] = cookiestr
                    # Drop back to GET request, we consumed the post
                    method = "GET"
                else:
                    # Need to send auth request
                    func = self.realms[realm]["authenticator"]
                    if "default_username" in self.realms[realm].keys():
                        username = self.realms[realm]["default_username"]
                        fstr = "func(self, method, username)"
        try:
            eval(fstr)
        except:
            log_error("Handler function died unexpectedly!", sys.exc_info())
            self.send_error(500, "Handler function died unexpectedly!")

        return

    def handleRequest(self, method):
        """Looks to see if we know how to handle the path and passes it off"""
        
        # Strip off any queries at store them separately
        idx = self.path.find("?")
        if idx != -1:
            self.query = self.path[idx:]
            self.path = self.path[:idx]
        else:
            self.query = ""

        # Parse Cookies
        self.cookies = {}
        try :
            parts = self.headers.get("Cookie").strip().split(";")
        except:
            # Exception above if no Cookie header
            parts = []
        for part in parts:
            cparts = part.split("=")
            if len(cparts)!=2:
                continue
            self.cookies[cparts[0]] = cparts[1]
        self.cookie_names = self.cookies.keys()
        
        # See if we have an exact match for this page
        if self.path in self.pages.keys():
            # Call the handler function
            func = self.pages[self.path]
            return self.callHandler(func, method)
        dirname = os.path.dirname(self.path)
        if dirname in self.dirs.keys():
            # Try and send the file back
            filename = os.path.basename(self.path)
            data = ""
            try:
                fp = open("%s/%s" % (self.dirs[dirname], filename), "r")
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
        
        # Otherwise tokenise the request and look for the most specific handler
        path = self.path
        while 1:
            (path, file) = os.path.split(path)
            if file == "" or path=="/":
                break
            if path in self.pages.keys():
                # Call the handler function
                func = self.pages[path]
                return self.callHandler(func, method)

        # We don't have a handler for the requested path
        self.send_error(404, "No handler for path: %s" % self.path)
        
    def do_GET(self):
        return self.handleRequest("GET")
    def do_POST(self):
        return self.handleRequest("POST")

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

    def end_headers(self):
        """Ouput any cookies that have been set"""

        # Add new cookies
        if len(self.cookies)>0:
            for name,value in self.cookies.items():
                if name not in self.cookie_names:
                    self.send_header("Set-Cookie", "%s=%s; path=/" % \
                            (name, value))

        # Delete removed cookies
        for name in self.cookie_names:
            if name not in self.cookies.keys():
                self.send_header("Set-Cookie", "%s=; path=/; " \
                        "expires=Wednesday, 09-Nov-99 23:12:40 GMT" % name)

        # Call the base class
        BaseHTTPRequestHandler.end_headers(self)
            
    # No logging for now
    def log_error(self, *args):
        pass
    def log_request(self, code='-', size='-'):
        pass

#####################################################################
# Server Initialisation
#####################################################################
def startCCSDServer(key, cert, cacert):
    """Initialises the CCSD Server.

    This function never returns as it enters a mainloop
    """
    global server_running, recurring

    try:
        # Port and logfile
        port = int(config_get(None, "port", DEFAULT_CLIENT_PORT))
        logfile = config_get(None, "request_log", DEFAULT_REQUEST_LOG)

        # Initialise an HTTP server
        httpd = AsyncHTTPServer(('', port), CCSDHandler)
        log_info("Server Started. Ready to serve requests...")
        server_running = True
    except:
        log_fatal("Could not initialise the server!", sys.exc_info())

    # Start the mainloop
    while server_running:
        try:
            # Check recurring functions to see if they need to be called
            now = time.time()
            for sched_time, func in recurring.items():
                if sched_time <= now:
                    try:
                        func()
                    except:
                        log_error("Unknown error in recurring function!", \
                                sys.exc_info())
                    del recurring[sched_time]
                    newTime = sched_time + func._interval
                    recurring[newTime] = func
            # put in a timeout so we don't monopolise the CPU
            asyncore.poll(30)
        except socket.error:
            # Socket operation died, ignore
            log_error("Socket operation failed! Continuing.", sys.exc_info())
            continue
        except SystemExit:
            # Ignore, server_running will be set to false shortly
            continue
        except:
            # Unknown ERROR
            (etype, value, tb) = sys.exc_info()
            log_error("Unexpected error caught by mainloop! - %s" % value, 
                    (etype, value, tb))

@catchEvent("shutdown")        
def stopCCSDServer(*args, **kwargs):
    """Stops the CCSD Server."""
    global server_running
    if server_running:
        server_running = False
    else:
        sys.exit(1)
