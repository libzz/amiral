<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Host Configuration
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
@include("host/zoominkey.php");
if (!isset($zoominkey)) {
    $zoominkey="";
}
@include("host/gmapskey.php");
if (!isset($gmapskey)) {
    $gmapskey="";
}


if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    display_host_list();
}

/********************************************************************
 * Add a Host
 * do=add
 * Optional Parameters
 ********************************************************************/
if ($_REQUEST["do"] == "add") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Look for posted data */
        $host = array();
        get_if_posted(&$host, "host_name");
        get_if_posted(&$host, "site_id");
        get_if_posted(&$host, "link_class_id");
        if ($host["site_id"]==-1) {
            unset($host["site_id"]);
        }
        get_if_posted(&$host, "asset_id");
        if ($host["asset_id"]==-1) {
            unset($host["asset_id"]);
        }
        get_if_posted(&$host, "distribution_id");
        get_if_posted(&$host, "kernel_id");
        if (isset($_POST["host_active"]) && $_POST["host_active"]=="yes") {
            $host["host_active"] = "t";
        } else {
            $host["host_active"] = "f";
        }
        if (isset($_POST["is_gateway"]) && $_POST["is_gateway"]=="yes") {
            $host["is_gateway"] = "t";
        } else {
            $host["is_gateway"] = "f";
        }
        $rv = do_xmlrpc("addHost", array($host), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not add Host: ".xmlrpc_error_string($rv));
            $action = $do;
            $smarty->assign("host", $host);
        } else {
            $action = "edit";
            header("Location: /mods/host/host.php?do=edit&amsg=true" .
                "&host_id=" . $rv);
        }
    }
    assignDistributions();
    assignKernels();
    assignLoopbacks();
    assignSiteListCombo(TRUE);
    $site_assets = array();
    $stock_assets = getStockAssets();
    $smarty->assign("site_assets", $site_assets);
    $smarty->assign("stock_assets", $stock_assets);
    /* Show the form */
    $smarty->assign("sheets", array("host.css"));
    $smarty->assign("scripts", array("host.js"));
    display_page("mods/host/hostaddform.tpl");
    
/********************************************************************
 * Edit a Host
 * do=edit
 * Optional Parameters
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Look for changed data */
        $host = array();
        get_if_posted(&$host, "host_id");
        get_if_posted(&$host, "host_name");
        get_if_post_modified(&$host, "site_id");
        get_if_post_modified(&$host, "asset_id");
        get_if_posted(&$host, "distribution_id");
        get_if_posted(&$host, "kernel_id");
        get_if_checked(&$host, "host_active");
        get_if_checked(&$host, "is_gateway");
        $rv = do_xmlrpc("updateHostDetails", array($_POST["host_id"], $host),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update Host: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Host details successfully updated.");
        }

    }
    if (!isset($_REQUEST["host_id"])) {
        ccs_notice("Host ID not set!");
        display_host_list();
    }
    displayHost($_REQUEST["host_id"]);

