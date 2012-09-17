<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Asset Management Interface - Asset Management
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
require("asset/asset_common.php");

if (isset($_REQUEST["added"])) {
    ccs_notice("Asset successfully added with ID:" . $_REQUEST["added"]);
}

if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    display_asset_list();
}

/********************************************************************
 * Add an Asset
 * do=add
 * Optional Parameters
 ********************************************************************/
if ($_REQUEST["do"] == "add") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $smarty->assign("sheets", array("asset.css"));
    $smarty->assign("scripts", array("asset.js"));
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Package up all the data */
        $asset = array();
        get_if_posted(&$asset, "asset_type");
        get_if_posted(&$asset, "description");
        get_if_posted(&$asset, "serial_no");
        $year = $_POST["date_purchased_Year"];
        $month = $_POST["date_purchased_Month"];
        $day = $_POST["date_purchased_Day"];
        $asset["date_purchased"] = "$year-$month-$day";
        get_if_posted(&$asset, "currency");
        get_if_posted(&$asset, "price");
        if (isset($_POST["enabled"]) && $_POST["enabled"]=="yes") {
            $asset["enabled"] = "t";
        } else {
            $asset["enabled"] = "f";
        }
        get_if_posted(&$asset, "supplier");
        get_if_posted(&$asset, "notes");
        /* Get the subassets and their properties*/
        $subassetstr = $_POST["subassets"] . " " . $_POST["new-subassets"];
        $subassets = explode(" ", trim($subassetstr));
        $sadata = array();
        foreach ($subassets as $idx=>$asset_type_subasset_id) {
            $asset_type_subasset_id = trim($asset_type_subasset_id);
            if ($asset_type_subasset_id == "") {
                continue;
            }
            $sadata[$asset_type_subasset_id] = array();
            $name = "subasset-" . $asset_type_subasset_id . "-enabled";
            if (isset($_POST[$name]) && $_POST[$name]=="yes") {
                $sadata[$asset_type_subasset_id]["enabled"] = "t";
            } else {
                $sadata[$asset_type_subasset_id]["enabled"] = "f";
            }
            $name = "subasset-" . $asset_type_subasset_id . "-propertylist";
            $properties = explode(" ", trim($_POST[$name]));
            $pdata = array();
            foreach ($properties as $idx2=>$subasset_property_id) {
                $name = "subasset-" . $asset_type_subasset_id . "-property-" .
                    $subasset_property_id . "-value";
                $pdata[$subasset_property_id] = $_POST[$name];
            }
            $sadata[$asset_type_subasset_id]["properties"] = $pdata;
        }
        $asset["subassets"] = $sadata;
        $asset_id = do_xmlrpc("addAsset", array($asset), $xmlrpc_conn, 
            TRUE, FALSE);
        if (xmlrpc_has_error($asset_id)) {
            ccs_notice("Could not add asset: ".xmlrpc_error_string($asset_id));
        } else {
            if ($_POST["go"]) {
                header("Location: " . $_POST["go"]);
            } else {
                header("Location: /mods/asset/asset.php?added=$asset_id");
            }
            exit;
        }
    }
    assignAssetTypes();
    $smarty->assign("cur_codes", $cur_codes);
    /* Show the form */
    display_page("mods/asset/assetaddform.tpl");

