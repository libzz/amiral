# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Contact Module - Provides classes to manipulate contacts and groups
#
# All contacts are stored in the contacts table. The contact_type field 
# determines what privileges and functionality each contact is able to
# access. By default there is only a single type of contact that exists
# in the system:
# user - Standard user account
# This contact type is used for all people who need an account in the 
# configuration system to maintain the network. Permissions for a user
# can be further configured by assigning the user to specific groups.
#
# Other modules can register additional contact types for their own use.
# Most of the functionality provided by this module is restricted to
# working with the 'user' contact_type.
#
# Author:       Matt Brown <matt@crc.net.nz>
# Author:       Chris Browning <chris.ckb@gmail.com>
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
import xmlrpclib
import crypt
import time
import re
import random
import smtplib
import sys
import time
from pyPgSQL import libpq

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE, ccsd_session
from crcnetd._utils.ccsd_server import exportViaXMLRPC

ccs_mod_type = CCSD_SERVER

class ccs_contact_error(ccsd_error):
    pass

CONTACT_TYPE_USER = "user"
CONTACT_TYPE_CUSTOMER = "customer"

users = None
customers = None
groups = None
#####################################################################
# Login Management Functions 
#####################################################################

def _getLogins(session_id, withPassword=False, ctype=None, all=False, \
    login_id=-1):
    """
    This function can retrieve infomation from the logins table, customers 
    table, and the admins table. It will fetch specific infomation on each
    type of login depending on what type you ask for. If login_id is specified
    it will return a single login, otherwise it will return a list of all 
    logins.
    """
    session = getSessionE(session_id)

    tsql = ""
    p = []

    #All requests get data from the first login and logins tables
    sql = "SELECT l.login_id, l.enabled, l.username, l.domain," \
            "fl.enabled as flenabled,fl.login_ts"

    #Fetch the password if requested
    if withPassword: sql += ", l.passwd"
    tsql = " logins l LEFT JOIN first_login fl ON " \
            "l.login_id=fl.login_id"

    
    if ctype == CONTACT_TYPE_USER:
        #Get admin infomation, all if specified
        if all:
            sql += ", a.* FROM admins a,"
        else:
            sql += ", a.admin_id FROM admins a,"
        tsql += " WHERE l.login_id=a.login_id"
    elif ctype == CONTACT_TYPE_CUSTOMER:
        #Get customer infomation, all if specified
        if all:
            sql += ", c.* FROM customers c,"
        else:
            sql += ", c.customer_id FROM customers c,"
        tsql += " WHERE l.login_id=c.login_id"
    else:
        sql += " FROM"

    #If we only want one result narrow the search
    if login_id != -1:
        tsql += " AND l.login_id = %s"
        p += [login_id]
    res = session.query(sql + tsql, p)

    # Determine the status taking into account first login states for users
    for contact in res:
        if contact["enabled"] == 1:
            contact["status"] = 1
        elif res[0]["flenabled"] == 1 and res[0]["login_ts"] == "":
            contact["status"] = 2
        else:
            contact["status"] = 0

    return res

def verifyLoginID(session_id, login_id):
    """
    Check that the login_id is valid and exists
    """
    global users
    session = getSessionE(session_id)

    # Check it's numeric
    try:
        login_id = int(login_id)
    except ValueError:
        raise ccs_contact_error("Login ID must be numeric!")

    # Check it exists
    if session.getCountOf("SELECT count(*) as n FROM logins WHERE " \
            "login_id=%s", (login_id)) != 1:
        raise ccs_contact_error("Invalid login ID!")

    return


@registerEvent("loginRemoved")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def delLogin(session_id, login_id):
    """Deletes the specified login from the database"""
    session = getSessionE(session_id)
    
    # Verify login_id is OK
    verifyLoginID(session_id, login_id)

    # Raise an event
    triggerEvent(session_id, "loginRemoved", login_id=login_id)
    
    # Delete the login. This will cascade and remove entries from 
    # group_membership and first_login tables any many more
    sql = "DELETE FROM logins WHERE login_id=%s"
    res = session.execute(sql, (login_id))

    return 0

