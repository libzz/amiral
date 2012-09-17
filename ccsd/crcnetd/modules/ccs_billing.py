# Copyright (C) 2007  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# CFengine Billing Infrastructure
#
# Manages all billing related tasks in the configuration system. Requires the
# RADIUS module to be loaded first, to provide traffic and usage information.
#
# Author:       Ivan Meredith <ivan@ivan.net.nz>
#               Matt Brown <matt@crc.net.nz>
#               Chris Browning <chris.ckb@gmail.com>
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
from crcnetd._utils.ccsd_email import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC, registerRecurring, \
        registerDailyAt
from crcnetd._utils.ccsd_config import config_get, config_getint, config_getboolean
#from crcnetd.modules.ccs_contact import addContact, editContact
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

from datetime import datetime, timedelta

from Cheetah.Template import Template

ccs_mod_type = CCSD_SERVER

invoice_store = None
billing_template_dir = None
trml_path = None
invoice_payment_day = None
invoice_payment_notify_days = None
DEFAULT_INVOICE_STORE = "/var/lib/ccsd/invoices"
DEFAULT_PAYMENT_DAY = 20
DEFAULT_PAYMENT_NOTIFY_DAYS = 2

CONNECTION_METHOD_WIRELESS = "Wireless"
CONNECTION_METHOD_ETHERNET = "Ethernet"
CONNECTION_METHODS = [ CONNECTION_METHOD_WIRELESS, CONNECTION_METHOD_ETHERNET ]

# The property name for the link to allocate ethernet customer IPs from
ETHERNET_CUSTOMER_LINK_PROPERTY = "ethernet_customer_link"

# The property name for the firewall class to give to ethernet customers
ETHERNET_CUSTOMER_FIREWALL_PROPERTY = "ethernet_customer_firewall"

class ccs_billing_error(ccsd_error):
    pass   

#####################################################################
# Billing Engine Scheduling Setup
#####################################################################
@registerEvent("billingRegularUpdate")
@registerRecurring(60*5)
def billingRegularUpdate():
    """Co-ordinates billing engine actions that should occur 'regularly'"""
    session = getSession(ADMIN_SESSION_ID)

    # Update customer state with the latest usage details from RADIUS
    log_info("Updating RADIUS usage details")
    sql = "UPDATE broadband_account SET last_updated=NOW(), used_mb=used_mb+" \
        "COALESCE(( SELECT SUM(t.acctinputoctets+t.acctoutputoctets)/1024/1024 " \
        "as mb FROM radius_session s, radius_traffic t, customers c INNER JOIN " \
        "logins l ON l.login_id= c.login_id WHERE s.radacctid=t.radacctid AND " \
        "(s.username=l.username OR (s.username= l.username || '@' || " \
        "l.domain)) AND c.login_id=broadband_account.login_id AND " \
        "t.accttime>broadband_account.last_updated), 0)"
    #session.execute(sql, ())

    # Trigger an event that can be picked up by other modules that wish to
    # perform tasks at this time
    triggerEvent(ADMIN_SESSION_ID, "billingRegularUpdate")

@registerEvent("billingDaily")
@registerEvent("billingWeekly")
@registerEvent("billingMonthly")
@registerDailyAt(00, 30, 00)
def updateNightly():
    """Co-ordinates billing engine actions that occur 'nightly'

    Also deals with 'nightly' actions that happen on a weekly or monthly
    basis.
    """
    
    # Trigger daily actions
    triggerEvent(ADMIN_SESSION_ID, "billingDaily")

    # XXX: Make day of week and day of month configurable
    # Trigger weekly actions
    if datetime.now().weekday() == 0:
        triggerEvent(ADMIN_SESSION_ID, "billingWeekly")

    # Trigger monthly actions
    if datetime.now().day == 1:
        triggerEvent(ADMIN_SESSION_ID, "billingMonthly")

    # Billing and data export requirements
    if datetime.now().day == 1:
        # Generate invoices on the first of the month
        generateInvoices()

    if datetime.now().day == 19:
        # Export the payments file on the 19th
        generatePaymentExport()

@registerEvent("billingMonthEnd")
@registerDailyAt(23, 59, 00)
def billingMonthEnd():
    """Triggers the end of month event for the billing system"""

    # Trigger end of month actions
    now = datetime.now()
    lastday = calendar.monthrange(now.year, now.month)[1]
    if datetime.now().day == lastday:
        triggerEvent(ADMIN_SESSION_ID, "billingMonthEnd")
        generateDiscounts()

#####################################################################
# Billing Plan manipulation
#####################################################################
class ccs_billing_plan(ccs_class):
    def __init__(self, session_id):
        self._session_id = session_id
    
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def addPlan(self,details):
        """
        Adds a plan into the database.
        details is the dictionary of data used to create the plan,
        it MUST contain a name for the plan.

        Returns true on success
        """

        session = getSessionE(self._session_id)
        
        props = ["plan_name", "description", "price", "radius_plan", \
                "included_mb", "cap_period", "cap_action", "cap_param", \
                "cap_price"]

        (sql, values) = buildInsertFromDict("billing_plan", props, 
                details)
        session.execute(sql,(values))
        
        sql = "SELECT currval('public.billing_plan_plan_id_seq') AS plan_id"

        return session.query(sql, ())
        
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def editPlan(self, details):
        """
        Changes a plan to the details provided in the dictionary "details"

        details MUST contain a plan_id key and value.
        """
        session = getSessionE(self._session_id)
        
        props = ["plan_name", "description", "price", "radius_plan", \
                "included_mb", "cap_period", "cap_action", "cap_param", \
                "cap_price"]
        plan_id = details["plan_id"]
        (sql, values) = buildUpdateFromDict("billing_plan", props, details, \
                "plan_id", plan_id)

        session.execute(sql, values)

        return True
        
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def removePlan(self, plan_id):
        """
        Removes a plan with the id of plan_id.

        Returns true on success.
        """
        session = getSessionE(self._session_id)

        sql = "DELETE FROM billing_plan WHERE plan_id=%s"

        res = session.execute(sql, (plan_id))
        
        return True

    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def listPlans(self):
        """
        Returns a list of all plans.
        """
        session = getSessionE(self._session_id)
        
        sql = "SELECT * FROM plans"

        return session.query(sql,())

    
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getPlan(self,plan_id):
        """
        Returns a dictionary of details about the plan with the id of
        plan_id
        """
        session = getSessionE(self._session_id)
        
        sql = "SELECT * FROM plans WHERE plan_id=%s"

        res =  session.query(sql, (plan_id))
        return res
    
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def addPlanDomain(self, plan_id, domain):
        """
        Adds a allowed domain to a plan
        """
        session = getSessionE(self._session_id)
        
        sql = "INSERT INTO plan_allowed_domains VALUES (%s,%s)"

        session.execute(sql, (plan_id, domain))
        return 1
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def delPlanDomain(self, plan_id, domain):
        """
        Removes an allowed domain from a plan
        """
        session = getSessionE(self._session_id)
        
        sql = "DELETE FROM plan_allowed_domains WHERE plan_id=%s AND domain=%s"

        session.execute(sql, (plan_id, domain))
        return 1
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getPlanDomains(self,plan_id):
        """
        Gets a list of allowed domains for a given plan
        """
        session = getSessionE(self._session_id)
        
        sql = "SELECT * FROM plan_allowed_domains WHERE plan_id=%s"

        res =  session.query(sql, (plan_id))
        return res
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getPlanAllowedDomains(self,plan_id):
        """
        Gets a list of domains that this domain could have addded
        to its list of allowed domains
        """
        session = getSessionE(self._session_id)
        sql = "SELECT v.* FROM v_domains v LEFT JOIN (SELECT domain FROM " \
            "plan_allowed_domains d WHERE plan_id = %s) AS d ON " \
            "v.domain = d.domain WHERE v.redirect IS NULL AND d.domain IS NULL"
        
        res =  session.query(sql, (plan_id))
        return res