/********************************************************************
 * Bulk asset add routines
 * do=add[soekris|wlancard]
 * Optional Parameters
 ********************************************************************/
} else if ($_REQUEST["do"] == "addsoekris") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $smarty->assign("sheets", array("asset.css"));
    $smarty->assign("scripts", array("soekrisadd.js"));
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        $asset = array();
        get_if_posted(&$asset, "asset_type");
        get_if_posted(&$asset, "description");
        $year = $_POST["date_purchased_Year"];
        $month = $_POST["date_purchased_Month"];
        $day = $_POST["date_purchased_Day"];
        $asset["date_purchased"] = "$year-$month-$day";
        get_if_posted(&$asset, "currency");
        get_if_posted(&$asset, "price");
        if (isset($_POST["enabled"]) && $_POST["enabled"]=="yes") {
            $asset["enabled"] = "t";
        } else {
            $asset["enabled"] = "f";
        }
        get_if_posted(&$asset, "supplier");
        get_if_posted(&$asset, "notes");
        /* Get the list of asset serial nos / mac addresses */
        $n = $_POST["no_soekris"];
        $isoekris = array();
        for ($i=1;$i<=$n;$i++) {
            $isoekris[$i] = array("serial"=>$_POST["isoekris_$i-serial"], 
                "mac"=>$_POST["isoekris_$i-mac"]);
        }
        $asset["isoekris"] = $isoekris;
        $r = do_xmlrpc("addSoekris", array($asset), $xmlrpc_conn, 
            TRUE, FALSE);
        if (xmlrpc_has_error($r)) {
            ccs_notice("Could not add asset: ".xmlrpc_error_string($r));
        } else {
            ccs_notice("$n Soekris assets successfully added");
            display_asset_list();
            exit;
        }
    }
    assignSoekrisAssetTypes();
    $smarty->assign("cur_codes", $cur_codes);
    /* Show the form */
    display_page("mods/asset/soekrisaddform.tpl");
    
} else if ($_REQUEST["do"] == "addwireless") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $smarty->assign("sheets", array("asset.css"));
    $smarty->assign("scripts", array("wirelessadd.js"));
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        $asset = array();
        get_if_posted(&$asset, "asset_type");
        get_if_posted(&$asset, "description");
        $year = $_POST["date_purchased_Year"];
        $month = $_POST["date_purchased_Month"];
        $day = $_POST["date_purchased_Day"];
        $asset["date_purchased"] = "$year-$month-$day";
        get_if_posted(&$asset, "currency");
        get_if_posted(&$asset, "price");
        if (isset($_POST["enabled"]) && $_POST["enabled"]=="yes") {
            $asset["enabled"] = "t";
        } else {
            $asset["enabled"] = "f";
        }
        get_if_posted(&$asset, "supplier");
        get_if_posted(&$asset, "notes");
        /* Get the list of asset serial nos / mac addresses */
        $n = $_POST["no_cards"];
        $icards = array();
        for ($i=1;$i<=$n;$i++) {
            $icards[$i] = array("serial"=>$_POST["icard_$i-serial"], 
                "mac"=>$_POST["icard_$i-mac"]);
        }
        $asset["icards"] = $icards;
        $r = do_xmlrpc("addWirelessCards", array($asset), $xmlrpc_conn, 
            TRUE, FALSE);
        if (xmlrpc_has_error($r)) {
            ccs_notice("Could not add asset: ".xmlrpc_error_string($r));
        } else {
            ccs_notice("$n Wireless card assets successfully added");
            display_asset_list();
            exit;
        }
    }
    assignWirelessCardAssetTypes();
    $smarty->assign("cur_codes", $cur_codes);
    /* Show the form */
    display_page("mods/asset/wirelessaddform.tpl");

