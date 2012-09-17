<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * HostAPd Web Interface for the CRCnet Configuration System
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

function assignHostHostAPd($service_id, $host_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id, $host_id);
    $service = do_xmlrpc("getHostHostAPdDetails", $p, $xmlrpc_conn,TRUE,FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve HostAP details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $smarty->assign("hostapd", $service);

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
    assignHostHostAPd($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->assign("sheets", array("service.css"));
    $smarty->assign("scripts", "hostapd.js");
    display_page("mods/service/hostapd.tpl");
       
/********************************************************************
 * Enable / Disable OPSF on a host interface
 * do=enableHostAPdInterface
 * do=disableHostAPdInterface
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * interface_id     The interface to enable/disable HostAPD on
 ********************************************************************/
} else if ($_REQUEST["do"] == "enableHostAPdInterface" || 
        $_REQUEST["do"] == "disableHostAPdInterface") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc($_REQUEST["do"], array($_REQUEST["service_id"], 
        $_REQUEST["host_id"], $_REQUEST["interface_id"]), 
        $xmlrpc_conn, TRUE, FALSE); 
    if ($_REQUEST["do"] == "enableHostAPdInterface") {
        echo "<script type=\"text/javascript\">$('hostapd-" . 
            $_REQUEST["interface_id"] . "').checked = true;</script>";
    } else {
        echo "<script type=\"text/javascript\">$('hostapd-" . 
            $_REQUEST["interface_id"] . "').checked = false;</script>";
    }
    exit;

} else if ($_REQUEST["do"] == "updateHostAPdInterface"){
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc($_REQUEST["do"], array($_REQUEST["service_id"], 
        $_REQUEST["host_id"], $_REQUEST["interface_id"], $_REQUEST["val"]), 
        $xmlrpc_conn, TRUE, FALSE); 
	header("Content-Type: text/javascript");
	echo "$('hostapd-" . 
		$_REQUEST["interface_id"] . "').disabled = false;";
    exit;
}

?>
