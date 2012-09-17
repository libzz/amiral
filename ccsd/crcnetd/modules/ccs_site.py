# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Site Module - Provides classes for manipulating physical location records
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

ccs_mod_type = CCSD_SERVER

class ccs_site_error(ccsd_error):
    pass

class ccs_site(ccs_class):
    """Represents a site (physical location) in the Configuration System.
    
    The members of this class loosely map to the fields of the site table
    in the database.
    """
    
    def __init__(self, session_id, site_id):
        """Initialises a new class for a specified site.
        
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
            raise ccs_site_error("Invalid session specified!")
        self._session_id = session_id
        
        # See if the specified site_id id makes sense
        try:
            sql = "SELECT * FROM site WHERE site_id=%s"
            res = session.query(sql, (site_id))
        except:
            raise ccs_site_error("Unable to retrieve site details!")
        
        # Store details 
        self.site_id = site_id
        self._properties = res[0]
                
    @registerEvent("siteModified")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True, "updateSiteDetails")
    def updateDetails(self, newDetails):
        """Updates the details of the site.

        newDetails should be a dictionary containing only those site parameters
        that have changed and need to be updated in the database.

        Returns ccs_site.SUCCESS, If an error occurs details can be retrieved
        through the getErrorMessage method.
        """
        
        session = getSessionE(self._session_id)

        # Check the data
        validateSite(session.session_id, newDetails)
        
        # Build SQL Update string
        props = ["location", "admin_contact_id", "tech_contact_id", \
                "gps_lat", "gps_long", "elevation", "comments"]
        (sql, values) = buildUpdateFromDict("site", props, newDetails, \
                "site_id", self.site_id)
               
        # Run the query
        res = session.execute(sql, values)
            
        # Trigger an Event
        triggerEvent(session.session_id, "siteModified", site_id=self.site_id)

        return self.returnSuccess()
    
    @exportViaXMLRPC(SESSION_RO, AUTH_USER, True, "getSite")
    def getDetails(self):
        """Returns a detailed object describing the site"""
        
        session = getSessionE(self._session_id)

        sql = "SELECT * FROM site_detail WHERE site_id=%s"
        res = session.query(sql, (self.site_id))
        if res == -1:
            return self.returnError("Failed to get site details!")

        return res[0]
    
    @registerEvent("siteRemoved")
    @exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR, True)
    def removeSite(self):
        """Removes the site from the database."""

        session = getSessionE(self._session_id)
        
        # Trigger an Event
        triggerEvent(session.session_id, "siteRemoved", site_id=self.site_id)
    
        # Delete the site, will cause cascaded deletes
        sql = "DELETE FROM site WHERE site_id=%s"
        res = session.execute(sql, (self.site_id))
        if res == -1:
            # DB Query failed, return fault
            return self.returnError("Failed to delete site!")

        return self.returnSuccess()

@registerEvent("siteAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def addSite(session_id, site):
    """Adds the specified site to the database
    
    If the site was sucessfully added to the data a dictionary with two
    items, (site_id and errMsg) is returned. errMsg may contain details
    of an error that occured but did not prevent the site from being
    added.
    """
    session = getSessionE(session_id)
    
    # verify site details
    validateSite(session_id, site)
    
    # insert the site record
    sql = "INSERT INTO site (site_id, location, admin_contact_id, " \
            "tech_contact_id, gps_lat, gps_long, elevation, comments) " \
            "VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s)"
    res = session.execute(sql, (site["location"], \
            site["admin_contact_id"], site["tech_contact_id"], \
            site["gps_lat"], site["gps_long"], site["elevation"], \
            site["comments"]))
    
    # Get the site_id that was created for the site
    sql = "SELECT currval('site_site_id_seq') as site_id"
    res = session.query(sql, ())
    site_id = res[0]["site_id"]
            
    # Raise the event
    triggerEvent(session_id, "siteAdded", site_id=site_id);
    
    return site_id

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getSiteList(session_id):
    """Returns a list of sites"""

    session = getSessionE(session_id)
    
    sql = "SELECT s.site_id, s.gps_lat, s.gps_long, s.elevation, " \
            "s.location, s.admin_contact_id, s.tech_contact_id, " \
            "c1.givenname || ' ' || c1.surname AS admin_contact_desc, " \
            "c2.givenname || ' ' || c2.surname AS tech_contact_desc, " \
            "count(sa.asset_id) as no_assets, count(sh.host_id) AS " \
            "no_hosts FROM site_contacts c1, site_contacts c2, site s LEFT JOIN " \
            "site_hosts sh ON s.site_id=sh.site_id LEFT JOIN site_assets " \
            "sa ON s.site_id=sa.site_id WHERE s.admin_contact_id=" \
            "c1.contact_id AND s.tech_contact_id=c2.contact_id GROUP BY " \
            "s.site_id, s.gps_lat, s.gps_long, s.elevation, s.location, " \
            "s.admin_contact_id, s.tech_contact_id, c1.givenname, " \
            "c1.surname, c2.givenname, c2.surname"
    res = session.query(sql, ())

    if len(res) < 1:
        return []
    
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getSiteContacts(session_id):
    session = getSessionE(session_id)
    sql = "SELECT * FROM site_contacts"
    return session.query(sql,())

def validateSite(session_id, details):
    """Validates the details are valid.

    This routine does not check for the existance of required data, it 
    only verifies that the fields in the supplied dictionary are valid.
    """
    
    # Location 
    if "location" in details.keys():
        if len(details["location"])<=0:
            raise ccs_site_error("Location must be more than 0 characters " \
                    "long!")
           
    # Contact IDs
    # XXX: TODO:
    #if "admin_contact_id" in details.keys():
    #        rv = verifyContactId(session, details["admin_contact_id"])
    #        if rv != "":
    #            return "Invalid admin contact: %s" % rv
    #if "tech_contact_id" in details.keys():
    #        rv = verifyContactId(session, details["tech_contact_id"])
    #        if rv != "":
    #            return "Invalid tech contact: %s" % rv
    
    return

def validateSiteId(session_id, site_id):
    """Checks that the specified siteID is valid (ie in the DB)"""

    session = getSessionE(session_id)
    try:
        rv = session.getCountOf("SELECT count(*) FROM site WHERE site_id=%s", \
                int(site_id))
        if rv != 1:
            raise ccs_site_error("Invalid Site ID! Site not found!")
    except:
        (type, value, tb) = sys.exc_info()
        log_error("Could not validate siteID!" , (type, value, tb))
        raise ccs_site_error("Exception while validating site ID! - %s" % \
                value)
    
    return ""

def getSiteName(session_id, site_id):
    """Returns the name of the specified site"""

    # Check we've been given a valid site_id
    try:
        if validateSiteId(session_id, site_id) != "":
            raise ccs_site_error("Invalid site ID!")
    except:
        # Invalid site ID
        log_warn("Invalid siteID passed to getSiteName!", sys.exc_info())
        return ""
        
    session = getSessionE(session_id)
    
    sql = "SELECT location FROM site WHERE site_id=%s"
    res = session.query(sql, (site_id))

    if len(res)!=1:
        raise ccs_site_error("Invalid result returned in getSiteName")
    
    return res[0]["location"]
