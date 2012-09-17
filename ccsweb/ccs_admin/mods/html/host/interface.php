<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Interface Configuration
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
require("host/host_common.php");

if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    display_host_list();
}

/********************************************************************
 * Add an Interface
 * do=add
 * Optional Parameters
 ********************************************************************/
if ($_REQUEST["do"] == "add") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Retrieve posted data */
        $interface = array();
        get_if_posted(&$interface, "interface_type");
        get_if_posted(&$interface, "host_id");
        get_if_posted(&$interface, "link_id");
        get_if_posted(&$interface, "subasset_id");
        get_if_posted(&$interface, "raw_interface");
        get_if_posted(&$interface, "bridge_interface");
        get_if_posted(&$interface, "ifname");
        get_if_checked(&$interface, "interface_active");
        get_if_posted(&$interface, "module_id");
        get_if_posted(&$interface, "ip_address");
        get_if_posted(&$interface, "alias_netmask");
        get_if_checked(&$interface, "master_interface");
        get_if_posted(&$interface, "master_channel");
        get_if_posted(&$interface, "master_mode");
        get_if_posted(&$interface, "vid");
        get_if_checked(&$interface, "monitor_interface");
        get_if_checked(&$interface, "use_gateway");
	    $interface["name"] = $interface["ifname"];
        $interface["alias_netmask"] = str_replace("/", "", 
            $interface["alias_netmask"]);
        $rv = do_xmlrpc("addInterface", array($interface), $xmlrpc_conn, 
            TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not add interface: ".xmlrpc_error_string($rv));
            $smarty->assign("interface", $interface);
        } else {
            ccs_notice("Interface (" . $interface["ifname"] . 
                ") successfully created.");
            displayHost($interface["host_id"]);
        }
    }
    assignModules(TRUE);
    $host = getHost($_REQUEST["host_id"]);
    $smarty->assign("host", $host);
    assignBridgeableInterfaces($host["interfaces"]);
    assignLinkModes("Managed", TRUE);
    if (isset($_REQUEST["subasset_id"])) {
        $smarty->assign("subasset_id", $_REQUEST["subasset_id"]);
        foreach ($host["interfaces"] as $idx=>$iface) {
            if ($iface["subasset_id"] == $_REQUEST["subasset_id"]) {
                $smarty->assign("subasset_desc", $iface["subasset_desc"]);
                break;
            }
        }
        assignLinks(TRUE, $_REQUEST["subasset_id"]);
        /* Lock the type depending on the subasset's supported functions */
        $funcs = getSubassetFunctions($_REQUEST["subasset_id"]);
        if (in_array("vap", $funcs)) {
            $smarty->assign("interface_type", $INTERFACE_TYPE_VAP);
            $smarty->assign("interface_type_desc", 
                $interface_types[$INTERFACE_TYPE_VAP]);
        } else {
            $smarty->assign("interface_type", $INTERFACE_TYPE_PHYSICAL);
            $smarty->assign("interface_type_desc", 
                $interface_types[$INTERFACE_TYPE_PHYSICAL]);
        }
    } else {
        assignLinks(TRUE);
        assignInterfaceTypes();
    }
    $smarty->assign("action", "add");
    $smarty->assign("sheets", array("interface.css"));
    $smarty->assign("scripts", array("interface.js"));
    display_page("mods/host/ifaceform.tpl");

