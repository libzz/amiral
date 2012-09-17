/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Asset Management Interface - Wireless Card Bulk Asset Addition
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
// Register Rules
var myrules = {
    '#asset_type' : function(element){
        element.onchange = asset_selected;
    },
    '#description' : function(element){
        element.onchange = validateDescription;
    },
	'#price' : function(element){
        element.onchange = validatePrice;
    },
	'#supplier' : function(element){
        element.onchange = validateSupplier;
    },
	'#no_cards' : function(element){
        element.onchange = noCardsChanged;
    },
};
Behaviour.register(myrules);
//Behaviour.addLoadEvent(initForm);

function asset_selected()
{

    disableForm();

    // Enable the form if a valid asset type has been selected
    asset_type_id = $F("asset_type");
    if (asset_type_id != -1) {
        enableForm(asset_type_id);
    }
    
}
function getAssetTypeName(asset_type_id)
{
    // Get the select box
    box = $("asset_type");
    if (!box) {
        return "";
    }

    for (i=0;i<box.options.length;i++) {
        if (box.options.item(i).value == asset_type_id) {
            return box.options.item(i).text;
        }
    }

    return "";

}
function disableForm()
{
    disableControl("description");
    disableControl("serialno");
    disableControl("date_purchased_Year");
    disableControl("date_purchased_Month");
    disableControl("date_purchased_Day");
    disableControl("currency");
    disableControl("price");
    disableControl("supplier");
    disableControl("enabled");
    disableControl("notes");

    setTextDefault("description", "");

    errCount = 0;
     
    clearError("description");
    clearError("serialno");
    clearError("price");
    clearError("supplier");
    
    target = $("icard-table");
    for (i=1;i<target.childNodes.length;i++) {
        t = target.childNodes.item(i);
        if (t.tagName == "TR") {
            parts = t.id.split("-");
            clearError(parts[0]);
            target.removeChild(t);
            i--;
        }
    }

    setInstructions("Please select the type of asset you would like to " +
        "add from the list below. You will then be able to enter the " +
        "remaining details for the asset.");
        
    disableSubmit();
    Behaviour.apply();

}
function enableForm(asset_type_id)
{

    setInstructions("Please wait while the information for the " +
        "specified asset type is retrieved for you...");

    enableControl("description");
    enableControl("date_purchased_Year");
    enableControl("date_purchased_Month");
    enableControl("date_purchased_Day");
    enableControl("currency");
    enableControl("price");
    enableControl("supplier");
    enableControl("enabled");
    enableControl("notes");

    setTextDefault("description", getAssetTypeName(asset_type_id));

    errCount = 0;
   
    validateDescription();
    validatePrice();
    validateSupplier();

    // Create the specified number of asset entries
    addCardRows($F("no_cards"));
    Behaviour.apply();

}
function addCardRows(n)
{
    var myrules = new Array();
   
    tbl = $("icard-table");
    for (i=1;i<=n;i++) {
        obj = $("icard_" + i + "-row");
        if (obj) {
            continue;
        }
        row = document.createElement("TR");
        row.id = "icard_" + i + "-row";
        head = document.createElement("TD");
        head.id = "icard_" + i + "-header";
        head.appendChild(document.createTextNode("#" + i));
        serial = document.createElement("TD");
        serialinput = document.createElement("INPUT");
        serialinput.type = "text";
        serialinput.id = "icard_" + i + "-serial";
        serialinput.name = serialinput.id;
        myrules["#" + serialinput.id] = function(element){
            element.onchange = validateCard;
        }
        serialinput.value = "";
        serial.appendChild(serialinput);
        mac = document.createElement("TD");
        macinput = document.createElement("INPUT");
        macinput.type = "text";
        macinput.id = "icard_" + i + "-mac";
        macinput.name = macinput.id;
        myrules["#" + macinput.id] = function(element){
            element.onchange = validateCard;
        }
        macinput.value =  "";
        mac.appendChild(macinput);
        row.appendChild(head);
        row.appendChild(serial);
        row.appendChild(mac);
        tbl.appendChild(row);
        setError("icard_" + i, "You must specify a serial number and " +
            "MAC address!");
    }
    Behaviour.register(myrules);

}
function noCardsChanged() 
{
    
    n = $F("no_cards");
    target = $("icard-table");
    
    if (target.childNodes.length==0) {
        addCardRows(n);
        return;
    }
    if (n == 0) {
        alert("Must be at least 1 card!");
        $("no_cards").value = "1";
        return;
    }

    c=0;
    for (i=1;i<target.childNodes.length;i++) {
        t = target.childNodes.item(i);
        if (t.tagName == "TR") {
            c++;
            if (c > n) {
                parts = t.id.split("-");
                clearError(parts[0]);
                target.removeChild(t);
                i--;
            }
        }
    }   
    if (c<n) {
        addCardRows(n);
    }
    Behaviour.apply();

}
function validateCard(e)
{
    name = e.target.id;
    parts = name.split("-");
    serial = $F(parts[0] + "-serial");
    mac = $F(parts[0] + "-mac");

    if (serial != "" && mac != "") {
        clearError(parts[0]);
    } else {
        setError(parts[0], "You must specify a serial number and " +
            "MAC address!");
    }

}
function validateDescription()
{
    value = $F("description");
    if (value == "") {
        setError("description", "You must enter a description!");
        return;
    }    
    if (value.length > 64) {
        setError("description", 
            "Description must not be more than 64 characters");
        return;
    }
    clearError("description");
}
function validateSerialno()
{
    value = $F("serialno");
    if (value == "") {
        setWarning("serialno", "Please enter a serial number!");
        return;
    }
    if (value.length > 32) {
        setError("serialno", 
            "Serial number must not be more than 32 characters");
        return;
    }
    clearError("serialno");
    
}
function validatePrice()
{
    value = $F("price");
    if (!isNumeric(value)) {
        setError("price", "Invalid price entered! Must be numeric!");
        return;
    }
    if (value == 0) {
        setWarning("price", "Price should be greater than 0!");
        return;
    }
    clearError("price");

}
function validateSupplier()
{
    value = $F("supplier");
    if (value == "") {
        setWarning("supplier", "Supplier should not be empty!");
        return;
    }
    clearError("supplier");

}
function validateForm()
{
    
    warncount = 0;
    
    // Get all TH elements
    headers = document.getElementsByTagName("TH");
    for (i=0;i<headers.length;i++) {
        th = headers.item(i);
        if (th.id.indexOf("-header") == -1)
            continue;
        if (th.className == "error") {
            name = getTextValue(th);
            alert("You must specify a value for the '" + name + "' field!");
            return false;
        }
        if (th.className == "warning") {
            warncount++;
        }
    }

    if (warncount > 0) {
        rv = confirm("One or more required fields are not completed. " +
            "Do you want to continue using their default values?");
        if (rv != 1) {
            return false;
        }
    }

    return true;

}
function setInstructions(text)
{

    item = $("instructions");
    ctext = item.firstChild;
    item.replaceChild(document.createTextNode(text), ctext);

}