#####################################################################
# Customer account manipulation and management
#####################################################################
class ccs_customer(ccs_class):
    def __init__(self, session_id):
        self._session_id = session_id
    

    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getCustomerList(self, page = -1, num = -1, search_field="", search_value=""):
        """
        This returns a list of customers. if page and num are specified the
        list returned will be a page of size num. If search_field and
        search_value are specified, a list will be returned of records matching
        the search term.
        """

        page = int(page)
        num = int(num)
        session = getSessionE(self._session_id)
        sql = "SELECT c.customer_id, l.username, c.givenname, c.surname, " \
                "b.plan_name, b.description as billing_plan_desc, " \
                "s.used_mb, s.cap_at_mb, s.plan_start, r.plan_name AS " \
                "radius_plan_name, r.upstream_kbps, r.downstream_kbps, " \
                "b.cap_period FROM logins l, customers c, radius_plan r, " \
                "billing_plan b, broadband_account s WHERE " \
                "s.plan_id=b.plan_id AND l.login_id=s.login_id AND " \
                "s.radius_plan=r.plan_id AND l.login_id=c.login_id" 
        
        # '~*' in the sql query means match case insenstive regex. The ^
        # infront ofthe %s is match from beginning of string.
        if search_field != "" and search_value != "":
            if search_field == 'username':
                table = 'l'
            else:
                table = 'c'
            sql += " AND %s.%s ~* '^%s'" % (table, search_field, search_value)
        
        res = session.query(sql, ())

        for temp in res:
            # Calculate some cap statistics
            temp["total_mb"] = int(temp["used_mb"])
            temp["cap_usage"] = "%.0f%%" % \
                    ((float(temp["total_mb"]) / float(temp["cap_at_mb"])) * 100)

            # Makes sure negative data amounts are not displayed
            for t in ["used_mb", "total_mb"]:
                if temp[t] < 0: temp[t] = 0
            if temp["cap_usage"].startswith("-"): temp["cap_usage"] = "0%"
            # Create an integer value of cap_usage
            temp["cap_usage_int"] = int(temp["cap_usage"][:-1])

            # Format the date into a nicer format
            d = temp["plan_start"][:10]
            d = datetime(int(d[:4]),int(d[5:7]),int(d[8:10]))
            temp["plan_start"] = d.strftime("%d %b %Y")
            
            # Work out time till next data reset
            if temp["cap_period"] == "weekly":
                t = list(time.localtime())
                t[2] += 6-datetime.now().weekday()
                t = time.localtime(time.mktime(t))
                temp["cap_period"] = time.strftime("%d %b %Y", t)
            elif temp["cap_period"] == "monthly":
                c = calendar.monthrange(datetime.now().year, 
                        datetime.now().month)[1]
                temp["cap_period"] = time.strftime("%d %%b %%Y" % (c), 
                        time.localtime())
            
            # Append the spend
            temp["radius_plan_desc"] = "%s - %d/%d" % \
                    (temp["radius_plan_name"], temp["upstream_kbps"], \
                    temp["downstream_kbps"])
        
        # Define a comparison function for sorting data.
        def _ressort(x, y):
            if x["username"] > y["username"]:
                return 1
            else:
                return -1
        
        res.sort(cmp=_ressort)
        
        # Work out how many pages worth of output there are before extracting
        # the page out of the output so that we can show the user how many
        # pages there are.
        pages = int(len(res)) / int(num)
        if len(res) % int(num) != 0:
            pages += 1
            
        # Shorten the results to just one page of size num.
        if num != -1 and page != -1:
            res = res[page*num-num:page*num]
        
        if len(res) == 0:
            pages = 1
            
        return [res, range(1, pages+1)]
        
    
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getSearchFields(self):
        """
        This function contains the field names that can be used for the
        search field in getCustomerList
        """
        return {"username":"Username","givenname":"First name",
                "surname":"Last name"}
    
    
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getRadiusPlans(self):
        """
        Gets a list of all radius plans and returns it.
        """
        session = getSessionE(self._session_id)

        sql = "SELECT * FROM radius_plan"

        return session.query(sql, ())

    def updateCustomerState(self, login_id, customer_id, plan_id, charged):
        session = getSessionE(self._session_id)

        #Check for a plan change.
        sql = "SELECT plan_id, charged FROM broadband_account WHERE login_id=%s"

        res = session.query(sql, (login_id))
        if charged != res[0]['charged']:
            sql = "UPDATE broadband_account SET charged=%s WHERE login_id=%s"
            session.execute(sql, (charged, login_id))
        
        #If there was a change stop the rest of the processing.
        if int(res[0]["plan_id"]) == int(plan_id):
            return True

        sql = "SELECT * from plans WHERE plan_id=%s"

        plans = session.query(sql, (plan_id))

        if len(res) != 1:
            raise ccs_billing_error("Plan does not exist")
        
        sql = "SELECT * FROM billing_record WHERE customer_id=%s" \
            "AND record_type = 'Plan' ORDER BY record_date DESC LIMIT 1"

        # Only to billing stuff if the account is charged
        if charged == 't':
            bill = session.query(sql, (customer_id))
            
            if len(bill) != 1:
                raise ccs_billing_error("Billing record does not exist..." \
                        "This wrong and bad")

            # How many days are there in the current month?
            daymonthend = calendar.monthrange(datetime.now().year, \
                datetime.now().month)[1]
            # Find when the billing record was made.
            daystart = time.strptime(bill[0]["record_date"][:19], \
                "%Y-%m-%d %H:%M:%S")[2]
            # Find todays day number.
            daynow = datetime.now().day
            
            # Calculate how much credit we would be giving the customer back based
            # on how far into the month they are, and when the billing record was
            # made.
            credit_percent = round(float(daynow-daymonthend)/ float(daymonthend),2)
            credit = bill[0]["amount"]

            # Calculate how much currency we are going to charge for this part of
            # the months plan based on how far through the month we are.
            new_days = daymonthend-daynow
            new_percent = round(float(new_days) /float(daymonthend),2)
            newamount = plans[0]["price"]

            sql = "INSERT INTO billing_record VALUES (%s, null, " \
                "CURRENT_TIMESTAMP, %s,%s, %s, 'Credit')"
            desc = "Credit %s days of: %s" % (daymonthend-daynow, bill[0]["description"])
            session.execute(sql, (customer_id, desc, credit, credit_percent))
                
            sql = "INSERT INTO billing_record VALUES (%s, null, " \
                "CURRENT_TIMESTAMP, %s, %s, %s, 'Plan')"

            # If it's a reasonable number, bill the customer for them
            if new_days > 0:
                description = "%s (%d days): %s" % \
                        (datetime.strftime(datetime.now(), "%b %Y"), new_days, \
                        plans[0]["description"])
                session.execute(sql, (customer_id, description, newamount, new_percent))

        sql = "UPDATE broadband_account SET plan_id=%s, cap_at_mb=%s, " \
            "radius_plan=%s WHERE login_id=%s"

        session.execute(sql, (plan_id, plans[0]["included_mb"], \
            plans[0]["radius_plan"], login_id))

    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def activateCustomer(self, customer_id, day):
        """Activates a customer's plan, and inserts first billing record"""
        session = getSessionE(self._session_id)    

        # If not in a changeset, create one to group these commands together
        commit = 0
        if session.changeset == 0:
            session.begin("Activate Customer", '', 1)
            commit = 1

        # Retrieve plan details if not activated yet
        sql = "SELECT p.description, price, login_id, charged FROM broadband_account " \
            "a JOIN billing_plan p USING(plan_id) JOIN customers c " \
            "USING(login_id) WHERE customer_id=%s AND a.activated IS NULL"

        res = session.query(sql, (customer_id))

        if len(res) != 1:
            raise ccs_billing_error("Could not activate: no activateable " \
                "account found")
            
        # Only bill if marked to charge
        if res[0]['charged'] == 't':
            # Determine how many days remain in this month
            now = datetime.now()
            then = datetime(now.year,now.month,int(day))
            monthend = calendar.monthrange(then.year, then.month)[1]
            today = then.day
            days = monthend - today
            quantity = round(float(days)/float(monthend), 2)
            
            # If it's a reasonable number, bill the customer for them
            if days > 0:
                description = "%s (%d days): %s" % \
                        (datetime.strftime(then, "%b %Y"), days, \
                        res[0]["description"])
                sql = "INSERT INTO billing_record (customer_id, invoice_id, " \
                        "record_date, description, amount, quantity, record_type) VALUES " \
                        "(%s, NULL, CURRENT_TIMESTAMP, %s, %s, %s, 'Plan')"
                session.execute(sql, (int(customer_id), description, \
                        res[0]["price"], quantity))
        
        # Mark the accound as activated
        sql = "UPDATE broadband_account SET activated = %s where " \
              "login_id = %s"
        session.execute(sql, (str(then), res[0]['login_id']))
        
        # If we started a changeset, commit it
        if commit == 1:
            session.commit()
        return True

    @registerEvent("customerAdded")
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def addCustomer(self, contact):
        """Adds the specified customer to the database
        
        If the customer was sucessfully added to the data a dictionary with two
        items, (customer_id and plain) is returned. Plain contains the password
        for the customer if one wasn't specified.
        """
        session = getSessionE(self._session_id)    
        
        # verify contact details
        verifyCustomer(self._session_id, contact, True)
        verifyLogin(self._session_id, contact, True)

        # create a password
        plain = createPassword(8)
        salt = createSalt()
        passwd = crypt.crypt(plain, salt)
        
        # If not in a changeset, create one to group these commands together
        commit = 0
        if session.changeset == 0:
            session.begin("Created new contact %s" % contact["username"], '', 1)
            commit = 1

        # Now setup the customer specific information
        if not contact.has_key("plan_id"):
            contact["plan_id"] = getDefaultPlanID(self._session_id)
        if not contact.has_key("billing_name"):
            contact["billing_name"] = "%s %s" % \
                    (contact["givenname"], contact["surname"])
        if not contact.has_key("billing_address"):
            contact["billing_address"] = contact["address"]
        if not contact.has_key("connection_method"):
            raise ccs_billing_error("Connection method must be specified!")
        if contact["connection_method"] not in CONNECTION_METHODS:
            raise ccs_billing_error("Invalid connection method!")
        # insert the login record
        sql = "INSERT INTO logins (login_id, username, domain, enabled, "\
            "passwd) VALUES (DEFAULT, %s, %s, %s, %s)" 
        session.execute(sql, (contact["username"], contact["domain"], 1, passwd))

        # Get the login_id that was created for the user
        sql = "SELECT currval('logins_login_id_seq') AS login_id"
        login_id = session.query(sql, ())[0][0]
        
        # insert the customer record
        sql = "INSERT INTO customers (customer_id, login_id, givenname, surname, " \
                "phone, email, address, billing_name, billing_address) VALUES (DEFAULT, " \
                "%s, %s, %s, %s, %s, %s, %s, %s)"
        session.execute(sql, (login_id, contact["givenname"], \
                contact["surname"], contact["phone"], contact["email"], \
                contact["address"], contact["billing_name"], contact["billing_address"]))
        
        # Get the customer_id that was created for the user
        sql = "SELECT currval('customers_customer_id_seq') AS customer_id"
        customer_id = session.query(sql, ())[0][0]
    
        # Retrieve plan details
        sql = "SELECT plan_id, description, included_mb, " \
                "radius_plan, price FROM plans WHERE plan_id=%s"
        res = session.query(sql, (contact["plan_id"]))

        #Setup account
        sql = "INSERT INTO broadband_account (account_id, login_id, plan_id, plan_start, cap_at_mb, last_updated, radius_plan, connection_method)" \
            "VALUES (DEFAULT, %s, %s, CURRENT_TIMESTAMP, %s, CURRENT_TIMESTAMP, %s, %s)"
        session.execute(sql, (login_id, contact['plan_id'], res[0]["included_mb"], res[0]["radius_plan"], contact['connection_method']))
        
        #Setup an email account for them
        sql = "INSERT INTO email_account(login_id, customer_id) VALUES (%s,%s)"
        session.execute(sql, (login_id, customer_id))

        #Create a shadow password after email_account exists
        updateShadowPassword(session, login_id, plain)

        # If we started a changeset, commit it
        if commit == 1:
            session.commit()
            
        # Raise an event
        triggerEvent(self._session_id, "customerAdded", login_id=login_id)

        return (customer_id, plain)

    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    @registerEvent("customerModified")  
    def genCustomerPassword(self, customer_id, login_id):
        from ccs_contact import verifyLoginID
        """
        Will generate a new password for a customer
        """
        session_id = self._session_id
        session = getSessionE(session_id)

        #Check values
        verifyLoginID(session_id, login_id)
        verifyCustomerID(customer_id)
        
        plain = createPassword(8)
        
        # Encrypt password
        salt = createSalt()
        passwd = crypt.crypt(plain, salt)
        sql = "UPDATE logins SET passwd=%s WHERE login_id=%s"
        session.execute(sql, (passwd, login_id))
        updateShadowPassword(session, login_id, plain)

        # Raise an event
        triggerEvent(session_id, "customerModified", login_id=login_id)

        return plain

    @registerEvent("customerModified")
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def editCustomer(self, contact):
        """Updates the specified customer in the database"""
        session = getSessionE(self._session_id)
        # verify contact and login details
        verifyCustomer(self._session_id, contact, False)
        verifyLogin(self._session_id, contact, False)
        
        # If not in a changeset, create one to group these commands together
        commit = 0
        if session.changeset == 0:
            session.begin("Created new contact %s" % contact["username"], '', 1)
            commit = 1

        #Update the customers table
        props = ['givenname', 'surname', 'billing_name', 'billing_address', \
            'address', 'email', 'phone']
        sql, p = buildUpdateFromDict('customers', props, contact, "login_id", contact["login_id"])
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
        
        if "passwd" in contact.keys() and len(contact["passwd"])>0:
            updateShadowPassword(session, contact["login_id"], plain)
        
        # Update the state table if necessary (plan changes, etc)
        if 'plan_id' in contact.keys():
            self.updateCustomerState(contact["login_id"], contact["customer_id"], contact["plan_id"], contact['charged'])
        # If we started a changeset, commit it
        if commit == 1:
            session.commit("Automatically generated changeset.")
            
        # Raise an event
        triggerEvent(self._session_id, "customerModified", login_id=contact['login_id'])

        return contact["customer_id"]

        
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getCustomer(self, customer_id, subAddress=False):
        """Get infomation about a customer"""
        session = getSessionE(self._session_id)

        sql = "SELECT c.*, p.plan_id, p.description as plan_desc , l.username, l.domain, l.login_id, b.connection_method, b.activated, b.charged FROM " \
                "customers c, broadband_account b, billing_plan p, logins l WHERE b.plan_id=p.plan_id " \
                "AND b.login_id=c.login_id AND customer_id=%s AND l.login_id=c.login_id"

        res = session.query(sql, (customer_id))

        # Ensure the billing address and name is filled in if possible
        contact = res[0]
        if subAddress and len(contact["billing_address"].strip()) <= 0:
            contact["billing_address"] = contact["address"]
        if subAddress and len(contact["billing_name"].strip()) <= 0:
            contact["billing_name"] = "%s %s" % (contact["givenname"], contact["surname"])

        # XXX: Store/Retrieve these properly!
        contact["bank"] = "00"
        contact["branch"] = "0000"
        contact["bankaccountno"] = "0000000"
        contact["banksuffix"] = "000"
        return contact

    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getHistoryDates(self, customer_id):
        """
        Gets the dates which data history for a customer can be obtained.
        """
        
        session = getSessionE(self._session_id)
    
        sql = "SELECT join_date FROM customers WHERE customer_id=%s"
        res = session.query(sql, (customer_id))
        join_date = time.strptime(res[0]["join_date"][:19], \
            "%Y-%m-%d %H:%M:%S")
        year = join_date[0]
        month = join_date[1]
        ret = {}
        caption = "%s %s"
        
        # We only archive 3 months, mark the archive date
        fyear = datetime.now().year
        fmonth = datetime.now().month - 3
        if fmonth < 1:
            fyear -= 1
            fmonth = 12 + fmonth

        # If the mark is closer to now that the join date, lock to archive mark
        if fyear > year:
            year = fyear
            month = fmonth
        elif fyear == year:
            if fmonth > month:
                month = fmonth
        
        while year != datetime.now().year or month <= datetime.now().month:
            ret["%04d%02d" % (year,month)] = caption % \
                    (calendar.month_abbr[month], year)
            month += 1
            if month > 12:
                month = 1
                year += 1
        
        return ret

    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getTrafficHistory(self, customer_id, year, month, startday=1):
        """Retrieves a dictionary indexed by day of month, containing the
        number of mb of traffic used on that day by the specified customer"""

        session = getSessionE(self._session_id)

        # Check valid dates have been specified
        year = int(year)
        month = int(month)
        if year == 0:
            year = time.localtime()[0]
        if month == 0:
            month = time.localtime()[1]

        # Days in the requested month
        no_days = calendar.monthrange(year, month)[1]
        
        # Initialise to 0
        days = dict([(day, {"input":0,"output":0}) \
                for day in range(1, no_days+1)])
        
        #Pad month
        if len(str(month)) == 1:
            month = "0%s" % month
        
        
        # Select the traffic
        res = session.query("SELECT t.accttime::date, sum(t.acctinputoctets) " \
            "as acctinputoctets, sum(t.acctoutputoctets) as acctoutputoctets " \
            "from radius_traffic_part_%s_%s t left join " \
            "radius_session_complete s using(radacctid)  where username = " \
            "(select username || '@'::text || domain from logins where " \
            "login_id = (select login_id from customers where customer_id = " \
            "%%s)) group by accttime::date, username order by " \
            "accttime::date;" % (year, month), (customer_id))
        for day in res:
            dno = int(day["accttime"].split( )[0].split('-')[2])
            #if dno < startday: continue
            days[dno]["input"] = int(round(day["acctinputoctets"]/1024/1024))
            days[dno]["output"] = int(round(day["acctoutputoctets"]/1024/1024))
        return days

