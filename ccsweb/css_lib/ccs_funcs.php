<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * This file provides common functions that are used throughout the interface
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
$session_info = array();

/* Kills the current session and logs the user out */
function do_logout() {

    global $xmlrpc_conn, $networks;
    
    /* Tell server we are going away */
    $r = do_xmlrpc("logout", array(), $xmlrpc_conn);
    
    /* Kill cookies */
    setcookie("ccsd_persist", "", 0, "/", $_SERVER["SERVER_NAME"], 1);

    /* Kill PHP session */
    $network = $_SESSION["network"];
    session_unset();
    $_SESSION["network"] = $network;
}

/* Processes a submitted login form */
function do_login() {

    global $xmlrpc_conn, $smarty, $networks;
    
    /* Get details from post */
    $username = $_POST["username"];
    $password = $_POST["password"];
    
    /* Determine which network we are trying to login to */
    if (isset($_POST["network"]) && isset($networks[$_POST["network"]])) {
        $_SESSION["network"] = $_POST["network"];
    } else if (count($networks)>1) {
        $_SESSION["network"] = $networks["default"]["name"];
    } else {
        $smarty->assign("errMsg", "Network not specified");
        display_page("welcome.tpl");
        exit;
    }
    if ($networks[$_SESSION["network"]]["type"] == "admin") {
        $login_func = "login";
    }else {
        $login_func = "customer_login";
    }
    /* Get the server to process the login */
    $rv = do_xmlrpc($login_func, array($username, $password), 
        $xmlrpc_conn, FALSE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $smarty->assign("errMsg", xmlrpc_error_string($rv));
        $smarty->assign("reason", AUTH_INVALID_CRED);
        $smarty->assign("username", $username);
        display_page("welcome.tpl");
    }

    /* Login succeeded, setup PHP session */
    $_SESSION["ccsd_session"] = $rv["sessionID"];
    $_SESSION["ccsd_username"] = $username;
    $_SESSION["ccsd_contact_id"] = $rv["login_id"];
    $_SESSION["sauth"] = $rv;
    get_session_info();

    /* Get group memebership information and cache it */
    cache_group_memberships();

    /* Setup cookie if requested */
    if ($_POST["persist"] == "yes") {
        $token = do_xmlrpc("getCookieToken", array(), $xmlrpc_conn);
        $expire = time()+(60*60*24*30);
        $network = $_SESSION["network"];
        setcookie("ccsd_persist", "$network:$username:$token", $expire, 
            "/", $_SERVER["SERVER_NAME"], 1);
    }

    redirect_to_previous();
}

function cache_group_memberships() {

    global $xmlrpc_conn, $smarty;
    
    /* Get the server to process the login */
    $rv = do_xmlrpc("getGroupMemberships", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $smarty->assign("errMsg", xmlrpc_error_string($rv));
        display_page("welcome.tpl");
    }
    $_SESSION["membershipCache"] = $rv;
}

/* Attempts to login a user using a cookie saved in their browser.
 *
 * Cookie Format: cookie format: username:token
 */
function do_cookie_logon($cookiedata) {
 
    global $xmlrpc_conn, $networks, $smarty;
    
    // Don't login because of an Ajax request
    if (isAjaxRequest()) {
        return SESSION_NONE;
    }

    // Break up the cookie into the various parts
    $parts = explode(":", stripslashes($cookiedata));
    // Check specified network still available
    if (!isset($networks[$parts[0]])) {
        $smarty->assign("errMsg", "Unable to login via cookie, network '" . 
            $parts[0] . "' is " . "no longer available via this interface.");
        display_page("welcome.tpl");
        exit;
    } else {
        $xmlrpc_conn = FALSE;
        $_SESSION["network"] = $parts[0];
    }
    $rv = do_xmlrpc("cookieLogin", array($parts[1], $parts[2]),
        $xmlrpc_conn, FALSE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $smarty->assign("errMsg", "Login via cookie failed (" . $parts[1] . 
            ") - " . xmlrpc_error_string($rv));
        setcookie("ccsd_persist", "", 0, "/", $_SERVER["SERVER_NAME"], 1);
        return SESSION_NONE;
    }
    /* Cookie login successful, we get a read only session */
    $_SESSION["ccsd_session"] = $rv["sessionID"];
    $_SESSION["ccsd_username"] = $parts[1];
    $_SESSION["sauth"] = $rv;
    get_session_info();

    /* Get group memebership information and cache it */
    cache_group_memberships();
    
    return $rv["mode"];
   }

