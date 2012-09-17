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
url = "https://" + site + "/mods/graphs/config-graphs.php"
// Register Validation Rules
var myrules = {
    '#type' : function(element){
        element.onchange = type_selected;
    },
    '#varname' : function(element){
        element.onchange = validataVarname;
    },
    '#colour' : function(element){
        element.onchange = validateColour;
    },
	'#text' : function(element){
        element.onchange = validateText;
    },
	'#cf' : function(element){
        element.onchange = validateCf;
    },
	'#graph_order' : function(element){
        element.onchange = validateOrder;
    }
    
};

Behaviour.register(myrules);
Behaviour.addLoadEvent(validateForm);

function validataVarname(){
    type_o = $("type");
    if (type_o)
        type = $F("type");
    box = document.getElementById("varname");  
    if (type == "VRULE"){
        if (box.value == ""){
            setError("varname", "Must set a time!");
            return;
        }
        var anum=/(^\d+$)|(^\d+\.\d+$)/
        if (!anum.test(box.value)){
            setError("varname", "Must be a number!");
            return;
        }
    }
    if (box.value == ""){
        setError("varname", "Must be supplied!");
        return;
    }
    clearError("varname");
}
function validateColour(){
    box = document.getElementById("colour");   
    if (box){
        if (box.value == ""){
            setError("colour", "Colour must be given!");
            return;
        }
        //Hex is required
        var anum=/(^[0123456789ABCDEFabcdef]+$)|(^[0123456789ABCDEFabcdef]+\.[0123456789ABCDEFabcdef]+$)/
        if (!anum.test(box.value)){
            setError("colour", "Invalid Characters!");
            return;
        }
        if (box.value.length != 6){
            setError("colour", "Need 6 charactors!");
            return;
        }
    }

    clearError("colour");
}
function validateText(){
    type_o = $("type");
    if (type_o)
        type = $F("type");
    box = document.getElementById("text");   
    if (box){
    if (box.value == ""){
        setError("text", "Chain must be given!");
        return;
    }}
        
    clearError("text");
}
function validateCf(){
    clearError("cf");
}
function validateOrder(){
    box = document.getElementById("graph_order");   
    if (box){
    if (box.value == ""){
        setError("order", "Must be given!");
        return;
    }
    var anum=/(^\d+$)|(^\d+\.\d+$)/
    if (!anum.test(box.value)){
        setError("order", "Must be a number!");
        return;
    }}
    clearError("order");
}


// When a type is selected update the variables (and page)
function type_selected()
{
    group_ido = $("group_id");
    if (group_ido)
        group_id = $F("group_id");
    class_ido = $("class_id");
    if (class_ido)
        class_id = $F("class_id");        
    graph_ido = $("graph_id");
    if (graph_ido)
        graph_id = $F("graph_id");
    part_ido = $("part_id");
    if (part_ido)
        part_id = $F("part_id");
    typeo = $("type");
    if (typeo)
        type = $F("type");        
    actiono = $("do");
    if (actiono)
        action = $F("do");          
    // Retrieve the list of available variables for this part
    pars = "do=getvars&group_id=" + group_id + "&graph_id=" + graph_id + "&part_id=" + part_id + "&type=" + type + "&class_id=" + class_id + "&action=" + action;
    myAjax = new Ajax.Updater({success: 'part-div'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion: insertList});
}

// Insert new infomation
function insertList(object, string) 
{
    object.innerHTML = string;
    Behaviour.apply();
    validateForm();
}

function validateForm()
{
    errCount=0;
    validataVarname();
    validateColour();
    validateText();
    validateCf();
    validateOrder();
}
