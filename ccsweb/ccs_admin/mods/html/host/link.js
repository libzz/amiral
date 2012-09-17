/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Asset Management Interface - Link Addition / Modification
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

errCount=0;
url = "https://" + site + "/mods/host/link.php";

// Register Validation Rules
var myrules = {
    '#mode' : function(element){
        element.onchange = mode_selected;
    },
    '#type' : function(element){
        element.onchange = type_selected;
    },
	'#description' : function(element){
        element.onchange = validateDescription;
    },
	'#essid' : function(element){
        element.onchange = validateESSID;
    },
	'#key' : function(element){
        element.onchange = validateKey;
    },
    '#class_id' : function(element){
        element.onchange = class_selected;
    },
	//'#network_address' : function(element){
    //    element.onchange = validateNWAddress;
    //},
    '#addform' : function(element){
        element.onsubmit = checkForm;
    },
    '#editform' : function(element){
        element.onsubmit = checkForm;
    },
};
Behaviour.register(myrules);
Behaviour.addLoadEvent(initForm);

function class_selected()
{
    // Get the selected Class ID
    class_id = $F("class_id");
           
    // Retrieve the suggested network address
    pars = "do=getSuggestedNetwork&class_id=" + class_id;
    myAjax = new Ajax.Updater({success: 'network_address-cell'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:insertNWAddress});
}
function insertNWAddress(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
    //validateNWAddress();
}
function type_selected()
{
    // Get the selected type
    type_name = $F("type");

    // Disable Wireless Entries if appropriate
    rows = new Array("essid", "channel", "key");
    for (i=0;i<rows.length;i++) {
        header = $(rows[i] + "-row");
        if (type_name != "Managed" && type_name != "Ad-Hoc") {
            Element.addClassName(header, "hidden");
            clearError(rows[i]);
        } else {
            Element.removeClassName(header, "hidden");
        }
    }
    if (type_name == "Managed" || type_name == "Ad-Hoc") {
        validateESSID();
        validateKey();
    }

    // Retrieve the list of modes
    pars = "do=getModeList&type_name=" + type_name;
    myAjax = new Ajax.Updater({success: 'mode-cell'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:insertModeList});

}
function insertModeList(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
    mode_selected();
}
function mode_selected()
{
    // Get the selected type
    mode = $F("mode");
    type_name = $F("type");

    // Nothing to do for not wireless links
    if (type_name != "Managed" && type_name != "Ad-Hoc") {
        return;
    }

    // Retrieve the list of modes
    pars = "do=getChannelList&mode=" + mode;
    myAjax = new Ajax.Updater({success: 'channel-cell'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError});

}
function validateDescription()
{
    box = $("description");
    if (box.value == "") {
        setError("description", "Description must be specified!");
        return;
    }
    if (box.value.length > 250) {
        setError("description", "Description must not be more than 250 " +
            "characters!");
        return;
    }
    clearError("description");
}
function validateESSID()
{
    header = $("essid-row")
    if (Element.hasClassName(header, "hidden")) {
        clearError("essid");
        return;
    }
    box = $("essid");
    if (box.value == "") {
        setError("essid", "ESSID must be specified!");
        return;
    }
    if (box.value.length > 64) {
        setError("essid", "ESSID must not be more than 64 characters!");
        return;
    }
    clearError("essid"); 
}
function validateKey()
{
    header = $("key-row")
    if (Element.hasClassName(header, "hidden")) {
        clearError("key");
        return;
    }
    box = $("key");
    if (box.value == "") {
        clearError("key");
        return;
    }
    if (box.value.length != 32) {
        setError("key", "WEP Key must be 32 characters!");
        return;
    }
    clearError("key"); 
}
function validateNWAddress()
{
    box = $("network_address");
    if (box.value == "") {
        setError("network_address", "Network Address must be specified!");
        return;
    }
    // XXX: XMLRPC up a validation call here
    clearError("network_address"); 
}

function initForm()
{
    // Use link ID as a key to determine whether to init fields or not
    // If link_id is not present, we are adding and the fields are initialised
    link_id = document.getElementById("link_id")    
    if (!link_id) {
        class_selected();
        type_selected();
    }
    // Always perform initial validation.
    validateForm();
}
function validateForm()
{
    validateDescription();
    validateESSID();
    validateKey();
    //validateNWAddress();
}
function checkForm()
{
    
    warncount = 0;
    
    // Get all TH elements
    headers = document.getElementsByTagName("TH");
    for (i=0;i<headers.length;i++) {
        th = headers.item(i);
        if (th.id.indexOf("-header") == -1)
            continue;
        if (Element.hasClassName(th, "error")) {
            name = getTextValue(th);
            alert("You must specify a value for the '" + name + "' field!");
            return false;
        }
        if (Element.hasClassName(th, "warning")) {
            warncount++;
        }
    }

    if (warncount > 0) {
        rv = confirm("There are some warnings present on the form. Do you " +
            "want to continue? This may cause problems later on.");
        if (rv != 1) {
            return false;
        }
    }

    return true;

}
