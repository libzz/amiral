<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id: index.php 1542 2007-05-21 02:08:55Z ckb6 $
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

$details = do_xmlrpc("getCustomerDetails", array(), $xmlrpc_conn, TRUE, FALSE);
if (xmlrpc_has_error($details)) {
    ccs_notice("Could not retrive details from the server: " .
        xmlrpc_error_string($details));
    $details = array();
}
$mailboxes = do_xmlrpc("getCustomerMailboxes", array(), $xmlrpc_conn, TRUE, FALSE);
if (xmlrpc_has_error($mailboxes)) {
    ccs_notice("Could not retrive mailboxes from the server: " .
        xmlrpc_error_string($mailboxes));
    $mailboxes = array();
}
if ($details["included_mb"] > 0){
    $details["percent"] = round($details["used_mb"]/$details["included_mb"]*100);
}
$smarty->assign("details", $details);

$c = 0;
foreach ($links as $idx=>$link) {
    $lids[$c] = $link["link_id"];
    $lnames[$c] = $link["description"];
    $c++;
}

$smarty->assign("modules", $ccs_modules);
$smarty->assign("mailboxes", $mailboxes);
display_page("index.tpl");

?>

