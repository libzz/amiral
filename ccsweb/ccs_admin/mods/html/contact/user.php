<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Authentication Display Interface - User manipulation
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
require("contact/contact_common.php");

function display_contact_list()
{
    global $xmlrpc_conn, $smarty;
    
    /* Check administrator privs */
    page_view_requires(AUTH_ADMINISTRATOR);
    
    /* Retrieve list of contacts */
    $contacts = do_xmlrpc("getUsers", array(), $xmlrpc_conn);
    usort($contacts, "contact_cmp");
    $smarty->assign("contacts", $contacts);

    display_page("mods/contact/userlist.tpl");

}

if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    display_contact_list();
}

/********************************************************************
 * Delete a contact 
 * do=delete
 * Required Paramters
 * contact_id
 * confirm
 * If confirm is not set a page is displayed asking the user to confirm
 * they wish to delete this contact.
 ********************************************************************/
if ($_REQUEST["do"] == "delete") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    if ($_REQUEST["confirm"] != "yes") {
        /* Get the contact data */
        if (assign_contact($_REQUEST["contact_id"]) != array()) {
            /* Ask the user to confirm deletion */
            display_page("mods/contact/userdel.tpl");
        }
    } else {
        /* Delete user */
        $rv = do_xmlrpc("delLogin", array($_REQUEST["contact_id"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not delete contact: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("User successfully deleted!");
        }
        /* Display contact list */
        display_contact_list();
    }
    
/********************************************************************
 * Add or Edit a contact 
 * do=add|edit
 * If 'process' is set the request must include all of the required 
 * contact fields (username, givenname, surname, email, type) and
 * may contain optional fields such as phone, passwd, etc.
 * If edit is set the request must also include 'contact_id'
 ********************************************************************/
} else if ($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Process submitted form */
        $contact_id = $_REQUEST["contact_id"];
        $contact = get_posted_contact();
        if (array_key_exists("newpass", $contact) && $contact["newpass"]!="") {
            $contact["passwd"] = $contact["newpass"];
        }
        $cid = do_xmlrpc("${do}Admin", array($contact), 
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($cid)) {
            ccs_notice("Could not $do contact: ".xmlrpc_error_string($cid));
            $action = $do;
            $smarty->assign("contact", $contact);
        } else {
            $action = "edit";
            ccs_notice("Contact ${do}ed successfuly$warn.");
            assign_contact($cid);
        }
    } else {
        if ($do == "edit") {
            /* Get the contact data */
            assign_contact($_REQUEST["contact_id"]);
        }
        $action = $do;
    }
    $smarty->assign("contact_types", $contact_types);
    $smarty->assign("action", $action);

    /* Show the add form */
    display_page("mods/contact/userform.tpl");
    
} else if ($_REQUEST["do"] == "gen") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $did = do_xmlrpc("genAdminPassword", array($_REQUEST["admin_id"], $_REQUEST["login_id"]), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($did)) {
        ccs_notice("Could not generate Admin password: ".xmlrpc_error_string($did));
    } else {
        ccs_notice("Admin password generated successfuly$warn.");
        $smarty->assign("plain_password", $did);
    }
    assign_contact($_REQUEST["admin_id"]);
    $smarty->assign("action", "edit");

    /* Show the add form */
    display_page("mods/contact/userform.tpl");

/********************************************************************
 * Assign a user ID to a contact 
 * do=assignuid
 * Required Paramters
 * contact_id
 ********************************************************************/
} else if ($_REQUEST["do"] == "assignuid") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    $contact = assign_contact($_REQUEST["contact_id"]);
    if (isset($contact["uid"]) && strlen($contact["uid"]) > 0) {
        ccs_notice("Contact already has uid of (" . $contact["uid"] .
            "). Unable to assign new uid.");
    } else {
        $p = $_REQUEST["contact_id"];
        $cid = do_xmlrpc("assignUID", array($p), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($cid)) {
            ccs_notice("Could not assign uid for contact: " . 
                xmlrpc_error_string($cid));
        } else {
            ccs_notice("Contact assigned uid " . $cid);
            assign_contact($_REQUEST["contact_id"]);
        }
    }
    $smarty->assign("contact_types", $contact_types);
    $smarty->assign("action", "edit");
    display_page("mods/contact/userform.tpl");

/********************************************************************
 * Disable a contact 
 * do=disable
 * Required Paramters
 * contact_id
 ********************************************************************/
} else if ($_REQUEST["do"] == "disable") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
    $contact_id = $_REQUEST["contact_id"];
    $rv = do_xmlrpc("disableLogin", array($contact_id),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        ccs_notice("Could not disable contact: ".xmlrpc_error_string($rv));
    } else {
        ccs_notice("Contact disabled.");
    }
    /* Display contact list */
    display_contact_list();
}

/* If we get here the page has been called incorrectly, display the list */
ccs_notice("Invalid Action Requested: " . $_REQUEST["do"]);
display_contact_list();

?>
