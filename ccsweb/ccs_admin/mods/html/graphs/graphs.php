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

//This function fetches and manipulates all data for the interface
//but the graphs themselves which is done before this is call.
//It also displays the page
function display_select_graph()
{
    global $smarty, $xmlrpc_conn;
    
    $host_id = $_REQUEST["host_id"];
    if ($_REQUEST["main"] != "host" && $_REQUEST["main"] != "")
        $host_id = -1;
    $e = do_xmlrpc("getEveryThing", array($host_id), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($e)) {
        ccs_notice("Could not data from server: " .
            xmlrpc_error_string($e));
        $e = array();
    }
    $hosts = $e[0];
    $links = $e[1];
    $groups = $e[2];
    $targets = $e[3];
    $times = $e[4];
    
    //Create arrays for host list
    //$ids = array();
    //$names = array();
    //$c = 0;
    //foreach ($hosts as $idx=>$host) {
    //    $ids[$c] = $host["host_id"];
    //    $names[$c] = $host["host_name"];
     //   $c++;
    //}

    //Create arrays for link list
    $lids = array();
    $lnames = array();
    $c = 0;
    foreach ($links as $idx=>$link) {
        $lids[$c] = $link["link_id"];
        $lnames[$c] = $link["description"];
        $c++;
    }
            
        
    //Create arrays for target list
//    $tids = array();
//    $tnames = array();
//    $c = 0;
//    foreach ($targets as $idx=>$target) {
//        $tids[$c] = "{$target["host_name"]}-{$target["graph_id"]}-{$target["num"]}-{$target["ip_address"]}-{$target["description"]}";
//        $tnames[$c] = "{$target["host_name"]} - {$target["title"]} - {$target["description"]} - {$target["ip_address"]}";
//        $c++;
//    }
//    
//    if(!isset($_REQUEST["time_id"])){
//        foreach ($times as $idx=>$t) {
//            if ($t["name"] == "Day"){
//                $smarty->assign("time_id", $t["time_id"]);
//            }
//        }
//    }

    $smarty->assign("times", $times);
    $smarty->assign("groups", $groups);
    //$smarty->assign("target_ids", $tids);
    //$smarty->assign("host_ids", $ids);
    $smarty->assign("hosts", $hosts);
    $smarty->assign("link_ids", $lids);
    //$smarty->assign("target_names", $tnames);
    //$smarty->assign("host_names", $names);
    $smarty->assign("link_names", $lnames);
    $smarty->assign("scripts", array("graphs.js"));
    display_page("mods/graphs/index.tpl");
}

/********************************************************************
 * Get a list graphs that is valid for a host
 * do=listgraphs
 * Required Parameters
 *  host_id
 ********************************************************************/
if ($_REQUEST["do"] == "listgraphs") {
    $p = array($_REQUEST["host_id"]);
    $groups = do_xmlrpc("getHostGraphs", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($group)) {
        ccs_notice("Could not retrieve host's graphs: " .
            xmlrpc_error_string($group));
        $groups = array();
    }
 
    $smarty->assign("host_id", $_REQUEST["host_id"]);
    $smarty->assign("group_id", $_REQUEST["group_id"]);
    $smarty->assign("groups", $groups);
    /* Show the form */
    $smarty->assign("sheets", array("host.css"));
    $smarty->assign("scripts", array("host.js"));
    display_page("mods/graphs/graphs-list.tpl");
/********************************************************************
 * Get the graphs for display
 * do=listgraphs
 * Required Parameters
 *  main
 * Optional Parameters
 *  mirror
 *  link_id
 *  host_id
 *  graph_id
 *  group_id
 *  target_id
 ********************************************************************/    
}else if ($_REQUEST["do"] == "getgraph") {
    if ($_REQUEST["main"] == "host"){
        $mirror = 'f';
        if ($_REQUEST["mirror"] == "on")
            $mirror = 't';
        $p = array($_REQUEST["host_id"], $_REQUEST["group_id"], $mirror);
        $e = do_xmlrpc("getGraphs", $p, $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($e)) {
            ccs_notice("Could not retrieve host: " .
                xmlrpc_error_string($e));
            $e = array();
        }
        $server = $e[0];
        $vgraphs = $e[1];
    }else if ($_REQUEST["main"] == "link"){
        $p = array($_REQUEST["link_id"], $_REQUEST["group_id"]);
        $e = do_xmlrpc("getLinkGraphs", $p, $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($e)) {
            ccs_notice("Could not retrieve host: " .
                xmlrpc_error_string($e));
            $e = array();
        }
        $server = $e[0];
        $vgraphs = $e[1];
    }else if ($_REQUEST["main"] == "target"){
        $e = do_xmlrpc("getGraphserver", array(), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($e)) {
            ccs_notice("Could not retrieve graghserver: " .
                xmlrpc_error_string($e));
            $e = array();
        }
        $server = $e;
        if ($_REQUEST["target_id"] != ''){
            list($host_name, $graph_id, $num, $ip_address,$description) = split("-",$_REQUEST["target_id"],5);
            $vgraphs = array(array("host_name"=>$host_name, "graph_id"=>$graph_id, "num"=>$num, "ip_address"=>$ip_address, "description"=>$description));
        }else
            $vgraphs = array();
        
    }else{
        $vgraphs = array();
    }

    $smarty->assign("server",  $server);
    $smarty->assign("mirror",  $_REQUEST["mirror"]);
    $smarty->assign("force",  $_REQUEST["force"]);
    $smarty->assign("main",  $_REQUEST["main"]);
    $smarty->assign("host_id", $_REQUEST["host_id"]);
    $smarty->assign("group_id", $_REQUEST["group_id"]);
    $smarty->assign("link_id", $_REQUEST["link_id"]);
    $smarty->assign("target_id", $_REQUEST["target_id"]);
    $smarty->assign("time_id", $_REQUEST["time_id"]);
    $smarty->assign("vgraphs", $vgraphs);
    $smarty->assign("num", $_REQUEST["num"]);
    $smarty->assign("sheets", array("graphs.css"));
    $smarty->assign("scripts", array("graphs.js"));
    display_select_graph();
     
}else{
    display_select_graph();
}
?>
