<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * BIND Web Interface for the CRCnet Configuration System
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

function assignBind($service_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id);
    $service = do_xmlrpc("getServiceDetails", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve DNS details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $links = assignLinks(TRUE);
    # Find the link that matches the selected DNS server link
    foreach ($links as $link_id => $link) {
        if ($link_id == $service["properties"]["dns_server_link"]["network_value"]) {
            $service["dns_server_link_desc"] = $link["netblock"];
        }
    }
    $smarty->assign("bind", $service);

    return $service;
}
function assignHostBind($service_id, $host_id) 
{
    global $smarty, $xmlrpc_conn;

    $bind = assignBind($service_id);

    $p = array($service_id, $host_id);
    $service = do_xmlrpc("getDNSServer", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve DNS details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $bind["host"] = $service;
    $smarty->assign("bind", $bind);

    return $bind;
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
    assignHostBind($_REQUEST["service_id"], $_REQUEST["host_id"]);
    $smarty->assign("sheets", array("service.css", "bind.css"));
    $smarty->assign("scripts", "bind.js");
    display_page("mods/service/bind.tpl");
    
/********************************************************************
 * Update the DNS details for the host
 * do=updateDNSServer
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * is_master        Is the host authorative for the domains
 * dns_server_ip    IP Address to run the DNS server from
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateDNSServer") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $p = array($_POST["service_id"], $_POST["host_id"], $_POST["is_master"],
        $_POST["dns_ip_address"]);
    $r = do_xmlrpc($_REQUEST["do"], $p, $xmlrpc_conn, TRUE, FALSE); 
    // XXX: Should return a 40x error if something went wrong
    exit;

/********************************************************************
 * Edit the network wide properties
 * do=edit
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    assignBind($_REQUEST["service_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "bind-props.js");
    display_page("mods/service/bind-props.tpl");

/********************************************************************
 * Update a property network-wide
 * do=updateBindProperty
 * Required Paramters
 * service_id       The service_id
 * propName         The property to update
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateBindProperty") {
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
    assignBind($_REQUEST["service_id"]);
    $smarty->display("mods/service/bind-propdetails.tpl");
    exit;

/********************************************************************
 * Update the state of bind on the host
 * do=updateBindState
 * Required Paramters
 * service_id       The service_id
 * host_id          Host the interface is on
 * value            The new value of the parameter
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateBindState") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    /* Return result */
    $r = do_xmlrpc("changeServiceHostState", 
        array($_REQUEST["service_id"], $_REQUEST["host_id"],
        $_REQUEST["value"]), $xmlrpc_conn, TRUE, FALSE);
    // XXX: Should return a 40x error if something went wrong
    exit;
        
}

?>
