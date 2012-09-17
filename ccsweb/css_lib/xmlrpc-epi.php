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

/************************************************
* xmlrpc client class.  basically a wrapper for *
* xu_rpc_http().                                *
************************************************/
class xmlrpc_client {
    var $path;
    var $server;
    var $port;
    var $errno;
    var $errstring;
    var $debug=0;
    var $username="";
    var $password="";
    var $cert="";
    var $certpass="";
    var $verifypeer=1;
    var $verifyhost=1;

    // constructor
    function xmlrpc_client($path, $server, $port=80) {
        $this->port=$port; $this->server=$server; $this->path=$path;
    }

    // public. for debugging info.
    function setDebug($in) {
        if ($in) {
            $this->debug=1;
        } else {
            $this->debug=0;
        }
    }

    // public. for http authentication.
    function setCredentials($u, $p) {
        $this->username=$u;
        $this->password=$p;
    }
    function setCertificate($cert, $certpass)
    {
        $this->cert = $cert;
        $this->certpass = $certpass;
    }
    function setSSLVerifyPeer($i)
    {
        $this->verifypeer = $i;
    }

    // public.  sent request to server.
    function send($method, $params, $timeout=0) {
      
        global $curltimes;

        if ($this->cert) {
            if (!function_exists('curl_init')) {
                $this->errstr='SSL unavailable on this install';
                $r=new xmlrpcresp(0, 7, "No SSL Support");
                return $r;
            }
        }

        // Create the payload
        $payload = xmlrpc_encode_request($method, $params);

        if ($this->cert) {        
            $curl = curl_init('https://' . $this->server . ':' . $this->port .
                $this->path);
            // whether to verify remote host's cert
            curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, $this->verifypeer);
            // whether to verify cert's common name (CN); 0 for no, 
            //1 to verify that it exists, 
            //and 2 to verify that it matches the hostname used
            curl_setopt($curl, CURLOPT_SSL_VERIFYHOST, $this->verifyhost);
        } else {
            $curl = curl_init('http://' . $this->server . ':' . $this->port .
                $this->path);
        }

        curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);
        // results into variable
        if ($this->debug) {
            curl_setopt($curl, CURLOPT_VERBOSE, 1);
        }
        curl_setopt($curl, CURLOPT_USERAGENT, 'ccsweb xmlrpc-epi $Revision$');
        // required for XMLRPC
        curl_setopt($curl, CURLOPT_POST, 1);
        // post the data
        curl_setopt($curl, CURLOPT_POSTFIELDS, $payload);
        // the data
        curl_setopt($curl, CURLOPT_HEADER, 1);
        // return the header too
        curl_setopt($curl, CURLOPT_HTTPHEADER, array('Content-Type: text/xml',
            'Accept-Charset: UTF-8'));
        // timeout is borked
        if ($timeout) {
            curl_setopt($curl, CURLOPT_TIMEOUT, $timeout==1 ? 1 : $timeout-1);
        }
        // set auth stuff
        if ($this->username && $this->password) {
            curl_setopt($curl, CURLOPT_USERPWD,$this->username . ":" .
                $this->password);
        }
        // set cert file
        if ($this->cert) {
            curl_setopt($curl, CURLOPT_SSLCERT, $this->cert);
        }
        // set cert password
        if ($this->certpass) {
            curl_setopt($curl, CURLOPT_SSLCERTPASSWD,$this->certpass);
        }
        $s = microtime_float();
        $result = curl_exec($curl);
        $e = microtime_float();
        $d = $e-$s;
        $curltimes[$method] = $d;
        
        if (!$result) {
            $resp = array();
            $resp["faultCode"] = 8;
            $resp["faultString"] = "Curl Error: " . curl_error($curl);
            curl_close($curl);
        } else {
            curl_close($curl);
            $resp = $this->parseResponse($result);
        }
        return $resp;
    }
    
    // public. parse xml, return as xmlrpcresp.
    function parseResponse($data="") {
        // see if we got an HTTP 200 OK, else bomb
        // but only do this if we're using the HTTP protocol.
        if(ereg("^HTTP",$data))
        {
            // Strip HTTP 1.1 100 Continue header if present
            while (ereg('^HTTP/1.1 1[0-9]{2}', $data))
            {
                $pos = strpos($data, 'HTTP', 12);
                // server sent a Continue header without any (valid) content 
                // following... // give the client a chance to know it
                if (!$pos && !is_int($pos)) // works fine in php 3, 4 and 5
                break;
                $data = substr($data, $pos);
            }
            if (!ereg("^HTTP/[0-9\\.]+ 200 ", $data))
            {
                $errstr= substr($data, 0, strpos($data, "\n")-1);
                $resp = array();
                $resp["faultCode"] = 7;
                $resp["faultString"] = "Invalid response code from remote " .
                    "server ( " . $errstr . ")";
                return $r;
            }
        }

        $php_val = xmlrpc_decode(strstr($data, "<?xml"));
        return $php_val;
    }
} // end class xmlrpc_client

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
    if (!is_array($r)) {
        return FALSE;
    }
    if (array_key_exists("faultCode", $r)) {
        return TRUE;
    } else {
        return FALSE;
    }
}

function xmlrpc_error_string($r) {
    $errMsg = $r["faultString"];
    if (is_array($errMsg)) {
        $errMsg = $errMsg["args"][0];
    }
    return $errMsg;
}
function xmlrpc_error_code($r) {
    $errCode = $r["faultCode"];
}

function _do_xmlrpc($conn, $func, $params)
{
    $r = $conn->send($func, $params, 0);
    return $r;
}
function _extract_xmlrpc_result($r) {
    return $r;
}
