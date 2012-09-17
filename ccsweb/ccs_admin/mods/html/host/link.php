<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Link Configuration
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
    display_link_list();
}

/********************************************************************
 * Add a Link
 * do=add
 * Optional Parameters
 ********************************************************************/
if ($_REQUEST["do"] == "add") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Look for posted data */
        $link = array();
        get_if_posted(&$link, "link_id");
        get_if_posted(&$link, "description");
        get_if_posted(&$link, "type");
        get_if_posted(&$link, "mode");
        get_if_posted(&$link, "class_id");
        get_if_posted(&$link, "essid");
        get_if_posted(&$link, "channel");
        get_if_posted(&$link, "key");
        get_if_posted(&$link, "network_address");
        if (isset($_POST["shared_network"]) && 
                $_POST["shared_network"]=="yes") {
            $link["shared_network"] = "t";
        } else {
            $link["shared_network"] = "f";
        }
        $rv = do_xmlrpc("addLink", array($link), $xmlrpc_conn,TRUE,FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not add Link: ".xmlrpc_error_string($rv));
            $action = $do;
            $smarty->assign("link", $link);
        } else {
            $action = "edit";
            ccs_notice("Link added successfully");
            display_link_list();
            exit;
        }
    }
    assignLinkTypes();
    assignLinkClasses();
    /* Show the form */
    $smarty->assign("sheets", array("link.css"));
    $smarty->assign("scripts", array("link.js"));
    display_page("mods/host/linkaddform.tpl");
    
/********************************************************************
 * Edit a link
 * do=edit
 * Optional Parameters
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Look for changed data */
        $host = array();
        $link_id = $_POST["link_id"];
        get_if_post_modified(&$link, "description");
        get_if_post_modified(&$link, "type");
        get_if_post_modified(&$link, "mode");
        get_if_post_modified(&$link, "class_id");
        get_if_post_modified(&$link, "essid");
        get_if_post_modified(&$link, "channel");
        get_if_post_modified(&$link, "key");
        get_if_post_modified(&$link, "network_address");
        get_if_checked(&$link, "shared_network");
        $rv = do_xmlrpc("updateLinkDetails", array($link_id, $link), 
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update link: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Link details successfully updated.");
            display_link_list();
            exit;
        }

    }
    if (!isset($_REQUEST["link_id"])) {
        ccs_notice("Link ID not set!");
        display_link_list();
    }
    displayLink($_REQUEST["link_id"]);

/********************************************************************
 * Delete a link 
 * do=delete
 * Required Paramters
 * link_id
 * confirm
 * If confirm is not set a page is displayed asking the user to confirm
 * they wish to delete this link.
 ********************************************************************/
} else if ($_REQUEST["do"] == "delete") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    if ($_REQUEST["confirm"] != "yes") {
        /* Get the site data */
        if (assignLink($_REQUEST["link_id"]) != array()) {
            /* Ask the user to confirm deletion */
            display_page("mods/host/linkdel.tpl");
        }
    } else {
        /* Delete host */
        $rv = do_xmlrpc("removeLink", array($_REQUEST["link_id"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not delete link: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Link successfully deleted!");
        }
        /* Display list */
        display_link_list();
    }
    
/********************************************************************
 * Return a suggested network address for the link.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=getSuggestedNetwork
 * Required Paramters
 * class_id         Class of the link being created
 * callback         Name of javascript function that results should be
 *                  processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "getSuggestedNetwork") {
    page_view_requires(AUTH_USER);
    /* Return result */
    $smarty->assign("name", "network_address");
    $value = do_xmlrpc("allocateNetwork", array($_REQUEST["class_id"]), 
        $xmlrpc_conn,TRUE,FALSE);
    if (xmlrpc_has_error($value)) {
        $value = "";
    }
    $smarty->assign("value", $value);
    $smarty->display("inputbox.tpl");
    exit;
    
/********************************************************************
 * Return possible link modes for the specified type.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=getModeList
 * Required Paramters
 * type_name        Type of link being created/edited
 * callback         Name of javascript function that results should be
 *                  processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "getModeList") {
    page_view_requires(AUTH_USER);
    /* Return result */
    assignLinkModes($_REQUEST["type_name"]);
    $smarty->display("pass:{html_options values=\$link_modes output=\$link_mode_descs name=\"mode\" id=\"mode\"}");
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
    assignChannelList($_REQUEST["mode"]);
    $smarty->display("pass:{html_options values=\$channels output=\$channel_descs name=\"channel\" id=\"channel\"}");
    exit;

}

/* If we get here the page has been called incorrectly, display the list */
ccs_notice("Invalid Action Requested: " . $_REQUEST["do"]);
display_link_list();

?>
