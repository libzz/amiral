<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * Firewall Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
require_once("ccs_init.php");
require_once("firewall_common.php");

function assignFirewallClass($service_id, $firewall_class_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $firewall_class_id);
    $fclass = do_xmlrpc("getFirewallClass", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($fclass)) {
        ccs_notice("Could not retrieve firewall class: " .
            xmlrpc_error_string($fclass));
        return array();
    }

    $smarty->assign("firewall_class_id", $fclass["firewall_class_id"]);
    $smarty->assign("firewall_class_name", $fclass["firewall_class_name"]);
    $smarty->assign("description", $fclass["description"]);
    $smarty->assign("contents", $fclass["contents"]);

    return $fclass;
}
function assignHostFirewall($service_id, $host_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $service = do_xmlrpc("getHostFirewallDetails", $p, $xmlrpc_conn,TRUE,FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve firewall details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $service["firewall_classes"] = getFirewallClassList($service_id);
    $select = getFirewallClassesSelect($service["firewall_classes"]);
    $select[-1] = "(Use network default)";
    $service["firewall_classes_select"] = $select;
    $smarty->assign("firewall", $service);

    return $service;
}
function assignFirewallInterface($service_id, $host_id, $interface_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $ifaces = do_xmlrpc("getFirewallInterfaces", $p, $xmlrpc_conn, TRUE,
        FALSE);
    if (xmlrpc_has_error($ifaces)) {
        ccs_notice("Could not retrieve firewall details: " .
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
    assignHostFirewall($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->assign("sheets", array("service.css", "firewall.css"));
    $smarty->assign("scripts", "firewall.js");
    display_page("mods/service/firewall.tpl");
    
/********************************************************************
 * Update the firewall class assigned to an interface
 * do=updateFirewallInterface
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * interface_id     The interface to enable/disable OSPF on
 * firewall_class_id The new firewall class for the interface
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateFirewallInterface") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc($_REQUEST["do"], array($_POST["service_id"], 
        $_POST["host_id"], $_POST["interface_id"], 
        $_POST["firewall_class_id"]), $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    assignFirewallInterface($_POST["service_id"], $_POST["host_id"], 
        $_POST["interface_id"]);
    $select = getFirewallClassesSelect(getFirewallClassList($service_id));
    $select[-1] = "(Use network default)";
    $smarty->assign("firewall_classes_select", $select);
    $smarty->display("mods/service/firewall-ilist.tpl");
    exit;
    
/********************************************************************
 * Edit the network wide Firewall properties
 * do=edit
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    assignFirewall($_REQUEST["service_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "firewall-props.js");
    display_page("mods/service/firewall-props.tpl");
    
/********************************************************************
 * Create a new Firewall Class
 * do=createFirewallClass
 ********************************************************************/
} else if ($_REQUEST["do"] == "createFirewallClass") {
    $smarty->assign("action", "create");
    $smarty->assign("sheets", array("service.css", "firewall.css"));
    $smarty->assign("scripts", "firewall-props.js");
    $details = array();
    get_if_posted(&$details, "firewall_class_name");
    get_if_posted(&$details, "description");
    get_if_posted(&$details, "contents");
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        $rv = do_xmlrpc("createFirewallClass", 
            array($_REQUEST["service_id"], $details),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not create class: ".xmlrpc_error_string($rv));
            $smarty->assign("firewall_class_name", 
                $_POST["firewall_class_name"]);
            $smarty->assign("description", stripslashes($_POST["description"]));
            $smarty->assign("contents", stripslashes($_POST["contents"]));
        } else {
            assignFirewall($_REQUEST["service_id"]);
            display_page("mods/service/firewall-props.tpl");
        }
    }
    $smarty->assign("service_id", $_REQUEST["service_id"]);
    display_page("mods/service/firewall-classform.tpl");
    
/********************************************************************
 * Modify a Firewall Class
 * do=updateFirewallClass
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateFirewallClass") {
    $smarty->assign("action", "update");
    $smarty->assign("sheets", array("service.css", "firewall.css"));
    $smarty->assign("scripts", "firewall-props.js");
    $details = array();
    get_if_posted(&$details, "firewall_class_id");
    get_if_posted(&$details, "firewall_class_name");
    get_if_posted(&$details, "description");
    get_if_posted(&$details, "contents");
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        $rv = do_xmlrpc("updateFirewallClass", 
            array($_REQUEST["service_id"], $details),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update class: ".xmlrpc_error_string($rv));
            $smarty->assign("firewall_class_id", $_POST["firewall_class_id"]);
            $smarty->assign("firewall_class_name", 
                $_POST["firewall_class_name"]);
            $smarty->assign("description", stripslashes($_POST["description"]));
            $smarty->assign("contents", stripslashes($_POST["contents"]));
        } else {
            assignFirewall($_REQUEST["service_id"]);
            display_page("mods/service/firewall-props.tpl");
        }
    } else {
        assignFirewallClass($_REQUEST["service_id"], 
            $_REQUEST["firewall_class_id"]);
    }
    $smarty->assign("service_id", $_REQUEST["service_id"]);
    display_page("mods/service/firewall-classform.tpl");
     
/********************************************************************
 * Delete a firewall class
 * do=deleteFirewallClass
 ********************************************************************/
} else if ($_REQUEST["do"] == "deleteFirewallClass") {
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "firewall-props.js");
    $rv = do_xmlrpc("removeFirewallClass", 
        array($_REQUEST["service_id"], $_REQUEST["firewall_class_id"]),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        ccs_notice("Could not delete class: ".xmlrpc_error_string($rv));
    }
    assignFirewall($_REQUEST["service_id"]);
    display_page("mods/service/firewall-props.tpl");
         
/********************************************************************
 * Update the state of the firewall on the host
 * do=updateFirewallState
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateFirewallState") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc("changeServiceHostState", 
        array($_POST["service_id"], $_POST["host_id"],
        $_POST["value"]), $xmlrpc_conn, TRUE, FALSE);
    // XXX: Should return a 40x error if something went wrong
    assignHostFirewall($_POST["service_id"], $_POST["host_id"]);
    $smarty->display("mods/service/firewall-hostdetails.tpl");
    exit;
    
/********************************************************************
 * Update a property of the firewall network-wide
 * do=updateFirewallProperty
 * Required Paramters
 * service_id       The service_id
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateFirewallProperty") {
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
    assignFirewall($_REQUEST["service_id"]);
    $smarty->display("mods/service/firewall-propdetails.tpl");
    exit;
    
}

?>