/********************************************************************
 * Configure an Interface
 * do=edit
 * Optional Parameters
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Look for changed data */
        $interface = array();
        get_if_posted(&$interface, "host_id");
        get_if_posted(&$interface, "interface_id");
        get_if_post_modified(&$interface, "interface_type");
        get_if_post_modified(&$interface, "link_id");
        get_if_post_modified(&$interface, "subasset_id");
        get_if_post_modified(&$interface, "raw_interface");
        get_if_post_modified(&$interface, "bridge_interface");
        get_if_post_modified(&$interface, "ifname");
        get_if_checked_modified(&$interface, "interface_active");
        get_if_post_modified(&$interface, "module_id");
        get_if_post_modified(&$interface, "ip_address");
        get_if_post_modified(&$interface, "alias_netmask");
        get_if_checked_modified(&$interface, "master_interface");
        get_if_post_modified(&$interface, "master_channel");
        get_if_post_modified(&$interface, "master_mode");
        get_if_checked_modified(&$interface, "monitor_interface");
        get_if_checked_modified(&$interface, "use_gateway");
        if ($interface["ifname"] != "") {
            $interface["name"] = $interface["ifname"];
        }
        $interface["alias_netmask"] = str_replace("/", "", 
            $interface["alias_netmask"]);
        $rv = do_xmlrpc("updateInterfaceDetails", 
            array($_REQUEST["interface_id"], $interface), $xmlrpc_conn, 
            TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update interface: " .
                xmlrpc_error_string($rv));
        } else {
            ccs_notice("Interface configuration successfully updated.");
            displayHost($interface["host_id"]);
        }

    }
    if (!isset($_REQUEST["host_id"])) {
        ccs_notice("Host ID not set!");
        display_host_list();
    }
    if (!isset($_REQUEST["interface_id"])) {
        ccs_notice("Interface ID not set!");
        displayHost($_REQUEST["host_id"]);
    }
    assignLinks(TRUE);
    assignModules(TRUE);
    $host = getHost($_REQUEST["host_id"]);
    $smarty->assign("host", $host);
    assignBridgeableInterfaces($host["interfaces"]);
    $link_id = -1;
    foreach ($host["interfaces"] as $idx=>$iface) {
        if ($iface["interface_id"] == $_REQUEST["interface_id"]) {
            $link_id = $iface["link_id"];
            $smarty->assign("iface", $iface);
            $smarty->assign("interface_type", $iface["interface_type"]);
            $smarty->assign("interface_type_desc", 
                $interface_types[$iface["interface_type"]]);
            $smarty->assign("subasset_id", $iface["subasset_id"]);
            $smarty->assign("subasset_desc", $iface["subasset_desc"]);
            assignLinkModes("Managed", TRUE);
            if ($iface["master_mode"]!="")
                assignChannelList($iface["master_mode"], TRUE);
            break;
        }
    }
    /* Show the form */
    $smarty->assign("action", "edit");
    $smarty->assign("sheets", array("interface.css"));
    $smarty->assign("scripts", array("interface.js"));
    display_page("mods/host/ifaceform.tpl");
    
/********************************************************************
 * Remove an interface from a host
 * do=remove
 * Required Paramters
 * host_id
 * interface_id
 * confirm
 * If confirm is not set a page is displayed asking the user to confirm
 * they wish to delete this host.
 ********************************************************************/
} else if ($_REQUEST["do"] == "remove") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    if ($_REQUEST["confirm"] != "yes") {
        /* Get the interface data */
        $host = assignHost($_REQUEST["host_id"]);
        $link_id = -1;
        foreach ($host["interfaces"] as $idx=>$iface) {
            if ($iface["interface_id"] == $_REQUEST["interface_id"]) {
                $link_id = $iface["link_id"];
                $smarty->assign("interface", $iface);
                break;
            }
        }
        /* Ask the user to confirm deletion */
        display_page("mods/host/ifacedel.tpl");
    } else {
        /* Delete interface */
        $rv = do_xmlrpc("removeInterface",
            array($_REQUEST["interface_id"]), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not delete interface: " .
                xmlrpc_error_string($rv));
        } else {
            ccs_notice("Interface successfully deleted!");
        }
        /* Display site list */
        displayHost($_REQUEST["host_id"]);
    }
    
