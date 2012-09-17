<?php
/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Provides an interface to the XML-RPC for PHP library originally written by
 * Edd Dumbill of Useful Information Company. 
 * 
 * This file will be loaded from ccs_xmlrpc.php if it is required.
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
require_once("xmlrpc.php");

function init_xmlrpc($host, $port, $path, $cert="") 
{
    /* Initialise the connection */
    $c=new xmlrpc_client($path, $host, $port);
    if ($cert!="") {
        $c->setSSLVerifyPeer(0); // XXX: Should fix this one day
        $c->setCertificate($cert, "");
    }
    if (check_server_version($c)) {
        return $c;
    }
    return FALSE;
}
function xmlrpc_has_error($r) {
    if (!is_object($r)) {
        return FALSE;
    }
    if ($r->faultCode() > 0) {
        return TRUE;
    }
    return FALSE;
}
function xmlrpc_error_string($r) {
    if (!is_object($r)) {
        return "Invalid object passed to xmlrpc_error_string";
    }
    $err = $r->faultString();
    if (is_array($err)) {
        $errMsg = $err["value"]->me["string"];
        if ($errMsg == "") {
            $err = _extract_xmlrpc_result($err);
            $errMsg = $err["args"][0];
        }
    } else {
        $errMsg = $err;
    }
    return $errMsg;
}
function xmlrpc_error_code($r) {
    $errCode = $r->faultCode();
    return $errCode;
}

function _do_xmlrpc($conn, $func, $params)
{
    $p2 = array();
    foreach ($params as $param) {
        $p2[] = enc($param);
    }
    $msg = new xmlrpcmsg($func,$p2);
    $r = $conn->send($msg, 0, $conn->cert != "" ? "https" : "http");
    return $r;
}
function _extract_xmlrpc_result($in) {
    $outarr = array();

    if (is_object($in)) {
        $v = $in->value();
        $inarr = $v->getval();
    } else {
        $inarr = $in;
    }
    if (!is_array($inarr)) {
        return $inarr;
    }

    foreach ($inarr as $key=>$val) {
        if (is_array($val)) {
            $outarr[$key] = _extract_xmlrpc_result($val);
            continue;
        } 
        if (is_object($val)) {
            $outarr[$key] = _extract_xmlrpc_result($val->getval());
            continue;
        }
        $outarr[$key] = $val;
    }
    
    return $outarr;
}
    
/* Create array */
function create_array($inarr) 
{

    $outarr = array();

    foreach ($inarr as $key=>$val) {
        $outarr[$key] = enc($val);
    }
    
    return $outarr;
    
}

/* Return an xmlrpcval for the variable */
function enc($val) {
    
    /* Arrays need to be specially encoded */
    if (is_array($val))
        return new xmlrpcval(create_array($val), "struct");

    //$val = stripslashes($val);

    /* try and determine other types... */
    if (is_string($val))
        return new xmlrpcval($val, "string");

    if (is_bool($val))
        return new xmlrpcval($val, "bool");

    if (is_double($val) || is_float($val))
        return new xmlrpcval($val, "double");

    if (is_numeric($val))
        return new xmlrpcval($val, "int");

    /* Otherwise let XMLRPC work it out */
    return new xmlrpcval($val, "");

}
/* Same as above but assume the variable comes from a post */
function enc_post($val) {
    if (is_string($val))
       $val = stripslashes($val);
    return enc($val);
}

/* Creates an XML struct member */
function create_struct_member($name, $value)
{

    $rv = "<member><name>$name</name><value>";
    
    /* Arrays need to be specially encoded */
    if (is_array($value)) {
        $rv .= "<struct>";
        foreach ($value as $key=>$val) {
            $rv .= create_struct_member($key, $val);
        }
        $rv .= "</struct>";
    }
    
    /* try and determine other types... */
    if (is_bool($value)) {
        $rv .= "<boolean>$value</boolean>";
    } else if (is_double($value) || is_float($value)) {
        $rv .= "<double>$value</double>";
    } else if (is_numeric($value)) {
        $rv .= "<int>$value</int>";
    } else {
        $rv .= "<string>$value</string>";
    }
    
    return $rv . "</value></member>";

}

    
?>
