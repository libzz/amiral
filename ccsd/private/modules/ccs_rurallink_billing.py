# Copyright (C) 2006  Rural Link Ltd.
#
# This file is an extension to crcnetd - CRCnet Configuration System Daemon
#
# RuralLink Billing Module - Provides logic for manipulating customer accounts
#                            according to the Rural Link business rules.
#
# Author:       Matt Brown <matt@crc.net.nz>
#               Ivan Meredith <ivan@ivan.net.nz>
# Version:      $Id$
#
# No usage or redistribution rights are granted for this file unless
# otherwise confirmed in writing by the copyright holder.
from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_config import config_getboolean, config_get
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from datetime import datetime, timedelta
from crcnetd._utils.ccsd_server import exportViaXMLRPC

from crcnetd.modules.ccs_billing import billing_email
from Cheetah.Template import Template

ccs_mod_type = CCSD_SERVER

#####################################################################
# Scheduled event handling
#####################################################################
@catchEvent("billingRegularUpdate")
def checkUsage(*args, **kwargs):
    """Check customer data usage. Perform cap actions and warnings as 
       necessary"""
    session = getSession(ADMIN_SESSION_ID)

    #Do warnings first to ensure that a warning email in generated
    sql = "SELECT cs.*, c.* FROM broadband_account cs, customers c WHERE " \
            "cs.login_id=c.login_id AND cs.used_mb > cs.cap_at_mb*0.8 " \
            "AND cs.warning_sent=false AND cs.charged=true"
    res = session.query(sql, ())
    for state in res:
        doCapWarn(state)
        
    #Do any cap ations required
    sql = "SELECT cs.*, c.* FROM broadband_account cs, v_customers c WHERE " \
            "cs.login_id=c.login_id AND cs.used_mb > cs.cap_at_mb"
    res = session.query(sql, ())
    for state in res:
        doCapAction(state)
        


@catchEvent("billingDaily")
def rurallinkBillingDaily(*args, **kwargs):
    """Peforms plan rollover for any daily plans"""
    doRollover("daily")

@catchEvent("billingWeekly")
def rurallinkBillingWeekly(*args, **kwargs):
    """Peforms plan rollover for any weekly plans"""
    doRollover("weekly")

@catchEvent("billingMonthly")
def rurallinkBillingMonthly(*args, **kwargs):
    """Peforms plan rollover for any monthly plans"""
    doRollover("monthly")

@catchEvent("billingMonthEnd")
def ruralllinkBillingMonthEnd(*args, **kwargs):
    """Generate billing records for all plans and users at the end of month"""
    doBilling()

#####################################################################
# Rural Link billing logic implementation
#####################################################################
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def processBilling(auth, as_at=None):
    doBilling(as_at)
    return True

def doBilling(as_at=None):
    """Called on the monthly event to charge the customer for their plan
    
    The monthly event is called on the last day of the month, so we add one
    to the current date to report the month that we're billing the customer
    for.
    """
    session = getSession(ADMIN_SESSION_ID)
    print "DOING BILLING"
    # Generate a billing record for each plan that is active in the system
    sql = "SELECT * FROM rollover"
    res = session.query(sql, ())

    n = timedelta(1)
    # Select all unbilled records up till NOW or the time specified, 
    # date the invoice one day earlier
    if as_at is None:
        datestr = datetime.strftime(datetime.now() + n, "%b %Y")
        db_time = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
    else:
        datestr = datetime.fromtimestamp(as_at).strftime("%b %Y")
        db_time = datetime.fromtimestamp(as_at).strftime("%Y-%m-%d %H:%M:%S")

    
    for ro in res:
        if ro['charged'] == 'f':
            continue

        sql = "INSERT INTO billing_record (customer_id, record_date, " \
            "description, amount, quantity, record_type) VALUES ((select customer_id from customers where login_id=%s), %s, " \
            "%s, %s, 1, 'Plan');"
        desc = "%s: %s" % (datestr, ro["description"])
        try:
            session.execute(sql, (ro["login_id"], db_time, desc, ro["price"]))
        except:
            log_error("Failed to generate billing record for contact #%s" % \
                    ro["login_id"], sys.exc_info())

def doRollover(type):
    """Handles resetting customer caps when their usage rolls over"""
    session = getSession(ADMIN_SESSION_ID)
    
    sql = "SELECT * FROM rollover WHERE cap_period=%s"
    res = session.query(sql, (type))
    for ro in res:
        try:           
            # Update the broadband_account table to reset the cap
            sql = "UPDATE broadband_account SET plan_start=CURRENT_TIMESTAMP, "\
                "cap_at_mb=%s, used_mb=0, radius_plan=%s WHERE login_id=%s"
            session.execute(sql, (ro["included_mb"], ro["radius_plan"], \
                    ro["login_id"]))
        except:
            log_error("Failed to reset cap and state for contact #%s" % \
                    ro["login_id"], sys.exc_info())

    #Reset the warning sent flags
    try:           
        sql = "UPDATE broadband_account SET warning_sent=false where exists " \
            "(select billing_plan.plan_id, billing_plan.cap_period from " \
            "billing_plan where broadband_account.plan_id = " \
            "billing_plan.plan_id AND billing_plan.cap_period=%s)"
        session.execute(sql, (type))
    except:
        log_error("Failed to reset warning_sent field")
    