/********************************************************************
 * Return the list of assets that a new interface on the specified host
 * and link could utilise.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=listInterfaceAssets
 * Required Paramters
 * host_id          Site the interface is to be added at
 * Optional Parameters
 * link_id          The link the interface is to be added to
 ********************************************************************/
} else if ($_REQUEST["do"] == "listInterfaceAssets") {
    page_view_requires(AUTH_USER);
	if ($_REQUEST["interface_type"] == $INTERFACE_TYPE_VAP)
		$link_id = -1;
	else
		$link_id = $_REQUEST["link_id"];
	
    $assets = do_xmlrpc("getInterfaceSubassets", 
        array($_REQUEST["host_id"], $link_id, 
        $_REQUEST["interface_id"], $_REQUEST["interface_type"]),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($assets)) {
        // XXX: Should return a 40x error if something went wrong
        exit;
    }
    usort($assets, "assetdesc_cmp");
    $asset_ids = array("-1");
    $asset_descs = array("Select an interface asset...");
    foreach ($assets as $idx=>$asset) {
        $asset_ids[] = $asset["subasset_id"];
        $asset_descs[] = $asset["description"];
    }
    $smarty->assign("subasset_ids", $asset_ids);
    $smarty->assign("subassets", $asset_descs);
    $smarty->display("pass:{html_options values=\$subasset_ids " .
        "output=\$subassets selected=\$iface.subasset_id name=\"" .
        "subasset_id\" id=\"subasset_id\"}");
    exit;
    
/********************************************************************
 * Return the list of interfaces that a VAP or VLAN interface could
 * be built upon.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=listRawInterfaces
 * Required Paramters
 * host_id          Site the interface is to be added at
 * interface_type   The type of interface the user wants to create
 ********************************************************************/
} else if ($_REQUEST["do"] == "listRawInterfaces") {
    page_view_requires(AUTH_USER);
    $ifaces = do_xmlrpc("getRawInterfaces", 
        array($_REQUEST["host_id"], $_REQUEST["interface_type"]),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($ifaces)) {
        // XXX: Should return a 40x error if something went wrong
        exit;
    }
    $iface_ids = array("-1");
    $iface_descs = array("Select an interface...");
    foreach ($ifaces as $idx=>$iface) {
        $iface_ids[] = $iface["interface_id"];
        $iface_descs[] = $iface["description"];
    }
    $smarty->assign("iface_ids", $iface_ids);
    $smarty->assign("ifaces", $iface_descs);
    $smarty->display("pass:{html_options values=\$iface_ids " .
        "output=\$ifaces selected=\$iface.raw_interface name=\"" .
        "raw_interface\" id=\"raw_interface\"}");
    exit;
    
/********************************************************************
 * Return the suggested IP address for the interface.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=getSuggestedIP
 * Required Paramters
 * link_id          The link the interface is to be added to
 * host_id          The host the interface is being added on
 * master_if        Whether the interface is an AP master
 * callback         Name of javascript function that results should be
 *                  processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "getSuggestedIP") {
    page_view_requires(AUTH_USER);
    $ip = do_xmlrpc("getIfaceSuggestedIP", array($_REQUEST["link_id"],
        $_REQUEST["host_id"], $_REQUEST["master_if"]), $xmlrpc_conn, TRUE,
        FALSE);
    if (xmlrpc_has_error($ip)) {
        // XXX: Should return a 40x error if something went wrong
        exit;
    }
    $smarty->assign("ip", $ip);
    $smarty->display("pass:<input type=\"text\" name=\"ip_address\" " .
        "id=\"ip_address\" value=\"{$ip}\" />");
    exit;
    
/********************************************************************
 * Return possible channels for the specified mode.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=getChannelList
 * Required Paramters
 * mode             Operating mode of the link
 * callback         Name of javascript function that results should be
 *                  processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "getChannelList") {
    page_view_requires(AUTH_USER);
    /* Return result */
    assignChannelList($_REQUEST["mode"], TRUE);
    $smarty->display("pass:{html_options values=\$channels " .
        "output=\$channel_descs name=\"master_channel\" id=\"" .
        "master_channel\" selected=\"" . $_REQUEST["oldchannel"] . "\"}");
    exit;

}

/* If we get here the page has been called incorrectly, display the list */
ccs_notice("Invalid Action Requested: " . $_REQUEST["do"]);
if (!isset($_REQUEST["host_id"])) {
    display_host_list();
} else {
    header("Location: /mods/host/host.php?do=edit&host_id=" . 
        $_REQUEST["host_id"]);    
}
?>
