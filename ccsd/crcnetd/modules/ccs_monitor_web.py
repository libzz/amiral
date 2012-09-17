# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# CRCnet Monitor Base Website Functionality
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
import time
import urllib

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_clientserver import registerPage, registerDir, \
        registerRealm
from crcnetd._utils.ccsd_config import config_get, init_pref_store, pref_get, \
        config_getboolean
from crcnetd.version import ccsd_version, ccsd_revision

class ccs_monitor_error(ccsd_error):
    pass

ccs_mod_type = CCSD_CLIENT

DEFAULT_RESOURCE_DIR = "/usr/share/ccsd/resources"
DEFAULT_MOTD_REFRESH = 60 * 60
DEFAULT_MOTD_URL = "http://www.crc.net.nz/motd"
DEFAULT_HELP_EMAIL = "help@crc.net.nz"
DEFAULT_URGENT_DETAILS = """<b>Matt Brown</b><br /><a href="mailto:""" \
        """matt@crc.net.nz">matt@crc.net.nz</a><br />+64 21 611 544""" \
        """<br /><br /><b>Jamie Curtis</b><br /><a href="mailto:""" \
        """jamie@wand.net.nz">jamie@wand.net.nz</a><br />+64 21 392 102"""
DEFAULT_PREF_FILE = "/var/lib/ccsd/preferences"
DEFAULT_ADMIN_PASS = "$1$pbz0c5l4$qPtttsQzkg3BHDQrKoKCK0" # 'admin'

menu = {}
MENU_TOP = "top"
MENU_BOTTOM = "bottom"
MENU_GROUP_HOME = "Ahome"
MENU_GROUP_GENERAL = "general"
MENU_GROUP_CONTACT = "zcontact"

CPE_ADMIN_REALM = "admin"
ADMIN_USERNAME = "admin"

monitor_prefs = None
realm = None

##############################################################################
# Module Helper Functions
##############################################################################
def returnErrorPage(request, message):
    """Displays an error message"""

    output = """<div class="content">
<h2>An Error Occurred!</h2><br />
<br />
<span class="error">%s</span><br /><br /></div>""" % message

    returnPage(request, "Error", output)
    
def returnPage(request, title, content, menuadd=None, scripts=[], styles=[]):
    """Returns a basic HTML page using the default template.

    title   - The desired page title
    content - An HTML blob to populate the content area of the page
    menuadd - An HTML blob to append to the end of the generated menus

    The template must allow substitution of the tokens %TITLE%,
    %CONTENT%, %MENU%, %SCRIPTS%, %STYLES% in the appropriate places.
    """

    # Get the template
    resourcedir = config_get("www", "resourcedir", DEFAULT_RESOURCE_DIR)
    tfile = "%s/page.html" % resourcedir
    try:
        fd = open(tfile, "r")
        template = fd.read()
        fd.close()
    except:
        log_error("Page template not available!", sys.exc_info())
        # Return a very cruddy basic page
        template = "<html><head><title>%TITLE%</title></head>" \
                "<body><h2>Menu</h2><br />%MENU%<br /><hr />" \
                "<h2>%TITLE%</h2><br />%CONTENT%</body></html>"
        
    # Substitute as necessary
    menustr = buildMenu()
    if menuadd is not None:
        menustr += menuadd
    scriptstr = stylestr = ""
    for script in scripts:
        scriptstr += """<script type="text/javascript" src="%s">""" \
                "</script>\n""" % script
    for style in styles:
        stylestr += """<link rel="stylesheet" type="text/css" src="%s""" \
                " />\n""" % style
    footer = "Page generated at: %s" % time.ctime()
    ip = getIfaceIPForIP(request.client_address[0])
    if ip == "":
        ip = request.headers.get("Host").strip()
    host = "http://%s" % ip
    output = template.replace("%SCRIPTS%", scriptstr).replace("%STYLES%", \
            stylestr).replace("%TITLE%", title).replace("%MENU%", \
            menustr).replace("%CONTENT%", content).replace("%FOOTER%", \
            footer).replace("%HOST%", host)
    
    # Send it away
    request.send_response(200)
    request.end_headers()
    request.wfile.write(output)
    request.finish()

def loginForm(request, method, username=""):
    """Request that the user enter their username / password"""
    global users

    # Display the form to get a new password
    output = """<div class="content"><h2>Authentication Required</h2>
<br />
Please enter your username and password below<br />
<br />
<form method="POST" action="%s">
<table>
<tr>
<th width="20%%">Username</th>
<td><input type="input" value="%s" name="username"></td>
</tr>
<tr>
<th width="20%%">Password</th>
<td><input type="password" value="" name="password" id="password"></td>
</tr>
<tr>
<td>&nbsp;</td>
<td><input type="submit" value="Login &gt;&gt;"></td>
</tr>
</table>
""" % (request.path, username)
    if username != "":
        output += """<script type="text/javascript" language="javascript">
$("password").focus();
</script>"""

    returnPage(request, "Authentication Required", output)

