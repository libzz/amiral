<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Provides an interface to the CRCnet configuration system via XML-RPC calls
 * to the CRCnet Configuration System Daemon.
 *
 * This file handles the basic setup / configuration of the PHP environment
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
function microtime_float()
{
   list($usec, $sec) = explode(" ", microtime());
   return ((float)$usec + (float)$sec);
}
$pstart = microtime_float();
$rpctimes = array();
$curltimes = array();

require_once("ccs_funcs.php");
require_once("ccs_menus.php");
require_once("ccs_modules.php");
require_once("ccs_xmlrpc.php");

/* PHP configuration */
ini_set("arg_separator.output", "&amp;");
ini_set("magic_quotes_gpc", "Off");

/* Constants */

/* Authentication state constants */
define("AUTH_OK", 0);
define("AUTH_NO_SESSION", 1);       /* Failed no session exists */
define("AUTH_INVALID_SESSION", 2);  /* Failed session exists but invalid */
define("AUTH_INSUF_SESSION", 3);    /* Failed session is ro, needs rw */
define("AUTH_INSUF_PERMS", 4);      /* Insufficient Permissions */
define("AUTH_INVALID_CRED", 5);     /* Incorrect username / password */
define("AUTH_EXPIRED", 6);          /* Session expired/timed out */
define("AUTH_INVALID_ACCOUNT", 7);  /* Wrong account type */

/* Group names to use for authentication */
define("AUTH_ADMINISTRATOR", "Administrators");
define("AUTH_WEBUSER", "Webusers");
define("AUTH_ASSET_MANAGER", "Asset Managers");
define("AUTH_USER", "Users");
define("AUTH_HELPDESK", "Helpdesk");

/* Session States */
define("SESSION_NONE", "NO");
define("SESSION_READONLY", "RO");
define("SESSION_READWRITE", "RW");

define("SESSION_REFRESH_TIME", 60*20);

/* Error handling variables */
$warning_msgs = array();
$debug_msgs = array();
$notice_msgs = array();

$bindir = dirname($_SERVER["DOCUMENT_ROOT"]) . "/bin";

/* Setup smarty */
require_once('smarty/libs/Smarty.class.php');
$smarty = new Smarty;
$smartydir = dirname($_SERVER["DOCUMENT_ROOT"]) . "/smarty";
$smarty->template_dir = $smartydir . "/templates/";
$smarty->compile_dir = $smartydir . "/templates_c/";
$smarty->config_dir = $smartydir . "/configs/";
$smarty->cache_dir = $smartydir . "/cache/";
$smarty->force_compile = 1;
$smarty->caching = 0;
$smarty->assign("do_debug", 1);

/* Setup a passthru template loader so we can do things like:
 * $smarty->display("pass:{smarty code here}")
 */
function spass_template ($tpl_name, &$tpl_source, &$smarty_obj)
{
    $tpl_source = $tpl_name;
    return true;
}

function spass_timestamp($tpl_name, &$tpl_timestamp, &$smarty_obj)
{
    $tpl_timestamp = time();
    return true;
}
function spass_secure($tpl_name, &$smarty_obj) { return true; }
function spass_trusted($tpl_name, &$smarty_obj) { }
$smarty->register_resource("pass", array("spass_template",
                                       "spass_timestamp",
                                       "spass_secure",
                                       "spass_trusted"));
                                       
/* Load modules */
$moddir = dirname($_SERVER["DOCUMENT_ROOT"]) . "/mods";
ccs_loadmodules($moddir);

/* Set vars to defaults */
$smarty->assign("online", "no");
$smarty->assign("session_state", "no");
$session_state = "no";

/* Check for existing PHP session */
session_set_cookie_params(0, "/",$_SERVER["SERVER_NAME"],1);
session_start();
$session_state = SESSION_NONE;
$SESSION["no_config"] = 0;

/* Load list of networks available */
ccs_loadconfig();
$nets = array_keys($networks);
$smarty->assign("networks", $nets);
if (isset($_POST["network"])) {
    $smarty->assign("network", $_POST["network"]);
} else if (isset($_SESSION["network"])) {
    $smarty->assign("network", $_SESSION["network"]);
} else {
    /* Select the first network in the list */
    $network = $nets[0];
    $_SESSION["network"] = $nets[0];
    $smarty->assign("network", $nets[0]);
}
/* Check for user logging in */
if (isset($_POST["function"]) && $_POST["function"]=="login") {
    $session_state = do_login();
}

if ($_SESSION["no_config"]==0) {
    $session_state = ccsd_session_valid();
    if ($session_state == SESSION_NONE && isset($_COOKIE['ccsd_persist'])) {
        /* Downgrade gracefully to a RO session using cookie */
        $session_state = do_cookie_logon($_COOKIE['ccsd_persist']);
    }
    /* Ensure user is completely logged out if no session exists now */
    if ($session_state == SESSION_NONE) {
        unset($_SESSION["ccsd_username"]);
        unset($_SESSION["ccsd_session"]);
        /* display expired error if a user was logged in */
        if (isset($_SESSION["ccsd_username"])) {
            $smarty->assign("reason", AUTH_EXPIRED);
            $smarty->assign("username", $_SESSION["ccsd_username"]);
        }
    }
}

/* Handle forgotten password requests before showing the login page */
if (isset($_REQUEST["function"]) && $_REQUEST["function"] == "forgotpass") {
    if ($_POST["process"] == "yes") {
        handle_forgotten_password();
        redirect_to_previous();
    } else {
        save_referer();
        display_page("forgotpass.tpl");
    }
}