/* Check whether the user needs a password change and display the page */
function check_password_change() {

    global $smarty;
    
    $sauth = $_SESSION["sauth"];
    if ($sauth["passchange"]) {
        $smarty->assign("reason", "To ensure the security of the " .
            "configuration system you must enter a new password before " .
            "using this site.");
        display_page("passchange.tpl");
    }

}

/* Change a users password */
function handle_password_change() {
    
    global $smarty, $xmlrpc_conn;
    
    $rv = do_xmlrpc("changePassword", array($_POST["curpassword"], 
        $_POST["password"], $_POST["password2"]), $xmlrpc_conn,
        TRUE, FALSE);
    if (xmlrpc_has_error($rv)) {
        $smarty->assign("reason", "ERROR: " . xmlrpc_error_string($rv));
        display_page("passchange.tpl");
    }
    ccs_notice("Password successfully changed.");
    $_SESSION["sauth"]["passchange"] = 0;

}   

/* Email a user a new password */
function handle_forgotten_password() {
    
    $r = do_xmlrpc("forgotPassword", array($_POST["username"]), 
        $xmlrpc_conn, FALSE, TRUE);
    ccs_notice("New password emailed.");

}

function display_changeset_history()
{

    global $xmlrpc_conn, $smarty;

    $p = array();
    if (isset($_POST["Date_Year"])) {
        $time = mktime(0,0,0,$_POST["Date_Month"],$_POST["Date_Day"],
            $_POST["Date_Year"]);
        array_push($p, $time);
        if (isset($_POST["days"])) {
            array_push($p, $_POST["days"]);
        }
    } else {
        $time = time();
    }
    $r = do_xmlrpc("getChangesetHistory", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        $hist = array();
        ccs_notice("Could not retrieve changeset history: " .
            xmlrpc_error_string($r));
    }
    $smarty->assign("changeset_hist", $r);
    $smarty->assign("daylist", array(1,2,3,4,5,6,7,8,9,10));
    $smarty->assign("time", $time);
    $smarty->assign("days", $_REQUEST["days"]);
    display_page("cshist.tpl");
}

function display_thread_status()
{

    global $xmlrpc_conn, $smarty;

    $r = do_xmlrpc("getThreadStatus", $p, $xmlrpc_conn, FALSE, TRUE);
    ksort($r);
    $smarty->assign("threads", $r);
    if (isAjaxRequest()) {
        $smarty->display("threadstatus.tpl");
        exit;
    } else {
        display_page("threadstatus-page.tpl");
    }
}

/* Stores the referrer in the session so that we can jump back to it after we
 * finish whatever interrupted the request
 */
function save_referer() {
    $_SESSION["from"] = $_SERVER["HTTP_REFERER"];
}

/* Stores the current location in the session so that we can jump back to it 
 * after we finish whatever interrupted the request
 */
function save_location() {
   $_SESSION["from"] = $_SERVER["REQUEST_URI"];
}

/* Redirect back to wherever we used to be */
function redirect_to_previous() {
    if (isset($_SESSION["from"]) && $_SESSION["from"]!="") {
        header("Location: " . $_SESSION["from"]);
    } else if (isset($_SERVER["HTTP_REFERER"]) && 
            $_SERVER["HTTP_REFERER"]!="") {
        header("Location: " . $_SERVER["HTTP_REFERER"]);
    } else {
        /* Jump back to the main page as a last resort */
        header("Location: " . getBaseURL());
    }
    $_SESSION["from"] = "";
    exit;
}

/* Checks if the user has sufficient rights to edit the page */
function page_edit_requires($group_name, $account_types=array("user"))
{
    global $smarty, $session_state;
    
    /* Must be able to view the page */
    $contact_id = get_contact_id($_SESSION["ccsd_username"]);
    page_view_requires($group_name, $contact_id);
    
    /* Must have a read write session */
    if ($session_state != SESSION_READWRITE) {
        require_login(AUTH_INSUF_SESSION);
    }

    /* Check account type */
    #if (user_in_type($contact_id, $account_types)!=1) {
    #    denied_page(AUTH_INVALID_ACCOUNT);
    #}
        
    return;
    
}

