<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Asset Management - Common Functions 
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

/* Setup the bottom menu */
if (NO_ASSET_MENU != 1) {
    ccs_menu_bottom_add(array(mk_menu_item("Assets", "/mods/asset/asset.php"),
        mk_menu_item("Asset Types", "/mods/asset/types.php"),
        mk_menu_item("Subasset Types", "/mods/asset/types.php?type=subasset"),
        mk_menu_item("Asset Properties", "/mods/asset/properties.php")));
    ccs_menu_bottom_include(array("mods/asset/assetmenuform.tpl"));
}

$cur_codes = array("ADF","ADP","AED","AFA","ALL","ANG","AON","ARS","ATS",
    "AUD","AWG","BBD", "BDT","BEF","BGL","BHD","BIF","BMD","BND","BOB",
    "BRL","BSD","BTN","BWP","BZD","CAD","CHF","CLP","CNY","COP","CRC",
    "CUP","CVE","CYP","CZK","DEM","DJF","DKK","DOP","DZD","ECS","EEK",
    "EGP","ESP","ETB","EUR","FIM","FJD","FKP","FRF","GBP","GHC","GIP",
    "GMD","GNF","GRD","GTQ","GYD","HKD","HNL","HRK","HTG","HUF","IDR",
    "IEP","ILS","INR","IQD","IRR","ISK","ITL","JMD","JOD","JPY","KES",
    "KHR","KMF","KPW","KRW","KWD","KYD","KZT","LAK","LBP","LKR","LRD",
    "LSL","LTL","LUF","LVL","LYD","MAD","MGF","MMK","MNT","MOP","MRO",
    "MTL","MUR","MVR","MWK","MXP","MYR","MZM","NAD","NGN","NIO","NLG",
    "NOK","NPR","NZD","OMR","PAB","PEN","PGK","PHP","PKR","PLZ","PTE",
    "PYG","QAR","ROL","RUB","SAR","SBD","SCR","SDD","SDP","SEK","SGD",
    "SHP","SIT","SKK","SLL","SOS","SRG","STD","SVC","SYP","SZL","THB",
    "TND","TOP","TRL","TTD","TWD","TZS","UAH","UGS","USD","UYP","VEB",
    "VND","VUV","WST","XAF","XAG","XAU","XCD","XEU","XOF","XPD","XPF",
    "XPT","YUN","ZAR","ZMK","ZWD");

$asset_details = array("description", "serial_no", "date_purchased",
    "currency", "price", "supplier", "notes", "enabled");

function display_asset_list()
{
    global $xmlrpc_conn, $smarty;

    page_view_requires(AUTH_ASSET_MANAGER);
    
    if (isset($_REQUEST["asset_type_id"]) && $_REQUEST["asset_type_id"]!=-1) {
        $p = array($_REQUEST["asset_type_id"]);
        $smarty->assign("asset_type_id", $_REQUEST["asset_type_id"]);
    } else if (isset($_REQUEST["site_id"]) && $_REQUEST["site_id"]!=-1) {
        $p = array(-1, $_REQUEST["site_id"]);
        $smarty->assign("site_id", $_REQUEST["site_id"]);
        $smarty->assign("asset_type_id", -1);
    } else {
        $p = array();
        $smarty->assign("asset_type_id", -1);
    }
    /* Retrieve list of assets */
    $assets = do_xmlrpc("getAssetList", $p, $xmlrpc_conn);

    /* Categorise and sort the list */
    $categories = array();
    foreach ($assets as $idx=>$val) {
        $atid = $val["asset_type_id"];
        if (!array_key_exists($atid, $categories)) {
            $categories[$atid] = array();
        }
        if ($val["location"] == "Assigned Assets") {
            $l = assignAssetLocation($val["asset_id"]);
            $val["location"] = $l["description"];
        }
        $categories[$atid][$val["asset_id"]] = $val;        
    }
    array_map(ksort, $categories);
    ksort($categories);
    
    $smarty->assign("assets", $categories);
    assignAssetTypesCombo();
    display_page("mods/asset/assetlist.tpl");

}
function assignAssetListCombo($header)
{
    global $xmlrpc_conn, $smarty;
    
    /* Retrieve list of assets */
    $assets = do_xmlrpc("getAssetList", array(), $xmlrpc_conn);

    $asset_ids = array();
    $asset_descs = array();
    $i=0;
    if ($header == TRUE) {
        $asset_ids[$i] = -1;
        $asset_descs[$i] = "Select an asset...";
        $i++;
    }
    foreach ($assets as $key=>$asset) {
        $asset_ids[$i] = $asset["asset_id"];
        $asset_descs[$i] = sprintf("[% 3s] %s" , $asset["asset_id"], 
            $asset["description"]);
        $i++;
    }

    $smarty->assign("asset_ids", $asset_ids);
    $smarty->assign("asset_descs", $asset_descs);

}

