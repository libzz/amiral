<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
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
require("ccs_init.php");

/* Assign common information */
$smarty->assign("sheets", array("/css/templateStatus.css", 
    "/css/configBrowser.css"));
$smarty->assign("path", explode("/", $_REQUEST["path"]));
 
/* Check for template generation requests */
if (isset($_REQUEST["function"])) {
    if ($_REQUEST["function"]=="generate") {
        $rv = do_xmlrpc("generateTemplate", array());
        header("Location: /configs/status/" . urlencode($rv));
    } else if ($_REQUEST["function"]=="status") {
        $key = stripslashes($_REQUEST["statsKey"]);
        $stats = do_xmlrpc("getTemplateStatus", array($key), $xmlrpconn, 
            TRUE, FALSE);
        if (xmlrpc_has_error($stats)) {
            $smarty->assign("percent", 0);
            $smarty->assign("statusText", "ERROR: " . 
                xmlrpc_error_string($stats));    
            $smarty->assign("error", 1);
            if (isAjaxRequest()) {
                display_page("templateStatusUpdate.tpl");
            } else {
                display_page("templateStatus.tpl");
            }
            exit;
        }
        $smarty->assign("stats", $stats);
        $smarty->assign("statsKey", urlencode($key));
        $smarty->assign("scripts", array("/js/templateStatus.js"));
        /* The progress is made up of 50% for the startup phase, which is 
         * controlled by the setupProgress variable. This phase exists until
         * the generated value goes to > 0. Then the remaining 50% is taken
         * up by the number of templates have been generated. Once the
         * finished variable is set to > 0 generation has completed.
         */
        $smarty->assign("stats", $stats);
        $total = $stats["planned"]["total"];
        if ($stats["generating"] > 0 && $total>0) {
            $success=0;
            $fails=0;
            $errors = array();
            foreach ($stats["generated"]["hosts"] as $host=>$templates) {
                foreach ($templates as $name=>$info) {
                    if ($name == "initiated" || $name=="finished" || 
                            $name=="error") {
                        continue;
                    }
                    if ($info["error"]=="") {
                        $success++;
                    } else {
                        $fails++;
                        $errors["hosts/$host/$name"] = $info["error"];
                    }
                }
            }
            foreach ($stats["generated"]["network"] as $template=>$info) {
                if ($info["error"]=="") {
                    $success++;
                } else {
                    $fails++;
                    $errors[$template] = $info["error"];
                }
            }
            $smarty->assign("errors", $errors);
            $stext = "$success/$total templates generated successfully, " .
                "$fails failures";
            if ($stats["finished"] > 0) {
                $skipped = $total - $success;
                if ($skipped > 0) {
                    $stext .= ", $skipped disabled";
                }
                $percent = 100;
                $time = $stats["finished"] - $stats["initiated"];
                $stext .= sprintf(". Generation took: %0.0f seconds", $time);
                $smarty->assign("revision", $stats["revision"]);
                $p = array("inputs");
                if ($stats["revision"]!=-1) {
                    if ($stats["revision"] != -1) {
                        array_push($p, $stats["revision"]);
                        $smarty->assign("keeprev", 1);
                    }
                    $r = do_xmlrpc("viewConfigAtPath", $p);
                    $smarty->assign("revision", $r[0]);
                } else {
                    $r = do_xmlrpc("viewConfigAtPath", $p);
                }
                $smarty->assign("path", "inputs");
                $smarty->assign("entries", $r[1]);
                    
            } else {
                $percent = ((int)((($success+$fails) / $total)*100))/2+50;
                // Don't let it finish this way, only go to 99% until we
                // receive the explicit finish notification
                if ($percent == 100) {
                    $percent = 99;
                }
            }
        } else {
            if($stats["finished"] > 0) {
                $serror = $stats["error"];
                $stext = "";
                $percent = 0;
            } else {
                $serror = "";
                $stext = "Initialising templates...";
                $percent = $stats["setupProgress"]/2;
            }
        }
        $smarty->assign("statusError", $serror);
        $smarty->assign("percent", $percent);
        $smarty->assign("statusText", $stext);    
        if (isAjaxRequest()) {
            display_page("templateStatusUpdate.tpl");
        } else {
            display_page("templateStatus.tpl");
        }
        exit;
    }
}

/* All other requests are to display information on config files */

/* Get the information from the server  */
$p = array($_REQUEST["path"]);
if (isset($_REQUEST["rev"]) && $_REQUEST["rev"]!="") {
    array_push($p, $_REQUEST["rev"]);
    $smarty->assign("keeprev", 1);
} else {
    array_push($p, NULL);
}
if (isset($_REQUEST["order"])) {
    array_push($p, $_REQUEST["order"]);
    $smarty->assign("order", $_REQUEST["order"]);
    if (isset($_REQUEST["desc"])) {
        array_push($p, $_REQUEST["desc"]);
        $smarty->assign("desc", $_REQUEST["desc"]);
    } else {
        $smarty->assign("desc", 0);
    }
} else {
    array_push($p, "date");
    $smarty->assign("order", "date");
    $smarty->assign("desc", 0);
}
$r = do_xmlrpc("viewConfigAtPath", $p);
$rev = $r[0];
$entries = $r[1];
$smarty->assign("revision", $rev);

if (count($entries)==1 && array_key_exists("contents", $entries[0])) {
    /* Single File */
    $smarty->assign("file", $entries[0]);
    if (isAjaxRequest()) {
        display_page("configBrowser.tpl");
    } else {
        display_page("configBrowserPage.tpl");
    }
} else {
    /* Directory Listing */
    $smarty->assign("entries", $entries);
    if (isAjaxRequest()) {
        display_page("configListing.tpl");
    } else {
        display_page("configListingPage.tpl");
    }
}
?>