def buildMenu():
    """Builds the HTML to display a menu from the registered items"""
    global menu
    
    output = ""
    for tmenu,contents in menu.items():
        output += """<div class="menu">\n"""
        title = contents["title"].replace("%HOSTNAME%", socket.gethostname())
        output += "<h2>%s</h2>\n" % title
        groups = contents["groups"].keys()
        groups.sort()
        for group in groups:
            items = contents["groups"][group]
            output += "<ul>\n"
            for url,caption in items.items():
                if not url.startswith("http://"):
                    url = "%%HOST%%%s" % url
                output += """<li><a href="%s">%s</a></li>\n""" % (url, caption)
            output += "</ul>\n"
        output += "</div><br />\n"
    
    return output
  
def registerMenu(menuName, title, reset=False):
    """Creates a new top level menu"""
    global menu
    
    if menuName in menu.keys():
        if not reset:
            menu[menuName]["title"] = title
            return

    menu[menuName] = {"title":title, "groups":{}}
    
def registerMenuItem(menuName, groupName, url, caption):
    """Register an item to be shown in the menu
    
    This can be called as a normal function or as a decorator.
    """
    global menu
    
    if menuName not in menu.keys():
        registerMenu(menuName, menuName)
    
    tmenu = menu[menuName]
    if groupName not in tmenu["groups"].keys():
        tmenu["groups"][groupName] = {}

    tmenu["groups"][groupName][url] = caption

    menu[menuName] = tmenu

    # Continue on, returning a no-op dcorator
    return lambda f:f

def HTable(data, columns, captions, tableid=""):
    """Creates a horizontal table of the data

    Columns is a list where each entry specifies the index of an item
    to display from the data dictionary.
    Captions specifies a caption for each column
    """
   
    if tableid=="":
         output = "<table>"
    else:
        output = """<table id="%s">""" % tableid
    
    # Output column headers
    output += "<thead>"
    for i in range(0,len(columns)):
        output += "<th>%s</th>" % captions[i]
    output += "</thead><tbody>"
    
    # Handle a dictionary or list of rows
    if type(data) == type({}):
        rows = data.values()
    else:
        rows = data

    # Output table body
    for rdata in rows:
        output += "<tr>"
        for item in columns:
            val = rdata[item]
            if item=="status":
                # Status column, do colouring
                cclass=""" class="status%s" """ % rdata[item].lower()
                if "statusdesc" in rdata:
                    val = rdata["statusdesc"]
            else:
                cclass=""
            output += "<td%s>%s</td>" % (cclass, val)
        output += "</tr>"

    # Finish table
    output += "</tbody></table>"

    return output

def generateSelect(name, value, options):
    """Generates a select box
    
    options should be a dictionary of key:value for the options of the box
    value should be the current value
    name should be the ID the select box should take in the document
    """

    # Convert lists to dictionaries
    if type(options) == type([]):
        o2 = {}
        for opt in options:
            o2[opt] = opt
        options = o2

    output = """<select id="%s" name="%s" value="%s">\n""" % \
        (name, name, value)
    keys = options.keys()
    keys.sort()
    for key in keys:
        label = options[key]
        sel = key == value and " selected" or ""
        output += """<option value="%s"%s>%s</option>\n""" % (key, sel, label)
    output += "</select>\n"

    return output

def getMonitorPrefs():
    global monitor_prefs
    return monitor_prefs

def getRealm():
    global realm
    return realm

##############################################################################
# Initialisation
##############################################################################
def ccs_init():
    global monitor_prefs, realm
    
    registerMenu(MENU_TOP, "%HOSTNAME%")
    registerMenu(MENU_BOTTOM, "External Links")
    registerMenuItem(MENU_TOP, MENU_GROUP_HOME, "/", "CPE Homepage")
    registerMenuItem(MENU_TOP, MENU_GROUP_CONTACT, "/contact", \
            "Contact Details")
    
    # Other modules can override these as necessary in ccs_init
    registerMenuItem(MENU_BOTTOM, MENU_GROUP_GENERAL, \
            "http://www.crc.net.nz/", "CRCnet Homepage")
    registerMenuItem(MENU_BOTTOM, MENU_GROUP_GENERAL, \
            "http://www.google.com/", "Google")

    resourcedir = config_get("www", "resourcedir", DEFAULT_RESOURCE_DIR)
    registerDir("/resources", resourcedir)

    # Initialise preferences store
    preffile = config_get("www", "preferences", DEFAULT_PREF_FILE)
    try:
        ensureFileExists(preffile)
        monitor_prefs = init_pref_store(preffile)
    except:
        log_fatal("Unable to initialise preference store: %s" % preffile, \
                sys.exc_info())

    realm = {"authenticator":loginForm, "users":{}, \
            "default_username":ADMIN_USERNAME}
    adminpass = pref_get(None, "admin_password", monitor_prefs, \
            DEFAULT_ADMIN_PASS)
    realm["users"][ADMIN_USERNAME] = adminpass
    registerRealm(CPE_ADMIN_REALM, realm)

