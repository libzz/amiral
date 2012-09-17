<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Authentication Display Interface - User manipulation
 * 
 * Author:       Ivan Meredith <ivan@ivan.net.nz
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


if (NO_BILLING_MENU != 1) {
    ccs_menu_bottom_add(array(mk_menu_item("Plans",
                    "/mods/billing/plan.php")));
    ccs_menu_bottom_add(array(mk_menu_item("Customers",
                    "/mods/billing/customer.php")));
    ccs_menu_bottom_add(array(mk_menu_item("Discounts",
                    "/mods/billing/discounts.php")));
    ccs_menu_bottom_add(array(mk_menu_item("Static Ip Pool",
                    "/mods/billing/static_ip.php")));
}

$CONNECTION_METHOD_WIRELESS="Wireless";
$CONNECTION_METHOD_ETHERNET="Ethernet";
$connection_methods = array($CONNECTION_METHOD_WIRELESS, 
    $CONNECTION_METHOD_ETHERNET);

function display_customer_list($p=1)
{
    global $xmlrpc_conn, $smarty;

    $n = 15;// Default number of entries to show
    $field = "";
    $search = "";

    session_start();

    if (isset($_REQUEST['num'])) {
        $_SESSION['num'] = $_REQUEST['num'];
        $n = $_SESSION['num'];
    } else if(isset($_SESSION['num'])) {
        $n = $_SESSION['num'];
    }

    if(isset($_REQUEST["search"])) {
        if(isset($_REQUEST["field"])) {
            $field = $_REQUEST["field"];
            $search = $_REQUEST["search"];
            $smarty->assign("field", $field);
            $smarty->assign("search", $search);
        }
    }

    $searchfields = do_xmlrpc("getSearchFields", array(), $xmlrpc_conn);
    if(xmlrpc_has_error($searchfields)) {
        ccs_notice("Could not retrieve search fields: "
                .xmlrpc_error_string($searchfields));
    }

    $res =  do_xmlrpc("getCustomerList", array($p,$n,$field,$search),
            $xmlrpc_conn, True, False);

    if(xmlrpc_has_error($res)){
        ccs_notice("Could not retrieve customers: "
                .xmlrpc_error_string($res));
    }

    $smarty->assign("searchfields", $searchfields);
    $smarty->assign("customers",$res[0]);
    $smarty->assign("pagenum", $res[1]);
    $smarty->assign("current_page", $p);
    $smarty->assign("max_page", $res[1][count($res[1])-1]);
    $smarty->assign("num_results",
       array("5"=>"5","10"=>"10","15"=>"15","20"=>"20","30"=>30,"50"=>50));
    $smarty->assign("num", $n);
    $smarty->assign("scripts", array("customerlist.js"));
    $smarty->assign("sheets", array("customer.css"));
    display_page("mods/billing/customerlist.tpl");
}


function getPlan($plan_id)
{
    global $xmlrpc_conn;

    $plan = do_xmlrpc("getPlan", array($plan_id), $xmlrpc_conn);
    return $plan;
}

function displayPLanList() 
{ 
    global $xmlrpc_conn, $smarty; 
    $res = do_xmlrpc("listPlans",array(), $xmlrpc_conn); 
    usort($res, "plan_cmp");
    $smarty->assign("plans", $res); 

    display_page("mods/billing/listplans.tpl"); 
}
function get_discounts($contact_id) 
{
    
    global $xmlrpc_conn;
    $discounts = do_xmlrpc("getCustomerDiscounts", array($contact_id), $xmlrpc_conn, True, False);
    if (xmlrpc_has_error($discounts)) {
        ccs_notice("Could not retrieve discounts: " .
            xmlrpc_error_string($discounts));
        $discounts = array();
    }
    return $discounts;
}
function get_customer($contact_id) 
{
    
    global $xmlrpc_conn;
    $customer = do_xmlrpc("getCustomer", array($contact_id), $xmlrpc_conn, True, False);
    if (xmlrpc_has_error($customer)) {
        ccs_notice("Could not retrieve customer: " .
            xmlrpc_error_string($customer));
        $customer = array();
    }
    $login_id = $customer["login_id"];
    $rv = do_xmlrpc("getLoginState", array($login_id), $xmlrpc_conn, True, False);
    if (xmlrpc_has_error($rv)) {
        $customer["status"] = -1;
    } else {
        $customer["status"] = $rv;
    }   

    return $customer;
}
function assign_static_ip($login_id)
{
    global $xmlrpc_conn, $smarty;

    $static_ip = do_xmlrpc("getStaticIP", array($login_id), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($static_ip)) {
        ccs_notice("Could not get data from server: " .
            xmlrpc_error_string($static_ip));
        $static_ip = array();
    }
    $smarty->assign("static_ip", $static_ip);
}
function assign_customer($contact_id) 
{

    global $smarty;
    

    $customer = get_customer($contact_id);
    $discounts = get_discounts($contact_id);

	assign_static_ip($customer['login_id']);
    $smarty->assign("customer", $customer);
    $smarty->assign("discounts", $discounts);
    return $customer;
}

function plan_cmp($a, $b)
{
	return strncmp($a['plan_name'], $b['plan_name'], 1024);
}

function assign_plan_list()
{
	global $smarty, $xmlrpc_conn;

	$plans = do_xmlrpc("listPlans", array(), $xmlrpc_conn, True, False);

	/* Let's sort the list, aye? */
	usort($plans, "plan_cmp");

	$smarty->assign("plans", $plans);

	return $plans;
}



?>
