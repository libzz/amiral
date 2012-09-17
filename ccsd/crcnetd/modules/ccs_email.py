from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_email import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC, registerRecurring, \
        registerDailyAt
from crcnetd._utils.ccsd_config import config_get, config_getint, config_getboolean
from crcnetd.modules.ccs_contact import verifyLogin, verifyCommon, updateShadowPassword
from crcnetd._utils.ccsd_service import ccsd_service, ccs_service_error, \
        registerService, getServiceInstance

from crcnetd.modules.ccs_interface import INTERFACE_TYPE_ALIAS, addInterface
from crcnetd.modules.ccs_link import ccs_link

import calendar
import os, os.path
import time
import re
import crypt

from Cheetah.Template import Template

ccs_mod_type = CCSD_SERVER

class ccs_email_error(ccsd_error):
    pass

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getEmailDomains(session_id, indirects=True):
    """
    Retrieve a list of all email domains
    """
    session = getSessionE(session_id)
    
    sql = "SELECT * from v_domains"
    if indirects == 'f':
        sql += " WHERE redirect IS NULL"

    return session.query(sql, ())

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getEmailDomain(session_id, domain):
    """
    Retrieve a full infomation about a particuler domain.
    Raises an error if the domain doesn't exist
    """
    session = getSessionE(session_id)
    
    sql = "SELECT * from v_domains where domain=%s"

    res = session.query(sql, (domain))

    if len(res) > 0:
        return res[0]
    else:
        raise ccs_email_error("Domain doesn't exist")

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getMailbox(session_id, login_id):
    """
    Retrieve full infomation about a perticuler email account
    Raises an error if the email account doesn't exist
    """
    session = getSessionE(session_id)
    
    sql = "SELECT * from v_mailboxes where login_id=%s"

    res = session.query(sql, (login_id))
    
    #Figure out whether it is tied to a broadband account
    sql = "SELECT count(login_id) FROM broadband_account WHERE login_id=%s"
    res2 = session.query(sql, (login_id))

    if len(res) > 0:
        if int(res2[0][0]) == 1:
            res[0]['restrict'] = 1
        else:
            res[0]['restrict'] = 0
        return res[0]
    else:
        raise ccs_email_error("Mailbox doesn't exist")
        
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getMailboxes(session_id, domain):
    """
    Retrieve a list of all email accounts that exist for a
    particular domain.
    If the domain does not exist it will raise an exception
    """
    session = getSessionE(session_id)
    
    verifyDomain(domain)
    sql = "SELECT * FROM v_mailboxes WHERE domain=%s"
    res = session.query(sql, (domain))
    
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getCustomersMailboxes(session_id, customer_id):
    from ccs_billing import verifyCustomerID
    """
    Retrieve a list of all email accounts that are ownedby a
    particular customer.
    If the customer does not exist it will raise an exception
    """
    session = getSessionE(session_id)
    
    verifyCustomerID(customer_id)
    sql = "SELECT * FROM v_mailboxes WHERE customer_id=%s"
    res = session.query(sql, (customer_id))
    
    return res

@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
@registerEvent("customerModified")  
def genMailboxPassword(session_id, login_id, owner_id):
    from ccs_contact import verifyLoginID
    """
    Will generate a new password for a login
    """
    session = getSessionE(session_id)

    #Check values
    verifyLoginID(session_id, login_id)
    verifyLoginID(session_id, owner_id)
    
    plain = createPassword(8)
    
    # Encrypt password
    salt = createSalt()
    passwd = crypt.crypt(plain, salt)
    sql = "UPDATE logins SET passwd=%s WHERE login_id=%s"
    session.execute(sql, (passwd, login_id))
    updateShadowPassword(session, login_id, plain)

    # Raise an event if this is the customers login
    if int(login_id) == int(owner_id):
        triggerEvent(session_id, "customerModified", login_id=login_id)

    return plain

