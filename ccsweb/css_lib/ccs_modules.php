<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Controls the registration and handling of interface extension modules
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
$ccs_modules = array();

/* Each module is represented by an entry in the above array. Each entry is
 * as class ccs_module created by the register_module function.
 */
class ccs_module {

    var $name;
    var $version;
    var $description;
    var $pages;
    var $menus;
    
}

/* Register a new module */
function register_ccs_module($name, $version, $desc, $pages, $menus) {

    global $ccs_modules;
    
    $mod = new ccs_module();
    $mod->name = $name;
    $mod->version = $version;
    $mod->desc = $desc;
    $mod->pages = $pages;
    $mod->menus = $menus;

    $ccs_modules[$name] = $mod;

    if (array_key_exists("top", $menus)) {
        ccs_menu_top_add($menus["top"]);
    }
    
    ccs_debug("$name Module registered.");

}

?>
