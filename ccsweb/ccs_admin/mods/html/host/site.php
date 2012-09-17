<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Site Addition / Editing
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
    display_site_list();
}

/********************************************************************
 * Add or Edit a Site
 * do=add
 * Optional Parameters
 ********************************************************************/
if ($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $do = $_REQUEST["do"];
    $smarty->assign("sheets", array("site.css"));
    $smarty->assign("scripts", array("site.js"));
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Process Submitted Form */
        $site_id = $_REQUEST["site_id"];
        $site = get_posted_site();
        if ($do == "add") {
            $f = "addSite";
            $p = array($site);
        } else {
            $f = "updateSiteDetails";
            $p = array($site_id, $site);
        }
        $rv = do_xmlrpc($f, $p, $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not $do site: ".xmlrpc_error_string($rv));
            $action = $do;
            $smarty->assign("site", $site);
        } else {
            $action = "edit";
            if ($do == "add") {
                $site_id = $rv;
            }
            ccs_notice("Site ${do}ed successfuly.");
            display_site_list();
        }
    } else {
        if ($do == "edit") {
            assign_site($_REQUEST["site_id"]);
        }
        $action = $do;
    } 
    /* Show the form */
    $smarty->assign("action", $action);
    assignContacts();
    display_page("mods/host/siteform.tpl");
    
/********************************************************************
 * Delete a site 
 * do=delete
 * Required Paramters
 * site_id
 * confirm
 * If confirm is not set a page is displayed asking the user to confirm
 * they wish to delete this site.
 ********************************************************************/
} else if ($_REQUEST["do"] == "delete") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    if ($_REQUEST["confirm"] != "yes") {
        /* Get the site data */
        if (assign_site($_REQUEST["site_id"]) != array()) {
            /* Ask the user to confirm deletion */
            display_page("mods/host/sitedel.tpl");
        }
    } else {
        /* Delete site */
        $rv = do_xmlrpc("removeSite", array($_REQUEST["site_id"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not delete site: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Site successfully deleted!");
        }
        /* Display site list */
        display_site_list();
    }

}

/* If we get here the page has been called incorrectly, display the list */
ccs_notice("Invalid Action Requested: " . $_REQUEST["do"]);
display_site_list();

?>