@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
def addMailbox(session_id, details):
    """
    Will create the required logon, and email account required
    to make a new mailbox. If a password is supplied it will be
    used otherwise a random one will be generated and returned.
    """
    session = getSessionE(session_id)
    
    #Check values
    verifyMailbox(details)

    # If not in a changeset, create one to group these commands together
    commit = 0
    if session.changeset == 0:
        session.begin("Created new Mailbox %s" % details["username"], '', 1)
        commit = 1

    # create a password if not provided
    if "passwd" in details.keys() and len(details['passwd']) > 1:
        plain = details['passwd']
    else:
        plain = createPassword(8)
    
    # Encrypt password
    salt = createSalt()
    passwd = crypt.crypt(plain, salt)
    
    # Create login 
    sql = "INSERT INTO logins(username, domain, passwd, enabled) VALUES(%s, " \
        "%s, %s, %s)"
    session.execute(sql, (details['username'], details['domain'], passwd, 1))
    
    # Get the login_id that was created for the user
    sql = "SELECT currval('logins_login_id_seq') AS login_id"
    details['login_id'] = session.query(sql, ())[0][0]
    updateShadowPassword(session, details['login_id'], plain)

    try:
        details['quota'] = int(details['quota'])
    except ValueError or KeyError:
        details['quota'] = -1
    try:
        if len(details['fwdto']) == 0:
            details['fwdto'] = -1
    except ValueError or KeyError:
        details['fwdto'] = -1

    # Create email account
    props = ['login_id', 'customer_id', 'quota', 'fwdto']
    sql, values = buildInsertFromDict("email_account", props, details, True)
    
    session.execute(sql,values)
    #sql = "INSERT INTO email_account(login_id, customer_id) VALUES (%s, %s)"
    #session.execute(sql, (login_id, customer_id))

    # If we started a changeset, commit it
    if commit == 1:
        session.commit()
 
    if "passwd" in details.keys() and len(details['passwd']) > 1:
        return (details['login_id'], "")
    else:
        return (details['login_id'], plain)

@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
@registerEvent("customerModified")  
def editMailbox(session_id, details):
    """
    Will edit an existing email account. If a password is supplied it will be
    used to update the logins table as well.
    """
    session = getSessionE(session_id)
    
    #Check values
    verifyMailbox(details)
    
    # If not in a changeset, create one to group these commands together
    commit = 0
    if session.changeset == 0:
        session.begin("Edited mailbox %s" % details["username"], '', 1)
        commit = 1

    # create a password
    if "passwd" in details.keys() and len(details['passwd']) > 1:
        plain = details['passwd']
        salt = createSalt()
        passwd = crypt.crypt(plain, salt)
        sql = "UPDATE logins SET passwd=%s WHERE login_id=%s"
        session.execute(sql, (passwd, details['login_id']))
        updateShadowPassword(session, details['login_id'], passwd)

    
    try:
        details['quota'] = int(details['quota'])
    except ValueError or KeyError:
        details['quota'] = -1

    try:
        if len(details['fwdto']) == 0:
            details['fwdto'] = -1
    except ValueError or KeyError:
        details['fwdto'] = -1

    # Update email account
    props = ['customer_id', 'quota', 'fwdto']
    sql, values = buildUpdateFromDict("email_account", props, details, "login_id", details['login_id'], True)

    session.execute(sql,values)
    
    # If we started a changeset, commit it
    if commit == 1:
        session.commit()

    #Figure out whether it is tied to a broadband account
    sql = "SELECT count(login_id) FROM broadband_account WHERE login_id=%s"
    res2 = session.query(sql, (details['login_id']))

    if int(res2[0][0]) == 1:
        triggerEvent(session_id, "customerModified", login_id=details['login_id'])
        
    return ""

@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
def delMailBox(session_id, login_id):
    from ccs_contact import verifyLoginID
    """
    Will delete the email account and if now redundant, the
    login as well.
    """
    
    #Check values
    verifyLoginID(login_id)
    
    #Check if there is no other account using this login
    if session.getCountOf("SELECT count(l.login_id) from " \
        "logins l left join customers c on l.login_id = " \
        "c.login_id left join admins a on a.login_id = l.login_id where " \
        "c.customer_id IS NULL and admin_id IS NULL AND l.login_id=%s") == 0:
 
        #remove the login (email account will be cascaded)
        sql = "DELETE FROM logins WHERE login_id=%s"
    else:
        #remove the email account (leave the login alone)
        sql = "DELETE FROM email_account WHERE login_id=%s"

    session.execute(sql,(login_id))
    
    return True

def verifyDomain(domain):
    """
    Verify that the requested domain exists.
    """
    session = getSessionE(ADMIN_SESSION_ID)
    
    # Check it exists
    if session.getCountOf("SELECT count(*) as n FROM email_domain WHERE " \
            "domain=%s", (domain)) != 1:
        raise ccs_email_error("Domain does not exist!")

    return 

    
