<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * Amplet Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
require_once("ccs_init.php");

function getAmpletGroups($service_id)
{
    global $xmlrpc_conn;
    
    $p = array($service_id);
    $groups = do_xmlrpc("getAmpletGroups", $p);
    return $groups;
}
function assignAmpletGroupSelect($service_id)
{
    global $xmlrpc_conn, $smarty;
    
    $p = array($service_id);
    $groups = do_xmlrpc("getAmpletGroups", $p);
    $names = array();
    $descs = array();
    foreach ($groups as $group) {
        $names[$group["amplet_group_id"]] = $group["group_name"];
        $descs[$group["amplet_group_id"]] = $group["group_description"];    
    }
    $smarty->assign("amplet_group_names", $names);
    $smarty->assign("amplet_groups", $descs);
    return $groups;
}
function assignAmplet($service_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id);
    $service = do_xmlrpc("getServiceDetails", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve amplet details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $service["groups"] = getAmpletGroups($service_id);
    $smarty->assign("amplet", $service);

    return $service;
}
function assignHostAmplet($service_id, $host_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $service = do_xmlrpc("getHostAmpletDetails", $p, $xmlrpc_conn,TRUE,FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve amplet details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $smarty->assign("amplet", $service);
    assignAmpletGroupSelect($service_id);
    
    return $service;
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
                    $propName, $_POST[$propName]), $xmlrpc_conn,
                TRUE, FALSE);
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
    assignHostAmplet($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->assign("sheets", array("service.css", "amplet.css"));
    $smarty->assign("scripts", "amplet.js");
    display_page("mods/service/amplet.tpl");
    
/********************************************************************
 * Edit the network wide Amplet properties
 * do=edit
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    assignAmplet($_REQUEST["service_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "amplet-props.js");
    display_page("mods/service/amplet-props.tpl");
    
/********************************************************************
 * Create a new Amplet Group
 * do=createAmpletGroup
 ********************************************************************/
} else if ($_REQUEST["do"] == "createAmpletGroup") {
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "amplet-props.js");
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        $rv = do_xmlrpc("createAmpletGroup", array($_REQUEST["service_id"],
            $_REQUEST["group_name"], $_REQUEST["group_description"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not create group: ".xmlrpc_error_string($rv));
        } else {
            assignAmplet($_REQUEST["service_id"]);
            display_page("mods/service/amplet-props.tpl");
        }
    }
    $smarty->assign("service_id", $_REQUEST["service_id"]);
    display_page("mods/service/amplet-createGroup.tpl");
    
/********************************************************************
 * Delete an AMPlet group
 * do=deleteAMPlet group
 ********************************************************************/
} else if ($_REQUEST["do"] == "deleteAmpletGroup") {
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "amplet-props.js");
    $rv = do_xmlrpc("removeAmpletGroup", array($_REQUEST["service_id"],
            $_REQUEST["amplet_group_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        ccs_notice("Could not delete group: ".xmlrpc_error_string($rv));
    }
    assignAmplet($_REQUEST["service_id"]);
    display_page("mods/service/amplet-props.tpl");
    
    
/********************************************************************
 * Update the state of amplet on the host
 * do=updateAmpletState
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateAmpletState") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc("changeServiceHostState", 
        array($_REQUEST["service_id"], $_REQUEST["host_id"],
        $_REQUEST["value"]), $xmlrpc_conn, TRUE, FALSE);
    // XXX: Should return a 40x error if something went wrong
    assignHostAmplet($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->display("mods/service/amplet-hostdetails.tpl");
    exit;
    
/********************************************************************
 * Update a property of amplet on the host
 * do=updateAmpletProperty
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateAmpletHostProperty") {
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
    assignHostAmplet($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->display("mods/service/amplet-hostdetails.tpl");
    exit;
    
/********************************************************************
 * Update a property of amplet network-wide
 * do=updateAmpletProperty
 * Required Paramters
 * service_id       The service_id
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateAmpletProperty") {
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
    assignAmplet($_REQUEST["service_id"]);
    $smarty->display("mods/service/amplet-propdetails.tpl");
    exit;

}

?>
