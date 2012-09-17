<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Asset Management Interface - Type Management
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

if (!isset($_REQUEST["type"]) || $_REQUEST["type"]!="subasset") {
    $type = "asset";
} else {
    $type = "subasset";
}

function display_type_list()
{
    global $xmlrpc_conn, $smarty;
    
    /* Check asset manager privs */
    page_view_requires(AUTH_ASSET_MANAGER);
    
    /* Retrieve list of asset types */
    assignAssetTypes();
    
    display_page("mods/asset/typelist.tpl");

}

function display_subasset_type_list()
{
    global $xmlrpc_conn, $smarty;
    
    /* Check asset manager privs */
    page_view_requires(AUTH_ASSET_MANAGER);
    
    assignSubassetTypes();

    display_page("mods/asset/subassettypelist.tpl");

}

if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    if ($type == "subasset") {
        display_subasset_type_list();
    } else {
        display_type_list();
    }
}

/********************************************************************
 * Delete an Asset Type 
 * do=delete
 * Required Paramters
 * asset_type_id
 * confirm
 * If confirm is not set a page is displayed asking the user to confirm
 * they wish to delete this asset type.
 ********************************************************************/
if ($_REQUEST["do"] == "delete" && $type=="asset") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    if ($_REQUEST["confirm"] != "yes") {
        /* Get the data */
        $smarty->assign("asset_type_id", $_REQUEST["asset_type_id"]);
        $smarty->assign("description", 
            getAssetType($_REQUEST["asset_type_id"]));
        /* Ask the user to confirm deletion */
        display_page("mods/asset/assettypedel.tpl");
    } else {
        /* Delete Asset Type */
        $r = do_xmlrpc("delAssetType", array($_REQUEST["asset_type_id"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrcp_has_error($r)) {
            ccs_notice("Could not delete asset type: " .
                xmlrpc_error_string($r));
        } else {
            ccs_notice("Asset Type successfully deleted!");
        }
        /* Display group list */
        display_type_list();
    }

/********************************************************************
 * Add / Edit an Asset Type 
 * do=add|edit
 * Required Paramters
 * asset_type_id        If editing, the id of the type
 * description          The description of the type
 ********************************************************************/
} else if (($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit") &&
        $type=="asset") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    /* Include the javascript for the subtype form */
    $smarty->assign("scripts", array("assettype.js"));
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Process submitted form */
        $asset_type_id = $_REQUEST["asset_type_id"];
        $description = $_REQUEST["description"];
        $atid = do_xmlrpc("${do}AssetType", array($asset_type_id,$description),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($atid)) {
            ccs_notice("Could not $do asset type: " .
                xmlrpc_error_string($atid));
            $action = $do;
            $atid = $asset_type_id;
        } else {
            $action = "edit";
            ccs_notice("Asset type ${do}ed successfuly$warn.");
        }
        $smarty->assign("asset_type_id", $atid);
        $smarty->assign("description", $description);
        assignAssetTypeAllowMod($atid);
        assignSubassetTypes();
        assignLinkedSubassets($atid);
    } else {
        if ($do == "edit") {
            $smarty->assign("asset_type_id", $_REQUEST["asset_type_id"]);
            $smarty->assign("description", 
                getAssetType($_REQUEST["asset_type_id"]));
            assignAssetTypeAllowMod($_REQUEST["asset_type_id"]);
            assignSubassetTypes();
            assignLinkedSubassets($_REQUEST["asset_type_id"]);
        }
        $action = $do;
    }
    $smarty->assign("action", $action);
    /* Show the form */
    display_page("mods/asset/assettypeform.tpl");

/********************************************************************
 * Delete a Subasset Type 
 * do=delete
 * Required Paramters
 * subasset_type_id
 * confirm
 * If confirm is not set a page is displayed asking the user to confirm
 * they wish to delete this subasset type.
 ********************************************************************/
 } else if ($_REQUEST["do"] == "delete" && $type=="subasset") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    if ($_REQUEST["confirm"] != "yes") {
        /* Get the data */
        $smarty->assign("subasset_type_id", $_REQUEST["subasset_type_id"]);
        $smarty->assign("description", 
            getSubassetType($_REQUEST["subasset_type_id"]));
        /* Ask the user to confirm deletion */
        display_page("mods/asset/subassettypedel.tpl");
    } else {
        /* Delete Subasset Type */
        $r = do_xmlrpc("delSubassetType", 
            array($_REQUEST["subasset_type_id"]), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($r)) {
            ccs_notice("Could not delete subasset type: " .
                xmlrpc_error_string($r));
        } else {
            ccs_notice("Subasset Type successfully deleted!");
        }
        /* Display group list */
        display_subasset_type_list();
    }