/* Checks if the current user has sufficient rights to view the page */
function page_view_requires($group_name, $contact_id=-1) {

    global $smarty, $session_state, $debug_mode;

    // Validator is always allowed in debug mode
    if (substr($_SERVER["HTTP_USER_AGENT"], 0, 13) == "W3C_Validator" &&
            $debug_mode==1) {
        return;
    }

    /* Check that the session is valid */
    if ($session_state == SESSION_NONE) {
        require_login(AUTH_INVALID_SESSION);
    }

    $group_id = get_group_id($group_name);
    if ($group_id == -1) {
        error_page("Invalid groupname ($group_name) passed to page_requires!");
    }
   
    if ($contact_id == -1) {
        $contact_id = get_contact_id($_SESSION["ccsd_username"]);
    }
    if ($contact_id == -1) {
        denied_page(AUTH_INVALID_CRED);
    }
        
    /* Check group membership */
    if (user_in_group($contact_id, $group_id)!=1) {
        denied_page(AUTH_INSUF_PERMS);
    }
    
    return;
    
}

function get_session_info() {
    global $xmlrpc_conn, $session_info;
       
    $r = do_xmlrpc("getSessionInformation", array(), $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        $age = time()-$_SESSION["session_info"][4];
        if (xmlrpc_error_code($r) >= 9000 || $age>SESSION_REFRESH_TIME) {
            /* Application error or session has expired anyway */
            ccs_warning("Failed to retrieve session information! " . 
                xmlrpc_error_string($r));
            $session_info = array(SESSION_NONE, 0, 0, 0, time());
            $_SESSION["session_info"] = $session_info;
            return;
        }
        /* Transient connection error, ignore */
        return;
    }
    array_push($r, time());
    $session_info=$r;
    $_SESSION["session_info"] = $session_info;
}
function refresh_session_info() {
    // Checks if the session information needs refetching
    if ($_SESSION["session_info"] == array()) {
        get_session_info();
    }
    if ((time()-$_SESSION["session_info"][4])>SESSION_REFRESH_TIME) {
        get_session_info();
    }
}
/* Checks with the server to determine whether the specified session ID is
 * still valid, and returns the type of session.
 *
 * Returns: SESSION_NONE - Invalid Session ID
 *          SESSION_RW - Valid session with read-write capabilities
 *          SESSION_RO - Valid session with read-only capablilities
 */
function ccsd_session_valid($sid=0) {
    refresh_session_info();    
    return $_SESSION["session_info"][0];
}

/* Retrieves the number of active sessions from the server */
function ccsd_no_sessions() {
    refresh_session_info();    
    return $_SESSION["session_info"][1];
}

/* Retrieves the changeset number of the current session */
function ccsd_changeset_no() {
    refresh_session_info();    
    return $_SESSION["session_info"][3];
}

/* Retrieves the number of changesets that are currently running (does not
 * include the current session's changeset
 */
function ccsd_no_changesets() {
    refresh_session_info();    
    return $_SESSION["session_info"][2];
}

/* Sets a notice message to be displayed 
 * These are generally displayed in a box at the top of the page below the
 * header, IE. They are very prominent. Use sparingly.
 */
function ccs_notice($msg) {
    $_SESSION["notice_msgs"][] = $msg;
}
/* Sets a warning message to be displayed 
 * These are generally displayed in a red box at the bottom of the page 
 */
function ccs_warning($msg) {
    $_SESSION["warning_msgs"][] = $msg;
}
/* Sets a debug message to be displayed 
 * These are generally displayed in a box at the bottom of the page 
 */
function ccs_debug($msg) {
    $_SESSION["debug_msgs"][] = $msg;
}

/* Helper function to display a smarty page. 
 *
 * Smarty should never be called directly as this function needs to ensure
 * that the templates are passed certain variables
 */
