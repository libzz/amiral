<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Asset Management Interface - Property Management
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

function display_property_list()
{
    global $xmlrpc_conn, $smarty;
    
    /* Check asset manager privs */
    page_view_requires(AUTH_ASSET_MANAGER);
    
    /* Retrieve list of contacts */
    $properties = do_xmlrpc("asset.getProperties", array(), $xmlrpc_conn);
    $smarty->assign("properties", $properties);

    display_page("mods/asset/propertylist.tpl");

}

if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    display_property_list();
}

/********************************************************************
 * Delete an Asset Property 
 * do=delete
 * Required Paramters
 * asset_property_id
 * confirm
 * If confirm is not set a page is displayed asking the user to confirm
 * they wish to delete this asset property.
 ********************************************************************/
if ($_REQUEST["do"] == "delete") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    if ($_REQUEST["confirm"] != "yes") {
        /* Get the data */
        $smarty->assign("asset_property_id", $_REQUEST["asset_property_id"]);
        $smarty->assign("description", 
            getAssetProperty($_REQUEST["asset_property_id"]));
        /* Ask the user to confirm deletion */
        display_page("mods/asset/assetpropdel.tpl");
    } else {
        /* Delete Asset Property */
        $r = do_xmlrpc("delAssetProperty", 
            array($_REQUEST["asset_property_id"]), $xmlrpc_conn, 
            TRUE, FALSE);
        if (xmlrpc_has_error($r)) {
            ccs_notice("Could not delete asset property: " .
                xmlrpc_error_string($r));
        } else {
            ccs_notice("Asset Property successfully deleted!");
        }
        /* Display list */
        display_property_list();
    }

/********************************************************************
 * Add / Edit an Asset Property 
 * do=add|edit
 * Required Paramters
 * asset_property_id    If editing, the id of the property
 * description          The description of the property
 ********************************************************************/
} else if (($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit")) {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Process submitted form */
        $asset_property_id = $_REQUEST["asset_property_id"];
        $description = $_REQUEST["description"];
        $rv = do_xmlrpc("${do}AssetProperty", 
            array($asset_property_id,$description), $xmlrpc_conn, 
            TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not $do asset property: " .
                xmlrpc_error_string($rv));
            $action = $do;
        } else {
            ccs_notice("Asset property ${do}ed successfuly$warn.");
            if ($do == "add") {
                if (isset($_REQUEST["go"])) {
                    header("Location: " . $_REQUEST["go"]);
                } else {
                    display_property_list();
                }
                exit;
            }
            $action = "edit";
            $warn = "";
            if (strlen($rv["errMsg"])>0) {
                $warn = "  - " . htmlspecialchars($rv["errMsg"]);
            } 
            if ($do == "add") {
                $asset_property_id = $rv["asset_property_id"];
            }
        }
        $smarty->assign("asset_property_id", $asset_property_id);
        $smarty->assign("description", $description);
    } else {
        if ($do == "edit") {
            $smarty->assign("asset_property_id", 
                $_REQUEST["asset_property_id"]);
            $smarty->assign("description", 
                getAssetProperty($_REQUEST["asset_property_id"]));
        }
        $action = $do;
    }
    if ($_REQUEST["back"] == "true") {
        $smarty->assign("referer", $_SERVER["HTTP_REFERER"]);
    }
    $smarty->assign("action", $action);
    /* Show the form */
    display_page("mods/asset/assetpropform.tpl");

/********************************************************************
 * Links a property to a subasset.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=addSubassetProperty
 * Required Paramters
 * subasset_type_id  The subasset type gaining a property
 * asset_property_id The property to add
 * default_value     The default value for the property
 * required          Whether the property is optional or reuqired
 * callback          Name of javascript function that results should be
 *                   processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "addSubassetProperty") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $res = "";
    $p = array($_REQUEST["subasset_type_id"], $_REQUEST["asset_property_id"],
        $_REQUEST["default_value"], $_REQUEST["required"]);
    $rv = do_xmlrpc("addSubassetProperty", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $res .= "<success>" . xmlrpc_error_code($rv) . "</success>";
        $res .= "<errMsg>" . xmlrpc_error_string($rv) . "</errMsg>";
    } else {
        if ($rv["subasset_property_id"] > 0) {
            $res .= "<success>0</success>";
            $res .= "<subasset_type_id>" . $_REQUEST["subasset_type_id"] . 
                "</subasset_type_id>";
            $res .= "<asset_property_id>" . $_REQUEST["asset_property_id"] . 
                "</asset_property_id>";
            $res .= "<subasset_property_id>" . 
                $rv["subasset_property_id"] . "</subasset_property_id>";
            $res .= "<default_value>" . $_REQUEST["default_value"] . 
                "</default_value>";
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
 * Update the details of a subasset property.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=updatedSubassetProperty
 * Required Paramters
 * subasset_property_id  The property being modified
 * default_value         The default value for the property
 * required              Whether the property is optional or reuqired
 * callback              Name of javascript function that results should be
 *                       processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "updateSubassetProperty") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $res = "";
    $p = array($_REQUEST["subasset_property_id"], 
        $_REQUEST["default_value"], $_REQUEST["required"]);
    $rv = do_xmlrpc("updateSubassetProperty", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $res .= "<success>" . xmlrpc_error_code($rv) . "</success>";
        $res .= "<errMsg>" . xmlrpc_error_string($rv) . "</errMsg>";
    } else {
        if ($rv["subasset_property_id"] > 0) {
            $res .= "<success>0</success>";
            $res .= "<subasset_property_id>" . 
                $rv["subasset_property_id"] . "</subasset_property_id>";
            $res .= "<default_value>" . $_REQUEST["default_value"] . 
                "</default_value>";
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
 * Removes a property from a subasset.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=removeSubassetProperty
 * Required Paramters
 * subasset_property_id  The property being modified
 * required              Whether the property is optional or reuqired
 * callback              Name of javascript function that results should be
 *                       processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "removeSubassetProperty") {
    page_edit_requires(AUTH_ASSET_MANAGER);
    $res = "";
    $p = array($_REQUEST["subasset_property_id"]);
    $rv = do_xmlrpc("removeSubassetProperty", $p, $xmlrpc_conn, TRUE, FALSE);
    if ($r->faultCode() > 0) {
        $res .= "<success>" . xmlrpc_error_code($rv) . "</success>";
        $res .= "<errMsg>" . xmlrpc_error_string($rv) . "</errMsg>";
    } else {
        if ($rv["subasset_property_id"] > 0) {
            $res .= "<success>0</success>";
            $res .= "<subasset_property_id>" . 
                $rv["subasset_property_id"] . "</subasset_property_id>";
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
display_property_list();

?>