##############################################################################
# Content Pages
##############################################################################
@registerPage("/motd")
def getMOTD(request, method):
    """Returns HTML to display the Message of the Day"""
    
    tmpdir = config_get(None, "tmpdir", DEFAULT_TMPDIR)
    motdFile = "%s/motd" % tmpdir
    motdRefreshInterval = config_get("www", "motd_refresh", \
            DEFAULT_MOTD_REFRESH)
    motdURL = config_get("www", "motdURL", DEFAULT_MOTD_URL)
    fetchMotd = config_getboolean("www", "fetch_motd", False)
    updateNote = ""
    
    try:
        mtime = os.stat(motdFile)[8]
    except:
        mtime = -1

    if (mtime == -1 or time.time()-mtime > motdRefreshInterval or \
            request.query.find("refreshMotd=true") != -1) and fetchMotd:
        # Get new MOTD
        try:
            o = urllib.URLopener()
            o.addheaders = [("User-agent", "crcnet-monitor/%s (r%s)" % \
                    (ccsd_version, ccsd_revision))]
            wfd = o.open(motdURL)
            fd = open(motdFile, "w")
            motd = wfd.read()
            fd.write(motd)
            fd.close
            wfd.close()
            mtime = time.time()
        except:
            log_error("Unable to fetch MOTD", sys.exc_info())
            motd = "Unable to retrieve latest news."
            mtime = -1
    else:
        try:
            fd = open(motdFile, "r")
            motd = fd.read()
            fd.close()
        except:
            motd = "No news available"
        
    # Calculate how long till next update
    if mtime != -1:
        updateAtSecs = (mtime + motdRefreshInterval) - time.time()
        updateAt = formatTime(updateAtSecs)
        retrieved = time.ctime(mtime)
        updateNote = "Retrieved at %s, next update in %s" % (retrieved, updateAt)

    # Generate the output
    output = """<h2>Latest News <span class="note">%s&nbsp;
<a href="/?refreshMotd=true">[Refresh Now]</a>
</span>
</h2><br />
%s
""" % (updateNote, motd.replace("\n", "<br />"))

    length = len(output)
    request.send_response(200)
    request.send_header("Length", length)
    request.end_headers()
    request.wfile.write(output)
    request.finish()
    return

@registerPage("/")
def homepage(request, method):
    
    
    # MOTD at the top
    liveMOTD = config_getboolean("www", "liveMOTD", False)
    homepage = config_get("www", "motdHomepage", "http://www.crc.net.nz")
    if liveMOTD:
        output = """<div class="content" id="motd">"""
        output += "<h2>Loading Latest News...</h2><br />"
        output += "Please wait while the latest news is retrieved."
    else:
        output = """<div class="content">"""
        output += "<h2>Latest News</h2><br />"
        output += "To keep up to date with the latest news "
        output += "please visit the homepage at "
        output += """<a href="%s">%s</a>""" % (homepage, homepage)
    output += "</div>"

    # Try and load the status summary from the status module
    try:
        from crcnetd.modules.ccs_monitor_status import getStatusSummary
        status = getStatusSummary()
    except:
        log_warn("Could not retrieve status summary", sys.exc_info())
        status = "CPE Status not available"
	
    # CPE Status
    output += """<div class="content">
<h2>CPE Status</h2><br />
%s
</div>
""" % status

    returnPage(request, "CPE Navigation", output, 
            scripts=["/resources/homepage.js"])

@registerPage("/contact")
def contactpage(request, method):
    
    output = ""
    
    # Get the template
    resourcedir = config_get("www", "resourcedir", DEFAULT_RESOURCE_DIR)
    tfile = "%s/contact.html" % resourcedir
    try:
        fd = open(tfile, "r")
        details = fd.read()
        fd.close()
    except:
        log_error("Contact HTML not available!", sys.exc_info())
        # Return a very cruddy basic page
        details = "No contact details available!"
        
    output += """<div class="content">%s</div>""" % details

    returnPage(request, "Contact Details", output)

