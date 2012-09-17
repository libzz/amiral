<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Service Configuration
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
require("ccs_init.php");
require("service/service_common.php");
require("host/host_common.php");

if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    display_service_list();
}

/* Handle service specific overrides */
$serviceName = getServiceName($_REQUEST["service_id"]);
$smarty->assign("service_name", $serviceName);
$dir = dirname($_SERVER["SCRIPT_FILENAME"]);
if (file_exists("$dir/$serviceName.php")) {
    require_once("$dir/$serviceName.php");
}

/********************************************************************
 * Configure a service
 * do=configure
 * Looks for a service specific file to display, or displays the 
 * generic service edit form
 ********************************************************************/
if ($_REQUEST["do"] == "configure") {
    /* Process posted values */
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        $c=0;
        foreach (explode(" ", trim($_POST["properties"])) as $idx=>$propName) {
            if ($_POST[$propName] == $_POST["${propName}-orig"]) {
                continue;
            }
            $rv = do_xmlrpc("updateServiceHostProperty", 
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
    assignHostService($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "service.js");
    display_page("mods/service/configureService.tpl");
    
/********************************************************************
 * Edit a service (network wide)
 * do=edit
 * Looks for a service specific file to display, or displays the 
 * generic service edit form
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    /* Process posted values */
    // XXX: TODO
    /* Display the generic service edit form */
    assignService($_REQUEST["service_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "service.js");
    display_page("mods/service/editService.tpl");
    
/********************************************************************
 * Disable/Enable a service
 * do=disable/enable
 * Optional Parameters
 ********************************************************************/
} else if ($_REQUEST["do"] == "disable") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $do = $_REQUEST["do"];
    $rv = do_xmlrpc("changeServiceState", array($_REQUEST["service_id"], "f"),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        ccs_notice("Could not disable service: ".xmlrpc_error_string($rv));
    }
    display_service_list();
    
} else if ($_REQUEST["do"] == "enable") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $do = $_REQUEST["do"];
    $rv = do_xmlrpc("changeServiceState", array($_REQUEST["service_id"], "t"),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        ccs_notice("Could not enable service: ".xmlrpc_error_string($rv));
    }
    display_service_list();
    
} 

/* If we get here the page has been called incorrectly, display the list */
ccs_notice("Invalid Action Requested: " . $_REQUEST["do"]);
display_service_list();

?>
