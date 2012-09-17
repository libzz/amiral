<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Provides an interface to the CRCnet configuration system via XML-RPC calls
 * to the CRCnet Configuration System Daemon.
 *
 * This file handles the XML-RPC interface to the daemon 
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

/* This uses the xmlrpc-epi-php extension if it is available, otherwise it
 * falls back to the usefull.in XMLRPC class that is included in the tarball.
 */
if (function_exists("xmlrpc_decode") && 0) {
    // This is take AGES to do requests, so disabled for now...
    require_once("xmlrpc-epi.php");
} else {
    require_once("xmlrpc-uic.php");
}

$rpctimes = array();

function start_xmlrpc()
{
    global $xmlrpc_conn, $networks;

    if (!$xmlrpc_conn) {
        $network = $networks[$_SESSION["network"]];
        $xmlrpc_conn = init_xmlrpc($network["host"], $network["port"], 
            $network["path"], $network["cert"]);
    }

    return $xmlrpc_conn;
}

function check_server_version($conn)
{
    /* If we have a valid session and then assume the server is good */
    if (isset($_SESSION["ccsd_session"])) {
        return TRUE;
    }

    /* Check server ident string matches what we expect */
    $r = _do_xmlrpc($conn, "getVersion", array());
    if (xmlrpc_has_error($r)) {
        /* Could not initialise connection */
        ccs_warning(xmlrpc_error_string($r));
        return FALSE;
    } else {
        $ident = _extract_xmlrpc_result($r);
        if (strncasecmp($ident, "CRCnet Configuration System Daemon",34)==0) {
            return TRUE;
        }
        ccs_warning("Invalid server: " . $ident);
    }
    return FALSE;
}

function do_xmlrpc($func, $params, $connection=NULL, $auth=TRUE, 
    $err_fatal=TRUE)
{
    
    global $xmlrpc_conn, $smarty, $rpctimes, $networks;
    
    $pstart = microtime_float();
    
    if ($connection == NULL) {
        $conn = $xmlrpc_conn;
        if ($conn == NULL) {
            $conn = start_xmlrpc();
        }
        if ($conn == NULL) {
            cancelIfAjaxRequest();
            $smarty->assign("errMsg", "Could not connect to configuration " .
                "server: https://" . $networks[$_SESSION["network"]]["host"] .
                ":" . $networks[$_SESSION["network"]]["port"] . 
                $networks[$_SESSION["network"]]["path"]);
            display_page("welcome.tpl");
            exit;
        }
    } else {
        $conn = $connection;
    }
    if ($auth) {
        $sauth = $_SESSION["sauth"];
        $params = array_merge(array($sauth), $params);
    }

    $r = _do_xmlrpc($conn, $func, $params);
    if (xmlrpc_has_error($r)) {
        $errMsg = xmlrpc_error_string($r);
        $smarty->assign("errMsg", "XMLRPC call to \"$func\" returned error: " .
		    $errMsg);
        if ($err_fatal) {
            display_page("error.tpl", 1);
            exit;
        }
        return $r;
    }
    $pend = microtime_float();
    $elapsed = $pend - $pstart;
    $rpctimes[] = array("function"=>$func,"time"=>$elapsed);

    return _extract_xmlrpc_result($r);

}
?>
