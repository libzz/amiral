<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Controls the display of menus in the interface
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
    
/* Menu Variables */
$ccs_menus = array();

/* There are 2 main menu areas:
 *
 * Top: should contain links to high-level areas of interest
 * Bottom: should contain links to pages within the current area of interest
 * Bottom Inc: Should contain pathname to a template to include after the 
 *              bottom menu.
 */
$ccs_menus["top"] = array();
$ccs_menus["top_funcs"] = array();
$ccs_menus["bottom"] = array();
$ccs_menus["bottom_inc"] = array();

/* Add a new menu to the top menu */
function ccs_menu_top_add($menu) {

    global $ccs_menus;
    
    // XXX: Validate incoming menus here 
    
    $ccs_menus["top"] = array_merge($menu, $ccs_menus["top"]);

}
function ccs_menu_top_funcs_add($menu) {

    global $ccs_menus;
    
    // XXX: Validate incoming menus here 
    
    $ccs_menus["top_funcs"] = array_merge($menu, $ccs_menus["top_funcs"]);

}

/* Add a new menu to the bottom menu */
function ccs_menu_bottom_add($menu) {

    global $ccs_menus;
    
    // XXX: Validate incoming menus here 
    
    $ccs_menus["bottom"] = array_merge($menu, $ccs_menus["bottom"]);

}

/* Add a new include file to the bottom menu */
function ccs_menu_bottom_include($path) {

    global $ccs_menus;
    
    // XXX: Validate incoming menus here 
    
    $ccs_menus["bottom_inc"] = array_merge($path, $ccs_menus["bottom_inc"]);

}

function check_menu_auth($item) {
    global $session_state;

    /* Check that the session is valid */
    if ($session_state == SESSION_NONE) {
        return false;
    }
    if (user_in_group($_SESSION["ccsd_contact_id"], $item["group"])) {
        return true;
    }
    echo "<!-- ${_SESSION["ccsd_username"]} not in ${item["group"]} for ${item["label"]}-->\n";
    return false;
}
function menu_sort($a, $b) {
    if ($a["order"] == $b["order"]) {
        return strcmp($a["label"], $b["label"]);
    }
    return $a["order"] - $b["order"];
}
/* Return the top menu */
function ccs_menu_get_top() {    
    global $ccs_menus;
    $tmp = array_filter($ccs_menus["top"], "check_menu_auth");
    usort($tmp, "menu_sort");
    return $tmp;
}
function ccs_menu_get_top_funcs() {    
    global $ccs_menus;
    $tmp = array_filter($ccs_menus["top_funcs"], "check_menu_auth");
    usort($tmp, "menu_sort");
    return $tmp;
}
/* Return the bottom menu */
function ccs_menu_get_bottom() {    
    global $ccs_menus;
    $tmp = array_filter($ccs_menus["bottom"], "check_menu_auth");
    usort($tmp, "menu_sort");
    return $tmp;
}
function ccs_menu_get_bottominc() { 
    global $ccs_menus;
    return $ccs_menus["bottom_inc"];
}

/* Helper function to create a menu item */
function mk_menu_item($label, $href, $group=AUTH_USER, $order=100) {
    return array("label"=>$label, "href"=>$href, "group"=>$group, 
        "order"=>$order);
}
?>
