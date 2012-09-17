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
    '#group_name' : function(element){
        element.onchange = validateName;
    }
};

Behaviour.register(myrules);
Behaviour.addLoadEvent(validateForm);

function validateName(){
    box = document.getElementById("group_name");  
    if (box.value == ""){
        setError("name", "Must be supplied!");
        return;
    }
    if (box.value.length > 64){
        setError("name", "Must be at most 64 Charictors long!");
        return;
    }
    clearError("name");
}

function validateForm()
{
    errCount=0;
    validateName();
}
