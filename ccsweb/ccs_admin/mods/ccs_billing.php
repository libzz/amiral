<?php
 /* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Index Page for billing
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 *				 Ivan Meredith <ivan@ivan.net.nz>
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
define(CCS_BILLING_VERSION, "0.1");

$menus = array();
$menus["top"] = array(mk_menu_item("Billing","/mods/billing/", AUTH_HELPDESK));

register_ccs_module("billing", CCS_BILLING_VERSION, 
    "Provides things", 
    $pages, $menus);
    
?>
