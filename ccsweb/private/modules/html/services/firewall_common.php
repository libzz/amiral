<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * Firewall Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
function getFirewallClassList($service_id)
{
    global $xmlrpc_conn;
    
    $p = array($service_id);
    $classes = do_xmlrpc("getFirewallClasses", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($areas)) {
        ccs_notice("Could not retrieve firewall class details: " .
            xmlrpc_error_string($classes));
        return array();
    }
    $rv = array();
    foreach ($classes as $idx=>$fclass) {
        $rv[$fclass["firewall_class_id"]] = $fclass;
    }
    return $rv;
}
function getFirewallClassesSelect($classes) {
    $rv = array();
    foreach ($classes as $idx=>$data) {
        $rv[$data["firewall_class_id"]] = $data["firewall_class_name"];
    }
    return $rv;
}
function assignFirewall($service_id) 
{
    global $smarty, $xmlrpc_conn;
    
    $p = array($service_id);
    $service = do_xmlrpc("getServiceDetails", $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve firewall details: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    $service["firewall_classes"] = getFirewallClassList($service_id);
    $service["firewall_classes_select"] = 
        getFirewallClassesSelect($service["firewall_classes"]);

    $smarty->assign("firewall", $service);

    return $service;
}
