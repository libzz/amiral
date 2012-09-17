<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Provides the interface for manipulating host configuration
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
define(CCS_HOST_VERSION, "1.0");

/* List of pages provided by this module */

/* List of menu entries provided by this module */
$menus = array();
$menus["top"] = array(mk_menu_item("Host Configuration","/mods/host/",
    AUTH_ADMINISTRATOR));

/* Register the damn thing */
register_ccs_module("host", CCS_ASSET_VERSION, 
    "Provides basic host configuration including interface management. " . 
    "Services are not configured in this module.",
    $pages, $menus);
    
?>
