<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Email managment interface
 *
 * Author:       Chris Browning <chris.ckb@gmail.com>
 * Version:      $Id$
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

function assign_owners()
{
    global $xmlrpc_conn, $smarty;

    $customers = do_xmlrpc("getCustomers", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($customers)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($customers));
        $customers = array();
    }
    $x = array();
    foreach ($customers as $key=>$val){
        $x[$val["domain"]] =$val["domain"];
    }
    $domains = array_unique($x);
    asort($domains);
    $newdomains = array();
    foreach ($domains as $key=>$val){
        $newdomains[$key] = array();
    }
    foreach ($customers as $key=>$val){
        $newdomains[$val["domain"]][$val["customer_id"]] = $val[username] . '@' .  $val[domain];
    }
    
    foreach ($newdomains as $key=>$val){
        asort($newdomains[$key]);
    }
    $smarty->assign("owners", $newdomains);
}
function assign_mailbox($login_id)
{
    global $xmlrpc_conn, $smarty;

    $p = array($login_id);
    $mailbox = do_xmlrpc("getMailbox", $p, $xmlrpc_conn, TRUE, FALSE);
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

    set_time_limit(60);

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
function display_list_domains()
{
    global $smarty, $xmlrpc_conn;
    
    $domains = do_xmlrpc("getEmailDomains", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($domains)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($domains));
        $domains = array();
    }
    $smarty->assign("domains", $domains);
    display_page("mods/email/domainlist.tpl");
}
if ($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit") {
    /* Check administrator privs */
    page_edit_requires(AUTH_HELPDESK);
    $do = $_REQUEST["do"];
    $action = $do;
    if ($_REQUEST["type"] == "domain"){
            if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
                $domain = get_posted_domain();
                $did = do_xmlrpc("${do}EmailDomain", array($domain), 
                    $xmlrpc_conn, TRUE, FALSE);
                if (xmlrpc_has_error($did)) {
                    ccs_notice("Could not $do domain: ".xmlrpc_error_string($did));
                    assign_owners();
                    $smarty->assign("domain", $domain);
                } else {
                    $action = "edit";
                    assign_owners();
                    ccs_notice("Domain ${do}ed successfuly$warn.");
                    $smarty->assign("domain", $domain);
                }


            }else{
                if ($do == 'edit'){
                    assign_domain($_REQUEST["domain"]);
                }
                assign_owners();
            }
            $smarty->assign("action", $action);
            display_page("mods/email/domainform.tpl");
    }else{
            if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
                $mailbox = get_posted_mailbox();
                $did = do_xmlrpc("${do}Mailbox", array($mailbox), 
                    $xmlrpc_conn, TRUE, FALSE);
                if (xmlrpc_has_error($did)) {
                    ccs_notice("Could not $do mailbox: ".xmlrpc_error_string($did));
                    if ($do == 'add'){
                        assign_owners();
                    }
                    $mailbox["domain"]= $_REQUEST["domain"];
                    $smarty->assign("mailbox", $mailbox);
                } else {
                    ccs_notice("Mailbox ${do}ed successfuly$warn.");
                    $action = "edit";
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
                    $mailbox["domain"]= $_REQUEST["domain"];
                    $smarty->assign("mailbox", $mailbox);
                    assign_owners();
                    assign_domain($mailbox["domain"]);
                }
            }
            $smarty->assign("action", $action);
            display_page("mods/email/mailboxform.tpl");
    }
     
}else if($_REQUEST["do"] == "gen"){
    page_edit_requires(AUTH_HELPDESK);
        $did = do_xmlrpc("genMailboxPassword", array($_REQUEST["mailbox"], $_REQUEST["owner_id"]), 
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($did)) {
            ccs_notice("Could not generate mailbox password: ".xmlrpc_error_string($did));
        } else {
            ccs_notice("Mailbox password generated successfuly$warn.");
            $smarty->assign("plain_password", $did);
        }
        assign_mailbox($_REQUEST["mailbox"]);
        $smarty->assign("action", "edit");
        display_page("mods/email/mailboxform.tpl");

    
}else{
    display_list_domains();
}
?>
