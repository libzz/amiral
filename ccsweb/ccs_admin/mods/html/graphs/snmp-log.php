<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Graph manipulation user interface
 *
 * Author:       Chris Browning <ckb6@cs.waikato.ac.nz>
 * Version:      $Id: hosteditform.tpl 1067 2006-10-05 22:55:17Z mglb1 $
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
require_once("ccs_init.php");
/* Setup the bottom menu */
ccs_menu_bottom_add(array(mk_menu_item("Graph Viewer", "/mods/graphs/graphs.php"),
    mk_menu_item("SNMP Discovery log", "/mods/graphs/snmp-log.php"),
    mk_menu_item("Configure Graphs", "/mods/graphs/config-graphs.php")
    ));

//This function fetches the logs
//It also displays the page
function display_log()
{
    global $smarty, $xmlrpc_conn;
    $entries = do_xmlrpc("getSnmpLogs", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($entries)) {
        ccs_notice("Could not log's: " .
            xmlrpc_error_string($entries));
        $entries = array();
    }
    $instrs = do_xmlrpc("getSnmpInstructions", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($instrs)) {
        ccs_notice("Could not get instructions: " .
            xmlrpc_error_string($instrs));
        $instrs = array();
    }    
    $counttimer = do_xmlrpc("getSnmpState", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($counttimer)) {
        ccs_notice("Could not get state: " .
            xmlrpc_error_string($counttimer));
        $counttimer = array();
    }       
    $state = $counttimer[0];
    $counttimer = $counttimer[1];
    $smarty->assign("counttimer", $counttimer);
    $smarty->assign("countstate", $state);
    $smarty->assign("instrs", $instrs);
    $smarty->assign("entries", $entries);
    $smarty->assign("scripts", array("snmp-log.js"));
    display_page("mods/graphs/snmp-log.tpl");
}

/********************************************************************
 * Delete a row from the table
 * do=delete
 * Required Parameters
 *  host_id
 *  class_id
 *  num
 ********************************************************************/
if ($_REQUEST["do"] == "delete") {
    if ($_REQUEST["confirm"] == "yes"){
        $p = array($_REQUEST["host_id"],$_REQUEST["class_id"],$_REQUEST["num"]);
        $error = do_xmlrpc("snmpDelete", $p, $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($error)) {
            ccs_notice("Could not delete entry: " .
                xmlrpc_error_string($error));
        }
        display_log();
    }else{
        $smarty->assign("host_id", $_REQUEST["host_id"]);
        $smarty->assign("class_id", $_REQUEST["class_id"]);
        $smarty->assign("num", $_REQUEST["num"]);
        $smarty->assign("host_name", $_REQUEST["host_name"]);
        $smarty->assign("class_name", $_REQUEST["class_name"]);
        display_page("mods/graphs/snmp-del.tpl");
    }
/********************************************************************
 * Delete a host from the table
 * do=deletehost
 * Required Parameters
 *  host_id
 ********************************************************************/    
}else if ($_REQUEST["do"] == "deletehost") {
    if ($_REQUEST["confirm"] == "yes"){
        $p = array($_REQUEST["host_id"]);
        $error = do_xmlrpc("snmpDeleteHost", $p, $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($error)) {
            ccs_notice("Could not delete host's entries: " .
                xmlrpc_error_string($error));
        }
        display_log();
    }else{
        $smarty->assign("host_id", $_REQUEST["host_id"]);
        $smarty->assign("host_name", $_REQUEST["host_name"]);
        display_page("mods/graphs/snmp-del.tpl");
    }

/********************************************************************
 * Flush/empty the entire table
 * do=flush
 ********************************************************************/    
}else if ($_REQUEST["do"] == "flush") {
    if ($_REQUEST["confirm"] == "yes"){
        $error = do_xmlrpc("snmpFlush", array(), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($error)) {
            ccs_notice("Could not flush table: " .
                xmlrpc_error_string($error));
        }
        display_log();
    }else{
        display_page("mods/graphs/snmp-del.tpl");
    }
}else if ($_REQUEST["do"] == "scanhost") {
    $error = do_xmlrpc("addSnmpInstruction", array($_REQUEST["host_id"],3), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($error)) {
        ccs_notice("Could not flush table: " .
            xmlrpc_error_string($error));
    }
    display_log();
}else{
    display_log();
}
?>
