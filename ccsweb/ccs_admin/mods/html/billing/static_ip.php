<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Billing - Customer Management
 * 
 * Author:       Chris Browning <chris@rurallink.co.nz>
 * Version:      $Id: customer.php 1604 2007-07-25 04:55:06Z ckb6 $
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
require("billing/billing_common.php");

function get_static_pools()
{
    $cid = do_xmlrpc("getStaticIPPoolStats", array(),
    	$xmlrpc_conn, TRUE, FALSE);
	if (xmlrpc_has_error($cid)) {
		ccs_notice("Could not fetch Static Pools: ".xmlrpc_error_string($cid));
		return array();
	} else {
		return $cid;
	}
}

function display_static_pool($pool_id)
{
	global $smarty;
    $cid = do_xmlrpc("getStaticIPPool", array($pool_id),
    	$xmlrpc_conn, TRUE, FALSE);
	if (xmlrpc_has_error($cid)) {
		ccs_notice("Could not fetch Static Pool: ".xmlrpc_error_string($cid));
		display_static_pools();
	} else {
		$smarty->assign("pool", $cid);
		display_page("mods/billing/pool.tpl");
	}
}
function display_static_pools()
{
	global $smarty;
	$pools = get_static_pools();
    $smarty->assign("pools", $pools);
    display_page("mods/billing/static_ip.tpl");
}
/********************************************************************
 ********************************************************************/
if ($_REQUEST["do"] == "show") {
    /* Check administrator privs */
    page_edit_requires(AUTH_HELPDESK);
	$pool_id = $_REQUEST['pool_id'];
	display_static_pool($pool_id);
} else if ($_REQUEST["do"] == "add") {
    /* Check administrator privs */
    page_edit_requires(AUTH_ADMINISTRATOR);
	if ($_REQUEST["process"] == "yes"){
		$cidr = $_REQUEST['cidr'];
		$description = $_REQUEST['description'];
 	   	$cid = do_xmlrpc("addStaticIPPool", array($cidr, $description),
	    	$xmlrpc_conn, TRUE, FALSE);
		if (xmlrpc_has_error($cid)) {
			ccs_notice("Could add IP pool: ".xmlrpc_error_string($cid));
    		display_page("mods/billing/static_ipform.tpl");
		} else {
			ccs_notice("Sucsessfully Added static pool.");
			display_static_pools();
		}
	}
	else
    	display_page("mods/billing/static_ipform.tpl");
} else if ($_REQUEST["do"] == "del") {
	if ($_REQUEST["confirm"] == "yes"){
		$pool_id = $_REQUEST['pool_id'];
 	   	$cid = do_xmlrpc("delStaticIPPool", array($pool_id),
	    	$xmlrpc_conn, TRUE, FALSE);
		if (xmlrpc_has_error($cid)) {
			ccs_notice("Could del IP pool: ".xmlrpc_error_string($cid));
		} else {
			ccs_notice("Sucsessfully removed static pool.");
		}
			display_static_pools();
	}else{
    	$smarty->assign("pool_id", $_REQUEST['pool_id']);
    	$smarty->assign("cidr", $_REQUEST['cidr']);
    	$smarty->assign("description", $_REQUEST['description']);
    	display_page("mods/billing/static_ipdel.tpl");
	}
} else if ($_REQUEST["do"] == "assign") {
	$login_id = $_REQUEST['login_id'];
	$customer_id = $_REQUEST['customer_id'];
	$pool_id = $_REQUEST['pool_id'];
	if ($_REQUEST["process"] == "yes"){
			$cid = do_xmlrpc("assignStaticIP", array($login_id, $pool_id),
				$xmlrpc_conn, TRUE, FALSE);
			if (xmlrpc_has_error($cid)) {
				ccs_notice("Could assign static IP: ".xmlrpc_error_string($cid));
			} else {
				ccs_notice("Sucsessfully assigned static IP.");
			}
			if ($_REQUEST['customer_id']){
				assign_customer($_REQUEST["customer_id"]);
				$smarty->assign("connection_methods", $connection_methods);
				$smarty->assign("customer_types", $customer_types);
				$smarty->assign("action", "edit");
			
				/* Show the add form */
				assign_plan_list();
				display_page("mods/billing/customerform.tpl");
			}else
				display_static_pools();
	}else{
				$pools = get_static_pools();
				$smarty->assign("pools", $pools);
				$smarty->assign("login_id", $login_id);
				$smarty->assign("customer_id", $customer_id);
				display_page("mods/billing/static_ipassign.tpl");
	}
} else if ($_REQUEST["do"] == "free") {
	$login_id = $_REQUEST['login_id'];
	$cid = do_xmlrpc("unassignStaticIP", array($login_id),
		$xmlrpc_conn, TRUE, FALSE);
	if (xmlrpc_has_error($cid)) {
		ccs_notice("Could free static IP: ".xmlrpc_error_string($cid));
	} else {
		ccs_notice("Sucsessfully freed static IP.");
	}
	if ($_REQUEST['customer_id']){
	    assign_customer($_REQUEST["customer_id"]);
	    $smarty->assign("connection_methods", $connection_methods);
	    $smarty->assign("customer_types", $customer_types);
	    $smarty->assign("action", "edit");
	
	    /* Show the add form */
		assign_plan_list();
	    display_page("mods/billing/customerform.tpl");
	}else
		display_static_pools();
} else 
	display_static_pools();
?>
