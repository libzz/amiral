<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * rrdbot Web Interface for the CRCnet Configuration System
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

function asignDepends($class_id)
{
    global $smarty, $xmlrpc_conn;
    $p = array($class_id);
    $classes2 = do_xmlrpc("getClassDepends", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($classes2)) {
        ccs_notice("Could not retrieve rrdbot details: " .
            xmlrpc_error_string($classes2));
    }

    $ids = array();
    $names = array();
    $c = 0;
    $ids[$i] = 0;
    $names[$c] = "No Dependancy";
    $c++;
    foreach ($classes2 as $idx=>$clas) {
        $ids[$c] = $clas["class_id"];
        $names[$c] = $clas["class_name"];
        $c++;
    }
    $smarty->assign("dependsids", $ids);
    $smarty->assign("dependsnames", $names);

}
function asignTypeField()
{
    global $smarty, $xmlrpc_conn;
   
    $typeids = array();
    $typenames = array();
    $typeids[0] = "ABSOLUTE";
    $typeids[1] = "COUNTER";
    $typeids[2] = "DERIVE";
    $typeids[3] = "GAUGE";
    $typenames[0] = "ABSOLUTE";
    $typenames[1] = "COUNTER";
    $typenames[2] = "DERIVE";
    $typenames[3] = "GAUGE";
    $smarty->assign("type_ids", $typeids);
    $smarty->assign("type_names", $typenames);
}

function asignCfField()
{
    global $smarty, $xmlrpc_conn;

    $cfids = array();
    $cfnames = array();
    $cfids[0] = "AVERAGE";
    $cfids[1] = "LAST";
    $cfids[2] = "MAX";
    $cfids[3] = "MIN";
    $cfnames[0] = "AVERAGE";
    $cfnames[1] = "LAST";
    $cfnames[2] = "MAX";
    $cfnames[3] = "MIN";
    $smarty->assign("cf_ids", $cfids);
    $smarty->assign("cf_names", $cfnames);
}
/********************************************************************
 * Function to display the list of classes
 ********************************************************************/
function displayClasses()
{
    global $smarty, $xmlrpc_conn;
    $classes = do_xmlrpc("listClasses", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($classes)) {
        ccs_notice("Could not retrieve rrdbot details: " .
            xmlrpc_error_string($classes));
    }
    foreach ($classes as $key=>$clas) {
        if ($clas["depends"] != 0) {
            foreach ($classes as $clas2) {
                if ($clas2["class_id"] == $clas["depends"]){
                    $classes[$key]["depends_name"] = $clas2["class_name"];
                }
            }
        }
    }

    $smarty->assign("classes", $classes);

    $smarty->assign("service_id", $_REQUEST["service_id"]);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "rrdbot-props.js");
    display_page("mods/service/rrdbot-props.tpl");
}

/********************************************************************
 * Function to display the edit class page
 ********************************************************************/
function displayEditClass()
{
    global $smarty, $xmlrpc_conn;
    
    asignDepends($_REQUEST["class_id"]);
    asignCfField();
    $p = array($_REQUEST["class_id"]);
    $classes = do_xmlrpc("getClass", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($classes)) {
        ccs_notice("Could not retrieve rrdbot details: " .
            xmlrpc_error_string($classes));
    }
    $p = array($_REQUEST["class_id"]);
    $parts = do_xmlrpc("getClassParts", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($parts)) {
        ccs_notice("Could not retrieve rrdbot details: " .
            xmlrpc_error_string($parts));
    }
    $smarty->assign("service_id", $_REQUEST["service_id"]);
    $smarty->assign("classes", $classes);
    $smarty->assign("parts", $parts);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "rrdbot-newclass.js");
    display_page("mods/service/rrdbot-editclass.tpl");
}
/********************************************************************
 * Configure a service on a specific host
 * do=configure
 ********************************************************************/
if ($_REQUEST["do"] == "configure") {

    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "rrdbot-props.js");
    display_page("mods/service/rrdbot-hostdetails.tpl");
    