function getAssetType($asset_type_id)
{
    
    global $xmlrpc_conn;

    $desc = do_xmlrpc("getAssetType", array($asset_type_id), $xmlrpc_conn,
        TRUE, FALSE);
    if (xmlrpc_has_error($desc)) {
        ccs_notice("Could not retrieve asset type: " . 
            xmlrpc_error_string($desc));
        $desc = "";
    }
    return $desc;
}
function assignAssetTypeAllowMod($asset_type_id)
{
    
    global $xmlrpc_conn, $smarty;

    $no = do_xmlrpc("getNoAssetsOfType", array($asset_type_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($no)) {
        ccs_notice("Could not retrieve asset type count: " .
            xmlrpc_error_string($no));
        $no = 1;
    }

    if ($no == 0) {
        $smarty->assign("allowmod", 1);
        return 1;
    }

    $smarty->assign("allowmod", 0);
    return 0;

}

function getSubassetType($subasset_type_id)
{
    
    global $xmlrpc_conn;

    $desc = do_xmlrpc("getSubassetType", array($subasset_type_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($desc)) {
        ccs_notice("Could not retrieve subasset type: " .
            xmlrpc_error_string($desc));
        $desc="";
    }

    return $desc;

}
/* Retrieve the list of subasset types */
function assignSubassetTypes() 
{
    
    global $smarty, $xmlrpc_conn;
    
    /* Retrieve list of subassets */
    $types = do_xmlrpc("getSubassetTypes", array(), $xmlrpc_conn);
    $smarty->assign("subasset_types", $types);
    return $types;
}
/* Retrieve the list of asset types */
function assignAssetTypes() 
{
    
    global $smarty, $xmlrpc_conn;
    
    $types = do_xmlrpc("getTypes", array(), $xmlrpc_conn);
    $smarty->assign("asset_types", $types);
    return $types;
}
function assignWirelessCardAssetTypes() 
{
    
    global $smarty, $xmlrpc_conn;
    
    $types = do_xmlrpc("getTypes", array(), $xmlrpc_conn);
    $t2 = array();
    foreach($types as $idx=>$data) {
        if (strstr(strtolower($data["description"]), "card")) {
            $t2[] = $data;
        }
    }
    $smarty->assign("asset_types", $t2);
    
    return $t2;
    
}
function assignSoekrisAssetTypes() 
{
    
    global $smarty, $xmlrpc_conn;
    
    $types = do_xmlrpc("getTypes", array(), $xmlrpc_conn);
    $t2 = array();
    foreach($types as $idx=>$data) {
        if (strstr(strtolower($data["description"]), "soekris")) {
            $t2[] = $data;
        }
    }
    $smarty->assign("asset_types", $t2);
    
    return $t2;
    
}
function assignAssetTypesCombo($header=TRUE) 
{
    
    global $smarty, $xmlrpc_conn;
    
    $types = assignAssetTypes();
    
    $ids = array();
    $descs = array();
    if ($header == TRUE) {
        $ids[0] = -1;
        $descs[0] = "Select an asset type...";
    }
    foreach ($types as $key=>$type) {
        $typeid = $type["asset_type_id"];
        $ids[$typeid] = $type["asset_type_id"];
        $descs[$typeid] = $type["description"];
    }

    $smarty->assign("asset_type_ids", $ids);
    $smarty->assign("asset_type_descs", $descs);

    return $types;
}

/* Retrieve the list of subassets linked to the specified type*/
function assignLinkedSubassets($asset_type_id) 
{
    
    global $smarty, $xmlrpc_conn;
    
    /* Retrieve list of subassets */
    $types = do_xmlrpc("getLinkedSubassets", 
        array($asset_type_id), $xmlrpc_conn);
    $smarty->assign("linked_subassets", $types);

    return $types;
}
/* Checks whether the subasset type can be modified */
function assignSubassetTypeAllowMod($subasset_type_id)
{
    
    global $xmlrpc_conn, $smarty;

    $no = do_xmlrpc("getNoSubassetsOfType", array($subasset_type_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($no)) {
        ccs_notice("Could not retrieve subasset instance count: " .
            xmlrpc_error_string($no));
        $no = 1;
    }
    
    if ($no == 0) {
        $smarty->assign("allowmod", 1);
        return 1;
    }

    $smarty->assign("allowmod", 0);
    return 0;

}
/* Retrieve an asset property */
function getAssetProperty($asset_property_id)
{
    
    global $xmlrpc_conn;

    $desc = do_xmlrpc("getAssetProperty", array($asset_property_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($desc)) {
        ccs_notice("Could not retrieve asset property: " .
            xmlrpc_error_string($desc));
        $desc="";
    }
    return $desc;
}
/* Retrieve the list of properties linked to the specified subasset type*/
function assignLinkedProperties($subasset_type_id) 
{
    
    global $smarty, $xmlrpc_conn;
    
    /* Retrieve list of linked properties */
    $props = do_xmlrpc("getLinkedProperties", array($subasset_type_id), 
        $xmlrpc_conn);
    $smarty->assign("linked_properties", $props);

    return $props;
}
/* Retrieve the list of properties */
function assignProperties() 
{
    
    global $smarty, $xmlrpc_conn;
    
    /* Retrieve list of subassets */
    $props = do_xmlrpc("getProperties", array(), $xmlrpc_conn);
    $smarty->assign("properties", $props);

    return $props;
}
/* Retrieve a list of assets attached to the specified asset */
function getAttachedAssets($asset_id)
{
    global $xmlrpc_conn;

    /* Retrieve the asset - will get subassets and properties too */
    return do_xmlrpc("getAttachedAssets", array($asset_id), $xmlrpc_conn);
}
/* Get an asset's details */
function getAsset($asset_id)
{
    
    global $xmlrpc_conn;
    
    $asset = do_xmlrpc("getAsset", array($asset_id), $xmlrpc_conn, TRUE, 
        FALSE);
    if (xmlrpc_has_error($asset)) {
        /* Could not find asset */
        ccs_notice("Asset ID #$asset_id does not refer to a valid asset " .
            "in the database");
        return false;
    }  
    return $asset;
}
/* Assign an asset to the form */
function assignAsset($asset_id)
{
    
    global $smarty, $xmlrpc_conn;

    /* Retrieve the asset - will get subassets and properties too */
    $asset = getAsset($asset_id);
    if (!$asset) {
        return false;
    }
    if ($asset["attached_to"] != "") {
        $asset["parent_asset"] = getAsset($asset["attached_to"]);
    } else {
        $asset["attached_assets"] = getAttachedAssets($asset_id);
    }
    $smarty->assign("asset", $asset);
    
    return $asset;
    
}
/* Assign an asset to the form */
function assignAssetByMac($mac)
{
    
    global $smarty, $xmlrpc_conn;

    /* Retrieve the asset - will get subassets and properties too */
    $asset = do_xmlrpc("getAssetByMac", array($mac), $xmlrpc_conn, TRUE, 
        FALSE);
    if (xmlrpc_has_error($asset)) {
        /* Could not find asset */
        ccs_notice("No asset with the MAC address '$mac' exists in the " .
            "database");
        return false;
    }   
    if ($asset["attached_to"] != "") {
        $asset["parent_asset"] = getAsset($asset["attached_to"]);
    } else {
        $asset["attached_assets"] = getAttachedAssets($asset["asset_id"]);
    }
    $smarty->assign("asset", $asset);

    return $asset;
    
}
/* Assign an assets history to the form */
function assignAssetHistory($asset_id)
{
    global $smarty, $xmlrpc_conn;

    /* Retrieve the asset history */
    $history = do_xmlrpc("getAssetHistory", array($asset_id), $xmlrpc_conn);
    $smarty->assign("history", $history);

    return $history;
}

/* Updates one of the assets details */
function updateAssetDetail($asset_id, $detail_name, $value)
{
    global $smarty, $xmlrpc_conn;

    $p = array($asset_id, $detail_name, $value);
    $r = do_xmlrpc("updateAssetDetail", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        $err = "Error updating asset detail ($detail_name): " . 
            xmlrpc_error_string($r) . ". Other details unaffected";
        ccs_notice($err);
        return $err;
    }

    return "";

}
/* Updates one of the assets properties */
function updateSubassetPropertyData($subasset_id, $subasset_property_id, 
    $value)
{
    
    global $smarty, $xmlrpc_conn;

    $p = array($subasset_id, $subasset_property_id, $value);
    $r = do_xmlrpc("updateSubassetPropertyData", $p, $xmlrpc_conn, 
        TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        $err = "Error updating subasset property ($subasset_property_id): " . 
            xmlrpc_error_string($r) . ". Other properties unaffected";
        ccs_notice($err);
        return $err;
    }

    return "";


}
/* Updates one of the subasset enabled states */
function updateSubassetEnabled($asset_id, $subasset_id, $value)
{
    
    global $smarty, $xmlrpc_conn;

    $p = array($asset_id, $subasset_id, $value);
    $r = do_xmlrpc("updateSubassetEnabled", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        $err = "Error updating subasset enabled ($subasset_id): " . 
            xmlrpc_error_string($r) . ". Other properties unaffected";
        ccs_notice($err);
        return $err;
    }

    return "";
}
/* Adds a new subasset to an asset */
function addSubasset($asset_id, $asset_type_subasset_id, $subasset)
{
    
    global $smarty, $xmlrpc_conn;

    $p = array($asset_id, $asset_type_subasset_id, $subasset);
    $r = do_xmlrpc("addSubasset", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        $err = "Error adding subasset ($asset_type_subasset_id): " . 
            xmlrpc_error_string($r);
        ccs_notice($err);
        return $err;
    }

    return "";

}
function assignSiteListCombo($header=FALSE)
{
    global $xmlrpc_conn, $smarty;
    
    /* Retrieve list of sites */
    $sites = do_xmlrpc("getSiteList", array(), $xmlrpc_conn);

    $site_ids = array();
    $site_descs = array();
    $i=0;
    if ($header == TRUE) {
        $site_ids[$i] = -1;
        $site_descs[$i] = "Select a site...";
        $i++;
    }
    foreach ($sites as $key=>$site) {
        $site_ids[$i] = $site["site_id"];
        $site_descs[$i] = $site["location"];
        $i++;
    }

    $smarty->assign("site_ids", $site_ids);
    $smarty->assign("site_descs", $site_descs);

}
/* Assign an assets location to the form */
function assignAssetLocation($asset_id)
{
    
    global $smarty, $xmlrpc_conn;

    /* Retrieve the asset history */
    $location = do_xmlrpc("getAssetLocation", array($asset_id), $xmlrpc_conn);
    $smarty->assign("location", $location);

    return $location;
}
?>
