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
define("NO_ASSET_MENU", "1");
require_once("asset/asset_common.php");

$INTERFACE_TYPE_MIN=0;
$INTERFACE_TYPE_PHYSICAL=1;
$INTERFACE_TYPE_VAP=2;
$INTERFACE_TYPE_VLAN=3;
$INTERFACE_TYPE_ALIAS=4;
$INTERFACE_TYPE_MAX=5;

$interface_types = array($INTERFACE_TYPE_PHYSICAL=>"Physical Interface", 
                        $INTERFACE_TYPE_VAP=>"Atheros VAP",
                        $INTERFACE_TYPE_VLAN=>"VLAN Interface",
                        $INTERFACE_TYPE_ALIAS=>"Aliased IP");

/* Setup the bottom menu */
ccs_menu_bottom_add(array(mk_menu_item("Sites", "/mods/host/site.php"),
    mk_menu_item("Hosts", "/mods/host/host.php"), 
    mk_menu_item("Links", "/mods/host/link.php"), 
    mk_menu_item("Network Map", "/mods/host/host.php?do=map")
    ));

function display_site_list()
{

    global $xmlrpc_conn, $smarty;

    $sites = do_xmlrpc("getSiteList", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($sites)) {
        ccs_notice("Could not retrieve site list: " .
            xmlrpc_error_string($sites));
        $sites = array();
    }
    usort($sites, "site_cmp");
    $smarty->assign("sites", $sites);

    display_page("mods/host/sitelist.tpl");
}

function display_host_list()
{

    global $xmlrpc_conn, $smarty;

    $hosts = do_xmlrpc("getHostList", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($hosts)) {
        ccs_notice("Could not retrieve host list: " .
            xmlrpc_error_string($hosts));
        $hosts = array();
    }
    usort($hosts, "host_cmp");
    $smarty->assign("hosts", $hosts);

    display_page("mods/host/hostlist.tpl");
}

function display_link_list()
{

    global $xmlrpc_conn, $smarty;

    $links = do_xmlrpc("getLinkList", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($links)) {
        ccs_notice("Could not retrieve link list: " .
            xmlrpc_error_string($hosts));
        $links = array();
    }
    $smarty->assign("links", $links);

    display_page("mods/host/linklist.tpl");
}

function displayHost($host_id)
{
    global $smarty;

    assignHost($host_id);
    assignSiteListCombo(TRUE);
    if (isset($_REQUEST["amsg"])) {
        ccs_notice("Host added successfully.");
    }
    /* Show the form */
    $smarty->assign("sheets", array("host.css"));
    $smarty->assign("scripts", array("host.js"));
    display_page("mods/host/hosteditform.tpl");
}
function displayLink($link_id)
{
    global $smarty;

    assignLink($link_id);
    /* Show the form */
    $smarty->assign("sheets", array("link.css"));
    $smarty->assign("scripts", array("link.js"));
    display_page("mods/host/linkeditform.tpl");
}

/* Assigns lists of contacts to the form */
function assignContacts()
{

    global $xmlrpc_conn, $smarty;

    /* Retrieve list of contacts */
    $contacts = do_xmlrpc("getSiteContacts", array(), $xmlrpc_conn);
    usort($contacts, "contact_cmp");
    
    $ids = array();
    $names = array();
    $c = 0;
    foreach ($contacts as $idx=>$contact) {
        $ids[$c] = $contact["contact_id"];
        $names[$c] = $contact["givenname"] . " " . $contact["surname"];
        $c++;
    }
    $smarty->assign("contact_ids", $ids);
    $smarty->assign("contacts", $names);

    return $contacts;

}

