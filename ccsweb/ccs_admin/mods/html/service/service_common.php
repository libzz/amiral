<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Service Configuration
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

function display_service_list()
{

    global $xmlrpc_conn, $smarty;

    $services = do_xmlrpc("getServiceList", array(),$xmlrpc_conn,TRUE,FALSE);
    if (xmlrpc_has_error($services)) {
        ccs_notice("Could not retrieve service list: " .
            xmlrpc_error_string($services));
        $services = array();
    }
    $smarty->assign("services", $services);

    display_page("mods/service/servicelist.tpl");

}

function getServiceName($service_id)
{

    global $xmlrpc_conn, $smarty;

    $name = do_xmlrpc("getServiceName", array($service_id), $xmlrpc_conn,
        TRUE, FALSE);
    if (xmlrpc_has_error($name)) {
        ccs_notice("Could not retrieve service name: " .
            xmlrpc_error_string($name));
        $name = "";
    }

    return $name;

}
function getService($service_id, $host_id=-1) 
{
    global $smarty, $xmlrpc_conn;
    
    if ($host_id != -1) {
        $p = array($service_id, $host_id);
        $func = "getServiceHostDetails";
    } else {
        $p = array($service_id);
        $func = "getServiceDetails";
    }
    
    $service = do_xmlrpc($func, $p, $xmlrpc_conn, TRUE, FALSE);
    if (xmlrpc_has_error($service)) {
        ccs_notice("Could not retrieve service: " .
            xmlrpc_error_string($service));
        $service = array();
    }
    return $service;
}
function assignService($service_id) 
{
    global $smarty;
    
    $service = getService($service_id);
    $smarty->assign("service", $service);
    
    return $service;

}function assignHostService($service_id, $host_id) 
{
    global $smarty;
    
    $service = getService($service_id, $host_id);
    $smarty->assign("service", $service);
    
    return $service;

}
