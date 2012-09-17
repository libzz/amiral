<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Email managment interface
 *
 * Author:       Chris Browning <chris.ckb@gmail.com>
 * Version:      $Id: email.php 1562 2007-06-26 21:43:38Z ckb6 $
 *
 * ccsweb is free software; you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation.
 *
 * ccsweb is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * ccsweb; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */
require_once("ccs_init.php");
function assign_domains()
{
    global $xmlrpc_conn, $smarty;

    $domains = do_xmlrpc("getCustomerAllowedDomains", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($domains)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($domains));
        $domains = array();
    }
    $smarty->assign("domains", $domains);

}
function assign_customers()
{
    global $xmlrpc_conn, $smarty;

    $customers = do_xmlrpc("getCustomers", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($customers)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($customers));
        $customers = array();
    }
    $smarty->assign("customers", $customers);
}
function assign_mailbox($login_id)
{
    global $xmlrpc_conn, $smarty;

    $p = array($login_id);
    $mailbox = do_xmlrpc("getCustomerMailbox", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($mailbox)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($mailbox));
        $mailbox = array();
    }
    $smarty->assign("mailbox", $mailbox);
}
function assign_domain($domain)
{
    global $xmlrpc_conn, $smarty;

    $p = array($domain);
    $domain = do_xmlrpc("getEmailDomain", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($domain)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($domain));
        $domain = array();
    }
    $mailboxes = do_xmlrpc("getMailboxes", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($mailboxes)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($mailboxes));
        $mailboxes = array();
    }
    $smarty->assign("mailboxes", $mailboxes);
    $smarty->assign("domain", $domain);
}
    
function get_posted_mailbox()
{

    $mailbox = array();

    get_if_posted(&$mailbox, "customer_id");
    get_if_posted(&$mailbox, "login_id");    
    get_if_posted(&$mailbox, "email");
    get_if_posted(&$mailbox, "quota");
    get_if_posted(&$mailbox, "fwdto");
    get_if_posted(&$mailbox, "owner");
    get_if_posted(&$mailbox, "username");
    get_if_posted(&$mailbox, "domain");
    get_if_posted(&$mailbox, "passwd");
    
    return $mailbox;

}
function get_posted_domain()
{

    $domain = array();

    get_if_posted(&$domain, "customer_id");
    get_if_posted(&$domain, "domain");
    get_if_posted(&$domain, "catchall");
    get_if_posted(&$domain, "redirect");
    get_if_posted(&$domain, "owner");
    
    return $domain;

}

//This function fetches and manipulates all data for the interface
//but the graphs themselves which is done before this is call.
//It also displays the page
function display_list_mailboxes()
{
    global $smarty, $xmlrpc_conn;
    
    $mailboxes = do_xmlrpc("getCustomerMailboxes", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($mailboxes)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($mailboxes));
        $mailboxes = array();
    }
    $smarty->assign("mailboxes", $mailboxes);
    display_page("mods/email/mailboxlist.tpl");
}
if ($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit") {
    $do = $_REQUEST["do"];
    if ($_REQUEST["type"] == "domain"){
            if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
                $domain = get_posted_domain();
                $did = do_xmlrpc("${do}CustomerEmailDomain", array($domain), 
                    $xmlrpc_conn, TRUE, FALSE);
                if (xmlrpc_has_error($did)) {
                    ccs_notice("Could not $do domain: ".xmlrpc_error_string($did));
                    $action = $do;
                    if ($do == 'add'){
                        assign_customers();
                    }
                    $smarty->assign("domain", $domain);
                } else {
                    $action = "edit";
                    ccs_notice("Domain ${do}ed successfuly$warn.");
                    $smarty->assign("domain", $domain);
                }


            }else{
                if ($do == 'edit'){
                    assign_domain($_REQUEST["domain"]);
                }else{
                    assign_customers();
                }
            }
            $smarty->assign("action", $_REQUEST["do"]);
            display_page("mods/email/domainform.tpl");
    }else{
            if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
                $mailbox = get_posted_mailbox();
                $did = do_xmlrpc("${do}CustomerMailbox", array($mailbox), 
                    $xmlrpc_conn, TRUE, FALSE);
                if (xmlrpc_has_error($did)) {
                    ccs_notice("Could not $do mailbox: ".xmlrpc_error_string($did));
                    $action = $do;
                    if ($do == 'add'){
                        assign_customers();
                    }
                    $mailbox["domain"]= $_REQUEST["domain"];
                    $smarty->assign("mailbox", $mailbox);
                } else {
                    ccs_notice("Mailbox ${do}ed successfuly$warn.");
                    $do = "edit";
                    if ($did[0]){
                        assign_mailbox($did[0]);
                        $smarty->assign("plain_password", $did[1]);
                    }else{
                        $mailbox["email"]= $_REQUEST["username"] . '@' . $_REQUEST["domain"];
                        $smarty->assign("mailbox", $mailbox);
                    }
                }


            }else{
                if ($do == 'edit'){
                    assign_mailbox($_REQUEST["mailbox"]);
                }else{
                    assign_domains();
                    $mailbox["domain"]= $_REQUEST["domain"];
                    $smarty->assign("mailbox", $mailbox);
                }
            }
            $smarty->assign("action", $do);
            display_page("mods/email/mailboxform.tpl");
    }
     
}else{
    display_list_mailboxes();
}
?>
