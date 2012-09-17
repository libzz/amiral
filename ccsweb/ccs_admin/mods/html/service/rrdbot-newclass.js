/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * rrdbot Web Interface for the CRCnet Configuration System
 *
 * Author:       Chris Browning <ckb6@cs.waikato.ac.nz>
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
errCount=0;

// Register Validation Rules
var myrules = {
    '#class_name' : function(element){
        element.onchange = validateClassName;
    },
    '#poll' : function(element){
        element.onchange = validatePoll;
    },
    '#interval' : function(element){
        element.onchange = validateInterval;
    },
    '#archive' : function(element){
        element.onchange = validateArchive;
    },
    '#key' : function(element){
        element.onchange = validateKey;
    }
};

Behaviour.register(myrules);
Behaviour.addLoadEvent(validateForm);

function  validateClassName(){
    box = document.getElementById("class_name");  
    if (box.value == ""){
        setError("class_name", "Must be supplied!");
        return;
    }
    if (box.value.length > 64){
        setError("class_name", "Must be at most 64 Charictors long!");
        return;
    }
    clearError("class_name");
}
function validatePoll(){
    box = document.getElementById("poll");  
    if (box.value == ""){
        setError("poll", "Must be supplied!");
        return;
    }
    if (box.value.length > 64){
        setError("poll", "Must be at most 64 Charictors long!");
        return;
    }
    clearError("poll");
}
function validateInterval(){
    box = document.getElementById("interval");  
    if (box.value == ""){
        setError("interval", "Must be supplied!");
        return;
    }
    if (box.value.length > 64){
        setError("interval", "Must be at most 64 Charictors long!");
        return;
    }
    clearError("interval");
}
function validateArchive(){
    box = document.getElementById("archive");  
    if (box.value == ""){
        setError("archive", "Must be supplied!");
        return;
    }
    if (box.value.length > 256){
        setError("archive", "Must be at most 64 Charictors long!");
        return;
    }
    clearError("archive");
}
function validateKey(){
    box = document.getElementById("key");  
    if (box.value.length > 64){
        setError("key", "Must be at most 64 Charictors long!");
        return;
    }
    clearError("key");
}
function validateForm()
{
    errCount=0;
    validateClassName();
    validatePoll();
    validateInterval();
    validateArchive();
    validateKey();
}