/********************************************************************
 * Edit the network wide rrdbot properties
 * do=edit
 ********************************************************************/
} else if ($_REQUEST["do"] == "edit") {
    displayClasses();   
    
/********************************************************************
 * Remove a class from the system
 * do=delete
 ********************************************************************/
} else if ($_REQUEST["do"] == "delete") {
    $p = array($_REQUEST["class_id"]);
    $classes = do_xmlrpc("removeClass", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($classes)) {
        ccs_notice("Could not remove class: " .
            xmlrpc_error_string($classes));
    } else {
        ccs_notice("Class remmoved successfully.");
    }

    displayClasses();
    
/********************************************************************
 * Edit a class's properties
 * do=editclass
 ********************************************************************/
} else if ($_REQUEST["do"] == "editclass") {
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        $clas = array();
        get_if_posted(&$clas, "class_id");
        get_if_posted(&$clas, "class_name");
        get_if_post_modified(&$clas, "poll");
        get_if_post_modified(&$clas, "interval");
        get_if_posted(&$clas, "cf");
        get_if_posted(&$clas, "archive");
        get_if_posted(&$clas, "depends");
        get_if_posted(&$clas, "upper_bound");
        get_if_posted(&$clas, "lower_bound");
        $rv = do_xmlrpc("updateClassDetails", array($_POST["class_id"], $clas),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {    
            ccs_notice("Could not update Class: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Class details successfully updated.");
        }
    }
    displayEditClass();

/********************************************************************
 * Create a new class
 * do=newclass
 ********************************************************************/
} else if ($_REQUEST["do"] == "newclass") {
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
    
        $clas = array();
        get_if_posted(&$clas, "class_id");
        get_if_posted(&$clas, "class_name");
        get_if_post_modified(&$clas, "poll");
        get_if_post_modified(&$clas, "interval");
        get_if_posted(&$clas, "cf");
        get_if_posted(&$clas, "archive");
        get_if_posted(&$clas, "key");
        get_if_posted(&$clas, "ipfromoid");
        get_if_posted(&$clas, "skip_software_loop");
        get_if_posted(&$clas, "upper_bound");
        get_if_posted(&$clas, "lower_bound");
        $rv = do_xmlrpc("addClass", array($clas),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not add Class: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Class details successfully added.");
        }
        displayClasses();
    }
    else
    {
        asignDepends(-1);
        asignCfField();
        $smarty->assign("service_id", $_REQUEST["service_id"]);
        $smarty->assign("sheets", "service.css");
        $smarty->assign("scripts", "rrdbot-newclass.js");
         display_page("mods/service/rrdbot-newclass.tpl");
    }

/********************************************************************
 * Remove a part from a class
 * do=deletepart
 ********************************************************************/    
} else if ($_REQUEST["do"] == "deletepart") {
    $p = array($_REQUEST["part_id"]);
    $classes = do_xmlrpc("removeClassPart", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($classes)) {
        ccs_notice("Could not retrieve rrdbot details: " .
            xmlrpc_error_string($classes));
    }
    displayEditClass();
    
/********************************************************************
 * Edit a Class part
 * do=editpart
 ********************************************************************/    
} else if ($_REQUEST["do"] == "editpart") {
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        $part = array();
        get_if_posted(&$part, "part_id");
        get_if_posted(&$part, "name");
        get_if_post_modified(&$part, "poll");
        get_if_post_modified(&$part, "type");
        get_if_posted(&$part, "min");
        get_if_posted(&$part, "max");
        $rv = do_xmlrpc("updateClassPartDetails", array($_POST["part_id"],$part),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not update Class pard: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Class part details successfully updated.");
        }
    }
        
    $p = array($_REQUEST["part_id"]);
    $parts = do_xmlrpc("getClassPart", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($parts)) {
        ccs_notice("Could not retrieve rrdbot details: " .
            xmlrpc_error_string($parts));
    }
    asignTypeField();
    $smarty->assign("service_id", $_REQUEST["service_id"]);
    $smarty->assign("class_id", $_REQUEST["class_id"]);
    $smarty->assign("parts", $parts);
    $smarty->assign("sheets", "service.css");
    $smarty->assign("scripts", "rrdbot-newpart.js");
    display_page("mods/service/rrdbot-editpart.tpl");
    
/********************************************************************
 * Create a new a Class part
 * do=newpart
 ********************************************************************/   
} else if ($_REQUEST["do"] == "newpart") {
    if (isset($_POST["process"]) && $_POST["process"]=="yes") {
        $part = array();
        get_if_posted(&$part, "class_id");
        get_if_posted(&$part, "part_id");
        get_if_posted(&$part, "name");
        get_if_post_modified(&$part, "poll");
        get_if_post_modified(&$part, "type");
        get_if_posted(&$part, "min");
        get_if_posted(&$part, "max");

        $rv = do_xmlrpc("addClassPart", array($part),
            $xmlrpc_conn, TRUE, FALSE);
        if (xmlrpc_has_error($rv)) {
            ccs_notice("Could not add Class part: ".xmlrpc_error_string($rv));
        } else {
            ccs_notice("Class part details successfully added.");
        }
        
        displayEditClass();
    }
    else
    {
        asignTypeField();
        $smarty->assign("class_id", $_REQUEST["class_id"]);
        $smarty->assign("service_id", $_REQUEST["service_id"]);
        $smarty->assign("sheets", "service.css");
        $smarty->assign("scripts", "rrdbot-props.js");
        $smarty->assign("scripts", "rrdbot-newpart.js");
        display_page("mods/service/rrdbot-newpart.tpl");

    }
}
?>