def doCapWarn(customer):
    session = getSession(ADMIN_SESSION_ID)

    sql = "SELECT cap_action, cap_param, cap_price, description FROM " \
            "billing_plan WHERE plan_id=%s"
    res = session.query(sql, (customer["plan_id"]))
    
    sql = "UPDATE broadband_account SET warning_sent='t' WHERE " \
        "login_id=%s"
    session.execute(sql,(customer["login_id"]))    

    subject = "Data Cap Notice: 80% used" 
    if res[0]["cap_action"] == "throttle":
        sendCapEmail(customer, subject, "throttle-warn")
    elif res[0]["cap_action"] == "purchase":
        customer["purchase_mb"] = res[0]["cap_param"]
        customer["purchase_price"] = "$%.2f" % (res[0]["cap_price"]*1.125)
        sendCapEmail(customer, subject, "purchase-warn")
    else:
        log_error("Unknown cap action '%s' for contact '%s'" % \
                (res[0]["cap_action"], customer['username']))

def doCapAction(customer):
    """Called when a customer has exceeded their cap.

    Rate limits or purchases more data for the customer, based on their chosen
    plan.
    """
    session = getSession(ADMIN_SESSION_ID)

    sql = "SELECT cap_action, cap_param, cap_price, description FROM " \
            "billing_plan WHERE plan_id=%s"
    res = session.query(sql, (customer["plan_id"]))
    
    used_mb = int(customer["used_mb"])
    subject = "Data Cap Notice: %.1fGB used." % (used_mb/1024.0) 
    
    if res[0]["cap_action"] == "throttle":
        # Customer has chosen to be throttled
        current_plan =  customer["radius_plan"]
        if current_plan == res[0]["cap_param"]:
            # Already throttled
            return
        else:
            # Throttle and notify
            sql = "UPDATE broadband_account SET radius_plan=%s WHERE " \
                    "login_id=%s"
            session.execute(sql,(res[0]["cap_param"], customer["login_id"]))
            log_info("Moved '%s' to plan %s (throttled)" % \
                    (customer["username"], res[0]["description"]))
            # Tell the customer
            sendCapEmail(customer, subject, "throttle")
    elif res[0]["cap_action"] == "purchase":
        # Customer has chosen to purchase more data
        cap_at_mb = customer["cap_at_mb"]
        used_mb = customer["used_mb"]
        
        # If the customer is leeching at full rate, it's possible that we may
        # have to purchase multiple extra blocks of usage to get their cap
        # back above their current data usage.
        extra_mb = 0
        extra_price = 0
        while cap_at_mb < used_mb:
            try:
                sql = "UPDATE broadband_account SET cap_at_mb=cap_at_mb+%s " \
                        "WHERE login_id=%s"
                session.execute(sql,(res[0]["cap_param"],
                    customer["login_id"]))
                
                sql = "INSERT INTO billing_record (customer_id, record_date, " \
                        "description, amount, quantity,record_type) VALUES (%%s, " \
                        "CURRENT_TIMESTAMP, '%sMB data pack', %%s, 1, 'Data')" % \
                        (res[0]["cap_param"])
                session.execute(sql, (customer["customer_id"], 
                    res[0]["cap_price"]))
                cap_at_mb += res[0]["cap_param"]
                log_info("Purchased %sMB block for '%s'. New cap: %sMB." % \
                        (res[0]["cap_param"], customer["username"], cap_at_mb))
                extra_mb += res[0]["cap_param"]
                extra_price += res[0]["cap_price"]
            except:
                log_error("Failed to purchase new block for '%s'!" % \
                        customer["username"], sys.exc_info())
                break
        # Tell the customer
        customer["purchased_mb"] = extra_mb
        customer["purchased_price"] = "$%.2f" % (extra_price*1.125)
        sendCapEmail(customer, subject, "purchase")
    else:
        log_error("Unknown cap action '%s' for contact '%s'" % \
                (res[0]["cap_action"], customer['username']))

def sendCapEmail(customer, subject, action):
    """Sends the user an email regarding their cap

    The second parameter is used to choose a template which decides the actual
    message that the user will receive. 
    Valid values are typically the same as the cap actions. 
    Eg (throttle, purchase), but can be any value that will find a valid file in
    the billing template directory.
    """
    from crcnetd.modules.ccs_billing import billing_template_dir

    # Can't send email if no template available
    if billing_template_dir is None:
        log_error("Failed to load cap email template; No template specified")
        return False
    template = "%s/cap-%s-email.tmpl" % (billing_template_dir, action)
    try:
        email_template = Template(file=template)
    except:
        log_error("Failed to load cap email template: %s" % template,
                sys.exc_info())
        return ""

    # Setup data for the body of the email
    info = {}
    info["customer"] = customer
    email_template._searchList = [info]
    email_template._CHEETAH__searchList += email_template._searchList

    # Send the email
    rv = billing_email(customer["email"], subject, 
            str(email_template).strip(), [])
    if rv:
        log_info("Emailed Cap Notice to '%s'" % customer["email"])
        return True
    else:
        log_error("Failed to email Cap Notice to '%s'" % customer["email"])
        return False