/********************************************************************
 * Edit an Asset
 * do=edit
 * Optional Parameters
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $smarty->assign("sheets", array("asset.css"));
    $smarty->assign("scripts", array("asset.js"));
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Look for changed data */
        $errFlag = 0;
        $nUpdated = 0;
        foreach ($asset_details as $idx=>$detail) {
            if (!isset($_POST[$detail]) && $detail!="enabled") {
                continue;
            }
            $orig = $_POST["${detail}-orig"];
            $new = $_POST["$detail"];
            if ($detail == "enabled") {
                if (isset($_POST["enabled"]) && $_POST["enabled"]=="yes") {
                    $new = "t";
                } else {
                    $new = "f";
                }
            }
            if ($new != $orig) {
                $res = updateAssetDetail($_POST["asset_id"], $detail, $new);
                if ($res != "") {
                    $errFlag = 1;
                } else {
                    $nUpdated++;
                }   
            }
        }
        /* Handle date purchased seperated */
        $year = $_POST["date_purchased_Year"];
        $month = $_POST["date_purchased_Month"];
        $day = $_POST["date_purchased_Day"];
        $date_purchased = sprintf("%s-%02d-%02d", $year, $month, $day);
        $t = explode(" ", $_POST["date_purchased-orig"]);
        if ($date_purchased != $t[0]) {
            $res = updateAssetDetail($_POST["asset_id"], "date_purchased", 
                $date_purchased);
            if ($res != "") {
                $errFlag = 1;
            } else {
                $nUpdated++;
            }
            $updated[] = "Date Purchased";
        }
        /* Look for changed subasset properties*/
        $subassets = explode(" ", trim($_POST["subassets"]));
        foreach ($subassets as $idx=>$subasset_id) {
            $subasset_id = trim($subasset_id);
            if ($subasset_id == "") {
                continue;
            }
            $name = "subasset-" . $subasset_id . "-enabled";
            $oname = "subasset-" . $subasset_id . "-enabled-orig";
            $old = $_POST[$oname];
            if (isset($_POST[$name]) && $_POST[$name]=="yes") {
                $new = "t";
            } else {
                $new = "f";
            }
            if ($new != $old) {
                $res = updateSubassetEnabled($_POST["asset_id"],  
                    $subasset_id, $new);
                if ($res != "") {
                    $errFlag = 1;
                } else {
                    $nUpdated++;
                }
            }
            $properties = explode(" ", 
                trim($_POST["subasset-" . $subasset_id . "-properties"]));
            foreach ($properties as $idx=>$subasset_property_id) {
                $nname = "subasset-" . $subasset_id . 
                    "-property-" . $subasset_property_id . "-value";
                $oname = "subasset-" . $subasset_id . 
                    "-property-" . $subasset_property_id . "-orig";
                $old = $_POST[$oname];
                $new = $_POST[$nname];
                if ($old != $new) {
                    $res = updateSubassetPropertyData($subasset_id,
                        $subasset_property_id, "$new");
                    if ($res != "") {
                        $errFlag = 1;
                    } else {
                        $nUpdated++;
                    }
                }
            }
        }
        /* Look for new subassets */
        $nsubassets = explode(" ", trim($_POST["new-subassets"]));
        foreach ($nsubassets as $idx=>$asset_type_subasset_id) {
            $asset_type_subasset_id = trim($asset_type_subasset_id);
            if ($asset_type_subasset_id == "") {
                continue;
            }
            $sadata = array();
            $name = "subasset-" . $asset_type_subasset_id . "-enabled";
            if (isset($_POST[$name]) && $_POST[$name]=="yes") {
                $sadata["enabled"] = "t";
            } else {
                $sadata["enabled"] = "f";
            }
            $name = "subasset-" . $asset_type_subasset_id . "-propertylist";
            $properties = explode(" ", trim($_POST[$name]));
            $pdata = array();
            foreach ($properties as $idx2=>$subasset_property_id) {
                $name = "subasset-" . $asset_type_subasset_id . "-property-" .
                    $subasset_property_id . "-value";
                $pdata[$subasset_property_id] = $_POST[$name];
            }
            $sadata["properties"] = $pdata;
            $res = addSubasset($_POST["asset_id"],  $asset_type_subasset_id, 
                $sadata);
            if ($res != "") {
                $errFlag = 1;
            } else {
                $nUpdated++;
            }        }
        if ($errFlag == 0 && $nUpdated>0) {
            ccs_notice("Asset successfully updated!");
        }

    }
    /* Check asset_id */
    if (!isset($_REQUEST["asset_id"]) && 
            !isset($_REQUEST["find_asset_mac"])) {
        ccs_notice("Asset ID not set or invalid asset specified!");
        display_asset_list();
    }
    if (isset($_REQUEST["asset_id"])) {
        $asset = assignAsset($_REQUEST["asset_id"]);
    } else if (isset($_REQUEST["find_asset_mac"])) {
        $asset = assignAssetByMac($_REQUEST["find_asset_mac"]);
    }
    if (!$asset) {
        /* Asset could not be found! */
        display_asset_list();
        exit;
    }
    $asset_id = $asset["asset_id"];
    assignAssetHistory($asset_id);
    $smarty->assign("cur_codes", $cur_codes);
    /* Show the form */
    display_page("mods/asset/asseteditform.tpl");
    