if ($session_state == SESSION_NONE && $_REQUEST["function"]!="login") {
    cancelIfAjaxRequest();
    /* Force user to front welcome page */
    require_login(AUTH_NO_SESSION);
}

/* Setup XML RPC connection */
$xmlrpc_conn = start_xmlrpc();
if ($xmlrpc_conn == FALSE) {
    cancelIfAjaxRequest();
    $smarty->assign("errMsg", "Could not connect to configuration server");
    display_page("welcome.tpl");
    exit;
}

/* Make sure there is always a HOME link in the menu bar */
ccs_menu_top_add(array(mk_menu_item("Home", "/", AUTH_USER, 1), 
    mk_menu_item("CFengine Management", "/cfengine", AUTH_ADMINISTRATOR, 999))
);

if (ccsd_changeset_no()>0) {
    ccs_menu_top_funcs_add(array(mk_menu_item("Commit Changeset", 
        "/?function=commitChangeset", AUTH_ADMINISTRATOR),
        mk_menu_item("Cancel Changeset", 
        "/?function=cancelChangeset", AUTH_ADMINISTRATOR)));
} else if ($session_state=="RW") {
    ccs_menu_top_funcs_add(array(mk_menu_item("Begin Changeset",
        "/?function=beginChangeset", AUTH_ADMINISTRATOR)));
} else {
    ccs_menu_top_funcs_add(array(mk_menu_item("Upgrade to RW session",
        "/?function=upgradeSession", AUTH_ADMINISTRATOR)));
}
ccs_menu_top_funcs_add(array(mk_menu_item("Changeset History", 
    "/?function=changesetHistory", AUTH_ADMINISTRATOR),
    mk_menu_item("Regenerate Conf. Files", 
    "/configs/generate", AUTH_ADMINISTRATOR)));

/* Global actions that could occur anywhere across the site */
if (isset($_REQUEST["function"])) {
    
    /* Login Request Form */
    if ($_REQUEST["function"] == "login") {
        if (isset($_SESSION["loginReason"])) {
            $smarty->assign("reason", $_SESSION["loginReason"]);
        }
        display_page("welcome.tpl");
    }

    /* Handle posted forms */
    if ($_POST["function"] == "logout") {
        do_logout();
        header("Location: " . getBaseURL());
        exit;
    }
    
    /* Passwords */
    if ($_REQUEST["function"] == "changepass") {
        if ($_POST["process"] == "yes") {
            handle_password_change();
            redirect_to_previous();
        } else {
            save_referer();
            display_page("passchange.tpl");
        }
    }
    
    /* Handle Changesets */
    if ($_REQUEST["function"]=="beginChangeset") {
        /* Start changeset */
        if (ccsd_no_changesets() > 0) {
            if (isset($_REQUEST["confirm"]) && $_REQUEST["confirm"]=="yes") {
                do_xmlrpc("beginChangeset", array());
            } else {
                /* Request changeset description from the user */
                save_referer();
                display_page("beginChangeset.tpl");
            }
        } else {
            save_referer();
            do_xmlrpc("beginChangeset", array());
        }
        get_session_info();        
        redirect_to_previous();
        exit;
    } else if ($_REQUEST["function"]=="commitChangeset") {
        if (isset($_REQUEST["confirm"]) && $_REQUEST["confirm"]=="yes") {
            /* Commit the changes */
            $rv=do_xmlrpc("commitChangeset",array($_REQUEST["description"]));
            $cs = $rv["changeset"];
            $rev = $rv["revision"];
            $note = "Changeset #$cs successfully commited.";
            if ($rev > 0) {
                $note .= " Configuration revision #$rev generated.";
            }
            ccs_notice($note);
        } else {
            /* Request changeset description from the user */
            save_referer();
            display_page("commitChangeset.tpl");
        }
        redirect_to_previous();
        get_session_info();
    } else if ($_REQUEST["function"]=="cancelChangeset") {
        /* Rollback the changeset */
        $r = do_xmlrpc("cancelChangeset", array());
        ccs_notice("Changeset cancelled successfully.");
        get_session_info();
        redirect_to_previous();
    } else if ($_REQUEST["function"]=="changesetHistory") {
        display_changeset_history();
    } else if ($_REQUEST["function"]=="threadStatus") {
        display_thread_status();
    } else if ($_REQUEST["function"]=="loginbarUpdate") {
        // Update the session information
        get_session_info();
        // Display the page fragment
        $smarty->assign("online", "yes");
        $smarty->assign("username", $_SESSION["ccsd_username"]);
        $smarty->assign("session_state", $session_state);
        if ($xmlrpc_conn) {
            if ($session_state != SESSION_NONE) {
                $smarty->assign("nsessions", ccsd_no_sessions());
                $smarty->assign("changeset", ccsd_changeset_no());
                $smarty->assign("changesets", ccsd_no_changesets());
            }
        } else {
            $smarty->assign("nsessions", "Unknown");
        }
        $smarty->assign("network", $_SESSION["network"]);
        if (isset($networks[$_SESSION["network"]])) {
            $netinfo = $networks[$_SESSION["network"]];
            $smarty->assign("network_name", $netinfo["name"]);
        }
        $smarty->assign("update", 1);
        $smarty->display("loginbar.tpl");
        exit;
    }

    /* Upgrade Session */
    if ($_REQUEST["function"]=="upgradeSession") {
        save_referer();
        $smarty->assign("reason", AUTH_INSUF_SESSION);
        display_page("welcome.tpl");
    }

}

/* Always check if a password change is needed */
check_password_change();

/* Control now passes back to the page that included ccs_init.php */
?>
