<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Authentication Display Interface - Common Functions 
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
ccs_menu_bottom_add(array(mk_menu_item("Users", "/mods/contact/user.php"),
    mk_menu_item("Groups", "/mods/contact/group.php")));


/* Retrieve a contact from the server and assign it to smarty */
function get_contact($contact_id) 
{
    
    global $xmlrpc_conn;
    $contact = do_xmlrpc("getAdmin", array($contact_id), $xmlrpc_conn, TRUE,
        FALSE);
    if (xmlrpc_has_error($contact)) {
        ccs_notice("Could not retrieve contact: " .
            xmlrpc_error_string($contact));
        $contact = array();
    }
    $login_id = $contact[0]["login_id"];
    $rv = do_xmlrpc("getLoginState", array($login_id), $xmlrpc_conn, 
        TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $contact[0]["status"] = -1;
    } else {
        $contact[0]["status"] = $rv;
    }   

    return $contact[0];
}
function assign_contact($contact_id) 
{

    global $smarty;
    
    $contact = get_contact($contact_id);
    $smarty->assign("contact", $contact);
    return $contact;
}

/* Retrieve a contact group from the server and assign it to smarty */
function get_group($group_id) 
{
    
    global $smarty, $xmlrpc_conn;

    $group = do_xmlrpc("getGroup", array($group_id), $xmlrpc_conn, TRUE,
     FALSE);
    if (xmlrpc_has_error($group)) {
        ccs_notice("Could not retrieve group: ".xmlrpc_error_string($group));
        $group = array();
    }
    $group_id = $group["contact_group_id"];
    $rv = do_xmlrpc("getGroupMemberCount", array($group_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $group["nmembers"] = "";
    } else {
        $group["nmembers"] = $rv;
    }   
    $smarty->assign("group", $group);

    return $group;
}
/* Retrieve the list of members in a group */
function get_members($group_id) 
{
    
    global $smarty, $xmlrpc_conn;

    $members = do_xmlrpc("getMembers", array($group_id), $xmlrpc_conn, 
        TRUE, FALSE);
    if (xmlrpc_has_error($members)) {
        ccs_notice("Could not retrieve group member list: " .
            xmlrpc_error_string($members));
        $members = array();
    }
    $smarty->assign("members", $members);

    return $members;
}
/* Retrieve the list of available users */
function get_avail($group_id) 
{
    
    global $smarty, $xmlrpc_conn;

    $avail = do_xmlrpc("getAvail", array($group_id), $xmlrpc_conn,
        TRUE, FALSE);
    if (xmlrpc_has_error($avail)) {
        ccs_notice("Could not retrieve available user list: " .
            xmlrpc_error_string($avail));
        $avail = array();
    }
    $smarty->assign("avail", $avail);

    return $avail;
}

/* Retrive a contact record from the _POST array */
function get_posted_contact()
{

    $contact = array();

    if (isset($_POST["enabled"]) && $_POST["enabled"]=="yes") {
        $contact["enabled"] = 1;
    } else {
        $contact["enabled"] = 0;
    }
    get_if_posted(&$contact, "admin_id");
    get_if_posted(&$contact, "login_id");
    get_if_posted(&$contact, "username");
    get_if_posted(&$contact, "domain");
    get_if_posted(&$contact, "givenname");
    get_if_posted(&$contact, "surname");
    get_if_posted(&$contact, "email");
    get_if_posted(&$contact, "address");
    get_if_posted(&$contact, "phone");
    get_if_posted(&$contact, "newpass");
    get_if_posted(&$contact, "type");
    get_if_posted(&$contact, "public_key");
    get_if_posted(&$contact, "shell");
    
    return $contact;

}

/* Retrive a group record from the _POST array */
function get_posted_group()
{

    $group = array();

    get_if_posted(&$group, "group_id");
    get_if_posted(&$group, "group_name");
    
    return $group;

}

function contact_cmp($a, $b)
{
    if ($a["username"] == $b["username"]) {
        return 0;
    }
    return ($a["username"] > $b["username"]) ? 1 : -1;
}
function group_cmp($a, $b)
{
    if ($a["group_name"] == $b["group_name"]) {
        return 0;
    }
    return ($a["group_name"] > $b["group_name"]) ? 1 : -1;
}

?>
