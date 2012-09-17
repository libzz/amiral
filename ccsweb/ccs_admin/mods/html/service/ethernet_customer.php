<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * Ethernet Customer Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
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
require_once("host/host_common.php");
require_once("service/firewall_common.php");

function getEthernetCustomersList($service_id)
{
    global $xmlrpc_conn;
    
    $p = array($service_id);
    $custs = do_xmlrpc("getEthernetCustomers", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($custs)) {
        ccs_notice("Could not retrieve ethernet customer details: " .
            xmlrpc_error_string($custs));
        return array();
    }
    return $custs;
}
function getEthernetCustomersSelect($custs) {
    $rv = array();
    foreach ($custs as $idx=>$cust) {
        $rv[$cust["customer_id"]] = $cust["username"] . ": " . 
            $cust["givenname"] . " " . $cust["surname"];
    }
    $rv[-1] = "(No customer)";
    return $rv;
}
function assignEthernetCustomer($service_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id);
    $service = do_xmlrpc("getServiceDetails", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve ethernet customer details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    assignLinks(TRUE);
    $firewall_service_id = do_xmlrpc("getServiceID", array("firewall"), 
        $xmlrpc_conn);
    assignFirewall($firewall_service_id);
    $smarty->assign("ethernet_customer", $service);

    return $service;
}
function assignHostCustomers($service_id, $host_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $ifaces = do_xmlrpc("getCustomerInterfaces", $p, $xmlrpc_conn,TRUE,FALSE);
    if (xmlrpc_has_error($ifaces)) {
        ccs_notice("Could not retrieve ethernet customer details: " .
            xmlrpc_error_string($ifaces));
        $ifaces = array();
    }
    $service = array("interfaces"=>$ifaces, "service_id"=>$service_id);
    $service["ethernet_customers"] = getEthernetCustomersList($service_id);
    $select = getEthernetCustomersSelect($service["ethernet_customers"]);
    $service["ethernet_customers_select"] = $select;
    $smarty->assign("ethernet_customer", $service);

    return $service;
}
function assignCustomerInterface($service_id, $host_id, $interface_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $ifaces = do_xmlrpc("getCustomerInterfaces", $p, $xmlrpc_conn, TRUE,
        FALSE);
    if (xmlrpc_has_error($ifaces)) {
        ccs_notice("Could not retrieve ethernet customer details: " .
            xmlrpc_has_error($ifaces));
        $ifaces = array();
    }
    foreach ($ifaces as $idx=>$iface) {
        if ($iface["interface_id"] == $interface_id) {
            $smarty->assign("iface", $iface);
            return $iface;
        }
    }

    return NULL;
}

if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    display_service_list();
}

/********************************************************************
 * Configure a service on a specific host
 * do=configure
 ********************************************************************/
if ($_REQUEST["do"] == "configure") {
    /* Display the generic service edit form */
    $smarty->assign("host", getHost($_REQUEST["host_id"], FALSE, FALSE));
    assignHostCustomers($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->assign("sheets", array("service.css", "ethernet_customer.css"));
    $smarty->assign("scripts", "ethernet_customer.js");
    display_page("mods/service/ethernet_customer.tpl");
    
/********************************************************************
 * Update the customer assigned to an interface
 * do=updateCustomerInterface
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * interface_id     The interface to enable/disable OSPF on
 * contact_id       The customer assigned to the interface
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateCustomerInterface") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $p = array($_POST["service_id"], $_POST["host_id"], $_POST["interface_id"],
        $_POST["customer_id"]);
    $r = do_xmlrpc($_REQUEST["do"], $p, $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    assignCustomerInterface($_POST["service_id"], $_POST["host_id"], 
        $_POST["interface_id"]);
    $select = getEthernetCustomersSelect(getEthernetCustomersList($service_id));
    $smarty->assign("ethernet_customers_select", $select);
    $smarty->display("mods/service/ethernet_customer-ilist.tpl");
    exit;

/********************************************************************
 * Edit the network wide Firewall properties
 * do=edit
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    assignEthernetCustomer($_REQUEST["service_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "ethernet_customer-props.js");
    display_page("mods/service/ethernet_customer-props.tpl");

/********************************************************************
 * Update a property of the firewall network-wide
 * do=updateFirewallProperty
 * Required Paramters
 * service_id       The service_id
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateEthernetCustomerProperty") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    if ($_REQUEST["value"]=="") {
        $r = do_xmlrpc("clearServiceProperty", 
            array($_REQUEST["service_id"], $propName), 
            $xmlrpc_conn, TRUE, FALSE); 
    } else {
        $r = do_xmlrpc("updateServiceProperty", 
            array($_REQUEST["service_id"], $_REQUEST["propName"],
            $_REQUEST["value"]), $xmlrpc_conn, TRUE, FALSE);
    }
    // XXX: Should return a 40x error if something went wrong
    assignEthernetCustomer($_REQUEST["service_id"]);
    $smarty->display("mods/service/ethernet_customer-propdetails.tpl");
    exit;
        
}

?>