def verifyCustomerID(customer_id):
    """
    Check that the customer_id is valid and exists
    """
    session = getSessionE(ADMIN_SESSION_ID)

    # Check it's numeric
    try:
        customer_id = int(customer_id)
    except TypeError:
        raise ccs_billing_error("Contact ID must be numeric!")

    # Check it exists
    if session.getCountOf("SELECT count(*) as n FROM customers WHERE " \
            "customer_id=%s", (customer_id)) != 1:
        raise ccs_billing_error("Invalid customer ID!")

    return 

def verifyCustomer(session_id, contact, add):
    """
    Check the fields in the dictionary for sanity for adding
    or editing a customer
    """
    from ccs_email import verifyDomain
    verifyCommon(session_id, contact, add)
    email = re.compile("^([a-z]([a-z0-9][a-z0-9._]?)*[a-z0-9]@[a-z0-9]+\.([a-z0-9][a-z0-9.]?)*[a-z0-9])?$")

    if "domain" not in contact.keys():
        raise ccs_billing_error("Domain must be specified")
    if "domain" in contact.keys():
        verifyDomain(contact["domain"])

    # Check that the username and domain combined are valid
    if 'username' in contact.keys():
        if email.match("%s@%s" % (contact['username'], contact['domain'])) \
            == None:
            raise ccs_billing_error("Invalid username")
    else:
        raise ccs_billing_error("Username must be supplied")

    if "customer_id" not in contact.keys() and not add:
        ccs_billing_error("Customer ID must be specified")
    if "customer_id" in contact.keys() and not add:
        verifyCustomerID(contact["customer_id"])
        

    #Ensure no xml invalid charictors are present
    exclude = re.compile("[&<>]")            
    if contact.has_key("billing_name") \
        and exclude.search(contact["billing_name"]) != None:
        raise ccs_billing_error("Characters &<> are not allowed")
        
    if contact.has_key("billing_address") \
        and exclude.search(contact["billing_address"]) != None:
        raise ccs_billing_error("Characters &<> are not allowed")
    
    return

