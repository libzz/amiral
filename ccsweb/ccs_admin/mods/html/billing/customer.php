<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Billing - Customer Management
 * 
 * Author:       Matt Brown <matt@crc.net.nz>
				 Ivan Meredith <ivan@ivan.net.nz>
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
require("ccs_init.php");
require("billing/billing_common.php");


function assign_domains()
{
    global $xmlrpc_conn, $smarty;

    $domains = do_xmlrpc("getEmailDomains", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($domains)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($domains));
        $domains = array();
    }
    $smarty->assign("domains", $domains);

}
function get_posted_customer()
{

    $customer = array();

    if (isset($_POST["enabled"]) && $_POST["enabled"]=="yes") {
        $customer["enabled"] = 1;
    } else {
        $customer["enabled"] = 0;
    }
    if (isset($_POST["charged"]) && $_POST["charged"]=="yes") {
        $customer["charged"] = 't';
    } else {
        $customer["charged"] = 'f';
    }

    get_if_posted(&$customer, "connection_method");
	get_if_posted(&$customer, "plan_id");
	get_if_posted(&$customer, "billing_address");
	get_if_posted(&$customer, "billing_name");
    get_if_posted(&$customer, "login_id");
    get_if_posted(&$customer, "customer_id");
    get_if_posted(&$customer, "username");
    get_if_posted(&$customer, "domain");
    get_if_posted(&$customer, "givenname");
    get_if_posted(&$customer, "surname");
    get_if_posted(&$customer, "email");
    get_if_posted(&$customer, "address");
    get_if_posted(&$customer, "phone");
    get_if_posted(&$customer, "newpass");
    
    return $customer;

}


if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    if(isset($_REQUEST["page"])){
        display_customer_list($_REQUEST["page"]);
    } else {
        display_customer_list();
    }
}

/********************************************************************
 * Add or Edit a customer 
 * do=add|edit
 * If 'process' is set the request must include all of the required 
 * customer fields (username, givenname, surname, email, type) and
 * may contain optional fields such as phone, passwd, etc.
 * If edit is set the request must also include 'contact_id'
 ********************************************************************/