/********************************************************************
 * Add / Edit an Subasset Type 
 * do=add|edit
 * Required Paramters
 * subasset_type_id     If editing, the id of the type
 * description          The description of the type
 ********************************************************************/
} else if (($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit") && 
        $type=="subasset") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    /* Include the javascript for the properties form */
    $smarty->assign("scripts", array("assetprop.js"));
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Process submitted form */
        $subasset_type_id = $_REQUEST["subasset_type_id"];
        $description = $_REQUEST["description"];
        $rv = do_xmlrpc("${do}SubassetType", 
            array($subasset_type_id,$description), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not $do subasset type: " .
                xmlrpc_error_string($rv));
            $action = $do;
            $smarty->assign("subasset_type_id", $subasset_type_id);
            $smarty->assign("description", $description);
        } else {
            $action = "edit";
            $warn = "";
            if (strlen($rv["errMsg"])>0) {
                $warn = "  - " . htmlspecialchars($rv["errMsg"]);
            } 
            if ($do == "add") {
                $subasset_type_id = $rv["subasset_type_id"];
            }
            ccs_notice("Subasset type ${do}ed successfuly$warn.");
            $smarty->assign("subasset_type_id", $subasset_type_id);
            $smarty->assign("description", $description);
        }
        assignSubassetTypeAllowMod($subasset_type_id);
        assignProperties();
        assignLinkedProperties($subasset_type_id);
    } else {
        if ($do == "edit") {
            $smarty->assign("subasset_type_id", 
                $_REQUEST["subasset_type_id"]);
            $smarty->assign("description", 
                getSubassetType($_REQUEST["subasset_type_id"]));
            assignSubassetTypeAllowMod($_REQUEST["subasset_type_id"]);
            assignProperties();
            assignLinkedProperties($_REQUEST["subasset_type_id"]);
        }
        $action = $do;
    }
    $smarty->assign("action", $action);
    /* Show the form */
    display_page("mods/asset/subassettypeform.tpl");
    
/********************************************************************
 * Adds a subasset type to an asset type.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=addSubassetLink
 * Required Paramters
 * asset_type_id    The asset type gaining a subasset type
 * subasset_type_id The type of subasset type to create
 * name             A descriptive name for this instance
 * required         Wether the subasset type is optional or reuqired
 * callback         Name of javascript function that results should be
 *                  processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "addSubassetLink") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $res = "";
    $p = array($_REQUEST["asset_type_id"], $_REQUEST["subasset_type_id"],
        $_REQUEST["name"], $_REQUEST["required"]);
    $rv = do_xmlrpc("addSubassetLink", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $res .= "<success>" . xmlrpc_error_code($rv) . "</success>";
        $res .= "<errMsg>" . xmlrpc_error_string($rv) . "</errMsg>";
    } else {
        if ($rv["asset_type_subasset_id"] > 0) {
            $res .= "<success>0</success>";
            $res .= "<asset_type_id>" . $_REQUEST["asset_type_id"] . 
                "</asset_type_id>";
            $res .= "<subasset_type_id>" . $_REQUEST["subasset_type_id"] . 
                "</subasset_type_id>";
            $res .= "<asset_type_subasset_id>" . 
                $rv["asset_type_subasset_id"] . "</asset_type_subasset_id>";
            $res .= "<name>" . $_REQUEST["name"] . "</name>";
            $res .= "<required>" . $_REQUEST["required"] . "</required>";
        } else {
            $res .= "<success>1</success><errMsg>" . $rv["errMsg"] . 
                "</errMsg>";
        }
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
 * Removes the subasset type from an asset type.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=removeSubassetLink
 * Required Paramters
 * asset_type_subasset_id   The id of the record to remove
 * required                 Whether the record is required or optional
 * callback                 Name of javascript function that results 
 *                          should be processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "removeSubassetLink") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $res = "";
    $p = array($_REQUEST["asset_type_subasset_id"]);
    $rv = do_xmlrpc("removeSubassetLink", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $res .= "<success>" . xmlrpc_error_code($rv) . "</success>";
        $res .= "<errMsg>" . xmlrpc_error_string($rv) . "</errMsg>";
    } else {
        if ($rv["asset_type_subasset_id"] > 0) {
            $res .= "<success>0</success>";
            $res .= "<asset_type_subasset_id>" . 
                $rv["asset_type_subasset_id"] . "</asset_type_subasset_id>";
            $res .= "<required>" . $_REQUEST["required"] . "</required>";
        } else {
            $res .= "<success>1</success><errMsg>" . $rv["errMsg"] . 
                "</errMsg>";
        }
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
 * Updates the status of a subasset link.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=updateSubassetLink
 * Required Paramters
 * asset_type_subasset_id   The id of the record to update
 * required                 Whether the record is required or optional
 * callback                 Name of javascript function that results 
 *                          should be processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateSubassetLink") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $res = "";
    $p = array($_REQUEST["asset_type_subasset_id"], $_REQUEST["required"]);
    $rv = do_xmlrpc("updateSubassetLink", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $res .= "<success>" . xmlrpc_error_code($rv) . "</success>";
        $res .= "<errMsg>" . xmlrpc_error_string($rv) . "</errMsg>";
    } else {
        if ($rv["asset_type_subasset_id"] > 0) {
            $res .= "<success>0</success>";
            $res .= "<asset_type_subasset_id>" . 
                $rv["asset_type_subasset_id"] . "</asset_type_subasset_id>";
            $res .= "<required>" . $_REQUEST["required"] . "</required>";
        } else {
            $res .= "<success>1</success><errMsg>" . $rv["errMsg"] . 
                "</errMsg>";
        }
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
display_type_list();

?>