#####################################################################
# Customer Interface Functions
#####################################################################
@exportViaXMLRPC(SESSION_RO, AUTH_AUTHENTICATED)
def getCustomerTrafficHistory(session_id, year, month, startday=1):
    customer = getCustomerDetails(session_id)

    cust = ccs_customer(session_id)
    
    res = cust.getTrafficHistory(customer['customer_id'], year, month, startday)

    return [customer['join_date'], res]
    
@exportViaXMLRPC(SESSION_RW, AUTH_AUTHENTICATED)
def getCustomerHistoryDates(session_id):
    customer = getCustomerDetails(session_id)
    
    cust = ccs_customer(session_id)

    res = cust.getHistoryDates(customer['customer_id'])

    return res

@exportViaXMLRPC(SESSION_RW, AUTH_AUTHENTICATED)
def getCustomerAllowedDomains(session_id):
    session = getSessionE(session_id)
    
    sql = "SELECT domain FROM plan_allowed_domains WHERE plan_id=" \
        "(SELECT plan_id FROM broadband_account WHERE login_id=%s)" \
        "UNION SELECT domain from email_domain WHERE customer_id= (" \
        "(SELECT customer_id from customers where login_id=%s));"
        
    res = session.query(sql, (session.login_id, session.login_id,))
    return res

@exportViaXMLRPC(SESSION_RW, AUTH_AUTHENTICATED)
def addCustomerMailbox(session_id, details):
    from ccs_email import addMailbox
    session = getSessionE(session_id)
    #XXX: Need to check the amount of emails that they are allowed
    #XXX: Need to check the domains that they are allowed
    customer = getCustomerDetails(session_id)
    details['customer_id'] = customer['customer_id']

    #This is a placeholder for a real quota from a plan
    details['quota'] = ''
    res = addMailbox(session_id, details)
    
    return res

@exportViaXMLRPC(SESSION_RW, AUTH_AUTHENTICATED)
def editCustomerMailbox(session_id, details):
    from ccs_email import editMailbox
    session = getSessionE(session_id)
    #XXX: Need to check the amount of emails that they are allowed
    #XXX: Need to check the domains that they are allowed
    checkCustomerOwnership(session_id, details['login_id'])
    customer = getCustomerDetails(session_id)
    details['customer_id'] = customer['customer_id']

    #This is a placeholder for a real quota from a plan
    details['quota'] = ''
    res = editMailbox(session_id, details)
    
    return res
def checkCustomerOwnership(session_id, login_id):
    """
    This function checks that the login_id can be traced back to
    the customer account that this session is associated to.
    Note, this function does not care if the requested login_id
    exists or not, this is good so that customers can't try probe
    how many email accounts we have.
    """
    session = getSessionE(session_id)
    sql = "SELECT l.login_id AS account_id, c.customer_id, c.login_id FROM " \
        "logins l INNER JOIN email_account e ON l.login_id=e.login_id INNER " \
        "JOIN customers c ON c.customer_id=e.customer_id WHERE c.login_id=%s" \
        "AND l.login_id=%s"
    res = session.query(sql, (session.login_id, login_id))

    if len(res) != 1:
        raise ccs_billing_error("You do not own this mailbox")
    return
    
    
@exportViaXMLRPC(SESSION_RW, AUTH_AUTHENTICATED)
def getCustomerMailboxes(session_id):
    """Return list of mailboxes this customer owns"""
    from ccs_email import getCustomersMailboxes
    session = getSessionE(session_id)
    sql = "SELECT customer_id from customers WHERE login_id=%s"
    customer_id = session.query(sql, (session.login_id))[0]['customer_id']
        
    return getCustomersMailboxes(session_id, customer_id)
    
@exportViaXMLRPC(SESSION_RW, AUTH_AUTHENTICATED)
def getCustomerMailbox(session_id, login_id):
    """Get details for a particulat mailbox this customer owns"""
    from ccs_email import getMailbox
    session = getSessionE(session_id)

    #Check that this customer owns the desired mailbox
    checkCustomerOwnership(session_id, login_id)

    return getMailbox(session_id, login_id)

@exportViaXMLRPC(SESSION_RO, AUTH_AUTHENTICATED)
def updateCustomerDetails(session_id, details):
    """Updates the specified customer in the database. Also send notification."""
    session = getSessionE(session_id)

    # verify contact and login details
    verifyCustomer(session_id, details, False)
    verifyLogin(session_id, details, False)
    msg = "%s@%s has updated their details. See below for details:\n\n" % (details['username'], details['domain'])

    customer = getCustomerDetails(session_id)

    #Figure out what has changed
    props = ['givenname', 'surname', 'billing_name', 'billing_address', \
            'address', 'email', 'phone']
    for prop in props:
        #There a some props we need to filter out just in case they are set
        if prop == 'plan_id':
            del details[prop]
        
        if details[prop] != customer[prop]:
            msg += "%s was changed from '%s' to '%s'\n" % (prop, customer[prop], details[prop])

    cust = ccs_customer(session_id)
    cust.editCustomer(details)
    send_from = config_get("billing", "email_from", "invoices")
    send_to = config_get("billing", "helpdesk_email", None)
    
    #Email notification to the helpdesk
    if send_to:
        send_mail(send_from, [send_to], "Customer Interface Update", msg)
    
    return True

@exportViaXMLRPC(SESSION_RO, AUTH_AUTHENTICATED)
def getCustomerDetails(session_id):
    """
    Gets details about the current authenticated customer.
    For use with the customer interface
    """
    session = getSessionE(session_id)
    
    #Get lots of info about the customer
    sql = "SELECT l.username, l.domain, c.*, p.*, r.*, s.* FROM " \
            "customers c, billing_plan p, radius_plan r, " \
            "broadband_account s, logins l WHERE r.plan_id = p.radius_plan " \
            "AND s.plan_id=p.plan_id AND l.login_id= c.login_id AND " \
            "c.customer_id=(SELECT customer_id from customers c2 where " \
            "s.login_id = c2.login_id AND c2.login_id=%s)"

    res = session.query(sql, (session.login_id))

    if res:
        res = res[0]

        #Get infomation about their data purchases since there last invoice
        sql = "SELECT count(*) as number, sum(amount) as amount from " \
            "billing_record where record_type='Data' AND invoice_id IS NULL " \
            "AND customer_id = %s"

        res2 = session.query(sql, (res['customer_id']))
        res['purchase_number'] = res2[0]['number']
        if res2[0]['amount'] == "":
            res2[0]['amount'] = 0
        res['purchase_cost'] = "%.2f" % float(res2[0]['amount'])
        if res["cap_period"] == "weekly":
            t = list(time.localtime())
            t[2] += 6-datetime.now().weekday()
            t = time.localtime(time.mktime(t))
            res["cap_period"] = time.strftime("%A %d/%m/%Y", t)
        elif res["cap_period"] == "monthly":
            c = calendar.monthrange(datetime.now().year, 
                    datetime.now().month)[1]
            t = list(time.localtime())
            t[2] = c
            t = time.localtime(time.mktime(t))
            res["cap_period"] = time.strftime("%A %d/%m/%Y", t)
        return res
    else:
        return []
    

#####################################################################
# Discount Handling
#####################################################################