if ($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit") {
    /* Check administrator privs */
    page_edit_requires(AUTH_HELPDESK);
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Process submitted form */
        $contact_id = $_REQUEST["contact_id"];
        $customer = get_posted_customer();
		$customer["type"] = "customer";
        if (array_key_exists("newpass", $customer) && $customer["newpass"]!="") {
            $customer["passwd"] = $customer["newpass"];
        }
        $cid = do_xmlrpc("${do}Customer", array($customer), 
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($cid)) {
            ccs_notice("Could not $do customer: ".xmlrpc_error_string($cid));
            $action = $do;
            $smarty->assign("customer", $customer);
            assign_domains();
        } else {
            $action = "edit";
            ccs_notice("Customer ${do}ed successfuly$warn.");
            if( $do == "add") {
                assign_customer($cid[0]);
                $smarty->assign("plain_password", $cid[1]);
            } else {
                assign_customer($cid);
            }
        }
    } else {
        if ($do == "edit") {
            /* Get the customer data */
            assign_customer($_REQUEST["contact_id"]);
        }else{
            assign_domains();
        }
        $action = $do;
    }
    $smarty->assign("connection_methods", $connection_methods);
    $smarty->assign("customer_types", $customer_types);
    $smarty->assign("action", $action);

    /* Show the add form */
	assign_plan_list();
    display_page("mods/billing/customerform.tpl");
    
} else if ($_REQUEST["do"] == "gen") {
    page_edit_requires(AUTH_HELPDESK);
    $did = do_xmlrpc("genCustomerPassword", array($_REQUEST["customer_id"], $_REQUEST["login_id"]), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($did)) {
        ccs_notice("Could not generate Customer password: ".xmlrpc_error_string($did));
    } else {
        ccs_notice("Customer password generated successfuly$warn.");
        $smarty->assign("plain_password", $did);
    }
    assign_customer($_REQUEST["customer_id"]);
    $smarty->assign("connection_methods", $connection_methods);
    $smarty->assign("customer_types", $customer_types);
    $smarty->assign("action", "edit");

    /* Show the add form */
	assign_plan_list();
    display_page("mods/billing/customerform.tpl");

/********************************************************************
 * Disable a customer 
 * do=disable
 * Required Paramters
 * contact_id
 ********************************************************************/
} else if ($_REQUEST["do"] == "disable") {
    /* Check administrator privs */
    page_edit_requires(AUTH_HELPDESK);
    $contact_id = $_REQUEST["contact_id"];
    $rv = do_xmlrpc("disableContact", array($contact_id),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        ccs_notice("Could not disable customer: ".xmlrpc_error_string($rv));
    } else {
        ccs_notice("Contact disabled.");
    }
    /* Display customer list */
    display_customer_list();
} else if ($_REQUEST["do"] == "history"){
    // Allow lookup by contact_id or username
    if(isset($_REQUEST["contact_id"])){
        $contact_id = $_REQUEST["contact_id"];
    } else if (isset($_REQUEST["username"])){
        $rv = do_xmlrpc("getCustomerList", 
            array(1, 1, "username", $_REQUEST["username"]), $xmlrpc_conn);
       if($rv[0][0]["username"] == ""){
            ccs_notice("Username does not exist: ".$_REQUEST["username"]);
            display_customer_list();
        }
        $contact_id = $rv[0][0]["contact_id"];
    }
    // Default to current month if not specified
    if (isset($_REQUEST["monthkey"])) {
        $monthkey = $_REQUEST["monthkey"];
    } else {
        $monthkey = date("Ym");
    }
    $customer = assign_customer($contact_id);
    // Fetch traffic information
    $p = array($contact_id, substr($monthkey, 0, 4), substr($monthkey, 4, 2));
    $result = do_xmlrpc("getTrafficHistory", $p, $xmlrpc_conn);
    ksort($result);
    // Remove any days from when the customer wasn't a customer
    $jd = explode(" ", $customer["join_date"]);
    $jd = explode("-", $jd[0]);
    $jmkey = $jd[0] . $jd[1];
    if ($jmkey == $monthkey) {
        for ($i=1; $i<$jd[2]; $i++) {
            unset($result[$i]);
        }
    }
    // Get information for the date select box
    $dates = do_xmlrpc("getHistoryDates", array($contact_id), $xmlrpc_conn);
    ksort($dates);
    // Assign it all
    $smarty->assign("history_dates", $dates);
    $smarty->assign("history", $result);
    $smarty->assign("monthkey", $monthkey);
    $smarty->assign("contact_id", $contact_id);
    display_page("mods/billing/history.tpl");
} else if ($_REQUEST["do"] == "activate") {
	$login_id = $_REQUEST['login_id'];
	$customer_id = $_REQUEST['customer_id'];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
		$day = $_REQUEST['day'];
		$cid = do_xmlrpc("activateCustomer", array($customer_id, $day),
			$xmlrpc_conn, TRUE, FALSE);
		if (xmlrpc_has_error($cid)) {
			ccs_notice("Could activate: ".xmlrpc_error_string($cid));
		} else {
			ccs_notice("Sucsessfully activated plan");
		}
		assign_customer($customer_id);
		$smarty->assign("action", "edit");
		$smarty->assign("connection_methods", $connection_methods);
		$smarty->assign("customer_types", $customer_types);
		/* Show the add form */
		assign_plan_list();
		display_page("mods/billing/customerform.tpl");
	}else{
		$smarty->assign("login_id", $login_id);
		$smarty->assign("customer_id", $customer_id);
		$smarty->assign("today", date("d"));
		$smarty->assign("month", date("F-Y"));
		display_page("mods/billing/activate.tpl");

	}
}
    
    

/* If we get here the page has been called incorrectly, display the list */
ccs_notice("Invalid Action Requested: " . $_REQUEST["do"]);
display_customer_list();

?>