function display_page($page, $error=0) {

    global $smarty, $debug_mode;
    global $admin_email, $session_state, $xmlrpc_conn;
    global $pstart, $rpctimes, $curltimes, $networks;
    
    /* Setup smarty variables for the login bar */
    $smarty->assign("online", "yes");
    $smarty->assign("username", $_SESSION["ccsd_username"]);
    $smarty->assign("session_state", $session_state);
    if ($xmlrpc_conn && $error==0) {
        if ($session_state != SESSION_NONE) {
            $smarty->assign("nsessions", ccsd_no_sessions());
            $smarty->assign("changeset", ccsd_changeset_no());
            $smarty->assign("changesets", ccsd_no_changesets());
        }
    } else {
        $smarty->assign("nsessions", "Unknown");
    }

    /* Write out notice / warning / debug messages */
    $smarty->assign("notice_msgs", $_SESSION["notice_msgs"]);
    $smarty->assign("warning_msgs", $_SESSION["warning_msgs"]);
    if ($debug_mode > 0) {
        ccs_debug("POST: " . print_r($_POST, 1));
        ccs_debug("REQUEST: " . print_r($_REQUEST, 1));
        ccs_debug("SESSION: " . print_r($_SESSION, 1));
        ccs_debug("COOKIE: " . print_r($_COOKIE, 1));
        $smarty->assign("debug_msgs", $_SESSION["debug_msgs"]);
    }
    $_SESSION["notice_msgs"] = array();
    $_SESSION["warning_msgs"] = array();
    $_SESSION["debug_msgs"] = array();

    /* Write out menus */
    $smarty->assign("top_menu", ccs_menu_get_top());
    $smarty->assign("top_funcs_menu", ccs_menu_get_top_funcs());
    $smarty->assign("bottom_menu", ccs_menu_get_bottom());    
    $smarty->assign("bottom_menu_inc", ccs_menu_get_bottominc());   

    /* Other always present variables */
    $smarty->assign("admin_email", $admin_email);
    $smarty->assign("username", $_SESSION["ccsd_username"]);
    $smarty->assign("page", $PHP_SELF);
    $smarty->assign("site_address", $_SERVER["HTTP_HOST"]);
    
    /* Network Information */
    $smarty->assign("network", $_SESSION["network"]);
    if (isset($networks[$_SESSION["network"]])) {
        $network = $networks[$_SESSION["network"]];
        $smarty->assign("network_name", $network["name"]);
    }

    /* Page execution time */
    $pend = microtime_float();
    $exectime = $pend - $pstart;
    usort($rpctimes, "cmp_rpctimes");
    $smarty->assign("rpctimes", $rpctimes);
    $smarty->assign("curltimes", $curltimes);
    $smarty->assign("exec_time", $exectime);

    /* Call smarty to display the page */
    $smarty->display($page);
    exit;
    
}
function cmp_rpctimes($a, $b) {
    if ($a["time"] == $b["time"]) return 0;
    return ($a["time"] > $b["time"]) ? -1 : 1;
}
/* Used to display the login form */
function require_login($reason) 
{
    $_SESSION["loginReason"] = $reason;
    save_location();
    header("Location: /?function=login");
    exit;
}
/* An error occured processing the page */
function error_page($reason)
{
    global $smarty;
    $smarty->assign("reason", $reason);
    display_page("error.tpl", TRUE);
}
/* No permissions */
function denied_page($reason)
{
    global $smarty;
    $smarty->assign("reason", $reason);
    display_page("denied.tpl", TRUE);
}

/* Reads the module directory and loads module files as appropriate */
function ccs_loadmodules($moddir) {
    
    /* Get list of files from directory */
    $dh  = @opendir($moddir);
    if ($dh == FALSE) {
        ccs_warning("Modules directory ($moddir) does not exist!");
        return;
    }  
    while (FALSE !== ($filename = readdir($dh))) {
        $poss_mods[] = $filename;
    }
    closedir($dh);
    
    /* Loop through list looking for files named appropriately */
    for ($i=0;$i<count($poss_mods);$i++) {
        $file = $poss_mods[$i];
        if (preg_match("/^ccs_.*\.php$/", $file)==1) {
            /* File with valid name found, load it */
            include_once("$moddir/$file");
        }
    }
    
}

/* Loads the configuration file */
function addNetwork($name, $site, $host, $port, $cert, $path, $email, $type)
{
    global $networks;
    
    $networks[$name] = array("name"=>$name, "site"=>$site, "host"=>$host,
        "port"=>$port, "cert"=>$cert, "path"=>$path, "email"=>$email, "type"=>$type);

}

function ccs_loadconfig()
{

    global $networks, $smarty;
    $networks = array();
    
    /* First look to see if PHP has been configured to give us a conffile */
    // XXX: This doesn't appear to work :(
    $iniconf = ini_get("ccs_config");
    if (strlen($iniconf)>0) {
        @include($iniconf);
        if (count($networks>0)) {
            return;
        }
    }

    /* If not use the one in the same directory as this script */
    @include("ccsweb.conf");
    if (count($networks)>0) {
        return;
    }

    /* FATAL ERROR - no configuration */
    $_SESSION["no_config"] = 1;
    $smarty->assign("errMsg", "No configuration file available!");
    
}


/* If the specified entry exists in the _POST array, it is inserted into the
 * provided array
 */
