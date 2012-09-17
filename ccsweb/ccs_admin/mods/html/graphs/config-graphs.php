<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Graph manipulation user interface
 *
 * Author:       Chris Browning <ckb6@cs.waikato.ac.nz>
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
require_once("ccs_init.php");
/* Setup the bottom menu */
ccs_menu_bottom_add(array(mk_menu_item("Graph Viewer", "/mods/graphs/graphs.php"),
    mk_menu_item("SNMP Discovery log", "/mods/graphs/snmp-log.php"),
    mk_menu_item("Configure Graphs", "/mods/graphs/config-graphs.php")
    ));

//This function fetches the groups
//It also displays the page
function display_groups()
{
    global $smarty, $xmlrpc_conn;
    $entries = do_xmlrpc("getGraphGroups", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($entries)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($entries));
        $entries = array();
    }
    $smarty->assign("entries", $entries);
    display_page("mods/graphs/config-graphs.tpl");
}

//This function fetches a group
//It also displays the page
function display_group()
{
    global $smarty, $xmlrpc_conn;
    $entries = do_xmlrpc("getGraphTypes", array($_REQUEST["group_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($entries)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($entries));
        $entries = array();
    }
    $group = do_xmlrpc("getGraphGroup", array($_REQUEST["group_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($group)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($group));
        $group = array();
    }
 
    $smarty->assign("action", "editgroup");
    $smarty->assign("group", $group);
    $smarty->assign("group_id", $_REQUEST["group_id"]);
    $smarty->assign("entries", $entries);

    $smarty->assign("scripts", "config-group.js");
    display_page("mods/graphs/config-group.tpl");      
}

//This function fetches a graph(type)
//It also displays the page
function display_type()
{
    global $smarty, $xmlrpc_conn;
    $entries = do_xmlrpc("getGraphParts", array($_REQUEST["graph_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($entries)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($entries));
        $entries = array();
    }    
    $graph = do_xmlrpc("getGraphType", array($_REQUEST["graph_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($graph)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($graph));
        $graph = array();
    }
    
    $classes = do_xmlrpc("listClasses", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($classes)) {
        ccs_notice("Could not get classes: " .
            xmlrpc_error_string($classes));
        $classes = array();    
    }    
    $smarty->assign("action", "edittype");
    $smarty->assign("graph", $graph);
    $smarty->assign("classes", $classes);
    $smarty->assign("group_id", $_REQUEST["group_id"]);
    $smarty->assign("graph_id", $_REQUEST["graph_id"]);
    $smarty->assign("entries", $entries);
    $smarty->assign("scripts", "config-type.js");
    display_page("mods/graphs/config-type.tpl");        

}
//This function fetches variables avalible to a part
function getVars($graph_id)
{
    global $smarty, $xmlrpc_conn;
    $vars = do_xmlrpc("getGraphVars", array($graph_id), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($vars)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($vars));
        $vars = array();    
    }
    $smarty->assign("vars", $vars);
    $smarty->assign("scripts", "config-part-div.js");
}

/********************************************************************
 * Edit a groups options
 * do=editgroup
 * Required Parameters
 *  group_id
 ********************************************************************/
if ($_REQUEST["do"] == "editgroup") {
    if ($_REQUEST["process"]=="yes") {
        $part = array();
        get_if_post_modified(&$part, "group_name");
        $rv = do_xmlrpc("updateGraphGroupDetails", array($_POST["group_id"],$part),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update Group: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Group details successfully updated.");
        }
    }
    display_group();
/********************************************************************
 * Edit a graphs options
 * do=edittype
 * Required Parameters
 *  group_id
 *  graph_id
 ********************************************************************/
}else if ($_REQUEST["do"] == "edittype") {
    if ($_REQUEST["process"]=="yes") {
        $part = array();
        if ($_POST["rigid"] == "on")
            $_POST["rigid"] = 't';
        else
            $_POST["rigid"] = 'f';
        if ($_POST["auto_comment"] == "on")
            $_POST["auto_comment"] = 't';
        else
            $_POST["auto_comment"] = 'f';
        get_if_post_modified(&$part, "title");
        get_if_post_modified(&$part, "virtical_label");
        get_if_post_modified(&$part, "upper");
        get_if_post_modified(&$part, "auto_comment");
        get_if_post_modified(&$part, "rigid");
        get_if_posted(&$part, "class_id");
        $rv = do_xmlrpc("updateGraphTypeDetails", array($_POST["graph_id"],$part),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update Graph: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Graph details successfully updated.");
        }
    }
    display_type();
/********************************************************************
 * Edit a graph parts options
 * do=edittype
 * Required Parameters
 *  group_id
 *  graph_id
 *  part_id
 ********************************************************************/    
}else if ($_REQUEST["do"] == "editpart") {
    if ($_REQUEST["process"]=="yes") {
        $part = array();
        get_if_post_modified(&$part, "type");
        get_if_post_modified(&$part, "graph_order");
        get_if_posted(&$part, "varname");
        get_if_post_modified(&$part, "filename");
        get_if_post_modified(&$part, "cf");
        get_if_post_modified(&$part, "colour");
        get_if_posted(&$part, "text");
        $part["text"] = stripslashes($part["text"]);
        
        $rv = do_xmlrpc("updateGraphPartDetails", array($_POST["part_id"],$part),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update Graph part: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Graph part details successfully updated.");
        }
    }

    $part = do_xmlrpc("getGraphPart", array($_REQUEST["part_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($part)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($part));
        $part = array();    
    }
    $items = do_xmlrpc("getClassParts", array($_REQUEST["class_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($items)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($items));
        $items = array();    
    }
    getVars($_REQUEST["graph_id"]);
    $smarty->assign("action", "editpart");
    $smarty->assign("part", $part);
    $smarty->assign("items", $items);
    $smarty->assign("class_id", $_REQUEST["class_id"]);
    $smarty->assign("group_id", $_REQUEST["group_id"]);
    $smarty->assign("graph_id", $_REQUEST["graph_id"]);
    $smarty->assign("part_id", $_REQUEST["part_id"]);
    display_page("mods/graphs/config-part.tpl");   
/********************************************************************
 * Dynamicly update avaliable vars
 * do=getvars
 * Required Parameters
 *  part_id
 ********************************************************************/  
}else if ($_REQUEST["do"] == "getvars") {
    $part = do_xmlrpc("getGraphPart", array($_REQUEST["part_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($part)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($part));
        $part = array();    
    }
    $items = do_xmlrpc("getClassParts", array($_REQUEST["class_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($items)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($items));
        $items = array();    
    }    
    $part["type"] = $_REQUEST["type"];
    $smarty->assign("action", $_REQUEST["action"]);
    $smarty->assign("items", $items);
    $smarty->assign("part", $part);
    getVars($_REQUEST["graph_id"]);
    display_page("mods/graphs/config-part-div.tpl");      
/********************************************************************
 * Add a new group
 * do=newgroup
 * Required Parameters
 ********************************************************************/      
}else if ($_REQUEST["do"] == "newgroup") {
    if ($_REQUEST["process"]=="yes") {
        $part = array();
        get_if_posted(&$part, "group_name");
        $rv = do_xmlrpc("addGraphGroup", array($part),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update Group: ".xmlrpc_error_string($rv));
            $group= array("group_name"=>$_REQUEST["group_name"]);
        } else {
            ccs_notice("Group details successfully updated.");
            display_groups();
            exit;
        }
    }
    $smarty->assign("action", "newgroup");
    $smarty->assign("group", $group);
    $smarty->assign("group_id", $_REQUEST["group_id"]);
    $smarty->assign("entries", $entries);
    $smarty->assign("scripts", "config-group.js");
    display_page("mods/graphs/config-group.tpl");     
/********************************************************************
 * Add a new graph
 * do=newtype
 * Required Parameters
 *  group_id
 ********************************************************************/     
}else if ($_REQUEST["do"] == "newtype") {
    if ($_REQUEST["process"]=="yes") {
        $part = array();
        get_if_posted(&$part, "title");
        get_if_posted(&$part, "class_id");
        get_if_posted(&$part, "group_id");
        get_if_posted(&$part, "virtical_label");
        $rv = do_xmlrpc("addGraphType", array($part),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update Graph: ".xmlrpc_error_string($rv));
            
            $graph= array("title"=>$_REQUEST["title"], "class_id"=>$_REQUEST["class_id"], "virtical_label"=>$_REQUEST["virtical_label"]);
        } else {
            ccs_notice("Graph details successfully updated.");
            display_group();
            exit;            
        }
    }
    
    $classes = do_xmlrpc("listClasses", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($classes)) {
        ccs_notice("Could not get classes: " .
            xmlrpc_error_string($classes));
        $classes = array();    
    }  
    $smarty->assign("classes", $classes);
    $smarty->assign("action", "newtype");
    $smarty->assign("graph", $graph);
    $smarty->assign("group_id", $_REQUEST["group_id"]);
    $smarty->assign("graph_id", $_REQUEST["graph_id"]);
    $smarty->assign("entries", $entries);
    $smarty->assign("scripts", "config-type.js");
    display_page("mods/graphs/config-type.tpl");    
/********************************************************************
 * Add a new graph part
 * do=newtype
 * Required Parameters
 *  group_id
 *  graph_id
 ********************************************************************/     
}else if ($_REQUEST["do"] == "newpart") {    
    $smarty->assign("part", array("type"=>"DEF"));
    if ($_REQUEST["process"]=="yes") {
        $part = array();
        get_if_posted(&$part, "graph_id");
        get_if_posted(&$part, "type");
        get_if_posted(&$part, "graph_order");
        get_if_posted(&$part, "varname");
        get_if_posted(&$part, "filename");
        get_if_posted(&$part, "cf");
        get_if_posted(&$part, "colour");
        get_if_posted(&$part, "text");
        $rv = do_xmlrpc("addGraphPart", array($part),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update Graph part: ".xmlrpc_error_string($rv));
            $part= array("type"=>$_REQUEST["type"], "graph_order"=>$_REQUEST["graph_order"], "varname"=>$_REQUEST["varname"], "filename"=>$_REQUEST["filename"] , "cf"=>$_REQUEST["cf"] , "colour"=>$_REQUEST["colour"], "text"=>$_REQUEST["text"]);
            //, ""=>$_REQUEST[""])
            $smarty->assign("part", $part);
        } else {
            ccs_notice("Graph part details successfully updated.");
        }
    }
    $items = do_xmlrpc("getClassParts", array($_REQUEST["class_id"]), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($items)) {
        ccs_notice("Could not get groups: " .
            xmlrpc_error_string($items));
        $items = array();    
    }

    getVars($_REQUEST["graph_id"]);
    $smarty->assign("action", "newpart");
    $smarty->assign("items", $items);
    $smarty->assign("group_id", $_REQUEST["group_id"]);
    $smarty->assign("class_id", $_REQUEST["class_id"]);
    $smarty->assign("graph_id", $_REQUEST["graph_id"]);
    $smarty->assign("part_id", $_REQUEST["part_id"]);
    display_page("mods/graphs/config-part.tpl");       
/********************************************************************
 * Remove a graph part
 * do=deletepart
 * Required Parameters
 *  group_id
 *  graph_id
 *  part_id
 ********************************************************************/   
}else if ($_REQUEST["do"] == "deletepart") {
    if ($_REQUEST["confirm"] == "yes"){
        $p = array($_REQUEST["part_id"]);
        $error = do_xmlrpc("removeGraphPart", $p, $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($error)) {
            ccs_notice("Could not delete part: " .
                xmlrpc_error_string($error));
        }
        display_type();
    }else{
        $part = do_xmlrpc("getGraphPart", array($_REQUEST["part_id"]), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($part)) {
            ccs_notice("Could not get groups: " .
                xmlrpc_error_string($part));
            $part = array();    
        }
    
        $smarty->assign("part", $part);
        $smarty->assign("group_id", $_REQUEST["group_id"]);
        display_page("mods/graphs/config-del.tpl");
    }
/********************************************************************
 * Remove a graph
 * do=deletetype
 * Required Parameters
 *  group_id
 *  graph_id
 ********************************************************************/     
}else if ($_REQUEST["do"] == "deletetype") {
    if ($_REQUEST["confirm"] == "yes"){
        $p = array($_REQUEST["graph_id"]);
        $error = do_xmlrpc("removeGraphType", $p, $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($error)) {
            ccs_notice("Could not delete graph: " .
                xmlrpc_error_string($error));
        }
        display_group();
    }else{
        $part = do_xmlrpc("getGraphType", array($_REQUEST["graph_id"]), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($part)) {
            ccs_notice("Could not get groups: " .
                xmlrpc_error_string($part));
            $part = array();    
        }
        $classes = do_xmlrpc("getClass", array($part["class_id"]), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($classes)) {
            ccs_notice("Could not get classes: " .
                xmlrpc_error_string($classes));
            $classes = array();    
        }    

        $smarty->assign("graph", $part);
        $smarty->assign("classes", $classes[0]);
        $smarty->assign("group_id", $_REQUEST["group_id"]);
        display_page("mods/graphs/config-del.tpl");
    }
/********************************************************************
 * Remove a group
 * do=deletegroup
 * Required Parameters
 *  group_id
 ********************************************************************/      
}else if ($_REQUEST["do"] == "deletegroup") {
    if ($_REQUEST["confirm"] == "yes"){
        $p = array($_REQUEST["group_id"]);
        $error = do_xmlrpc("removeGraphGroup", $p, $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($error)) {
            ccs_notice("Could not delete part: " .
                xmlrpc_error_string($error));
        }
        display_groups();
    }else{
        $part = do_xmlrpc("getGraphGroup", array($_REQUEST["group_id"]), $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($part)) {
            ccs_notice("Could not get group: " .
                xmlrpc_error_string($part));
            $part = array();    
        }
    
        $smarty->assign("group", $part);
        $smarty->assign("group_id", $_REQUEST["group_id"]);
        display_page("mods/graphs/config-del.tpl");
    }    
/********************************************************************
 * Default to displaying the groups
 ********************************************************************/      
}else{
    display_groups();
}
?>
