<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * Quagga Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
require_once("ccs_init.php");

function getOSPFAreaList($service_id)
{
    global $xmlrpc_conn;
    
    $p = array($service_id);
    $areas = do_xmlrpc("getQuaggaOSPFAreas", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($areas)) {
        ccs_notice("Could not retrieve area details: " .
            xmlrpc_error_string($areas));
        $areas = array();
    }
    return $areas;
}
function getStaticList($service_id, $host_id)
{
    global $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $statics = do_xmlrpc("getQuaggaStaticRoutes", $p, $xmlrpc_conn, TRUE, 
        FALSE);
    if (xmlrpc_has_error($statics)) {
        ccs_notice("Could not retrieve static route details: " .
            xmlrpc_error_string($statics));
        $statics = array();
    }
    return $statics;
}
function assignQuagga($service_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id);
    $service = do_xmlrpc("getServiceDetails", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve quagga details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $service["areas"] = getOSPFAreaList($service_id);
    $smarty->assign("quagga", $service);

    return $service;
}
function assignHostQuagga($service_id, $host_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $service = do_xmlrpc("getHostQuaggaDetails", $p, $xmlrpc_conn,TRUE,FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve quagga details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $service["areas"] = getOSPFAreaList($service_id);
    $service["statics"] = getStaticList($service_id, $host_id);
    $smarty->assign("quagga", $service);

    return $service;
}
function assignOSPFInterface($service_id, $host_id, $interface_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $ifaces = do_xmlrpc("getQuaggaOSPFInterfaces", $p, $xmlrpc_conn, TRUE,
        FALSE);
    if (xmlrpc_has_error($ifaces)) {
        ccs_notice("Could not retrieve quagga details: " .
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
    assignHostQuagga($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->assign("sheets", array("service.css", "quagga.css"));
    $smarty->assign("scripts", "quagga.js");
    display_page("mods/service/quagga.tpl");
    
/********************************************************************
 * Edit the network wide Quagga properties
 * do=edit
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    assignQuagga($_REQUEST["service_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "quagga-props.js");
    display_page("mods/service/quagga-props.tpl");
    
/********************************************************************
 * Create a new OSPF area
 * do=createOSPFArea
 ********************************************************************/
} else if ($_REQUEST["do"] == "createOSPFArea") {
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "quagga-props.js");
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        $rv = do_xmlrpc("createOSPFArea", array($_REQUEST["service_id"],
            $_REQUEST["area_no"], $_REQUEST["link_class_id"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not create area: ".xmlrpc_error_string($rv));
        } else {
            assignQuagga($_REQUEST["service_id"]);
            display_page("mods/service/quagga-props.tpl");
        }
    }
    assignLinkClasses(TRUE);
    $smarty->assign("service_id", $_REQUEST["service_id"]);
    display_page("mods/service/quagga-createOSPFArea.tpl");
    
/********************************************************************
 * Delete an OSPF area
 * do=deleteOSPFArea
 ********************************************************************/
} else if ($_REQUEST["do"] == "deleteOSPFArea") {
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "quagga-props.js");
    $rv = do_xmlrpc("removeOSPFArea", array($_REQUEST["service_id"],
            $_REQUEST["area_no"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        ccs_notice("Could not delete area: ".xmlrpc_error_string($rv));
    }
    assignQuagga($_REQUEST["service_id"]);
    display_page("mods/service/quagga-props.tpl");
    
/********************************************************************
 * Enable / Disable OPSF on a host interface
 * do=enableOSPFInterface
 * do=disableOSPFInterface
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * interface_id     The interface to enable/disable OSPF on
 ********************************************************************/
} else if ($_REQUEST["do"] == "enableOSPFInterface" || 
        $_REQUEST["do"] == "disableOSPFInterface") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc($_REQUEST["do"], array($_REQUEST["service_id"], 
        $_REQUEST["host_id"], $_REQUEST["interface_id"]), 
        $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    assignOSPFInterface($_REQUEST["service_id"], $_REQUEST["host_id"], 
        $_REQUEST["interface_id"]);
    if ($_REQUEST["do"] == "enableOSPFInterface") {
        $smarty->assign("areas", getOSPFAreaList($_REQUEST["service_id"]));
    }
    $smarty->display("mods/service/quagga-ospf-ilist.tpl");
    exit;
    
/********************************************************************
 * Update an OSPF property on a host interface
 * do=updateOSPFInterface
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * interface_id     The interface to enable/disable OSPF on
 * param            The parameter to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateOSPFInterface") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc($_REQUEST["do"], array($_REQUEST["service_id"], 
        $_REQUEST["host_id"], $_REQUEST["interface_id"], 
        $_REQUEST["param"], $_REQUEST["value"]), $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    assignOSPFInterface($_REQUEST["service_id"], $_REQUEST["host_id"], 
        $_REQUEST["interface_id"]);
    $smarty->assign("areas", getOSPFAreaList($_REQUEST["service_id"]));
    $smarty->display("mods/service/quagga-ospf-ilist.tpl");
    exit;
    
/********************************************************************
 * Update the state of quagga on the host
 * do=updateQuaggaState
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateQuaggaState") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc("changeServiceHostState", 
        array($_REQUEST["service_id"], $_REQUEST["host_id"],
        $_REQUEST["value"]), $xmlrpc_conn, TRUE, FALSE);
    // XXX: Should return a 40x error if something went wrong
    assignHostQuagga($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->display("mods/service/quagga-hostdetails.tpl");
    exit;
    
/********************************************************************
 * Update a property of quagga on the host
 * do=updateQuaggaProperty
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateQuaggaHostProperty") {
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
    assignHostQuagga($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->display("mods/service/quagga-hostdetails.tpl");
    exit;
    
/********************************************************************
 * Update a property of quagga network-wide
 * do=updateQuaggaProperty
 * Required Paramters
 * service_id       The service_id
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateQuaggaProperty") {
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
    assignQuagga($_REQUEST["service_id"]);
    $smarty->display("mods/service/quagga-propdetails.tpl");
    exit;
    
/********************************************************************
 * Create a template for a new static route ROW
 * do=newStatic
 ********************************************************************/
} else if ($_REQUEST["do"] == "newStatic") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $static = array("static_id" => "NEW");
    $smarty->assign("static", $static);
    $smarty->display("mods/service/quagga-static-row.tpl");
    exit;
    
/********************************************************************
 * Create a new static route
 * do=createStatic
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * static route parameters
 ********************************************************************/
} else if ($_REQUEST["do"] == "createStatic") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $details = array();
    $details["host_id"] = $_REQUEST["host_id"];
    $details["description"] = $_REQUEST["description"];
    $details["prefix"] = $_REQUEST["prefix"];
    $details["next_hop"] = $_REQUEST["next_hop"];
    $r = do_xmlrpc("quaggaCreateStatic", array($_REQUEST["service_id"], 
        $details), $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    $smarty->assign("statics", getStaticList($_REQUEST["service_id"],
        $_REQUEST["host_id"]));
    $smarty->display("mods/service/quagga-static.tpl");
    exit;

/********************************************************************
 * Update a property of a static route
 * do=updateStatic
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * static_id        The route to update
 * param            The parameter to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateStatic") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc("quaggaUpdateStatic", array($_REQUEST["service_id"], 
        $_REQUEST["static_id"], $_REQUEST["param"], 
        $_REQUEST["value"]), $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    $smarty->assign("statics", getStaticList($_REQUEST["service_id"],
        $_REQUEST["host_id"]));
    $smarty->display("mods/service/quagga-static.tpl");
    exit;
    
/********************************************************************
 * Remove a static route
 * do=removeStatic
 * Required Paramters
 * service_id       The service_id
 * static_id        The route to update
 ********************************************************************/
} else if ($_REQUEST["do"] == "removeStatic") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc("quaggaRemoveStatic", array($_REQUEST["service_id"], 
        $_REQUEST["static_id"]), $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    $smarty->assign("statics", getStaticList($_REQUEST["service_id"],
        $_REQUEST["host_id"]));
    $smarty->display("mods/service/quagga-static.tpl");
    exit;

}

?>
