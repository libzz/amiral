<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * DHCP Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
require_once("ccs_init.php");

function assignDHCP($service_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id);
    $service = do_xmlrpc("getServiceDetails", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve DHCP details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $smarty->assign("dhcp", $service);

    return $service;
}
function assignHostDHCP($service_id, $host_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $service = do_xmlrpc("getHostDHCPDetails", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve DHCP details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $smarty->assign("dhcp", $service);

    return $service;
}
function assignDHCPInterface($service_id, $host_id, $interface_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $ifaces = do_xmlrpc("getDHCPInterfaces", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($ifaces)) {
        ccs_notice("Could not retrieve DHCP details: " .
            xmlrpc_error_string($ifaces));
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
    /* Process posted values */
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        $c=0;
        foreach (explode(" ", trim($_POST["properties"])) as $idx=>$propName) {
            if ($_POST[$propName] == $_POST["${propName}-orig"]) {
                continue;
            }
            $rv = do_xmlrpc("updateServiceProperty", 
                array($_REQUEST["service_id"], $_REQUEST["host_id"], 
                    $propName, $_POST[$propName]), $xmlrpc_conn, TRUE, FALSE);
            if (xmlrpc_has_error($rv)) {
                ccs_notice("Could not update property: " .
                    xmlrpc_error_string($rv));
            } else {
                $c++;
            }
        }
        if ($_POST["service_host_enabled"]!=
                $_POST["service_host_enabled-orig"]) {
            $rv = do_xmlrpc("changeServiceHostState", 
                array($_REQUEST["service_id"], $_REQUEST["host_id"], 
                    $_POST["service_host_enabled"]), $xmlrpc_conn,
                    TRUE, FALSE);
            if (xmlrpc_has_error($rv)) {
                ccs_notice("Could not update enabled status: " . 
                    xmlrpc_error_string($rv));
            } else {
                $c++;
            }
        }   
        if ($c) {
            ccs_notice("Service properties updated.");
        } 
    }
    /* Display the generic service edit form */
    $smarty->assign("host", getHost($_REQUEST["host_id"], FALSE, FALSE));
    assignHostDHCP($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "dhcp.js");
    display_page("mods/service/dhcp.tpl");
    
/********************************************************************
 * Edit the network wide DHCP properties
 * do=edit
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    assignDHCP($_REQUEST["service_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "dhcp-props.js");
    display_page("mods/service/dhcp-props.tpl");
    
/********************************************************************
 * Enable / Disable DHCP on a host interface
 * do=enableDHCPInterface
 * do=disableDHCPInterface
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * interface_id     The interface to enable/disable OSPF on
 ********************************************************************/
} else if ($_REQUEST["do"] == "enableDHCPInterface" || 
        $_REQUEST["do"] == "disableDHCPInterface") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc($_REQUEST["do"], array($_REQUEST["service_id"], 
        $_REQUEST["host_id"], $_REQUEST["interface_id"]), 
        $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    assignDHCPInterface($_REQUEST["service_id"], $_REQUEST["host_id"], 
        $_REQUEST["interface_id"]);
    $smarty->display("mods/service/dhcp-ilist.tpl");
    exit;
    
/********************************************************************
 * Update a DHCP property on a host interface
 * do=updateDHCPInterface
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * interface_id     The interface to update
 * param            The parameter to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateDHCPInterface") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc($_REQUEST["do"], array($_REQUEST["service_id"], 
        $_REQUEST["host_id"], $_REQUEST["interface_id"], 
        $_REQUEST["param"], $_REQUEST["value"]), 
        $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    assignDHCPInterface($_REQUEST["service_id"], $_REQUEST["host_id"], 
        $_REQUEST["interface_id"]);
    $smarty->display("mods/service/dhcp-ilist.tpl");
    exit;
    
/********************************************************************
 * Update the state of DHCP on the host
 * do=updateDHCPState
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateDHCPState") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc("changeServiceHostState", 
        array($_REQUEST["service_id"], $_REQUEST["host_id"],
        $_REQUEST["value"]), $xmlrpc_conn, TRUE, FALSE);
    // XXX: Should return a 40x error if something went wrong
    assignHostQuagga($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->display("mods/service/dhcp-hostdetails.tpl");
    exit;
    
/********************************************************************
 * Update a property of quagga on the host
 * do=updateDHCPHostProperty
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateDHCPHostProperty") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    if ($_REQUEST["value"]=="") {
        $r = do_xmlrpc("clearServiceHostProperty", 
            array($_REQUEST["service_id"], $_REQUEST["host_id"], 
            $propName), $xmlrpc_conn, TRUE, FALSE); 
    } else {
        $r = do_xmlrpc("updateServiceHostProperty", 
            array($_REQUEST["service_id"], $_REQUEST["host_id"], 
            $_REQUEST["propName"], $_REQUEST["value"]), 
                $xmlrpc_conn, TRUE, FALSE);
    }
    // XXX: Should return a 40x error if something went wrong
    assignHostDHCP($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->display("mods/service/dhcp-hostdetails.tpl");
    exit;
    
/********************************************************************
 * Update a property of DHCP network-wide
 * do=updateDHCPProperty
 * Required Paramters
 * service_id       The service_id
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateDHCPProperty") {
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
    assignDHCP($_REQUEST["service_id"]);
    $smarty->display("mods/service/dhcp-propdetails.tpl");
    exit;

}

?>
