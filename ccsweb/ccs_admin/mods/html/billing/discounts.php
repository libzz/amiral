<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Billing - Discount Management
 *
 * Author:       Chris Browning <chris.ckb@gmail.com>
 *
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

function get_posted_discount()
{
    $discount = array();
    get_if_posted(&$discount, "discount_id");
    get_if_posted(&$discount, "discount_name");
    get_if_posted(&$discount, "description");
    get_if_posted(&$discount, "amount");
    return $discount;
}
function get_posted_customer_discount()
{
    $discount = array();
    get_if_posted(&$discount, "discount_id");
    get_if_posted(&$discount, "customer_id");
    get_if_posted(&$discount, "start_date");
    get_if_posted(&$discount, "end_date");
    get_if_posted(&$discount, "recurring");
    get_if_posted(&$discount, "customer_discount_id");
    if ($discount["recurring"] == 'on')
        $discount["recurring"] = 't';
    else
        $discount["recurring"] = 'f';
    
    return $discount;
}
function get_discount($discount_id)
{
    global $xmlrpc_conn;

    $discount = do_xmlrpc("getBillingDiscount", array($discount_id), $xmlrpc_conn, True, False);
    if (xmlrpc_has_error($discount)) {
            ccs_notice("Could not get discount: ".xmlrpc_error_string($discount));
    }

    return $discount;
}
function get_customer_discount($customer_discount_id)
{
    global $xmlrpc_conn;

    $discount = do_xmlrpc("getCustomerDiscount", array($customer_discount_id), $xmlrpc_conn, True, False);    
    if (xmlrpc_has_error($discount)) {
            ccs_notice("Could not get customer discount: ".xmlrpc_error_string($discount));
    }

    return $discount;
}
 
function assign_discount($discount_id)
{
    global $smarty;

    $discount = get_discount($discount_id);
    
    $smarty->assign("discount", $discount[0]);
    return $discount;
} 
function assign_customer_discount($customer_discount_id)
{
    global $smarty;

    $discount = get_customer_discount($customer_discount_id);
    if (xmlrpc_has_error($discount)) {
            ccs_notice("Could not get discount: ".xmlrpc_error_string($discount));
    }
    
    $smarty->assign("discount", $discount[0]);
    return $discount;
}
function assign_discountlist()
{
    global $xmlrpc_conn, $smarty; 
    $res = do_xmlrpc("listBillingDiscounts",array(), $xmlrpc_conn); 
    $smarty->assign("discounts", $res);
}
function displayDiscountList() 
{ 
    global $smarty; 
    assign_discountlist();
    display_page("mods/billing/listdiscounts.tpl"); 
}
if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
	displayDiscountList();
}

if ($_REQUEST["do"] == "deleteBillingDiscount"){
	page_edit_requires(AUTH_HELPDESK);

	if ($_REQUEST["confirm"] != "yes") {
		assign_discount($_REQUEST["discount_id"]);
		display_page("mods/billing/discountdel.tpl");
        
	} else {
        /* Delete discount */
        $rv = do_xmlrpc("removeBillingDiscount", array($_REQUEST["discount"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not delete discount: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Discount successfully deleted!");
        }
        /* Display discount list */
        displayDiscountList();
    }
} else if($_REQUEST["do"] == "addBillingDiscount" || $_REQUEST["do"] == "editBillingDiscount"){
    page_edit_requires(AUTH_HELPDESK);
    $do = $_REQUEST["do"];
    if(isset($_REQUEST["process"]) && $_REQUEST["process"] == "yes"){
        $discount = get_posted_discount();
        $res = do_xmlrpc("${do}", array($discount), $xmlrpc_conn);

        if(xmlrpc_has_error($res)) {
            ccs_notice("Could not $do discount: ".xmlrpc_error_string($res));
            $smarty->assign("discount", $discount);
            $smarty->assign("action", $do);
            display_page("mods/billing/discountaddform.tpl");
        } else {
            displayDiscountList();
        }
    } else {
        $smarty->assign("action", $do);
        if($do == "editBillingDiscount"){
            assign_discount($_REQUEST["discount_id"]);
        }
        display_page("mods/billing/discountaddform.tpl");
    }
} else if($_REQUEST["do"] == "addCustomerDiscount" || $_REQUEST["do"] == "editCustomerDiscount"){    
    page_edit_requires(AUTH_HELPDESK);
    $do = $_REQUEST["do"];
    if(isset($_REQUEST["process"]) && $_REQUEST["process"] == "yes"){
        $discount = get_posted_customer_discount();
        $res = do_xmlrpc("${do}", array($discount), $xmlrpc_conn);

        if(xmlrpc_has_error($res)) {
            ccs_notice("Could not $do discount: ".xmlrpc_error_string($res));
            $smarty->assign("discount", $discount);
            $smarty->assign("action", $do);
            display_page("mods/billing/customerdiscountaddform.tpl");
        } else {
            /* Get the customer data */
            assign_customer($_REQUEST["customer_id"]);
            $action = "edit";
            $smarty->assign("connection_methods", $connection_methods);
            $smarty->assign("customer_types", $customer_types);
            $smarty->assign("action", $action);
    
            /* Show the add form */
        	assign_plan_list();
            display_page("mods/billing/customerform.tpl");
            displayDiscountList();
        }
    } else {
        $smarty->assign("action", $do);
        $smarty->assign("contact_id", $_REQUEST["contact_id"]);
        assign_discountlist();
        if($do == "editCustomerDiscount"){
            assign_customer_discount($_REQUEST["customer_discount_id"]);
        }
        display_page("mods/billing/customerdiscountaddform.tpl");
    }
}else if ($_REQUEST["do"] == "deleteCustomerDiscount"){
	page_edit_requires(AUTH_HELPDESK);

	if ($_REQUEST["confirm"] != "yes") {
		assign_customer_discount($_REQUEST["customer_discount_id"]);
		display_page("mods/billing/customerdiscountdel.tpl");
        
	} else {
        /* Delete discount */
        $rv = do_xmlrpc("removeCustomerDiscount", array($_REQUEST["customer_discount_id"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not delete discount: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Discount successfully deleted!");
        }
    assign_customer($_REQUEST["contact_id"]);
    $action = "edit";
    $smarty->assign("connection_methods", $connection_methods);
    $smarty->assign("customer_types", $customer_types);
    $smarty->assign("action", $action);

    /* Show the add form */
    assign_plan_list();
    display_page("mods/billing/customerform.tpl");
    }    
}
?>
