<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Billing - Plan Management
 * 
 * Author:       Matt Brown <matt@crc.net.nz>
				 Ivan Meredith <ivan@ivan.net.nz>
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
require("billing/billing_common.php");

function get_posted_plan()
{
    $plan = array();
    get_if_posted(&$plan, "plan_id");
    get_if_posted(&$plan, "plan_name");
    get_if_posted(&$plan, "description");
    get_if_posted(&$plan, "price");
    get_if_posted(&$plan, "radius_plan");
    get_if_posted(&$plan, "included_mb");
    get_if_posted(&$plan, "cap_period");
    get_if_posted(&$plan, "cap_action");
    get_if_posted(&$plan, "cap_param");
    get_if_posted(&$plan, "cap_price");
    return $plan;
}

function get_radius_plans()
{
    global $xmlrpc_conn;

    $radius_plans = do_xmlrpc("getRadiusPlans", array(), $xmlrpc_conn, True, False);

    return $radius_plans;
}

function get_plan($plan_id)
{
    global $xmlrpc_conn;

    $plan = do_xmlrpc("getPlan", array($plan_id), $xmlrpc_conn, True, False);

    return $plan;
}
 
function assign_plan($plan_id)
{
    global $smarty;

    $plan = get_plan($plan_id);
    
    $smarty->assign("plan", $plan[0]);
    return $plan;
}


if (!isset($_REQUEST["do"]) || $_REQUEST["do"] == "") {
	displayPlanList();
}

if ($_REQUEST["do"] == "delete"){
	page_edit_requires(AUTH_HELPDESK);

	if ($_REQUEST["confirm"] != "yes") {
		assign_plan($_REQUEST["plan_id"]);
		display_page("mods/billing/plandel.tpl");
        
	} else {
        /* Delete plan */
        $rv = do_xmlrpc("removePlan", array($_REQUEST["plan"]),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not delete plan: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Plan successfully deleted!");
        }
        /* Display plan list */
        displayPlanList();
    }
} else if($_REQUEST["do"] == "add" || $_REQUEST["do"] == "edit"){
    page_edit_requires(AUTH_HELPDESK);
    $do = $_REQUEST["do"];
    if(isset($_REQUEST["process"]) && $_REQUEST["process"] == "yes"){
        $plan = get_posted_plan();
        $res = do_xmlrpc("${do}Plan", array($plan), $xmlrpc_conn);

        if(xmlrpc_has_error($res)) {
            ccs_notice("Could not $do plan: ".xmlrpc_error_string($res));
            $smarty->assign("plan", $plan);
            $smarty->assign("action", $do);
            display_page("mods/billing/planaddform.tpl");
        } else {
            displayPLanList();
        }
    } else {
        $smarty->assign("action", $do);
        $smarty->assign("radius_plans", get_radius_plans());
        if($do == "edit"){
            assign_plan($_REQUEST["plan_id"]);
        }
        display_page("mods/billing/planaddform.tpl");
    }
}
        

            