class ccs_billing_discount(ccs_class):
    def __init__(self, session_id):
        self._session_id = session_id
    
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def addBillingDiscount(self,details):
        """
        Adds a discount into the database.
        details is the dictionary of data used to create the discount,
        it MUST contain a name for the discount.

        Returns true on success
        """

        session = getSessionE(self._session_id)
        
        props = ["discount_name", "description", "amount"]

        (sql, values) = buildInsertFromDict("billing_discount", props, 
                details)
        session.execute(sql,(values))
        
        sql = "SELECT currval('public.billing_discount_discount_id_seq') AS discount_id"

        return session.query(sql, ())
        
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def editBillingDiscount(self, details):
        """
        Changes a discount to the details provided in the dictionary "details"

        details MUST contain a discount_id key and value.
        """
        session = getSessionE(self._session_id)
        
        props = ["discount_name", "description", "amount"]
        discount_id = details["discount_id"]
        (sql, values) = buildUpdateFromDict("billing_discount", props, details, \
                "discount_id", discount_id)

        session.execute(sql, values)

        return True
        
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def removeBillingDiscount(self, discount_id):
        """
        Removes a discount with the id of discount_id.

        Returns true on success.
        """
        session = getSessionE(self._session_id)

        sql = "DELETE FROM billing_discount WHERE discount_id=%s"

        res = session.execute(sql, (discount_id))
        
        return True

    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def listBillingDiscounts(self):
        """
        Returns a list of all discounts.
        """
        session = getSessionE(self._session_id)
        
        sql = "SELECT * FROM billing_discount"

        return session.query(sql,())

    
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getBillingDiscount(self,discount_id):
        """
        Returns a dictionary of details about the discount with the id of
        discount_id
        """
        session = getSessionE(self._session_id)
        
        sql = "SELECT * FROM billing_discount WHERE discount_id=%s"

        res =  session.query(sql, (discount_id))
        return res

class ccs_customer_discount(ccs_class):
    def __init__(self, session_id):
        self._session_id = session_id
    
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def addCustomerDiscount(self,details):
        """
        Adds a discount into the database.
        details is the dictionary of data used to create the discount,
        it MUST contain a name for the discount.

        Returns true on success
        """

        session = getSessionE(self._session_id)
        
        props = ["customer_id", "discount_id", "start_date", "recurring", "end_date"]
        nulls = []
        if "end_date" in details and details["end_date"] == '':
            nulls.append("end_date");
        (sql, values) = buildInsertFromDict("customer_discount", props, 
                details, False, nulls)
        session.execute(sql,(values))
        
        sql = "SELECT currval('public.customer_discount_customer_discount_id_seq') AS customer_discount_id"

        return session.query(sql, ())
        
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def editCustomerDiscount(self, details):
        """
        Changes a discount to the details provided in the dictionary "details"

        details MUST contain a discount_id key and value.
        """
        session = getSessionE(self._session_id)
        
        props = ["customer_id", "discount_id", "start_date", "recurring", "end_date"]
        nulls = []
        if "end_date" in details and details["end_date"] == '':
            nulls.append("end_date");
        customer_discount_id = details["customer_discount_id"]
        (sql, values) = buildUpdateFromDict("customer_discount", props, details, \
                "customer_discount_id", customer_discount_id, False, nulls)

        session.execute(sql, values)

        return True
        
    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def removeCustomerDiscount(self, customer_discount_id):
        """
        Removes a discount with the id of discount_id.

        Returns true on success.
        """
        session = getSessionE(self._session_id)

        sql = "DELETE FROM customer_discount WHERE customer_discount_id=%s"

        res = session.execute(sql, (customer_discount_id))
        
        return True

    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def listCustomerDiscounts(self):
        """
        Returns a list of all discounts.
        """
        session = getSessionE(self._session_id)
        
        sql = "SELECT * FROM discount_view"

        return session.query(sql,())

    
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getCustomerDiscounts(self,customer_id):
        """
        Returns a dictionary of details about the discount with the id of
        discount_id
        """
        session = getSessionE(self._session_id)
        
        sql = "SELECT * FROM discount_view WHERE customer_id=%s"

        res =  session.query(sql, (customer_id))
        if res:
            for r in res:
                d = r['start_date'][:10]
                d = datetime(int(d[:4]),int(d[5:7]),int(d[8:10]))
                r["start_date"] = d.strftime("%d-%m-%Y")
                if r['end_date']:
                    d = r['end_date'][:10]
                    d = datetime(int(d[:4]),int(d[5:7]),int(d[8:10]))
                    r["end_date"] = d.strftime("%d-%m-%Y")
        return res
        
    @exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK, True)
    def getCustomerDiscount(self,customer_discount_id):
        """
        Returns a dictionary of details about the discount with the id of
        discount_id
        """
        session = getSessionE(self._session_id)
        
        sql = "SELECT * FROM discount_view WHERE customer_discount_id=%s"

        res =  session.query(sql, (customer_discount_id))
        if res:
            for r in res:
                d = r['start_date'][:10]
                d = datetime(int(d[:4]),int(d[5:7]),int(d[8:10]))
                r["start_date"] = d.strftime("%d-%m-%Y")
                if r['end_date']:
                    d = r['end_date'][:10]
                    d = datetime(int(d[:4]),int(d[5:7]),int(d[8:10]))
                    r["end_date"] = d.strftime("%d-%m-%Y")
        return res

def lookupDiscount(discount_id):
    session = getSessionE(ADMIN_SESSION_ID)
    sql = "SELECT * from billing_discount where discount_id=%s"
    try:
        discount = session.query(sql, (discount_id))[0]
    except:
        log_error("Failed to retrive billing_discount", sys.exc_info())
        discount = None
    return discount
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def processDiscounts(auth, as_at=None):
    generateDiscounts(as_at)
    return True

def generateDiscounts(as_at=None):
    session = getSessionE(ADMIN_SESSION_ID)
    sql = "SELECT * from customer_discount"
    try:
        discounts = session.query(sql, ())
    except:
        log_error("Failed to retrive discount records", sys.exc_info())
        discounts=[]

    # Select all unbilled records up till NOW or the time specified, 
    # date the invoice one day earlier
    if as_at is None:
        now_time =  datetime.today().strftime("%Y-%m-%d")
        db_time =  datetime.today().strftime("%Y-%m-%d %H%M%S")
    else:
        now_time = datetime.fromtimestamp(as_at).strftime("%Y-%m-%d")
        db_time = datetime.fromtimestamp(as_at).strftime("%Y-%m-%d %H%M%S")

    for discount in discounts:

        # Calculate the dates
        d = discount['start_date'][:10]
        d = datetime(int(d[:4]),int(d[5:7]),int(d[8:10]))
        start_time = d.strftime("%Y-%m-%d")

        if discount['end_date']:
            d = discount['end_date'][:10]
            d = datetime(int(d[:4]),int(d[5:7]),int(d[8:10]))
            end_time = d.strftime("%Y-%m-%d")
        else:
            end_time = now_time
        #Discard no recurring discounts that are not due
        if discount["recurring"] == False:
            if start_time != now_time:
                continue

        #Discard expired or not yet mature discounts
        elif not (now_time >= start_time and now_time <= end_time):
            continue
        
        #Give the discount
        billing_discount = lookupDiscount(discount['discount_id'])
        if billing_discount:
            sql = "INSERT INTO billing_record (customer_id, record_date, " \
                "description, amount, quantity, record_type) VALUES (%s, %s, " \
                "%s, %s, 1, 'Discount');"
            datestr = datetime.strftime(datetime.now(), "%b %Y")
            desc = "%s: %s" % (datestr, billing_discount["description"])
            try:
                session.execute(sql, (discount["customer_id"], db_time, desc, \
                    billing_discount["amount"]*-1))
            except:
                log_error("Failed to generate discount record for contact #%s" % \
                        ro["customer_id"], sys.exc_info())              


#####################################################################
# Accounting Export Handling
#####################################################################
def generateAccountingExport():
    #XXX: TODO
    pass

#####################################################################
# Payment Import/Export Handling
#####################################################################
@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
def runPaymentExport(session_id):
    return generatePaymentExport()

def generatePaymentExport():
    global billing_template_dir
    session = getSessionE(ADMIN_SESSION_ID)

    # Can't generate export file if there is no template available
    if billing_template_dir is None:
        return ""
    template = "%s/payment-export.tmpl" % billing_template_dir
    try:
        payment_export_template = Template(file=template)
    except:
        log_error("Failed to load payment export template", sys.exc_info())
        return ""

    # Retrieve a list of unpaid invoices, and some details regarding them
    invoices = session.query("SELECT * FROM billing_invoice WHERE " \
            "invoice_paid IS FALSE", ())
    invoices = map(_calculateInvoiceDetails, invoices)
    
    # Get the filename for the export
    exportno, filename = getPaymentExportFilename()
    if exportno is None or filename is None:
        log_error("Failed to retrieve payment export filename")
        return ""

    # Prepare to pass the data to the template
    info = {}
    info["invoices"] = invoices
    info["template_dir"] = billing_template_dir
    info["crlf"] = "\r\n"
    info["time"] = time
    info["exportno"] = exportno
    info["payment_date"] = time.time()
    payment_export_template._searchList = [info]
    payment_export_template._CHEETAH__searchList += payment_export_template._searchList

    # Process the template and save the file
    f= open(filename, "w")
    f.write(str(payment_export_template))
    f.close()
    
    return filename