function get_if_posted(&$dest, $varname)
{
    if (isset($_POST[$varname]))
        $dest[$varname] = stripslashes($_POST[$varname]);
}
function get_if_post_modified(&$dest, $varname)
{
    if (isset($_POST[$varname])) {
        if (isset($_POST["{$varname}-orig"])) {
            if ($_POST[$varname] == $_POST["{$varname}-orig"]) {
                return;
            }
        }
        $dest[$varname] = stripslashes($_POST[$varname]);
    }
}
function get_if_checked(&$dest, $varname)
{
    $new = "";
    $old = "";
    
    if (isset($_POST[$varname]) && 
            ($_POST[$varname]=="yes" || $_POST[$varname]=="t")) {
        $new = "t";
    } else {
        $new = "f";
    }
    $dest[$varname] = $new;
}
function get_if_checked_modified(&$dest, $varname)
{
    $new = "";
    $old = "";
    
    if (isset($_POST[$varname]) && 
        ($_POST[$varname]=="yes" || $_POST[$varname]=="t")) {
        $new = "t";
    } else {
        $new = "f";
    }
    if (isset($_POST["${varname}-orig"]) && 
            ($_POST["${varname}-orig"]=="yes" || 
            $_POST["${varname}-orig"]=="t")) {
        $old = "t";
    } else {
        $old = "f";
    }
    if ($new != $old) {
        $dest[$varname] = $new;
    }
}
/* Get a group id from it's name */
function get_group_id($group_name)
{
    global $xmlrpc_conn;

    $gid = do_xmlrpc("getGroupID", array($group_name),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($gid)) {
        ccs_notice("Could not determine group id: " . 
            xmlrpc_error_string($gid));
        return -1;
    }
    return $gid;
}
/* Get a contact id from username */
function get_contact_id($username)
{
    global $xmlrpc_conn;

    $cid = do_xmlrpc("getAdminID", array($username), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($cid)) {
        $avail = array();
        ccs_notice("Could not determine contact id: " .
            xmlrpc_error_string($cid));
        return -1;
    }
    return $cid;
}

/* Determine whether the specified contact is of the specified type */
function user_in_type($contact_id, $types)
{
    $type = get_contact_type($contact_id);
    if (in_array($type, $types)) {
        return 1;
    }

    return 0;
}
/* Get the users account type */
function get_contact_type($contact_id)
{
   
    global $xmlrpc_conn;

    $type = do_xmlrpc("getContactType", array($contact_id), 
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($type)) {
        ccs_notice("Could not retrieve contact type: " .
            xmlrpc_error_string($type));
        return -1;
    }
    return $type;

}

/* Determine whether the specified contact is the the specified group */
function user_in_group($contact_id, $group_id)
{
    global $xmlrpc_conn;

    // Special case for logged in user
    if ($contact_id == $_SESSION["ccsd_contact_id"]) {
        return in_array($group_id, $_SESSION["membershipCache"]);
    }

    $r = do_xmlrpc("isGroupMemberU", array($contact_id, $group_id),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        $avail = array();
        ccs_notice("Could not determine group membership: " .
            xmlrpc_error_string($r));
        return FALSE;
    } else {
        if ($r == 0) {
            return FALSE;
        } else {
            return TRUE;
        }
    }

    // Assert: Shouldn't get here
    return FALSE;

}
/* Determine whether the specified group is the the specified group */
function group_in_group($group_id, $parent_group_id)
{
    global $xmlrpc_conn;

    $r = do_xmlrpc("isGroupMemberG", array($group_id, $parent_group_id),
        $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($r)) {
        $avail = array();
        ccs_notice("Could not determine group membership: " .
            xmlrpc_error_string($r));
        return FALSE;
    } else {
        if ($r == 0) {
            return FALSE;
        } else {
            return TRUE;
        }
    }

    // Assert: Shouldn't get here
    return FALSE;

}

/* Returns the base URL of this installation */
function getBaseURL()
{
    $url = "";
    if ($_SERVER["HTTPS"]=="on") {
        $url = "https://";
    } else {
        $url = "http://";
    }
    $url = "${url}" . $_SERVER["SERVER_NAME"] . "/";

    return $url;
}

function isAjaxRequest()
{
    if ($_SERVER["HTTP_X_REQUESTED_WITH"] == "XMLHttpRequest") {
        return true;
    }
    return false;
}
function cancelIfAjaxRequest()
{
    if ($_SERVER["HTTP_X_REQUESTED_WITH"] == "XMLHttpRequest") {
        header("HTTP/1.0 503 No active session");
        exit;
    }
}
?>