/********************************************************************
 * View an Assets History
 * do=history
 * Required Parameters
 * asset_id
 * Optional Parameters
 ********************************************************************/
} else if ($_REQUEST["do"] == "history") {
    page_view_requires(AUTH_ASSET_MANAGER);
    if (!isset($_REQUEST["asset_id"])) {
        ccs_notice("Asset ID not set!");
        display_asset_list();
    }
    assignAsset($_REQUEST["asset_id"]);
    assignAssetHistory($_REQUEST["asset_id"]);
    /* Show the form */
    display_page("mods/asset/assethistory.tpl");
    
/********************************************************************
 * Change an assets location
 * do=assign
 * Required Parameters
 * asset_id
 * Optional Parameters
 ********************************************************************/
} else if ($_REQUEST["do"] == "assign") {
    $smarty->assign("sheets", array("asset.css"));
    page_edit_requires(AUTH_ASSET_MANAGER);
    if (!isset($_REQUEST["asset_id"])) {
        ccs_notice("Asset ID not set!");
        display_asset_list();
    }
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        if ($_POST["type"] == "site") {
            $p = array($_POST["asset_id"], $_POST["new_site"]);
            $f = "moveAssetToSite";
        } else if ($_POST["type"] == "asset") {
            $p = array($_POST["asset_id"], $_POST["new_asset"]);
            $f = "attachAssetTo";
        } else {
            $p = array($_POST["asset_id"], $_POST["thing_name"]);
            $f = "assignAssetTo";
        }
        $r = do_xmlrpc($f, $p, $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($r)) {
            ccs_notice("Could not update asset location: " .
                xmlrpc_error_string($r));
        } else {
            if (isset($_POST["from"]) && strlen($_POST["from"])>0) {
                header("Location: " . $_POST["from"]);
            } else {
                header("Location: /mods/asset/asset.php");
            }
            exit;
        } 
    }
    // XXX: Check whether the location really can be changed here!
    $smarty->assign("can_change", 1);
    assignAsset($_REQUEST["asset_id"]);
    assignAssetListCombo(TRUE);
    assignSiteListCombo(TRUE);
    assignAssetLocation($_REQUEST["asset_id"]);
    if (isset($_REQUEST["from"]) || isset($_REQUEST["back"])) {
        $smarty->assign("from", $_SERVER["HTTP_REFERER"]);
    }
    
    /* Show the form */
    display_page("mods/asset/assignasset.tpl");
    