def getPaymentExportFilename(export_date=None, exportno=None):
    """Payment export files are named NN-YYYY-MM-DD and stored under invoices/

    This function returns the full path to the export file for the specified 
    date. 

    NN is a serial number that is incremented for each new export. If neither
    the export_date or exportno is specified, the returned filename will be 
    suitable for a new export that is to be generated and processed today. 

    If either export_date or export_no is specified, then the matching 
    file is located and the full path to it returned.
    """
    global invoice_store
    base_dir = "%s/payment-exports" % invoice_store
    
    # Load list of files in the export directory
    pattern = re.compile("^([\d]{2})-([\d]{4}-[\d]{2}-[\d]{2})\.txt$")
    maxno = 0
    maxdate = 0
    ensureDirExists(base_dir)
    for file in os.listdir(base_dir):
        # Check if it matches the expected pattern
        parts = pattern.match(file)
        if not parts: continue
        # Extract the parts
        fexportno = int(parts.group(1))
        fdate = parts.group(2)
        # Store max no
        if fexportno > maxno: maxno = fexportno
        # Check for matches
        if export_date is not None:
            if time.strftime("%Y-%m-%d", time.localtime(export_date)) == fdate:
                return fexportno, "%s/%s" % (base_dir, file)
        if exportno is not None:
            if fexportno == exportno:
                return fexportno, "%s/%s" % (base_dir, file)
    
    # Return None if searching failed to find correct file
    if export_date is not None or exportno is not None:
        return None, None
    
    # Build new name
    exportno = maxno+1
    return exportno, "%s/%02d-%s.txt" % \
            (base_dir, exportno, time.strftime("%Y-%m-%d"))
    
#####################################################################
# Invoice Handling
#####################################################################
def _calculateInvoiceDetails(invoice):
    """Calculates details about the invoice, and adds to the dictionary"""
    cust = ccs_customer(ADMIN_SESSION_ID)

    invoice = filter_keys(invoice)
    ts = time.strptime(invoice["invoice_date"][:-3], "%Y-%m-%d %H:%M:%S")
    invoice["invoice_date"] = ts
    invoice["invoice_date_str"] = time.strftime("%d %b %Y", 
            invoice["invoice_date"])
    invoice["payment_date"] = getInvoicePaymentDate(time.mktime( \
            invoice["invoice_date"]))
    invoice["payment_date_str"] = time.strftime("%d %b %Y", 
            time.localtime(invoice["payment_date"]))
    invoice["payment_notify_date"] = getInvoicePaymentNotifyDate(time.mktime( \
            invoice["invoice_date"]))
    invoice["payment_notify_date_str"] = time.strftime("%d %b %Y", 
            time.localtime(invoice["payment_notify_date"]))
    #Don't do gst on credits        
    if invoice["invoice_subtotal"] > 0:
        invoice["gst"] = "%.2f" % (float(invoice["invoice_subtotal"]) * 0.125)
        invoice["total"] = "%.2f" % (float(invoice["invoice_subtotal"]) * 1.125)
    else:
        invoice["gst"] = 0
        invoice["total"] = "%.2f" % (float(invoice["invoice_subtotal"]))
    invoice["invoice_subtotal"] = "%.2f" % invoice["invoice_subtotal"]
    invoice["contact"] = cust.getCustomer(invoice["customer_id"], True)
    if invoice["invoice_file"] is None or invoice["invoice_file"] == "":
        invoice["invoice_file"] = getInvoiceFilename(invoice["contact"]["username"], invoice["invoice_id"], 
            time.mktime(invoice["invoice_date"]))
    return invoice

@exportViaXMLRPC(SESSION_RO, AUTH_HELPDESK)
def getInvoice(session_id, invoice_id):
    """Retrieves an invoice from the database and returns a dictionary"""
    session = getSessionE(session_id)

    # Fetch the invoice
    invoice = session.query("SELECT * FROM billing_invoice WHERE " \
            "invoice_id=%s", (invoice_id))
    if len(invoice) != 1:
        return None

    # Calculate some data about it
    invoice = _calculateInvoiceDetails(invoice[0])

    # Fetch the records
    records = session.query("SELECT * FROM billing_record WHERE " \
            "invoice_id=%s", (invoice_id))
    records.sort(_sort_records)
    invoice["records"] = map(_process_records, records)
    
    return invoice

def _sort_records(a, b):
    """Sorts billing Records"""
    tsa = time.strptime(a["record_date"][:-3], "%Y-%m-%d %H:%M:%S")
    tsb = time.strptime(b["record_date"][:-3], "%Y-%m-%d %H:%M:%S")
    return cmp(tsa, tsb)

def _process_records(record):
    """Helper function to prepare invoice records for passing to templates"""
    record = filter_keys(record)
    ts = time.strptime(record["record_date"][:-3], "%Y-%m-%d %H:%M:%S")
    record["record_date_str"] = time.strftime("%d %b %Y", ts)
    record["calculated_amount"] = "%.2f" % (float(record["amount"]) * \
            float(record["quantity"]))
    record["quantity"] = "%.2f" % float(record["quantity"])
    return record

@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
def getInvoicePDF(auth, invoice_id):
    filename = generateInvoicePDF(invoice_id, None)
    return filename

def generateInvoicePDF(invoice_id, overview):
    """Generates a PDF for the specified invoice and saves it to a file"""
    global billing_template_dir, trml_path

    # Can't generate PDF if there is no template available
    if billing_template_dir is None:
        return ""
    template = "%s/invoice.tmpl" % billing_template_dir
    try:
        invoice_template = Template(file=template)
    except:
        log_error("Failed to load invoice template", sys.exc_info())
        return ""

    # Fetch session info
    session = getSessionE(ADMIN_SESSION_ID)

    # Fetch the invoice
    invoice = getInvoice(ADMIN_SESSION_ID, invoice_id)

    # Get the desired location for the PDF
    invoice_file = invoice["invoice_file"]

    # Build the dictionary of data to pass to the template
    info = {}
    info["invoice_id"] = invoice_id
    info["invoice"] = invoice
    info["template_dir"] = billing_template_dir
    info["invoice_file"] = os.path.basename(invoice_file)
    info["dolarify"] = _dolarify
    invoice_template._searchList = [info]
    invoice_template._CHEETAH__searchList += invoice_template._searchList

    if overview:
        overview.write("\"%s\",%s,%s\n" % (invoice['contact']['username'], invoice_id, invoice['total']))
    
    # Check for previously unpaid invoices
    # XXX: TODO

    # Ensure the directory exists
    ensureDirExists(os.path.dirname(invoice_file))

    # Process the template and save the RML file
    if invoice_file.endswith(".pdf"):
        invoice_file = invoice_file[:-4]
    f= open("%s.rml" % invoice_file, "w")
    f.write(str(invoice_template).strip())
    f.close()
    
    # Process the RML via TRML2PDF to get the final invoice
    if log_command("python2.3 %s %s.rml > %s.pdf" % 
            (trml_path, invoice_file, invoice_file)) is None:
        return "%s.pdf" % invoice_file
    else:
        return ""

def _dolarify(value, sf=10):
    fstr = "<pre class=\"currency\">$%% %d.2f</pre>" % sf
    return fstr % float(value)

@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
def sendInvoice(auth, invoice_id):
    send_from = config_get("billing", "email_from", "invoices")
    sendInvoicePDF(send_from, invoice_id)
    return True

def inspectInvoice(invoice):
    """Preforms checks to see if the invoice seems sain enough to
       just send on to a customer or not"""

    # If there is not exactly one plan record in the invoice redirect
    plans = 0
    for record in invoice['records']:
        if record['record_type'] == "Plan":
            plans += 1
    if plans != 1:
        return False

    # If the invoice is more than $150 redirect
    if float(invoice['total']) > 150.0:
        return False

    # If the invoice is less than $0 redirect
    if float(invoice['total']) < 0.0:
        return False

    return True
    
def sendInvoicePDF(send_from, invoice_id):
    """Emails a copy of the the specified invoice to the customer"""
    global billing_template_dir
    cc_email = config_get("billing", "cc_email", None)
    if cc_email is None:
        cc_email = []
    else:
        cc_email = [cc_email]

    # Can't send email if no template available
    if billing_template_dir is None:
        return False
    template = "%s/invoice-email.tmpl" % billing_template_dir
    try:
        invoice_email_template = Template(file=template)
    except:
        log_error("Failed to load invoice email template", sys.exc_info())
        return ""
    session = getSessionE(ADMIN_SESSION_ID)

    # Retrieve invoice
    invoice = getInvoice(ADMIN_SESSION_ID, invoice_id)

    # Get the location of the PDF
    invoice_file = invoice["invoice_file"]

    # Check the PDF exists
    if not os.path.exists("%s" % invoice_file):
        invoice_file = generateInvoicePDF(invoice_id, None)
        if invoice_file == "":
            # Couldn't generate it, return false
            return False

    # Setup data for the body of the email
    info = {}
    info["invoice_id"] = invoice_id
    info["invoice"] = invoice
    info["template_dir"] = billing_template_dir
    invoice_email_template._searchList = [info]
    invoice_email_template._CHEETAH__searchList += invoice_email_template._searchList

    # If force_invoice is specified, all outgoing invoices is redirected to the
    # specified address
    force_invoice = config_get("billing", "force_invoice", None)
    if force_invoice is not None:
        invoice["contact"]["email"] = force_invoice
        
    # Pass the invoice of to be inspected, the inspection will decide whether
    # the invoice can be send to the customer, or needs to be checked first by
    # a real person.
    safe = inspectInvoice(invoice)
    safe_invoice = config_get("billing", "helpdesk_email", None)
    if not safe and safe_invoice:
        invoice["contact"]["email"] = safe_invoice
        
    # Send the email
    rv = billing_email(invoice["contact"]["email"], "Invoice #%s" % invoice_id,
            str(invoice_email_template).strip(), [invoice_file])
    if rv:
        log_info("Emailed Invoice #%s to '%s'" % \
                (invoice_id, invoice["contact"]["email"]))
        return True
    else:
        return False

