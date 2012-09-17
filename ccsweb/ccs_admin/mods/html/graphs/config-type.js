/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Graph manipulation user interface
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
    '#title' : function(element){
        element.onchange = validateName;
    },
    '#virtical_label' : function(element){
        element.onchange = validateLabel;
    }
};

Behaviour.register(myrules);
Behaviour.addLoadEvent(validateForm);

function validateName(){
    box = document.getElementById("title");  
    if (box.value == ""){
        setError("title", "Must be supplied!");
        return;
    }
    if (box.value.length > 64){
        setError("title", "Must be at most 64 Charictors long!");
        return;
    }
    clearError("title");
}
function validateLabel(){
    box = document.getElementById("virtical_label");  
    if (box.value.length > 64){
        setError("label", "Must be at most 64 Charictors long!");
        return;
    }
    clearError("label");
}

function validateForm()
{
    errCount=0;
    validateName();
    validateLabel();
}
