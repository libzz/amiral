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
    '#name' : function(element){
        element.onchange = validateName;
    },
    '#poll' : function(element){
        element.onchange = validatePoll;
    },
    '#max' : function(element){
        element.onchange = validateMax;
    },
    '#min' : function(element){
        element.onchange = validateMin;
    }
};

Behaviour.register(myrules);
Behaviour.addLoadEvent(validateForm);

function  validateName(){
    box = document.getElementById("name");  
    if (box.value == ""){
        setError("name", "Must be supplied!");
        return;
    }
    if (box.value.length > 64){
        setError("name", "Must be at most 64 Charictors long!");
        return;
    }
    var anum=/(^[A-Za-z0-9-_]+$)|(^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$)/
    if (!anum.test(box.value)){
        setError("name", "Must be a number!");
        return;
    }

    clearError("name");
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
function validateMax(){
    box = document.getElementById("max");  
    var anum=/($^)|(^\d+$)|(^\d+\.\d+$)/
    if (!anum.test(box.value)){
        setError("max", "Must be a number!");
        return;
    }
    clearError("max");
}
function validateMin(){
    box = document.getElementById("min");  
    var anum=/($^)|(^\d+$)|(^\d+\.\d+$)/
    if (!anum.test(box.value)){
        setError("min", "Must be a number!");
        return;
    }
    clearError("min");
}
function validateForm()
{
    errCount=0;
    validateName();
    validatePoll();
    validateMax();
    validateMin();
}