def getInvoiceFilename(username, invoice_id, invoice_date):
    global invoice_store

    # The first directory is based on the invoice date
    dstr = datetime.fromtimestamp(invoice_date).strftime("%Y-%m-%d")
    invoice_dir = "%s/%s" % (invoice_store, dstr)

    # Determine the base name of the invoice
    invoice_file = "%s/%s-%s" % (invoice_dir, invoice_id, username)
    return invoice_file

def getInvoicePaymentDate(invoice_date):
    """Calculates the date that an invoice should be paid by"""
    global invoice_payment_day

    # Invoices are due on the specified day, but may need to be next month
    # if that day is before the date of this invoice
    t = datetime.fromtimestamp(invoice_date)
    if t.day >= invoice_payment_day:
        if t.month < 12:
            dd = datetime(t.year, t.month+1, invoice_payment_day)
        else:
            dd = datetime(t.year+1, 1, invoice_payment_day)
    else:
        dd = datetime(t.year, t.month, invoice_payment_day)
    return int(dd.strftime("%s"))

def getInvoicePaymentNotifyDate(invoice_date):
    """Calculates the date by which payment for an invoice can be stopped"""
    global invoice_payment_notify_days

    t = datetime.fromtimestamp(getInvoicePaymentDate(invoice_date))
    t -= timedelta(days=invoice_payment_notify_days)
    return int(t.strftime("%s"))

def generateInvoiceID():
    """Returns a new invoice ID, generated from the database sequence"""
    session = getSessionE(ADMIN_SESSION_ID)
    return session.getCountOf("SELECT nextval('billing_invoice_id_seq') " \
            "AS next", ())

@exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK)
def processInvoices(auth, as_at=None):
    return generateInvoices(as_at)

def generateInvoices(as_at=None):
    global invoice_store
    """Generates customer invoices based on the currently uninvoiced records

    An invoice is created by assigning an invoice ID to each record in the 
    billing_records table and then creating an invoice entry in the 
    billing_invoice table.

    Finally a PDF of the invoice is generated and saved in a specified
    directory.

    The optional parameter, as_at can be used to generate invoices for a 
    previous date. If this parameter is not specified, an invoice is generated
    for all uninvoiced billing records created up until the current point in time.

    Invoices are always generated for one day in the past. E.g an invoice
    created on 1st Jan 2007 (or with as_at set to 1st Jan 2007) will be dated
    31 Dec 2006.  
    """
    session = getSessionE(ADMIN_SESSION_ID)
    overview = None
    overview_str = "Invoice log:\n"
    send_email = config_getboolean("billing", "email", True)
    send_from = config_get("billing", "email_from", "invoices")
    send_overview = config_get("billing", "email_overview", None)

    # Select all unbilled records up till NOW or the time specified, 
    # date the invoice one day earlier
    if as_at is None:
        rdate = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        invoice_date = datetime.today()
    else:
        rdate = datetime.fromtimestamp(as_at).strftime("%Y-%m-%d %H:%M:%S")
        invoice_date = datetime.fromtimestamp(as_at)
    invoice_date -= timedelta(days=1)
    invoice_date = invoice_date.strftime("%Y-%m-%d")
    log_info("Generating invoices for %s with records up until %s" % \
            (invoice_date, rdate))

    if send_overview:
        ts = time.strptime(invoice_date, "%Y-%m-%d")
        file = getInvoiceFilename("view.csv", "over", time.mktime(ts))
        ensureDirExists(os.path.dirname(file))
        overview = open(file, 'w')

    # Sum all unbilled records up til the specified time
    records = session.query("SELECT customer_id, SUM(amount*quantity) AS " \
            "total FROM non_invoiced_billing_records WHERE record_date<=%s " \
            "GROUP BY customer_id", (rdate))
    if len(records) == 0:
        log_info("No billing records found. No invoices created!")
        overview_str += "No billing records found. No invoices created!\n"
        if overview:
            overview.close()
        return True
    count = 0
    total = 0
    for record in records:
        # Step 1 assign the records to an invoice
        customer_id = int(record["customer_id"])
        try:
            session.begin("Invoice for contact id: %s" % customer_id, '', 1)
            invoice_id = generateInvoiceID()
            session.execute("INSERT INTO billing_invoice (customer_id, " \
                    "invoice_id, invoice_date, invoice_subtotal) VALUES " \
                    "(%s, %s, %s, %s)",
                    (customer_id, invoice_id, invoice_date, record["total"]))
            session.execute("UPDATE billing_record SET invoice_id=%s" \
                    " WHERE customer_id=%s AND invoice_id IS NULL " \
                    "AND record_date<=%s", 
                    (invoice_id, customer_id, rdate))
            session.commit()
            count += 1
        except:
            log_error("Failed to generate invoice for contact %s!" % \
                    customer_id, sys.exc_info())
            overview_str += "Failed to generate invoice for contact %s!\n" % \
                    customer_id
            session.rollback()
            continue
        log_info("Invoice #%s created for contact #%s" % \
                (invoice_id, customer_id))
        total += 1
        # Step 2 generate a PDF and optionally email it to the customer
        try:
            filename = generateInvoicePDF(invoice_id, overview)
            if filename == "":
                log_error("Failed to generate PDF for invoice #%s" % 
                        invoice_id)
            rv = False
            if send_email:
                rv = sendInvoicePDF(send_from, invoice_id)
                if not rv:
                    log_error("Failed to send PDF for invoice #%s" % 
                            invoice_id)
                    overview_str += "Failed to send invoice for contact %s!\n" % \
                        customer_id
            session.execute("UPDATE billing_invoice SET invoice_file=%s, " \
                    "email_sent=%s WHERE invoice_id=%s", 
                    (filename, rv and 't' or 'f', invoice_id))
        except:
            log_error("Exception processing new invoice #%s!" % invoice_id,
                    sys.exc_info())
            overview_str += "Failed to process invoice for contact %s!\n" % \
                customer_id
    log_info("%s invoices successfuly created out of %s." % (count, total))
    overview_str += "%s invoices successfuly created out of %s.\n" % (count, total)
    if send_overview:
        # The first directory is based on the invoice date
        invoice_date = time.mktime(ts)
        dstr = datetime.fromtimestamp(invoice_date).strftime("%Y-%m-%d")
        invoice_dir = "%s/%s" % (invoice_store, dstr)
        try:
            os.remove("/tmp/invoices.zip")
        except OSError:
            pass
            
        log_command("zip -j /tmp/invoices.zip -r %s -i \*.pdf" % invoice_dir)
        overview.close()
        send_mail(send_from, [send_overview], "Invoices overview", overview_str, [file, "/tmp/invoices.zip"])
    return True

#####################################################################
# Email
#####################################################################
def billing_email(to, subject, msg, attachments):
    """Sends an email from the billing system.

    All billing email should go through this function it takes care of
    redirecting email if necessary, and ensures the helpdesk is BCC'd
    on all outgoing email.
    """

    # If force_email is specified, all outgoing email is redirected to the
    # specified address(es)
    force_email = config_get("billing", "force_email", None)
    if force_email is not None:
        to = force_email.split(",")
    else:
        to = [to]

    # If bcc_email is specified, all outgoing email is BCC'd to the specified
    # address(es)
    bcc_email = config_get("billing", "bcc_email", None)
    if bcc_email is not None:
        bcc_email = bcc_email.split(",")
    else:
        bcc_email = []

    # Send the actual email
    send_from = config_get("billing", "email_from", "invoices")
    return send_mail(send_from, to, subject, msg, attachments, bcc=bcc_email)