/********************************************************************
 * Delete a host 
 * do=delete
 * Required Paramters
 * host_id
 * confirm
 * If confirm is not set a page is displayed asking the user to confirm
 * they wish to delete this host.
 ********************************************************************/
} else if ($_REQUEST["do"] == "delete") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    if ($_REQUEST["confirm"] != "yes") {
        /* Get the site data */
        if (assignHost($_REQUEST["host_id"]) != array()) {
            /* Ask the user to confirm deletion */
            display_page("mods/host/hostdel.tpl");
        }
    } else {
        /* Delete host */
        $rv = do_xmlrpc("removeHost", array($_REQUEST["host_id"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not delete host: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Host successfully deleted!");
        }
        /* Display site list */
        display_host_list();
    }

/********************************************************************
 * Generate configuration files for a host
 * do=generateHostConfig
 * Required Paramters
 * host_id
 ********************************************************************/
} else if ($_REQUEST["do"] == "generateHostConfig") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    if (!isset($_REQUEST["host_name"])) {
        ccs_notice("Host name not set!");
        display_host_list();
    }
    $rv = do_xmlrpc("generateTemplate", 
        array(array($_REQUEST["host_name"]=>array())));
    header("Location: /configs/status/" . urlencode($rv));
    exit();
    
/********************************************************************
 * Generate new SSH keys for a host
 * do=generateSSHKeys
 * Required Paramters
 * host_id
 ********************************************************************/
} else if ($_REQUEST["do"] == "generateSSHKeys") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    if (!isset($_REQUEST["host_id"])) {
        ccs_notice("Host ID not set!");
        display_host_list();
    }
    $rv = do_xmlrpc("createSSHHostKeys", array($_REQUEST["host_id"]),
            $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        ccs_notice("Could not create SSH Host Keys: " .
            xmlrpc_error_string($rv));
    } else {
        ccs_notice("SSH Keys successfully generated!");
    }
    displayHost($_REQUEST["host_id"]);
    
/********************************************************************
 * Generate new CFengine keys for a host
 * do=generateCFengineKeys
 * Required Paramters
 * host_id
 ********************************************************************/
} else if ($_REQUEST["do"] == "generateCFengineKeys") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    if (!isset($_REQUEST["host_id"])) {
        ccs_notice("Host ID not set!");
        display_host_list();
    }
    $rv = do_xmlrpc("createCfengineHostKeys", array($_REQUEST["host_id"]),
            $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        ccs_notice("Could not create CFengine Host Keys: " .
            xmlrpc_error_string($rv));
    } else {
        ccs_notice("CFengine Keys successfully generated!");
    }
    displayHost($_REQUEST["host_id"]);