@registerEvent("loginModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def disableLogin(session_id, login_id):
    """Disables the account of the specified login"""
    session = getSessionE(session_id)
    
    # Verify login_id is OK
    verifyLoginID(session_id, login_id)

    # If not in a changeset, create one to group these commands together
    commit = 0
    if session.changeset == 0:
        session.begin("Disabled login %s" % login_id, '', 1)
        commit = 1

    sql = "UPDATE logins SET enabled=0 WHERE login_id=%s"
    session.execute(sql, (login_id))

    sql = "UPDATE first_login SET enabled=0 WHERE login_id=%s"
    session.execute(sql, (login_id))
       
    # If we started a changeset, commit it
    if commit == 1:
        session.commit("Automatically generated changeset.")
    
    # Raise an event
    triggerEvent(session_id, "loginModified", login_id=login_id)
    
    return 0
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getLoginState(session_id, login_id):
    """Returns the state of the login

    0 = Disabled
    1 = Active / Enabled 
    2 = Pending first login
    """
    session = getSessionE(session_id)
    
    # Verify login_id is OK
    verifyLoginID(session_id, login_id)
    
    sql = "SELECT l.enabled, fl.enabled as flenabled, " \
            "fl.login_ts FROM logins l LEFT JOIN first_login fl ON " \
            "l.login_id=fl.login_id WHERE l.login_id=%s"
    res = session.query(sql, (login_id))

    if res[0]["enabled"] == 1:
        return 1
    elif res[0]["flenabled"] == 1 and res[0]["login_ts"] == "":
        return 2
    else:
        return 0
        
def verifyLogin(session_id, contact, add):
    """
    Checks the dictionary for sanity. Will through
    an exception if there is a problem
    """
    # enabled
    if "enabled" not in contact.keys():
        raise ccs_contact_error("Account status must be specified")
    if contact["enabled"] < 0 or contact["enabled"] > 1:
        raise ccs_contact_error("Invalid account status")
    
    # username 
    if "username" in contact.keys():
        # Ensure lowercase
        contact["username"] = contact["username"].lower()
        
        # Check length
        if len(contact["username"])>18:
            raise ccs_contact_error("Username must not be more than " \
                    "18 characters long")
        if len(contact["username"])<4:
            raise ccs_contact_error("Username must be at least 4 " \
                    "characters long")

        # Check for invalid form
        accept = re.compile("[a-z][a-z0-9.]*[a-z0-9]+$")
        if not accept.match(contact["username"]):
            raise ccs_contact_error("Username must start with a " \
                    "letter, contain only a-z, 0-9 and period(.), " \
                    "and may not end with a period(.).")
    else:
        raise ccs_contact_error("Username must be specified")
        
        
    return

def updateShadowPassword(session, login_id, plain):
    #See if we need to update shadow logins table
    sql = "SELECT l.login_id from logins l join email_account e " \
        "on l.login_id = e.login_id left join admins a " \
        "on a.login_id=l.login_id where a.login_id isnull " \
        "AND l.login_id = %s;"
    res = session.query(sql, (login_id))

    if len(res) == 1:
        #Determine whether we add or update the shadow password
        sql = "SELECT login_id FROM logins_shadow WHERE login_id = %s"
        res = session.query(sql, (login_id))
        if len(res) == 1:
            sql = "UPDATE logins_shadow SET passwd=%s WHERE login_id=%s"
            session.execute(sql, (plain, login_id))
        else:
            sql = "INSERT INTO logins_shadow VALUES (%s, %s)"
            session.execute(sql, (login_id, plain))

@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def changePassword(session_id, curPass, newPass, newPass2):
    """Allows a user to change their password"""
    session = getSessionE(session_id)

    # Check old password
    sql = "SELECT l.*, fl.enabled as flstate FROM logins l LEFT JOIN " \
            "first_login fl ON l.login_id=fl.login_id WHERE l.login_id=%s"
    contact = session.query(sql, (session.login_id))
    if len(contact) != 1 or len(contact[0]["passwd"]) <= 0:
        raise ccs_contact_error("Old password is incorrect!")
    if crypt.crypt(curPass, contact[0]["passwd"]) != contact[0]["passwd"]:
        raise ccs_contact_error("Old password is incorrect!")

    # Check new passwords
    if newPass != newPass2:
        raise ccs_contact_error("New passwords do not match!")
    
    enabled = contact[0]["enabled"]
    
    # Reset the enable state if first_login was set
    if contact[0]["flstate"] is not None and contact[0]["flstate"]!="":
        enabled = contact[0]["flstate"]
        session.execute("DELETE FROM first_login WHERE login_id=%s", \
                contact[0]["login_id"])

    # Update the password
    session.execute("UPDATE logins SET passwd=%s, enabled=%s WHERE " \
            "login_id=%s", \
            (crypt.crypt(newPass, createSalt()), enabled, \
            contact[0]["login_id"]))
            
    updateShadowPassword(session, contact[0]["login_id"], newPass)
     
    sql = "SELECT email FROM admins where login_id=%s"
    email = session.query(sql, (session.login_id))
    if len(email) == 1:
        # Send email
        try:
            _sendPasswordModifiedEmail(email[0]['email'])
        except:
            log_warn("Unable to send password change notification!", \
                    sys.exc_info())

    log_info("Password changed for %s" % session.username)
    # Raise an event
    triggerEvent(session_id, "loginModified", login_id=session.login_id)
    
    return 0
#####################################################################
# Admin Management Functions 
#####################################################################
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getUsers(session_id):
    """Returns the list of daemon users"""
    return _getLogins(session_id, False, CONTACT_TYPE_USER, True)
    
@exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK)
def getCustomers(session_id):
    """Returns the list of customers"""
    return _getLogins(session_id, False, CONTACT_TYPE_CUSTOMER, True)

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getAdmin(session_id, admin_id):
    """Return a single admin"""
    return _getAdmin(session_id, admin_id)

def _getAdmin(session_id, admin_id, withPassword=False):
    """Fetch an admin from the database"""
    session = getSessionE(session_id)

    # Verify admin_id is OK
    verifyAdminID(session_id, admin_id)

    sql = "SELECT l.login_id, a.admin_id, a.surname, a.givenname, a.phone, a.email, l.username, l.domain, " \
        "a.uid, a.address, a.public_key, a.shell, l.enabled, l.lastlog"
    if withPassword: sql += ", l.passwd"
    sql += " FROM admins a, logins l WHERE admin_id=%s AND l.login_id=a.login_id" 
    res = session.query(sql, (admin_id))
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getAdminID(session_id, username):
    global users
    """
    Returns the admin_id of the user with the specified username
    """  
    session = getSessionE(session_id)
    return users[username]["admin_id"]
    

def _getUsername(session_id, admin_id):
    """Returns the username of the specified admin"""
    session = getSessionE(session_id)

    sql = "SELECT username FROM logins WHERE login_id=(select login_id from admins where admin_id=%s)"
    res = session.query(sql, (admin_id))

    if len(res) != 1:
        return ""

    return res[0]["username"]

     