#####################################################################
# Ethernet Customer Service
#####################################################################
class ethernet_customer_service(ccsd_service):
    """Configures customers onto ethernet interfaces"""
    
    serviceName = "ethernet_customer"
    allowNewProperties = True
    networkService = False

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getEthernetCustomers")
    def getCustomers(self):
        """Returns a list of customers who receive ethernet services"""
        session = getSessionE(self._session_id)

        # Get the interface details
        res = session.query("SELECT * FROM v_customers WHERE " \
                "connection_method=%s", (CONNECTION_METHOD_ETHERNET))
        return map(filter_keys, res)

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getCustomerInterfaces")
    def getInterfaces(self, host_id):
        """Returns customer details for the interfaces for the host"""
        session = getSessionE(self._session_id)

        # Get the interface details
        res = session.query("SELECT i.*, ci.customer_id FROM " \
                "interface i LEFT JOIN customer_interface ci ON " \
                "i.interface_id=ci.interface_id WHERE i.host_id=%s", 
                (host_id))
        
        # Loop through and collapse alias interfaces into the raw interface
        ifaces = {}
        names = {}
        tmp = []
        for iface in res:
            if iface["customer_id"] == "":
                iface["customer_id"] = -1
            if iface["interface_type"] == INTERFACE_TYPE_ALIAS:
                tmp.append(filter_keys(iface))
                continue
            ifaces[iface["name"]] = filter_keys(iface)
            ifaces[iface["name"]]["customer"] = None
            names[iface["interface_id"]] = iface["name"]
        for iface in tmp:
            # Aliases with no associated customer are discarded
            if iface["customer_id"] == -1: continue
            name = names[iface["raw_interface"]]
            if ifaces[name]["customer"] is not None:
                log_warn("Multiple customers assigned to interface %s. " \
                        "Ignoring all but the first!" % iface["name"])
                continue
            ifaces[name]["customer"] = iface

        return ifaces

    @exportViaXMLRPC(SESSION_RW, AUTH_HELPDESK, True)
    def updateCustomerInterface(self, host_id, interface_id, customer_id):
        """Updates the customer that is assigned to the interface
        
        interface_id should be the id for the raw_interface the customer is
        assigned to. The actual link record will be created against an alias
        interface linked to this raw_interface.
        """
        session = getSessionE(self._session_id)
        iface = None
        host_id = int(host_id)
        interface_id = int(interface_id)
        customer_id = int(customer_id)
        for ifname, temp in self.getInterfaces(host_id).items():
            if temp["interface_id"] == interface_id:
                iface = temp
                break
        if iface is None:
            raise ccs_billing_error("Unknown interface")

        # Handle removal now
        if int(customer_id)==-1:
            session.begin("Removing customer from interface '%s'" % \
                    (iface["name"]), '', 1)
            try:
                # Remove the link
                session.execute("DELETE FROM customer_interface WHERE " \
                        "interface_id=%s", (iface["customer"]["interface_id"]))
                # Remove the alias interface
                session.execute("DELETE FROM interface WHERE interface_id=%s",
                        (iface["customer"]["interface_id"]))
                session.commit()
            except:
                session.rollback()
                (etype, value, tb) = sys.exc_info()
                log_error("Failed to remove customer: %s" % value, 
                        (etype, value, tb))
                raise ccs_billing_error("Failed to remove customer: %s" % \
                        value)
            return True

        # Get the link to allocate IP address from
        values = self.getPropertyValues()
        link_id = values[ETHERNET_CUSTOMER_LINK_PROPERTY]
        if link_id == -1:
            raise ccs_billing_error("No IP link specified. " \
                    "Please configure the customer ethernet service!")

        # Get the firewall class to use
        firewall_class_id = values[ETHERNET_CUSTOMER_FIREWALL_PROPERTY]
        if firewall_class_id == -1:
            raise ccs_billing_error("No firewall class specified. " \
                    "Please configure the customer ethernet service!")
                    
        # Validate that the specified customer is allowed to go onto
        # an ethernet interface
        custc = ccs_customer(self._session_id)
        cust = custc.getCustomer(customer_id)
        if cust["connection_method"] != CONNECTION_METHOD_ETHERNET:
            raise ccs_billing_error("%s is a Wireless customer and " \
                    "cannot be assigned to an Ethernet interface!" % \
                    cust["username"])
            
        session.begin("Configured customer '%s' on interface '%s'" % \
                (cust["username"], iface["name"]), '', 1)
        try:
            # Create / Find an Alias interface on the specified interface
            # for this customers real IP address
            alias_id = -1
            res = session.query("SELECT i.interface_id, i.ip_address " \
                    "FROM interface i LEFT JOIN " \
                    "customer_interface ci ON i.interface_id=" \
                    "ci.interface_id WHERE i.host_id=%s " \
                    "AND i.interface_type=%s AND i.raw_interface=%s",
                    (host_id, INTERFACE_TYPE_ALIAS, interface_id))
            if len(res) > 0:
                link = ccs_link(self._session_id, link_id)
                for temp in res:
                    # Find an existing interface in the right range
                    if not link.isValidIP(temp["ip_address"]):
                        continue
                    alias_id = temp["interface_id"]
                    break
            if alias_id == -1:
                # Create a new alias interface
                iface={}
                iface["interface_type"] = INTERFACE_TYPE_ALIAS
                iface["raw_interface"] = interface_id
                iface["host_id"] = host_id
                iface["link_id"] = link_id
                iface["interface_active"] = "t"
                iface["bridge_interface"] = ""
                iface["alias_netmask"] = "32"
                iface["ip_address"] = ""
                alias_id = addInterface(self._session_id, iface)
            
            done = False
            # Link to the interface
            try:
                session.execute("INSERT INTO customer_interface (" \
                        "customer_id, interface_id) VALUES " \
                        "(%s, %s)", (customer_id, alias_id))
                # Success
                session.commit()
                done = True
            except:
                (etype, value, tb) = sys.exc_info()
                # Assume this is because the record already exists
                pass

            # Insert failed, try update
            if not done:
                try:
                    session.execute("UPDATE customer_interface SET " \
                            "customer_id=%s WHERE interface_id=%s", 
                            (customer_id, interface_id))
                except:
                    # Log the previous error
                    log_error("Failed to insert customer interface record!", \
                            (etype, value, tb))
                    # Now log this error
                    log_error("Failed to update customer interface record!", \
                            sys.exc_info())

            # Setup firewall
            firewall = getServiceInstance(self._session_id, "firewall")
            try:
                firewall.addService(host_id)
            except:
                # Assume due to already existing...
                pass
            firewall.updateFirewallInterface(host_id, interface_id, \
                    firewall_class_id)

            # Make permanent and return
            session.commit()
            return True
        except:
            session.rollback()
            (etype, value, tb) = sys.exc_info()
            log_error("Failed to setup customer interface record!", \
                        (etype, value, tb))
            raise ccs_billing_error("Exception updating customer interface!")

        # Somethign bad happened
        return False

    def getHostTemplateVariables(self, host_id):
        """Returns a dictionary containing template variables for a host

        See the getTemplateVariables function for more details.
        """
        session = getSessionE(self._session_id)

        # Call base class to get the basics
        variables = ccsd_service.getHostTemplateVariables(self, host_id)

        # Get the interfaces
        res = session.query("SELECT * FROM customer_interfaces WHERE " \
                "host_id=%s", (host_id))
        ifaces = {}
        for iface in res:
            ifaces[iface["interface_name"]] = filter_keys(iface)
        variables["interfaces"] = ifaces

        return variables

    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("Initialising ethernet customer service", '', 1)        
        try:

            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (ethernet_customer_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS service_id", ())

            # Setup the link and firewall properties
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, required) " \
                "VALUES (DEFAULT, %s, %s, 'integer', -1, 't')", \
                (service_id, ETHERNET_CUSTOMER_LINK_PROPERTY))
            session.execute("INSERT INTO service_prop (service_prop_id, " \
                "service_id, prop_name, prop_type, default_value, required) " \
                "VALUES (DEFAULT, %s, %s, 'integer', -1, 't')", \
                (service_id, ETHERNET_CUSTOMER_FIREWALL_PROPERTY))
                
            # Commit the changese
            session.commit()
            
            log_info("Created ethernet customer service entries")
        except:
            session.rollback()
            log_error("Unable to initialise ethernet customer service " \
                    "database entries!", sys.exc_info())
            raise ccs_billing_error("Failed to setup database tables!")

        return service_id

#####################################################################
# Module initialisation
#####################################################################
def ccs_init():
    global invoice_store, billing_template_dir, trml_path, invoice_payment_day
    global invoice_payment_notify_days

    # Register the service
    registerService(ethernet_customer_service)

    # Load the path where we store generated invoices
    invoice_store = config_get("billing", "invoice_store", 
            DEFAULT_INVOICE_STORE)

    # Load common data, like the path to trml2pdf and the # days given to pay
    trml_path = config_get("billing", "trml2pdf" , "trml2pdf")
    invoice_payment_day = config_getint("billing", "payment_day", 
            DEFAULT_PAYMENT_DAY)
    invoice_payment_notify_days = config_getint("billing", "payment_notify_days", 
            DEFAULT_PAYMENT_NOTIFY_DAYS)

    # Load the location of the billing templates
    default_dir = "%s/billing_templates" % os.path.dirname(DEFAULT_CONFFILE)
    billing_template_dir = config_get("billing", "template_dir", default_dir)