/********************************************************************
 * Display a network map (ZoomIn)
 * do=map
 ********************************************************************/
} else if ($_REQUEST["do"] == "map") {
    $r = do_xmlrpc("getSiteList", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        ccs_notice("Could not retrieve site list: " .
            xmlrpc_error_string($r));
        $r = array();
    }
    foreach ($r as $site) {
	$sites[$site["site_id"]] = $site;
    }
    $hosts = do_xmlrpc("getHostList", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($hosts)) {
        ccs_notice("Could not retrieve host list: " .
            xmlrpc_error_string($hosts));
        $hosts = array();
    }
    $links = do_xmlrpc("getLinkList", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($links)) {
        ccs_notice("Could not retrieve link list: " .
            xmlrpc_error_string($links));
        $links = array();
    }   
    foreach ($hosts as $idx=>$host) {
        $hosts[$idx]["gps_lat"] = 0;
        $hosts[$idx]["gps_long"] = 0;
        $site = $sites[$host["site_id"]];
        if ($site["gps_lat"] == 0 || $site["gps_long"] == 0) {
            continue;
        }
        // Convert WGS48 to NZGD49
        $lat = $site["gps_lat"];
        $long = $site["gps_long"];
        $res = shell_exec("$bindir/wgs48tonztm $lat $long");
        $bits = explode(" ", trim($res));
        if (strstr("failed", $res) != FALSE || count($bits) != 2) {
            ccs_notice("Could not convert to NZGD49 ($res): " . 
                $host["host_name"]);
            continue;
        }
        $hosts[$idx]["gps_lat"] = $bits[1];
        $hosts[$idx]["gps_long"] = $bits[0];
        $hosts[$idx]["ifaces"] = getHostInterfaces($hosts[$idx]["host_id"]);
    }
    $smarty->assign("hosts", $hosts);
    $smarty->assign("sheets", array("host.css"));
    $smarty->assign("scripts", 
        //array("/js/zoomin2.js",
        array("http://mapapi.zoomin.co.nz/?v=7&apikey=".$zoominkey,
        "map.js"));
    display_page("mods/host/map.tpl");
    
/********************************************************************
 * Display a network map (Google)
 * do=map
 ********************************************************************/
} else if ($_REQUEST["do"] == "gmap") {
    $r = do_xmlrpc("getSiteList", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        ccs_notice("Could not retrieve site list: " .
            xmlrpc_error_string($r));
        $r = array();
    }
    foreach ($r as $site) {
	$sites[$site["site_id"]] = $site;
    }
    $hosts = do_xmlrpc("getHostList", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($hosts)) {
        ccs_notice("Could not retrieve host list: " .
            xmlrpc_error_string($hosts));
        $hosts = array();
    }
    $links = do_xmlrpc("getLinkList", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($links)) {
        ccs_notice("Could not retrieve link list: " .
            xmlrpc_error_string($links));
        $links = array();
    }   
    foreach ($hosts as $idx=>$host) {
        $hosts[$idx]["gps_lat"] = 0;
        $hosts[$idx]["gps_long"] = 0;
        $site = $sites[$host["site_id"]];
        if ($site["gps_lat"] == 0 || $site["gps_long"] == 0) {
            continue;
        }
        $hosts[$idx]["gps_lat"] = $site["gps_long"]*-1;
        $hosts[$idx]["gps_long"] = $site["gps_lat"];
        $hosts[$idx]["ifaces"] = getHostInterfaces($hosts[$idx]["host_id"]);
    }
    $smarty->assign("hosts", $hosts);
    $smarty->assign("sheets", array("host.css"));
    $smarty->assign("scripts", 
        array("http://maps.google.com/maps?file=api&amp;v=2&amp;key=".$gmapskey,
        "gmap.js"));
    display_page("mods/host/map.tpl");

/********************************************************************
 * Return the list of assets that a new host at the specified site
 * could utilise.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=listSiteAssets
 * Required Paramters
 * site_id          Site the host is to be added at
 * callback         Name of javascript function that results should be
 *                  processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "listSiteAssets") {
    page_view_requires(AUTH_USER);
    /* Return XML result */
    if ($_REQUEST["site_id"] != -1) {
        $site_assets = getSiteAssets($_REQUEST["site_id"]);
    } else {
        $site_assets = array();
    }
    $stock_assets = getStockAssets();
    $smarty->assign("site_assets", $site_assets);
    $smarty->assign("stock_assets", $stock_assets);
    //$smarty->assign("host", getHost($_REQUEST["host_id"]));
    $smarty->display("mods/host/host-assetlist.tpl");
    exit;
    
/********************************************************************
 * Add a new service to a host
 * do=addServiceToHost
 ********************************************************************/
} else if ($_REQUEST["do"] == "addServiceToHost") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $rv = do_xmlrpc("addService", array($_REQUEST["service_id"], 
        $_REQUEST["host_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        # XXX: How should we handle this? Return a 405 error or something?
    }

    $smarty->assign("cservices", getHostServices($_REQUEST["host_id"]));
    $smarty->assign("services", 
        getHostUnconfiguredServices($_REQUEST["host_id"]));
    $smarty->assign("host_id", $_REQUEST["host_id"]);
    $smarty->display("mods/host/host-slist.tpl");
    exit;
    
/********************************************************************
 * Remove a new service to a host
 * do=removeServiceFromHost
 ********************************************************************/
} else if ($_REQUEST["do"] == "removeServiceFromHost") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $rv = do_xmlrpc("removeService", array($_REQUEST["service_id"], 
        $_REQUEST["host_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        # XXX: How should we handle this? Return a 405 error or something?
    }

    $smarty->assign("cservices", getHostServices($_REQUEST["host_id"]));
    $smarty->assign("services", 
        getHostUnconfiguredServices($_REQUEST["host_id"]));
    $smarty->assign("host_id", $_REQUEST["host_id"]);
    $smarty->display("mods/host/host-slist.tpl");
    exit;
 
}

/* If we get here the page has been called incorrectly, display the list */
ccs_notice("Invalid Action Requested: " . $_REQUEST["do"]);
display_host_list();

?>