def _sendWelcomeEmail(to, username, passwd):
    """Sends the user a welcome email containing their username and password"""
    global parent
    
    admin_email = config_get("network", "admin_email", DEFAULT_ADMIN_EMAIL)
    site_name = config_get("network", "site_name", DEFAULT_SITE_NAME)
    site_address = config_get("network", "site_address", DEFAULT_SITE_ADDRESS)
    smtp_server = config_get("network", "smtp_server", "localhost")
    
    msg = """To: %s
From: %s Administrator <%s>
Subject: Configuration System Account Created
    
Hi, 

This is an automated message to notify you that an account has been created
for you in the %s.

To activate your account you will need to login to the website with the 
following username and password:

    Username:   %s
    Password:   %s
    Website:    %s
    
Once you have sucessfully logged in you will be asked to change your password
before your account is fully activated. 

If you have problems or questions please contact %s.
""" % (to, site_name, admin_email, site_name, username, passwd, \
        site_address, admin_email)

    s = smtplib.SMTP(smtp_server)
    s.sendmail(admin_email, [to], msg)
    s.close()	    


@registerEvent("adminAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def addAdmin(session_id, contact):
    """Adds the specified admin to the database
    
    If the admin was sucessfully added to the data a dictionary with two
    items, (admin_id and errMsg) is returned. errMsg may contain details
    of an error that occured but did not prevent the admin from being
    added.
    """
    session = getSessionE(session_id)    
    
    # verify admin details
    verifyAdmin(session_id, contact, True)

    # create a password
    plain = createPassword(8)
    salt = createSalt()
    passwd = crypt.crypt(plain, salt)
    
    # If not in a changeset, create one to group these commands together
    commit = 0
    if session.changeset == 0:
        session.begin("Created new admin %s" % contact["username"], "", 1)
        commit = 1

    # insert the login record
    sql = "INSERT INTO logins (login_id, username, domain, enabled, "\
        "passwd) VALUES (DEFAULT, %s, %s, %s, %s)" 
    session.execute(sql, (contact["username"], contact["domain"], 1, passwd))

    # Get the login_id that was created for the user
    sql = "SELECT currval('logins_login_id_seq') AS login_id"
    login_id = session.query(sql, ())[0][0]
    
    # insert the admin record
    sql = "INSERT INTO admins (admin_id, login_id, givenname, surname, " \
            "phone, email, address) VALUES (DEFAULT, " \
            "%s, %s, %s, %s, %s, %s)"
    session.execute(sql, (login_id, contact["givenname"], \
            contact["surname"], contact["phone"], contact["email"], \
            contact["address"]))
    
    # Get the admin_id that was created for the user
    sql = "SELECT currval('admins_admin_id_seq') AS admin_id"
    admin_id = session.query(sql, ())[0][0]
    
    # Add them to the users group and force their
    # password to be changed when the first login
    sql = "INSERT INTO first_login (login_id, enabled) VALUES " \
            "(%s, %s)"
    session.execute(sql, (login_id, contact["enabled"]))
   
    addMemberU(session_id, getGroupID(session_id, "Users"), admin_id)

    # Email the user their password and some instructions
    try:
        _sendWelcomeEmail(contact["email"], contact["username"], plain)
    except:
        log_warn("Welcome email not sent to new user: %s" % \
                contact["username"], sys.exc_info())

    # If we started a changeset, commit it
    if commit == 1:
        session.commit("Automatically generated changeset.")

        
    # Raise an event
    triggerEvent(session_id, "adminAdded", login_id=login_id)
    
    return admin_id
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def genAdminPassword(session_id, admin_id, login_id):
    """
    Will generate a new password for a Admin
    """
    session = getSessionE(session_id)
    #Check values
    verifyLoginID(session_id, login_id)
    verifyAdminID(session_id, admin_id)
    
    sql = "SELECT username || '@' || domain AS username FROM logins WHERE login_id=%s"
    res = session.query(sql, (login_id))
    forgotPassword(res[0]['username'])
    
    return "True"
    
@registerEvent("adminModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def editAdmin(session_id, contact):
    """Updates the specified admin in the database"""
    session = getSessionE(session_id)

    # verify admin and login details
    verifyAdmin(session_id, contact, False)
    verifyLogin(session_id, contact, False)
    
    # If not in a changeset, create one to group these commands together
    commit = 0
    if session.changeset == 0:
        session.begin("Updated admin %s" % contact["username"], '', 1)
        commit = 1

    #Update the admins table
    props = ['givenname', 'surname', 'billing_name', 'billing_address', \
        'address', 'email', 'phone', 'uid', 'shell', 'public_key']
    sql, p = buildUpdateFromDict('admins', props, contact, "login_id", contact["login_id"])
    session.execute(sql, p)

    # Check for changed password
    if "passwd" in contact.keys() and len(contact["passwd"])>0:
        plain = contact["passwd"]
        salt = createSalt()
        contact["passwd"]= crypt.crypt(plain, salt)

    #Update the logins table
    props = ['passwd', 'enabled']
    sql, p = buildUpdateFromDict('logins', props, contact, "login_id", contact["login_id"])
    session.execute(sql, p)
    
    # If we started a changeset, commit it
    if commit == 1:
        session.commit("Automatically generated changeset.")
    
    # Raise an event
    triggerEvent(session_id, "adminModified", login_id=contact['login_id'])
    return contact["admin_id"]
        
def verifyAdminID(session_id, admin_id):
    """
    Check that the admin_id is valid and exists
    """
    
    session = getSessionE(session_id)

    # Check it's numeric
    try:
        admin_id = int(admin_id)
    except ValueError:
        raise ccs_contact_error("Contact ID must be numeric!")

    # Check it exists
    if session.getCountOf("SELECT count(*) as n FROM admins WHERE " \
            "admin_id=%s", (admin_id)) != 1:
        raise ccs_contact_error("Invalid admin ID!")

    return 

def _sendPasswordModifiedEmail(to):
    """Sends the user an email that their password was changed"""
    global parent
    
    admin_email = config_get("network", "admin_email", DEFAULT_ADMIN_EMAIL)
    site_name = config_get("network", "site_name", DEFAULT_SITE_NAME)
    site_address = config_get("network", "site_address", DEFAULT_SITE_ADDRESS)
    smtp_server = config_get("network", "smtp_server", "localhost")
    
    msg = """To: %s
From: %s Administrator <%s>
Subject: Configuration System Password Changed
    
Hi, 

This is an automated message to notify you that your password for the %s
was changed.

If you did not initiate this password change please contact %s IMMEDIATELY.
""" % (to, site_name, admin_email, site_name, admin_email)

    s = smtplib.SMTP(smtp_server)
    s.sendmail(admin_email, [to], msg)
    s.close()	    


def _sendPasswordEmail(to, passwd):
    """Sends the user a welcome email containing their username and password"""
    global parent
    
    admin_email = config_get("network", "admin_email", DEFAULT_ADMIN_EMAIL)
    site_name = config_get("network", "site_name", DEFAULT_SITE_NAME)
    site_address = config_get("network", "site_address", DEFAULT_SITE_ADDRESS)
    smtp_server = config_get("network", "smtp_server", "localhost")
    
    msg = """To: %s
From: %s Administrator <%s>
Subject: Configuration System Password
    
Hi, 

A new password has been created for you in the %s.

    Password:   %s
   
Once you have sucessfully logged in you will be asked to change your password
before your account is fully activated again. 

If you have problems or questions please contact %s.
""" % (to, site_name, admin_email, site_name, passwd, admin_email)

    s = smtplib.SMTP(smtp_server)
    s.sendmail(admin_email, [to], msg)
    s.close()	    

@exportViaXMLRPC(SESSION_NONE, AUTH_NONE)
def forgotPassword(username):
    """Emails the user a new password when they have forgotten it"""
    session = getSession(ADMIN_SESSION_ID)

    username, domain = username.split('@')
    
    contact = session.query("SELECT l.*, a.admin_id, a.email, fl.enabled AS flstate FROM " \
            "(logins l INNER JOIN admins a ON a.login_id=l.login_id) LEFT JOIN first_login fl ON l.login_id=" \
            "fl.login_id WHERE username=%s AND domain=%s", (username, domain))
    if len(contact) != 1:
        log_warn("New pasword request for unknown user: %s@%s" % (username, domain))
        return 0

    # create a password
    plain = createPassword(8)
    salt = createSalt()
    passwd = crypt.crypt(plain, salt)

    # Update the password
    session.execute("UPDATE logins SET passwd=%s, enabled=1 WHERE " \
            "login_id=%s", (passwd, contact[0]['login_id']))
    if contact[0]["flstate"] is None or contact[0]["flstate"]=="":
        sql = "INSERT INTO first_login (login_id, enabled) VALUES " \
                "(%s, %s)"
        session.execute(sql, (contact[0]["login_id"], contact[0]["enabled"]))
    
    # Send email
    try:
        _sendPasswordEmail(contact[0]["email"], plain)
    except:
        log_warn("Unable to send forgotten password notification!", \
                sys.exc_info())
    log_info("New password emailed to %s@%s" % (username, domain))

    return 0

@registerEvent("adminModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def assignUID(session_id, admin_id):
    """Allocates a user id (uid) to the admin"""
    session = getSessionE(session_id)
    
    # Verify admin_id is OK
    verifyAdminID(session_id, admin_id)

    contact = getAdmin(session_id, admin_id)

    sql = "UPDATE admins SET uid=nextval('uid_seq') WHERE admin_id=%s"
    session.execute(sql, (admin_id))

    sql = "SELECT currval('uid_seq') as uid"
    res = session.query(sql, ())
    
    # Raise an event
    triggerEvent(session_id, "adminModified", login_id=login_id)

    return res[0]["uid"]
   
def verifyAdmin(session_id, contact, add):
    """
    Checks the dictionary fields for sanity for adding or
    editing an admin
    """
    verifyCommon(session_id, contact, add)
    email = re.compile("^([a-z]([a-z0-9][a-z0-9._]?)*[a-z0-9]@[a-z]+\.([a-z][a-z.]?)*[a-z])?$")

    # Check domain
    if "domain" not in contact.keys():
        raise ccs_contact_error("Domain must be specified")

    # Check that the username and domain combined are valid
    if 'username' in contact.keys():
        if email.match("%s@%s" % (contact['username'], contact['domain'])) \
            == None:
            raise ccs_contact_error("Invalid username")
    else:
        raise ccs_contact_error("Username must be supplied")
    
    
    if "admin_id" not in contact.keys() and not add:
        ccs_contact_error("Admin ID must be specified")
    if "admin_id" in contact.keys() and not add:
        verifyAdminID(session_id, contact["admin_id"])
#    if "shell" in contact.keys():
#        sql += ", shell=%s" % libpq.PgQuoteString(contact["shell"])
#    if "public_key" in contact.keys():
#        sql += ", public_key=%s" % libpq.PgQuoteString(contact["public_key"])
    return

def verifyCommon(session_id, contact, add):
    """Checks the contact details are sane"""
    
    #Ensure no xml invalid charictors are present
    exclude = re.compile("[&<>]")
    if contact.has_key("givenname") \
        and exclude.search(contact["givenname"]) != None:
        raise ccs_contact_error("Characters &<> are not allowed")
    if contact.has_key("surname") \
        and exclude.search(contact["surname"]) != None:
        raise ccs_contact_error("Characters &<> are not allowed")
    if contact.has_key("address") \
        and exclude.search(contact["address"]) != None:
        raise ccs_contact_error("Characters &<> are not allowed")
    
    # Verify id's
    if "login_id" not in contact.keys() and not add:
        raise ccs_contact_error("Login ID must be specified")
    if "login_id" in contact.keys() and not add:
        verifyLoginID(session_id, contact["login_id"])

           
    # name
    if "givenname" not in contact.keys() or len(contact["givenname"])<=0:
        raise ccs_contact_error("First name must be specified")

    if "surname" not in contact.keys() or len(contact["surname"])<=0:
        raise ccs_contact_error("Last name must be specified")
    
    # Validate email if present
    if "email" in contact.keys():
        mpat = re.compile(".*@.*\..*")
        if mpat.match(contact["email"]) == None:
            raise ccs_contact_error("Invalid email address")

    # Validate phone # if present
    if "phone" in contact.keys() and len(contact["phone"])>0:
        mpat = re.compile("\+\d{2} \d{1,3} [\d ]{6,10}")
        if mpat.match(contact["phone"]) == None:
            raise ccs_contact_error("Invalid phone number")
           
    # Seems to be OK
    return

#####################################################################
# Admin Group Management Functions 
#####################################################################
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGroups(session_id):
    """Returns the list of admin groups"""
    session = getSessionE(session_id)

    sql = "SELECT * FROM admin_group"
    res = session.query(sql, ())
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGroupMemberCount(session_id, group_id):
    """Returns the number of members in the specified group"""
    session = getSessionE(session_id)
    verifyGroupID(session_id, group_id)
    
    sql = "SELECT count(*) as n FROM group_membership WHERE " \
            "parent_group_id=%s"
    n = session.getCountOf(sql, (group_id))
    # XXX: Maybe account for groups being members of groups here...
    return n

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGroup(session_id, group_id):
    """Return a single group"""
    session = getSessionE(session_id)

    # Verify group_id is OK
    verifyGroupID(session_id, group_id)

    sql = "SELECT * FROM admin_group WHERE admin_group_id=%s"
    res = session.query(sql, (group_id))
    return res[0]

def _getGroupname(session_id, group_id):
    """Returns the groupname of the specified group"""
    session = getSessionE(session_id)

    # Verify group_id is OK
    verifyGroupID(session_id, group_id)
    
    sql = "SELECT * FROM admin_group WHERE admin_group_id=%s"
    res = session.query(sql, (group_id))
    if len(res) != 1:
        return ""
    return res[0]["group_name"]

@registerEvent("groupRemoved")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def delGroup(session_id, group_id):
    """Deletes the specified group from the database"""
    session = getSessionE(session_id)

    # Verify group_id is OK
    verifyGroupID(session_id, group_id)

    # Raise an event
    triggerEvent(session_id, "groupRemoved", group_id=group_id)
    
    # This delete should automatically cause group_membership records to
    # be deleted also as the database is created with ON DELETE CASCADE
    sql = "DELETE FROM admin_group WHERE admin_group_id=%s"
    session.execute(sql, (group_id))

    return 0

@registerEvent("groupAdded")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def addGroup(session_id, group):
    """Adds the specified group to the database
    
    If the group was sucessfully added to the data a dictionary with two
    items, (group_id and errMsg) is returned. errMsg may contain details
    of an error that occured but did not prevent the group from being
    added.
    """
    session = getSessionE(session_id)
    
    # verify group details
    verifyGroup(session_id, group, True)

    # insert the group record
    sql = "INSERT INTO admin_group (admin_group_id, group_name) VALUES " \
            "(DEFAULT, %s)"
    session.execute(sql, (group["group_name"]))
    
    # Get the group_id that was created for the group
    sql = "SELECT currval('admin_group_admin_group_id_seq') as " \
            "admin_group_id"
    res = session.query(sql, ())
    group_id = res[0]["admin_group_id"]
    
    # Raise the event
    triggerEvent(session_id, "groupAdded", group_id=group_id)
    
    return group_id

@registerEvent("groupModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def editGroup(session_id, group):
    """Updates the specified group in the database"""
    session = getSessionE(session_id)
    
    # verify group details
    verifyGroup(session_id, group, False)
    
    # Update the record
    sql = "UPDATE admin_group SET group_name=%s WHERE admin_group_id=%s"
    session.execute(sql, (group["group_name"], group["group_id"]))
    
    # Raise the event
    triggerEvent(session_id, "groupModified", group_id=group["group_id"])
    
    return 0

#@registerEvent("groupModified")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def assignGID(session_id, group_id):
    """Allocates a group id (gid) to the group"""
    session = getSessionE(session_id)
    
    # Verify group_id is OK
    verifyGroupID(session_id, group_id)

    sql = "UPDATE admin_group SET gid=nextval('gid_seq') WHERE " \
            "admin_group_id=%s"
    session.execute(sql, (group_id))

    sql = "SELECT currval('gid_seq') as gid"
    res = session.query(sql, ())
    
    # Raise the event
    triggerEvent(session_id, "groupModified", group_id=group_id)

    return res[0]["gid"]

@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def addMember(session_id, parent_group_id, member):
    """Adds a user or a group to a group.

    This function is a wrapper for the more specific addMemberG or addMemberU
    functions.
    """
    session = getSessionE(session_id)

    try:
        # Check first char of member to see if we are adding a group
        if member[0] == "g":
            group_id = int(member[1:])
            admin_id = -1
        elif member[0] == "u":
            admin_id = int(member[1:])
            group_id = -1
        else:
            raise ccs_contact_error("Invalid member ID")
        
        # Verify group_id is OK
        verifyGroupID(session_id, parent_group_id)
        if group_id != -1:
            verifyGroupID(session_id, group_id)
        # Verify contact_id is OK
        if admin_id != -1:
            verifyAdminID(session_id, admin_id)
    except KeyError:
        raise ccs_contact_error("Invalid admin or group id!")

    if admin_id != -1:
        return addMemberU(session_id, parent_group_id, admin_id)
    
    if group_id != -1:
        return addMemberG(session_id, parent_group_id, group_id)

    raise ccs_contact_error("Insufficient parameters to addMember!")
            
@registerEvent("memberAddedU")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def addMemberU(session_id, group_id, admin_id):
    """Adds the specified contact to the specified group
    
    Returns a string in the format "<username>;u<contact_id>"
    """
    session = getSessionE(session_id)

    # XXX: Check for existing group membership here
    
    sql = "INSERT INTO group_membership (parent_group_id, admin_id) " \
            "VALUES (%s, %s)"
    session.execute(sql, (group_id, admin_id))

    username = _getUsername(session_id, admin_id)
    result = "%s;u%d" % (username, admin_id)
    
    # Raise the event
    triggerEvent(session_id, "memberAddedU", group_id=group_id, \
            admin_id=admin_id)
    
    return result
    
@registerEvent("memberAddedG")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def addMemberG(session_id, parent_group_id, group_id):
    """Adds the specified group to the specified group

    Returns a string in the format "<groupname>;g<group_id>"
    """
    session = getSessionE(session_id)
            
    # XXX: Check for existing group membership here
    sql = "INSERT INTO group_membership (parent_group_id, group_id) " \
            "VALUES (%s, %s)"
    session.execute(sql, (parent_group_id, group_id))

    groupname = _getGroupname(session_id, group_id)
    result = "%s;g%d" % (groupname, group_id)
    
    # Raise the event
    triggerEvent(session_id, "memberAddedG", parent_group_id=parent_group_id, \
            group_id=group_id)
    
    return result

@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def delMember(session_id, parent_group_id, member):
    """Remove a user or group from a group
    
    This function is a wrapper for the more specific delMemberG or delMemberU
    functions.
    """
    session = getSessionE(session_id)
    
    try:
        # Check first char of member to see if we are remvoing a group
        if member[0] == "g":
            group_id = int(member[1:])
            admin_id = -1
        elif member[0] == "u":
            admin_id = int(member[1:])
            group_id = -1
        else:
            raise ccs_contact_error("Invalid member ID")
        
        # Verify group_id is OK
        verifyGroupID(session_id, parent_group_id)
        if group_id != -1:
            verifyGroupID(session_id, group_id)
        # Verify admin_id is OK
        if admin_id != -1:
            verifyAdminID(session_id, admin_id)
    except KeyError:
        raise ccs_contact_error("Invalid contact or group id!")

    if admin_id != -1:
        return delMemberU(session_id, parent_group_id, admin_id)
    
    if group_id != -1:
        return delMemberG(session_id, parent_group_id, group_id)

    raise ccs_contact_error("Insufficient parameters for delMember!")

@registerEvent("memberRemovedU")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def delMemberU(session_id, group_id, admin_id):
    """Removes the specified contact from the specified group
    
    Returns a string in the format "<username>;u<admin_id>"
    """
    session = getSessionE(session_id)

    sql = "DELETE FROM group_membership WHERE parent_group_id=%s AND " \
            "admin_id=%s"
    session.execute(sql, (group_id, admin_id))

    username = _getUsername(session_id, admin_id)
    result = "%s;u%d" % (username, admin_id)

    # Raise the event
    triggerEvent(session_id, "memberRemovedU", group_id=group_id, \
            admin_id=admin_id)
   
    return result

@registerEvent("memberRemovedG")
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def delMemberG(session_id, parent_group_id, group_id):
    """Removes the specified group from the specified group
    
    Returns a string in the format "<groupname>;g<group_id>"
    """
    session = getSessionE(session_id)
    
    sql = "DELETE FROM group_membership WHERE parent_group_id=%s AND " \
            "group_id=%s"
    session.execute(sql, (parent_group_id, group_id))

    groupname = _getGroupname(session_id, group_id)
    result = "%s;g%d" % (groupname, group_id)

    # Raise the event
    triggerEvent(session_id, "memberRemovedG", \
            parent_group_id=parent_group_id, group_id=group_id)

    return result

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getMembers(session_id, group_id):
    """Returns the list of users / groups in the specified group"""
    session = getSessionE(session_id)

    # Verify group_id is OK
    verifyGroupID(session_id, group_id)

    sql = "SELECT gm.admin_id, gm.group_id, l.username, l.domain, a.givenname, " \
            "a.surname, g.group_name FROM group_membership gm LEFT JOIN " \
            "(admins a LEFT JOIN logins l ON l.login_id = a.login_id) ON gm.admin_id=a.admin_id LEFT JOIN " \
            "admin_group g ON gm.group_id=g.admin_group_id WHERE " \
            "gm.parent_group_id=%s ORDER BY g.group_name, l.username"
    res = session.query(sql, (group_id))
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getAvail(session_id, group_id):
    """Returns the list of users / groups not in the specified group"""
    session = getSessionE(session_id)
    
    # Verify group_id is OK
    verifyGroupID(session_id, group_id)
    sql = "SELECT c.admin_id, l.username, c.givenname, c.surname, " \
        "g.admin_group_id, g.group_name FROM (((admins c INNER JOIN " \
        "logins l ON c.login_id=l.login_id) LEFT JOIN group_membership gm " \
        "ON c.admin_id=gm.admin_id AND gm.parent_group_id=%(c)s) FULL JOIN " \
        "(admin_group g LEFT JOIN group_membership gm2 ON " \
        "g.admin_group_id=gm2.group_id AND gm2.parent_group_id=%(c)s) ON " \
        "l.passwd=g.group_name) WHERE ((c.admin_id IS NOT NULL AND " \
        "(gm.parent_group_id IS NULL OR gm.parent_group_id!=%(c)s)) OR " \
        "(g.admin_group_id IS NOT NULL AND (gm2.parent_group_id IS NULL OR " \
        "gm2.parent_group_id!=%(c)s) AND g.admin_group_id!=%(c)s)) ORDER BY " \
        "g.group_name, l.username"

    res = session.query(sql, {"c":group_id})
    if len(res) < 1:
        return []

    # Filter out groups that are parents of this group
    res2 = []
    for member in res:
        # Skip normal contacts
        if member["admin_group_id"] == "":
            res2.append(member)
            continue
        # Check group membership
        if isGroupMemberG(session_id, group_id, member["admin_group_id"]):
            continue
        # It's ok 
        res2.append(member)
    return res2

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def isGroupMemberG(session_id, group_id, parent_group_id, recurse=True):
    """Determines if the specified group is a member of the group."""

    # Verify group_id is OK
    verifyGroupID(session_id, group_id)
    
    # Verify parent_group_id is OK
    verifyGroupID(session_id, parent_group_id)
    
    # Verify other params
    if recurse != 0 and recurse != 1:
        raise ccs_contact_error("Recurse must be 0 or 1")

    session = getSessionE(session_id)

    # Lookup contact only first
    sql = "SELECT count(*) as n FROM group_membership WHERE " \
            "parent_group_id=%s AND group_id=%s"
    n = session.getCountOf(sql, (parent_group_id, group_id))

    # Check for a membership record
    if n > 0:
        return True
    
    # Otherwise check subgroups
    if recurse:
        # Get list of subgroups - excluding the one we are looking for
        sql = "SELECT group_id FROM group_membership WHERE " \
                "parent_group_id=%s AND group_id IS NOT NULL AND group_id!=%s"
        res = session.query(sql, (parent_group_id, group_id))
       
        # Loop through groups looking for membership
        for gres in res:
            rv = isGroupMemberG(session_id, group_id, gres["group_id"])
            if rv:
                return True
    
    # Not a member
    return False

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def isGroupMemberU(session_id, admin_id, group_id, recurse=True):
    """Determines if the specified admin is a member of the group."""
    # Verify group_id is OK
    res = verifyGroupID(session_id, group_id)
    
    # Verify admin_id is OK
    res = verifyAdminID(session_id, admin_id)
    
    # Verify other params
    if recurse != 0 and recurse != 1:
        raise ccs_contact_error("Recurse must be 0 or 1")

    session = getSessionE(session_id)

    # Lookup contact only first
    sql = "SELECT count(*) as n FROM group_membership WHERE " \
            "parent_group_id=%s AND admin_id=%s"
    res = session.getCountOf(sql, (group_id, admin_id))

    # Check for a membership record
    if res > 0:
        return True
    
    # Otherwadminck subgroups
    if recurse:
        # Get list of groups
        sql = "SELECT group_id FROM group_membership WHERE " \
            "parent_group_id=%s AND group_id IS NOT NULL"
        res = session.query(sql, (group_id))
        # Loop through groups looking for membership
        for gres in res:
            rv = isGroupMemberU(session_id, admin_id, gres["group_id"])
            if rv:
                return True

    # Not a member
    return False
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGroupID(session_id, group_name):
    """Returns the id of the group with the specified name"""
    session = getSessionE(session_id)
    
    sql = "SELECT * from admin_group WHERE group_name=%s"
    res = session.query(sql, (group_name))
    
    if len(res) < 1:
        return -1

    return res[0]["admin_group_id"]

def verifyGroupID(session_id, group_id):
    
    session = getSessionE(session_id)

    # Check it's numeric
    try:
        group_id = int(group_id)
    except ValueError:
        raise ccs_contact_error("Group ID must be numeric!")

    if session.getCountOf("SELECT count(*) as n FROM admin_group " \
            "WHERE admin_group_id=%s", (group_id)) != 1:
        raise ccs_contact_error("Invalid group_id! Group does not exist.")

    return

def verifyGroup(session_id, group, add):
    """Checks the group details are sane"""

    # Verify group_id
    if "group_id" not in group.keys() and not add:
        raise ccs_contact_error("Group ID must be specified")
    if "group_id" in group.keys() and not add:
        verifyGroupID(session_id, group["group_id"])
    
    # Group name 
    if "group_name" not in group.keys() or len(group["group_name"])<=0:
        raise ccs_contact_error("Group name must be specified")

    return

#####################################################################
# Cache Management
####################################################################
@catchEvent("loginModified")
def updateLoginInCache(eventName, host_id, session_id, login_id):
    global users, customers
    login_id = int(login_id)
    try:
        admin = users[login_id]
        triggerEvent(session_id, "adminModified", login_id=login_id)
    except:
        pass
    try:
        customer = customers[login_id]
        triggerEvent(session_id, "customerModified", login_id=login_id)
    except:
        pass

@catchEvent("adminAdded")
@catchEvent("customerAdded")
@catchEvent("adminModified")
@catchEvent("customerModified")
def updateContactInCache(eventName, host_id, session_id, login_id):
    global users, customers
    logon_id = int(login_id)
    
    if eventName[0] == 'a':
        type = CONTACT_TYPE_USER
        cache = users
    else:
        type = CONTACT_TYPE_CUSTOMER
        cache = customers

    # Retrieve new record
    contact = filter_keys(_getLogins(session_id, True, type, False, login_id)[0])
    # Delete old username based record, incase username or domain changed
    try: del cache["%s@%s" % (cache[login_id]["username"], cache[login_id]["domain"])]
    except: pass

    # Store new record
    cache["%s@%s" % (contact["username"], contact["domain"])] = contact
    cache[login_id] = contact

@catchEvent("loginRemoved")
def removeContactFromCache(eventName, host_id, session_id, login_id):
    global users, customers
    logon_id = int(login_id)
    
    try:
        del users["%s@%s" % (users[login_id]["username"], users[login_id]["domain"])]
        del users[login_id]
    except:
        pass
    try:
        del customers["%s@%s" % (customers[login_id]["username"], customers[login_id]["domain"])]
        del customers[login_id]
    except:
        pass


@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR)
def getUserCache(session_id):
    global users
    return users

@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR)
def getCustomerCache(session_id):
    global customers
    return customers

@catchEvent("groupAdded")
@catchEvent("groupModified")
def updateGroupInCache(eventName, host_id, session_id, group_id):
    global groups
    group_id = int(group_id)
    group = filter_keys(getGroup(session_id, group_id))
    try: del groups[groups[group_id]["group_name"]]
    except: pass

    # Retrieve membership information
    members = getMembers(ADMIN_SESSION_ID, group["admin_group_id"])
    t = filter(lambda x: x["admin_id"]!="", members)
    group["members"] = map(lambda x: x["admin_id"], t)
    t = filter(lambda x: x["group_id"]!="", members)
    group["group_members"] = map(lambda x: x["group_id"], t)
    # Store
    groups[group["group_name"]] = group
    groups[group_id] = group

@catchEvent("groupRemoved")
def removeGroupFromCache(eventName, host_id, session_id, group_id):
    global groups
    group_id = int(group_id)
    group = filter_keys(getGroup(session_id, group_id))
    del groups[groups[group_id]["group_name"]]
    del groups[group_id]

@exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR)
def getGroupCache(session_id):
    global groups
    return groups

@catchEvent("memberAddedU")
@catchEvent("memberAddedG")
@catchEvent("memberRemovedU")
@catchEvent("memberRemovedG")
def updateMemberCache(eventName, host_id, session_id, **kwargs):
    global groups
    # Determine which list to modify
    if eventName.endswith("U"): 
        list = "members"
        member_id = int(kwargs["admin_id"])
        group_id = int(kwargs["group_id"])
    else: 
        list = "group_members"
        member_id = int(kwargs["group_id"])
        group_id = int(kwargs["parent_group_id"])
    # Determine whether to append or remove
    if eventName.find("Added") != -1: action = "append"
    else: action = "remove"
    # Do it
    groups[group_id][list].__getattribute__(action)(member_id)

#####################################################################
# Initialisation 
#####################################################################
def ccs_init():
    """Module initialisation function"""
    global users, groups, customers

    # Check if there is at least one administrator
    gid = getGroupID(ADMIN_SESSION_ID, "Administrators")
    n = getMembers(ADMIN_SESSION_ID, gid)

    if (len(n)<1):
        # Check if there is a user called admin
        uid = getAdminID(ADMIN_SESSION_ID, "admin")
        if uid==-1:
            # Create a new admin user and email a password to root@domain
            admin = {"username":"admin", "givenname":"System", \
                    "surname":"Administrator", "phone":"", \
                    "email":"root@%s" % config_get("network", "domain"), \
                    "address":"", "type":CONTACT_TYPE_USER, "enabled":1}
            try:
                uid = addContact(ADMIN_SESSION_ID, admin)
                log_info("Created admin user")
                if uid<0:
                    raise ccs_contact_error("Unable to create admin user!")
            except:
                (type, value, tb) = sys.exc_info()
                log_fatal("There is no administrative user! - %s" % value)
        # Add the existing (or newly created) user called 'admin' to the 
        # Administators group
        res = addMemberU(ADMIN_SESSION_ID, gid, uid)
        if res != "":
            log_info("User %s promoted to Administrator" % res.split(";")[0])
        else:
            log_fatal("No members in Administrators group and unable to " \
                    "promote user named 'admin'!")

    # Setup user and group information caches for use in authentication
    users = {}
    groups = {}
    
    customers = {}
    contacts = _getLogins(ADMIN_SESSION_ID, True, CONTACT_TYPE_USER)
    for user in contacts: 
        users["%s@%s" % (user["username"], user["domain"])] = user
        users[int(user["login_id"])] = user

    contacts = _getLogins(ADMIN_SESSION_ID, True, CONTACT_TYPE_CUSTOMER)
    for user in contacts: 
        customers["%s@%s" % (user["username"], user["domain"])] = user
        customers[int(user["login_id"])] = user
        
    for group in map(filter_keys, getGroups(ADMIN_SESSION_ID)):
        # Retrieve membership information
        members = getMembers(ADMIN_SESSION_ID, group["admin_group_id"])
        t = filter(lambda x: x["admin_id"]!="", members)
        group["members"] = map(lambda x: x["admin_id"], t)
        t = filter(lambda x: x["group_id"]!="", members)
        group["group_members"] = map(lambda x: x["group_id"], t)
        # Store
        groups[group["group_name"]] = group
        groups[int(group["admin_group_id"])] = group
