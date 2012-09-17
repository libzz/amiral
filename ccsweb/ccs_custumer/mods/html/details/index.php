<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Billing - Customer Management
 * 
 * Author:       Matt Brown <matt@crc.net.nz>
				 Ivan Meredith <ivan@ivan.net.nz>
 * Version:      $Id: customer.php 1567 2007-06-27 05:49:49Z ckb6 $
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
//require("billing/billing_common.php");
function assign_customer()
{
    global $xmlrpc_conn, $smarty;
    $customer = do_xmlrpc("getCustomerDetails", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($customer)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($customer));
        $customer = array();
    }
    $smarty->assign("customer", $customer);
}
function display_customer()
{
    global $xmlrpc_conn, $smarty;
    assign_customer();
    display_page("mods/details/customerform.tpl");

}
function get_posted_customer()
{

    $customer = array();

    if (isset($_POST["enabled"]) && $_POST["enabled"]=="yes") {
        $customer["enabled"] = 1;
    } else {
        $customer["enabled"] = 0;
    }

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
    return $customer;

}


/********************************************************************
 * Add or Edit a customer 
 * do=add|edit
 * If 'process' is set the request must include all of the required 
 * customer fields (username, givenname, surname, email, type) and
 * may contain optional fields such as phone, passwd, etc.
 * If edit is set the request must also include 'contact_id'
 ********************************************************************/
if ($_REQUEST["do"] == "edit") {
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Process submitted form */
        $contact_id = $_REQUEST["contact_id"];
        $customer = get_posted_customer();
		$customer["type"] = "customer";
        if (array_key_exists("newpass", $customer) && $customer["newpass"]!="") {
            $customer["passwd"] = $customer["newpass"];
        }
        $cid = do_xmlrpc("updateCustomerDetails", array($customer), 
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($cid)) {
            ccs_notice("Could not $do customer: ".xmlrpc_error_string($cid));
            $action = $do;
            $smarty->assign("customer", $customer);
        } else {
            $action = "edit";
            ccs_notice("Customer ${do}ed successfuly$warn.");
            if( $do == "add") {
                assign_customer();
                $smarty->assign("plain_password", $cid[1]);
            } else {
                assign_customer();
            }
        }
    } else {
        if ($do == "edit") {
            /* Get the customer data */
            assign_customer();
        }
        $action = $do;
    }
    $smarty->assign("connection_methods", $connection_methods);
    $smarty->assign("customer_types", $customer_types);
    $smarty->assign("action", $action);

    /* Show the add form */
    display_page("mods/details/customerform.tpl");
}   
display_customer();

?>