function getHost($host_id, $get_interfaces=TRUE, $get_services=TRUE) 
{
    global $smarty, $xmlrpc_conn;
    
    $host = do_xmlrpc("getHost", array($host_id), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($host)) {
        ccs_notice("Could not retrieve host: ".xmlrpc_error_string($host));
        $host = array();
    } else {
        if ($get_interfaces)
            $host["interfaces"] = getHostInterfaces($host_id, 
                $host["asset_id"]);
        if ($get_services)
            $host["services"] = getHostServices($host_id);
    }
    return $host;
}

function assignHost($host_id) 
{
    global $smarty;
    
    $host = getHost($host_id);
    $smarty->assign("host", $host);
    if ($host["site_id"] != -1) {
        $site_assets = getSiteAssets($host["site_id"]);
    } else {
        $site_assets = array();
    }
    $stock_assets = getStockAssets();
    $smarty->assign("site_assets", $site_assets);
    $smarty->assign("stock_assets", $stock_assets);
    
    $services = getHostUnconfiguredServices($host_id);
    $smarty->assign("services", $services);

    $status = getHostStatus($host_id);
    $smarty->assign("status", $status);

    assignDistributions();
    assignKernels();
    
    return $host;

}
function getHostInterfaces($host_id, $asset_id=-1)
{
    global $xmlrpc_conn, $INTERFACE_TYPE_ALIAS, $INTERFACE_TYPE_VLAN;
    
    $ifaces = do_xmlrpc("getHostInterfaces", array($host_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($ifaces)) {
        $ifaces = array();
        ccs_notice("Could not retrieve host interfaces: " .
            xmlrpc_error_string($ifaces));
    }
    $names = array();
    foreach($ifaces as $idx=>$iface) {
        if ($iface["subasset_id"] != "") {
            if ($iface["asset_id"] == $asset_id) {
                $ifaces[$idx]["subasset_desc"] = "Host's " . $iface["sa_name"];
            } else {
                $ifaces[$idx]["subasset_desc"] = 
                    sprintf("[%3s] %s", $iface["asset_id"], $iface["sa_desc"]);
            }
        } else {
            $ifaces[$idx]["subasset_desc"] = "No Subasset Assigned";
        }
        if ($iface["interface_id"] != "") {
            if ($iface["interface_active"]=="t") {
                $ifaces[$idx]["statuscode"] = "OK";
                $ifaces[$idx]["status"] = "Enabled";
            } else {
                $ifaces[$idx]["statuscode"] = "WARNING";
                $ifaces[$idx]["status"] = "Disabled";
            }
        } else {
            $ifaces[$idx]["statuscode"] = "UNCONFIGURED";
            $ifaces[$idx]["status"] = "Unconfigured";
            $ifaces[$idx]["name"] = $ifaces[$idx]["sa_name"];
        }
        if ($iface["alias_netmask"] != "") {
            $ifaces[$idx]["alias_netmask"] = "/" . $iface["alias_netmask"];
        }
        $iface["ifname"] = $iface["name"];
        # Store names to generate bridge descriptions
        if ($iface["interface_id"]!="")
            $names[$iface["interface_id"]] = $iface["name"];
    }
    # Generate bridge/alias descriptions
    foreach ($ifaces as $idx=>$iface) {
        if ($iface["bridge_interface"]!="") {
            $ifaces[$idx]["bridge_desc"] = "Bridged onto " .
                $names[$iface["bridge_interface"]];
        } else {
            $ifaces[$idx]["bridge_desc"] = "";
        }
        if ($iface["interface_type"] == $INTERFACE_TYPE_VLAN) {
            $ifaces[$idx]["subasset_desc"] = "VLAN on " .
                $names[$iface["raw_interface"]];
        }
        if ($iface["interface_type"] == $INTERFACE_TYPE_ALIAS) {
            $ifaces[$idx]["subasset_desc"] = "Aliased IP on " .
                $names[$iface["raw_interface"]];
        }
    }
    usort($ifaces, "iface_cmp");
    
    return $ifaces;  
}
# Short helper array for sorting interfaces based on status, names must match
# values given in the function above
$slevels = array("Enabled"=>0,"Disabled"=>1,"Unconfigured"=>2);
function iface_cmp($a, $b)
{
    global $slevels;

    if ($a["status"] != $b["status"]) {
        $acode = $slevels[$a["status"]];
        $bcode = $slevels[$b["status"]];
        return $acode - $bcode;
    }

    /* Status is identical sort alphabetically on name */
    return strcmp($a["name"], $b["name"]);
    
}
function getHostServices($host_id)
{
    global $xmlrpc_conn;

    $services = do_xmlrpc("getHostServices", array($host_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($services)) {
        ccs_notice("Could not retrieve host services: " .
            xmlrpc_error_string($services));
        $services = array();
    }
    foreach($services as $idx=>$service) {
        $services[$idx]["statuscode"] = "OK";
        $services[$idx]["status"] = "Enabled";
        if ($service["enabled"] == $service["service_enabled"] || 
                $service["enabled"]=="") {
            if ($service["service_enabled"]=="f") {
                $services[$idx]["statuscode"] = "WARNING";
                $services[$idx]["status"] = "Disabled";
            }
        } else {
            if ($service["enabled"]=="t") {
                $services[$idx]["statuscode"] = "OK";
                $services[$idx]["status"] = "Enabled (This host only)";
            } else if ($service["enabled"]=="f") {
                $services[$idx]["statuscode"] = "WARNING";
                $services[$idx]["status"] = "Disabled (This host only)";
            }
        }
    }
    return $services;  
}
function getSiteAssets($site_id)
{
    global $xmlrpc_conn;

    $assets = do_xmlrpc("getAvailHostAssets", array($site_id), $xmlrpc_conn, 
        TRUE, FALSE);
    if (xmlrpc_has_error($assets)) {
        # XXX: How to handle?
        return array();
    }
    usort($assets, "assetid_cmp");
    return $assets;
}
function getStockAssets()
{
    return getSiteAssets(-1);
}

function getHostStatus($host_id)
{
    global $xmlrpc_conn;
    
    $status = do_xmlrpc("getHostStatus", array($host_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($status)) {
        $err = xmlrpc_error_string($status);
        if (strstr($err, "No status information")===FALSE) {
            ccs_notice("Could not retrieve host status: $err");
        }
        $status = array();
    }
    return $status;  
}

function getHostUnconfiguredServices($host_id)
{
    global $xmlrpc_conn;

    $services = do_xmlrpc("getHostUnconfiguredServices", array($host_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($services)) {
        ccs_notice("Could not retrieve host services: " .
            xmlrpc_error_string($services));
        $services = array();
    }
    foreach($services as $idx=>$service) {
        if ($service["enabled"]=="t") {
            $services[$idx]["statuscode"] = "OK";
            $services[$idx]["status"] = "Not configured for this host";
        } else if ($service["enabled"]=="f") {
            $services[$idx]["statuscode"] = "WARNING";
            $services[$idx]["status"] = "Disabled (Globally)";
        }
    }
    
    return $services;  
}

function assignLoopbacks()
{
    global $xmlrpc_conn, $smarty;
    
    $loopbacks = do_xmlrpc("getLoopbackRanges", array(), $xmlrpc_conn,
        TRUE, FALSE);
    if (xmlrpc_has_error($loopbacks)) {
        $loopbacks = array();
        ccs_notice("Could not retrieve distribution list: " .
            xmlrpc_error_string($loopbacks));
    }
    $ids = array();
    $names = array();
    $c = 0;
    foreach ($loopbacks as $idx=>$loopback) {
        $ids[$c] = $loopback["link_class_id"];
        $names[$c] = $loopback["description"];
        $c++;
    }
    $smarty->assign("loopback_ids", $ids);
    $smarty->assign("loopbacks", $names);

    return $distributions;
}
function assignDistributions() 
{
    
    global $xmlrpc_conn, $smarty;
    
    $distributions = do_xmlrpc("getDistributions", array(), $xmlrpc_conn,
        TRUE, FALSE);
    if (xmlrpc_has_error($distributions)) {
        $distributions = array();
        ccs_notice("Could not retrieve distribution list: " .
            xmlrpc_error_string($distributions));
    }
    $ids = array();
    $names = array();
    $c = 0;
    foreach ($distributions as $idx=>$distrib) {
        $ids[$c] = $distrib["distribution_id"];
        $names[$c] = $distrib["description"];
        $c++;
    }
    $smarty->assign("distribution_ids", $ids);
    $smarty->assign("distributions", $names);

    return $distributions;
}

function assignKernels() 
{
    
    global $xmlrpc_conn, $smarty;
    
    $kernels = do_xmlrpc("getKernels", array(), $xmlrpc_conn,
        TRUE, FALSE);
    if (xmlrpc_has_error($kernels)) {
        $kernels = array();
        ccs_notice("Could not retrieve kernel list: " . 
            xmlrpc_error_string($kernels));
    }
    $ids = array();
    $names = array();
    $c = 0;
    foreach ($kernels as $idx=>$kernel) {
        $ids[$c] = $kernel["kernel_id"];
        $names[$c] = $kernel["upstream_release"] . $kernel["local_version"];
        $c++;
    }
    $smarty->assign("kernel_ids", $ids);
    $smarty->assign("kernels", $names);

    return $kernels;

}

function assignLinks($header=FALSE, $subasset_id=-1) 
{
    
    global $xmlrpc_conn, $smarty;
    
    $links = do_xmlrpc("getLinkList", array($subasset_id), $xmlrpc_conn,
        TRUE, FALSE);
    if (xmlrpc_has_error($links)) {
        $links = array();
        ccs_notice("Could not retrieve link list: " .
            xmlrpc_error_string($links));
    }
    $ids = array();
    $names = array();
    $c = 0;
    if ($header == TRUE) {
        $ids[$i] = -1;
        $names[$c] = "Select a link...";
        $c++;
    }
    foreach ($links as $idx=>$link) {
        $ids[$c] = $link["link_id"];
        $names[$c] = $link["description"];
        $c++;
    }
    $smarty->assign("link_ids", $ids);
    $smarty->assign("links", $names);

    return $links;

}

/* Retrieve the list of assets that could be used as an interface at the
 * specified site and possibly on the specified link 
 */
function assignIfaceSubassetList($host_id, $link_id=-1, $interface_id=-1,
        $header=FALSE)
{
    global $xmlrpc_conn, $smarty;
    
    $subassets = do_xmlrpc("getInterfaceSubassets", 
        array($host_id, $link_id, $interface_id), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($subassets)) {
        $subassets = array();
        ccs_notice("Could not retrieve asset list for interface: " .
            xmlrpc_error_string($subassets));
    }
    usort($subassets, "assetdesc_cmp");
    $ids = array();
    $names = array();
    $c = 0;
    if ($header == TRUE) {
        $ids[$i] = -1;
        $names[$c] = "Select an interface asset...";
        $c++;
    }
    foreach ($subassets as $idx=>$subasset) {
        $ids[$c] = $subasset["subasset_id"];
        $names[$c] = $subasset["description"];
        $c++;
    }
    $smarty->assign("subasset_ids", $ids);
    $smarty->assign("subasset_desc", $names);

    return $subassets;

}

/* Retrieve the list of possible drivers and assign to the form */
function assignModules($header=FALSE)
{
    global $xmlrpc_conn, $smarty;
    
    $modules = do_xmlrpc("getModules", array(), $xmlrpc_conn,
        TRUE, FALSE);
    if (xmlrpc_has_error($modules)) {
        ccs_notice("Could not retrieve module list: " .
            xmlrpc_error_string($modules));
        $modules = array();
    }
    $ids = array();
    $names = array();
    $c = 0;
    if ($header == TRUE) {
        $ids[$c] = -1;
        $names[$c] = "Select a module...";
        $c++;
    }
    foreach ($modules as $idx=>$module) {
        $ids[$c] = $module["module_id"];
        $names[$c] = $module["module_name"];
        $c++;
    }
    $smarty->assign("module_ids", $ids);
    $smarty->assign("modules", $names);

    return $modules;

}

/* Retrive a site record from the _POST array */
function get_posted_site()
{

    $site = array();

    get_if_posted(&$site, "site_id");
    get_if_posted(&$site, "location");
    get_if_posted(&$site, "tech_contact_id");
    get_if_posted(&$site, "admin_contact_id");
    get_if_posted(&$site, "gps_lat");
    get_if_posted(&$site, "gps_long");
    get_if_posted(&$site, "elevation");
    get_if_posted(&$site, "comments");
    
    return $site;

}
function assign_site($site_id) 
{

    global $smarty, $xmlrpc_conn;
    
    $site = do_xmlrpc("getSite", array($site_id), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($site)) {
        ccs_notice("Could not retrieve site: " . xmlrpc_error_string($site));
        $site = array();
    }
    $smarty->assign("site", $site);
    return $site;
}
function assignLink($link_id) 
{

    global $smarty, $xmlrpc_conn;
    
    $link = do_xmlrpc("getLink", array($link_id), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($link)) {
        ccs_notice("Could not retrieve link: ".xmlrpc_error_string($link));
        $link = array();
    }
    assignLinkTypes();
    assignLinkModes($link["type"]);
    assignChannelList($link["mode"]);
    assignLinkClasses();
    $smarty->assign("link", $link);
    return $link;
}

function assignLinkTypes() 
{

    global $smarty, $xmlrpc_conn;
    
    $types = do_xmlrpc("getLinkTypes", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($types)) {
        ccs_notice("Could not retrieve link types: " .
            xmlrpc_error_string($types));
        $types = array();
    }
    usort($types, "type_cmp");
    $ids = array();
    $names = array();
    $c = 0;
    foreach ($types as $idx=>$type) {
        $ids[$c] = $type["type_name"];
        $names[$c] = $type["description"];
        $c++;
    }
    $smarty->assign("link_types", $ids);
    $smarty->assign("link_type_descs", $names);
    return $types;
}
function assignLinkModes($type_name, $header=FALSE) 
{

    global $smarty, $xmlrpc_conn;
    
    $modes = do_xmlrpc("getLinkModes", array($type_name), $xmlrpc_conn, 
        TRUE, FALSE);
    if (xmlrpc_has_error($modes)) {
        ccs_notice("Could not retrieve link modes: " .
            xmlrpc_error_string($modes));
        $modes = array();
    }
    usort($modes, "mode_cmp");
    $ids = array();
    $names = array();
    $c = 0;
    if ($header) {
        $ids[$c] = "";
        $names[$c++] = "Use link mode";
    }
    foreach ($modes as $idx=>$mode) {
        $ids[$c] = $mode["mode"];
        $names[$c] = $mode["description"];
        $c++;
    }
    $smarty->assign("link_modes", $ids);
    $smarty->assign("link_mode_descs", $names);
    return $modes;
}
function assignChannelList($mode, $header=FALSE) 
{

    global $smarty, $xmlrpc_conn;
    
    $chans = do_xmlrpc("getChannelList", array($mode), $xmlrpc_conn, 
        TRUE, FALSE);
    if (xmlrpc_has_error($chans)) {
        ccs_notice("Could not retrieve mode channel list: " .
            xmlrpc_error_string($chans));
        $chans = array();
    }
    usort($chans, "channel_cmp");
    $ids = array();
    $names = array();
    $c = 0;
    if ($header) {
        $ids[$c] = -1;
        $names[$c++] = "Use link channel";
    }
    foreach ($chans as $idx=>$channel) {
        $ids[$c] = $channel["channel"];
        $names[$c] = str_replace(" ", "&nbsp;", $channel["description"]);
        $c++;
    }
    $smarty->assign("channels", $ids);
    $smarty->assign("channel_descs", $names);
    return $chans;
}
function assignLinkClasses($header=FALSE) 
{

    global $smarty, $xmlrpc_conn;
    
    $classes = do_xmlrpc("getLinkClasses", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($classes)) {
        ccs_notice("Could not retrieve link classes: " .
            xmlrpc_error_string($classes));
        $classes = array();
    }
    $ids = array();
    $names = array();
    $c = 0;
    if ($header == TRUE) {
        $ids[$i] = -1;
        $names[$c] = "Select a link class...";
        $c++;
    }   
    foreach ($classes as $idx=>$class) {
        $ids[$c] = $class["link_class_id"];
        $names[$c] = $class["description"];
        $c++;
    }
    $smarty->assign("link_class_ids", $ids);
    $smarty->assign("link_class_descs", $names);
    return $classes;
}

function assignInterfaceTypes()
{
    global $smarty, $interface_types;

    $ids = array();
    $names = array();
    foreach ($interface_types as $id=>$name) {
        $ids[] = $id;
        $names[] = $name;
    }
    $smarty->assign("interface_type_ids", $ids);
    $smarty->assign("interface_types", $names); 
    
}
function assignBridgeableInterfaces($iface_list)
{
    global $smarty;

    $ids = array(-1);
    $names = array("Do not bridge interface");
    foreach ($iface_list as $idx=>$iface) {
        # Skip unconfigured interfaces
        if ($iface["interface_id"]=="")
            continue;
        # Skip interfaces that are already bridging
        if ($iface["bridge_interface"]!="")
            continue;
        # Add others to the list of available interfaces
        $ids[] = $iface["interface_id"];
        $names[] = $iface["name"];
    }
    $smarty->assign("bridge_interfaces", $ids);
    $smarty->assign("bridge_interface_descs", $names);
    
    return $arr;
}
function getSubassetFunctions($subasset_id)
{
    global $xmlrpc_conn;
    
    $funcs = do_xmlrpc("getSubassetFunctions", array($subasset_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($funcs)) {
        ccs_notice("Could not retrieve subasset functions: " . 
            xmlrpc_error_string($funcs));
        $funcs  = array();
    }
    return $funcs;
}

/* Comparison functions to set up the correct display ordering for various
 * items. 
 */
function type_cmp($a, $b) {
    return gen_cmp($a["type_name"], $b["type_name"]);
}
function mode_cmp($a, $b) {
    /* Order by frequency of use
     * 802.11b > 802.11g > 802.11a 
     * 100Mbps > 10Mbps
     */    
    if ($a["mode"] == $b["mode"]) return 0;
    if ($a["mode"] == "b") return -1;
    if ($b["mode"] == "b") return 1;
    if ($a["mode"] == "g") return -1;
    if ($b["mode"] == "g") return 1;
    if ($a["mode"] == "a") return -1;
    if ($b["mode"] == "a") return 1;
    return -(gen_cmp($a["mode"], $b["mode"]));
}
function channel_cmp($a, $b) {
    return gen_cmp($a["channel"], $b["channel"]);
}
function contact_cmp($a, $b) {
    return gen_cmp($a["username"], $b["username"]);
}
function host_cmp($a, $b) {
    return gen_cmp($a["host_name"], $b["host_name"]);
}
function site_cmp($a, $b) {
    return gen_cmp($a["location"], $b["location"]);
}
function assetdesc_cmp($a, $b) {
    return gen_cmp($a["description"], $b["description"]);
}
function assetid_cmp($a, $b) {
    return gen_cmp($a["asset_id"], $b["asset_id"]);
}
function gen_cmp($a, $b) {
    if ($a==$b) return 0;
    return ($a > $b) ? 1 : -1;
}