/********************************************************************
 * Retreives a list of subassets for the specified asset type.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=listSubassetTypes
 * Required Paramters
 * asset_type_id         The asset type to retrieve subassets for
 * callback              Name of javascript function that results should be
 *                       processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "listSubassetTypes") {
    page_view_requires(AUTH_ASSET_MANAGER);
    $res = "";
    $p = array($_REQUEST["asset_type_id"]);
    /* Retrieve list of subassets */
    $types = do_xmlrpc("getLinkedSubassets", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($types)) {
        $res .= "<success>" . xmlrpc_error_code($types) . "</success>";
        $res .= "<errMsg>" . xmlrpc_error_string($types) . "</errMsg>";
    } else {
        $sres = "";
        foreach ($types as $idx=>$subasset) {
            $sres .= "<subasset>";
            $sres .= "<required>" . $subasset["required"] . "</required>";
            $sres .= "<description>" . $subasset["description"] . 
                "</description>";
            $sres .= "<name>" . $subasset["name"] . "</name>";
            $sres .= "<asset_type_subasset_id>" . 
                $subasset["asset_type_subasset_id"] . 
                "</asset_type_subasset_id>";
            $sres .= "<subasset_type_id>" . $subasset["subasset_type_id"] . 
                "</subasset_type_id>";
            /* Get properties */
            $sres .= "<properties>";
            $p = array($subasset["subasset_type_id"]);
            $props = do_xmlrpc("getLinkedProperties", $p, $xmlrpc_conn,
                TRUE, FALSE);
            if (xmlrpc_has_error($props)) {
                $res .= "<success>" . xmlrpc_error_code($props) . "</success>";
                $res .= "<errMsg>" . xmlrpc_error_string($props) . "</errMsg>";
                break;
            } else {
                foreach ($props as $idx=>$prop) {
                    $sres .= "<property>";
                    $sres .= "<required>" . $prop["required"] . "</required>";
                    $sres .= "<description>" . $prop["description"] . 
                        "</description>";
                    $sres .= "<subasset_property_id>" . 
                        $prop["subasset_property_id"] . 
                        "</subasset_property_id>";
                    $sres .= "<asset_property_id>" . 
                        $prop["asset_property_id"] . "</asset_property_id>";
                    $sres .= "<default_value>" . 
                        $prop["default_value"] . "</default_value>";
                    $sres .= "</property>";
                }
            }
            $sres .= "</properties>";
            $sres .= "</subasset>";
        }
    }
    if ($res == "") {
        $res .= "<success>0</success><errMsg></errMsg>";
        $res .= $sres;
    }
    /* Return XML result */
    header("Content-type: text/xml");
    echo "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n" .
        "<response>\n" .
        "<method>" . $_REQUEST["callback"] . "</method>\n" .
        "<result>$res</result>\n" .
        "</response>\n";
    exit;

/********************************************************************
 * Retreives a list of properties for the specified subasset type.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=listSubassetProperties
 * Required Paramters
 * asset_type_id         The asset type to retrieve subassets for
 * callback              Name of javascript function that results should be
 *                       processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "listSubassetProperties") {
    page_view_requires(AUTH_ASSET_MANAGER);
    $res = "";
    $p = array($_REQUEST["subasset_type_id"]);
    /* Retrieve list of linked properties */
    $props = do_xmlrpc("getLinkedProperties", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($props)) {
        $res .= "<success>" . xmlrpc_error_code($props) . "</success>";
        $res .= "<errMsg>" . xmlrpc_error_string($props) . "</errMsg>";
    } else {
        $sres = "";
        $sres .= "<subasset>";
        $sres .= "<required>" . $_REQUEST["required"] . "</required>";
        $sres .= "<description>" . $_REQUEST["description"] . 
            "</description>";
        $sres .= "<name>" . $_REQUEST["name"] . "</name>";
        $sres .= "<asset_type_subasset_id>" .
            $_REQUEST["asset_type_subasset_id"] . 
            "</asset_type_subasset_id>";
        $sres .= "<subasset_type_id>" . $_REQUEST["subasset_type_id"] . 
                "</subasset_type_id>";
        $sres .= "<properties>";
        foreach ($props as $idx=>$prop) {
            $sres .= "<property>";
            $sres .= "<required>" . $prop["required"] . "</required>";
            $sres .= "<description>" . $prop["description"] . 
                "</description>";
            $sres .= "<subasset_property_id>" . 
                $prop["subasset_property_id"] . 
                "</subasset_property_id>";
            $sres .= "<asset_property_id>" . 
                $prop["asset_property_id"] . "</asset_property_id>";
            $sres .= "<default_value>" . 
                $prop["default_value"] . "</default_value>";
            $sres .= "</property>";
        }
        $sres .= "</properties>";
        $sres .= "</subasset>";
        $res .= "<success>0</success><errMsg></errMsg>";
        $res .= $sres;
    }
    /* Return XML result */
    header("Content-type: text/xml");
    echo "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n" .
        "<response>\n" .
        "<method>" . $_REQUEST["callback"] . "</method>\n" .
        "<result>$res</result>\n" .
        "</response>\n";
    exit;

}

/* If we get here the page has been called incorrectly, display the list */
ccs_notice("Invalid Action Requested: " . $_REQUEST["do"]);
display_asset_list();

?>
