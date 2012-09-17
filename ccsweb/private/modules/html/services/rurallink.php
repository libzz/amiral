<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * RuralLink Service Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
require_once("ccs_init.php");

function assignRurallink($service_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id);
    $service = do_xmlrpc("getServiceDetails", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve rurallink details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $smarty->assign("rurallink", $service);

    return $service;
}

if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    display_service_list();
}

/********************************************************************
 * Edit the network wide Quagga properties
 * do=edit
 ********************************************************************/
if ($_REQUEST["do"] == "edit") {
    assignRurallink($_REQUEST["service_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "rurallink-props.js");
    display_page("mods/service/rurallink-props.tpl");
    
    
/********************************************************************
 * Update a property network-wide
 * do=updateRurallinkProperty
 * Required Paramters
 * service_id       The service_id
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateRurallinkProperty") {
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
    assignRurallink($_REQUEST["service_id"]);
    $smarty->display("mods/service/rurallink-propdetails.tpl");
    exit;
    
}

?>