@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
def addEmailDomain(session_id, details):
    """
    Create a new email domain
    """
    session = getSessionE(ADMIN_SESSION_ID)
    
    #Check values
    verifyEmailDomain(details)
    try:
        if len(details['catchall']) == 0:
            details['catchall'] = -1
    except ValueError or KeyError:
        details['catchall'] = -1
    try:
        if len(details['redirect']) == 0:
            details['redirect'] = -1
    except ValueError or KeyError:
        details['redirect'] = -1
    
    props = ['customer_id', 'domain', 'catchall', 'redirect']
    sql, values = buildInsertFromDict("email_domain", props, details, True)
    
    session.execute(sql,values)
    
    return True

@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
def editEmailDomain(session_id, details):
    """
    Edit existing email domain
    """
    session = getSessionE(ADMIN_SESSION_ID)
    
    #Check values
    verifyEmailDomain(details)

    try:
        if len(details['catchall']) == 0:
            details['catchall'] = -1
    except ValueError or KeyError:
        details['catchall'] = -1
    try:
        if len(details['redirect']) == 0:
            details['redirect'] = -1
    except ValueError or KeyError:
        details['redirect'] = -1
    props = ['customer_id', 'domain', 'catchall', 'redirect']
    sql, values = buildUpdateFromDict("email_domain", props, details, "domain", details['domain'], True)
    
    session.execute(sql,values)
    
    return True


def verifyMailbox(details):
    """
    Verify all email account related fields.
    Raise exceptions if a field is not valid
    """
    from ccs_billing import verifyCustomerID
    # These are strict matchs as they will be used on the customer interface
    email = re.compile("^([a-z]([a-z0-9][a-z0-9._]?)*[a-z0-9]@" \
        "[a-z0-9]+\.([a-z0-9][a-z0-9.]?)*[a-z0-9])?$")

    # Check customer ID
    if 'customer_id' in details.keys():
        verifyCustomerID(details["customer_id"])
    else:
        raise ccs_email_error("Customer ID must be supplied")
    
    # Check domain exists
    if 'domain' in details.keys() and len(details['domain']) > 1:
        verifyDomain(details["domain"])
    else:
        raise ccs_email_error("Domain must be supplied")
    
    # Check that the username and domain combined are valid
    if 'username' in details.keys():
        if email.match("%s@%s" % (details['username'], details['domain'])) \
            == None:
            raise ccs_email_error("Invalid username")
    else:
        raise ccs_email_error("Username must be supplied")

    # Check quota if it exists
    if "quota" in details.keys() and len(details['quota']) > 1:
        # Check it's numeric
        try:
            quota_id = int(details['quota'])
        except ValueError:
            raise ccs_email_error("Quota must be numeric!")
    
    # Check forward to address
    if "fwdto" in details.keys() and \
        email.match(details["fwdto"]) == None:
        
        raise ccs_email_error("Invalid forward-to email address")

    return
    
def verifyEmailDomain(details):
    """
    Verify all fields related to an email domain raises
    an exception on an invalid field
    """
    from ccs_billing import verifyCustomerID
    # These are strict matchs as they will be used on the customer interface
    email = re.compile("^([a-z]([a-z0-9][a-z0-9._]?)*[a-z0-9]@" \
        "[a-z0-9]+\.([a-z0-9][a-z0-9.]?)*[a-z0-9])?$")
    domain = re.compile("^([a-z0-9]+\.([a-z0-9][a-z0-9.]?)*[a-z0-9])?$")

    # Check customer ID
    if 'customer_id' in details.keys():
        verifyCustomerID(details["customer_id"])
    else:
        raise ccs_email_error("Customer ID must be supplied")

    #Check domain and emails
    if 'domain' in details.keys() and len(details['domain']) > 1:
        if domain.match(details["domain"]) == None:
            raise ccs_email_error("Invalid domain")
    else:
        raise ccs_email_error("Domain must be supplied")

    if "catchall" in details.keys() and \
        email.match(details["catchall"]) == None:
        
        raise ccs_email_error("Invalid catchall email address")

    if "redirect" in details.keys() and \
        domain.match(details["redirect"]) == None:
        raise ccs_email_error("Invalid redirect email address")

    return

def cleanLogins():
    """
    Clean up routine that will find logins that are no longer used
    by any other table.
    """
    session = getSessionE(ADMIN_SESSION_ID)
    sql = "DELETE from logins where login_id=(SELECT l.login_id from " \
        "logins l left join customers c on l.login_id = " \
        "c.login_id left join admins a on a.login_id = l.login_id left join " \
        "email_account e on e.login_id = l.login_id where c.customer_id IS " \
        "NULL and admin_id IS NULL and e.customer_idIS NULL)"
    session.execute(sql, ())
    return
