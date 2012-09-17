<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Authentication Display Interface - Group manipulation
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

/* Include the javascript for the group membership form */
$smarty->assign("scripts", array("groupform.js"));

function process_member($id, $func)
{

    global $xmlrpc_conn;
    
    $rv = do_xmlrpc("${func}Member", array($_REQUEST["group_id"], $id),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $res = "error,-1, " . xmlrpc_error_string($rv);
    } else {
        $res .= "success," . $rv . ",Success";
    }

    return $res;
    
}

function display_group_list()
{
    global $xmlrpc_conn, $smarty;
    
    /* Check administrator privs */
    page_view_requires(AUTH_ADMINISTRATOR);
    
    /* Retrieve list of contacts */
    $groups = do_xmlrpc("getGroups", array(), $xmlrpc_conn);
    usort($groups, "group_cmp");
    /* Setup group member values */
    foreach ($groups as $entry=>$group) {
        $group_id = $group["admin_group_id"];
        $rv = do_xmlrpc("getGroupMemberCount", array($group_id), $xmlrpc_conn,
            TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not retrieve group member count: " . 
                xmlrpc_error_string($rv));
            $group["nmembers"] = "";
        } else {
            $group["nmembers"] = $rv;
        }
        $groups[$entry] = $group;
    }

    $smarty->assign("groups", $groups);
    display_page("mods/contact/grouplist.tpl");

}

if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
    display_group_list();
}

/********************************************************************
 * Delete a group 
 * do=delete
 * Required Paramters
 * group_id
 * confirm
 * If confirm is not set a page is displayed asking the user to confirm
 * they wish to delete this group.
 ********************************************************************/
if ($_REQUEST["do"] == "delete") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    if ($_REQUEST["confirm"] != "yes") {
        /* Get the group data */
        if (get_group($_REQUEST["group_id"]) != array()) {
            /* Ask the user to confirm deletion */
            display_page("mods/contact/groupdel.tpl");
        }
    } else {
        /* Delete group */
        $rv = do_xmlrpc("delGroup", array($_REQUEST["group_id"]), 
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not delete group: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Group successfully deleted!");
        }
        /* Display group list */
        display_group_list();
    }
    
/********************************************************************
 * Add or Edit a group 
 * do=add|edit
 * If 'process' is set the request must include all of the required 
 * 'group_name' field
 * If edit is set the request must also include 'group_id'
 ********************************************************************/
} else if ($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $do = $_REQUEST["do"];
    if (isset($_REQUEST["process"]) && $_REQUEST["process"]=="yes") {
        /* Process submitted form */
        $group_id = $_REQUEST["group_id"];
        $group = get_posted_group();
        $rv = do_xmlrpc("${do}Group", array($group), $xmlrpc_conn, TRUE,
            FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not $do group: ".xmlrpc_error_string($rv));
            $action = $do;
            $smarty->assign("group", $group);
        } else {
            $action = "edit";
            $group_id = $rv;
            ccs_notice("Group ${do}ed successfuly$warn.");
            get_group($group_id);
            get_members($group_id);
            get_avail($group_id);
        }
    } else {
        if ($do == "edit") {
            /* Get the group data */
            get_group($_REQUEST["group_id"]);
            /* Get the membership data */
            get_members($_REQUEST["group_id"]);
            get_avail($_REQUEST["group_id"]);
        }
        $action = $do;
    }
    $smarty->assign("action", $action);
    /* Show the form */
    display_page("mods/contact/groupform.tpl");
    
/********************************************************************
 * Assign a group ID to a contact 
 * do=assigngid
 * Required Paramters
 * group_id
 ********************************************************************/
} else if ($_REQUEST["do"] == "assigngid") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $group = get_group($_REQUEST["group_id"]);
    if (isset($group["gid"]) && strlen($group["gid"]) > 0) {
        ccs_notice("Group already has gid of (" . $group["gid"] .
            "). Unable to assign new gid.");
    } else {
        $rv = do_xmlrpc("assignGID", array($_REQUEST["group_id"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not assign uid for group: " . 
                xmlrpc_error_string($rv));
        } else {
            ccs_notice("Group assigned gid " . $rv);
            get_group($_REQUEST["group_id"]);
            get_members($_REQUEST["group_id"]);
            get_avail($_REQUEST["group_id"]);
        }
    }
    $smarty->assign("action", "edit");
    display_page("mods/contact/groupform.tpl");

/********************************************************************
 * Add a contact to a group.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=addmember
 * Required Paramters
 * group_id         Group to add contact to
 * new_members      Comma seperated list of member_id's to add
 *                  member_ids should be in the form t# where t is either
 *                  'g' or 'u' (to denote group/user) and # is the actual
 *                  id
 * callback         Name of javascript function that results should be
 *                  processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "addmember") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $res = "";
    $nm = explode(",", $_REQUEST["new_members"]);
    for ($i=0;$i<count($nm);$i++) {
        if ($res != "") {
            $res .= "*";
        }
        $res .= process_member($nm[$i], "add");
    }
    if ($res == "") {
        $res = "error,-1,No members specified!";
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
 * Remove a contact from a group.
 * This function is called via an XMLHttpRequest object from the 
 * javascript on the page. Hence it returns XML rather than a normal
 * page
 * do=delmember
 * Required Paramters
 * group_id         Group to delete contact from
 * old_members      Comma seperated list of member_id's to remove
 *                  member_ids should be in the form t# where t is either
 *                  'g' or 'u' (to denote group/user) and # is the actual
 *                  id
 * callback         Name of javascript function that results should be
 *                  processed by.
 ********************************************************************/
} else if ($_REQUEST["do"] == "delmember") {
    page_edit_requires(AUTH_ADMINISTRATOR);
    $res = "";
    $nm = explode(",", $_REQUEST["old_members"]);
    for ($i=0;$i<count($nm);$i++) {
        if ($res != "") {
            $res .= "*";
        }
        $res .= process_member($nm[$i], "del");
    }
    if ($res == "") {
        $res = "error,-1,No members specified!";
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
display_group_list();

?>
