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

ccs_menu_bottom_add(array(mk_menu_item("Configuration Status", "/cfengine/",
    AUTH_ADMINISTRATOR),
    mk_menu_item("Manage CFengine Inputs", "/cfengine/inputs")
    ));

/* Send push requests */
if (isset($_POST["update"])) {
    $p = array();
    page_edit_requires(AUTH_ADMINISTRATOR);
    $hosts = array_keys($_POST["update"]);
    array_push($p, $hosts);
    $params = array();
    if (isset($_POST["dist_upgrade"])) {
        $params[] = "-Ddist_upgrade";
    }
    if (isset($_POST["delay_restart"])) {
        $params[] = "-s";
    }
    if (isset($_POST["classes"]) && $_POST["classes"]!="") {
        $c = explode(",", $_POST["classes"]);
        foreach ($c as $classname) {
            $params[] = "-D$classname";
        }
    }
    if ($params != array()) {
        array_push($p, $params);
    }
    do_xmlrpc("pushConfig", $p);
}

/* Assign common information */
$smarty->assign("sheets", "/css/cfengine.css");
$smarty->assign("scripts", "/js/cfengine.js");

/* Get the information from the server */
if ($_REQUEST["action"] == "inputs") {
    /* Display input configuration */

}

/* Default is to show configuration status */
$logs = do_xmlrpc("getCfRunLogs", array());
ksort($logs);
$smarty->assign("cfrunLogs", $logs);

if (isAjaxRequest()) {
    display_page("cfengine.tpl");
} else {
    display_page("cfenginePage.tpl");
}
?>
