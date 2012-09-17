/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Asset Management Interface - Asset Addition
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

function asset_selected()
{

    // Get the select box
    box = document.getElementById("asset_type");
    asset_type_id = box.options.item(box.selectedIndex).value;
   
    disableForm();
    
    if (asset_type_id != -1) {
        enableForm(asset_type_id);
    }
    
}
function getAssetTypeName(asset_type_id)
{
    // Get the select box
    box = document.getElementById("asset_type");
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
    
    target = document.getElementById("required-subassets");
    while (target.childNodes.length > 0) {
        target.removeChild(target.firstChild);
    }

    setInstructions("Please select the type of asset you would like to " +
        "add from the list below. You will then be able to enter the " +
        "remaining details for the asset.");
        
    target = document.getElementById("subassets");
    target.setAttribute("value", "");
    disableSubmit();

}
function enableForm(asset_type_id)
{

    setInstructions("Please wait while the information for the " +
        "specified asset type is retrieved for you...");

    enableControl("description");
    enableControl("serialno");
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
    validateSerialno();
    validatePrice();
    validateSupplier();

    // Retrieve the subassets
    url = "https://" + site + "/mods/asset/asset.php?do=" +
        "listSubassetTypes&asset_type_id=" + asset_type_id +
        "&callback=processEnableForm";
    loadXMLDoc(url, null);
    // Wait until all requests have completed
    if (req != null) {
        setTimeout("complete()", 100);
    } else {
        complete();
    }
}

function processEnableForm(result) 
{

    if (result.length < 1) {
        alert("Invalid result received!");
        return;
    }
    
    t = result[0].getElementsByTagName("success")[0];
    if (!t) {
        alert("Invalid result - Misformed XML!");
        return;
    }
    success = t.firstChild.data;
    if (success != 0) {
        t = result[0].getElementsByTagName("errMsg")[0];
        errMsg = t.firstChild.data;
        alert(errMsg);
        return;
    }
    
    subassets = "";
    for (i=2;i<result[0].childNodes.length;i++) {
        subasset = result[0].childNodes.item(i);
        name = addSubasset(subasset);
        if (name == "") {
            return;
        }
        subassets += name + " ";
    }
    target = document.getElementById("subassets");
    target.setAttribute("value", subassets);
    
    setInstructions("Please enter the initial data for this asset using " +
        "the fields below. If you have entered incorrect data, or have " +
        "failed to complete a required field a warning or error icon will " +
        "appear to the right of the heading. You will not be able to add " +
        "the asset while errors are present on the form.");
    
}
function addSubasset(subasset)
{
    // Get required stats
    t = subasset.getElementsByTagName("required")[0];
    if (!t) {
        alert("Invalid result - Misformed subasset XML!");
        return "";
    }       
    required = t.firstChild.data;
    if (required == "t") {
        return addRequiredSubasset(subasset);
    } else {
        return addOptionalSubasset(subasset);
    }
}
function addRequiredSubasset(subasset)
{

    description = getFromTagName(subasset, "description");
    name = getFromTagName(subasset, "name");
    asset_type_subasset_id = 
        getFromTagName(subasset, "asset_type_subasset_id");
    subasset_type_id = getFromTagName(subasset, "subasset_type_id");

    div = document.createElement("div");
    div.id = "subasset-" + asset_type_subasset_id;
    div.className = "subasset";

    h2 = document.createElement("h2");
    h2.appendChild(document.createTextNode(description + " - " + name));
    div.appendChild(h2);

    table = document.createElement("table");
    table.id = "subasset-" + asset_type_subasset_id + "-properties";
    div.appendChild(table);

    target = document.getElementById("required-subassets");
    target.appendChild(div);

    // Add enabled row
    row = document.createElement("tr");
    header = document.createElement("th");
    header.setAttribute("width", 200);
    header.appendChild(document.createTextNode("Enabled"));
    row.appendChild(header);
    cell = document.createElement("td");
    field = document.createElement("input");
    field.setAttribute("type", "checkbox");
    field.setAttribute("name", "subasset-" + asset_type_subasset_id + 
        "-enabled");
    field.setAttribute("value", "yes");
    field.setAttribute("checked", "");
    cell.appendChild(field);
    row.appendChild(cell);
    table.appendChild(row);

    // Add dynamic property rows
    properties = subasset.getElementsByTagName("properties")[0];
    propids = "";
    for (j=0;j<properties.childNodes.length;j++) {
        prop = properties.childNodes.item(j);
        required = getFromTagName(prop, "required");
        description = getFromTagName(prop, "description");
        subasset_property_id = getFromTagName(prop, "subasset_property_id");
        default_value = getFromTagName(prop, "default_value");
        id = "subasset-" + asset_type_subasset_id + "-property-" + 
            subasset_property_id;

        row = document.createElement("tr");
        header = document.createElement("th");
        header.setAttribute("width", 200);
        header.id = "sap-" + id + "-header";
        header.appendChild(document.createTextNode(description));
        row.appendChild(header);
        cell = document.createElement("td");
        field = document.createElement("input");
        field.setAttribute("type", "text");
        field.setAttribute("size", "32");
        field.setAttribute("name", id + "-value");
        field.setAttribute("onchange", "validateSap('" + id + "','" + 
            required + "');");
        field.setAttribute("value", default_value);
        field.id = "sap-" + id + "-value"
        field.className = "assetdetails";
        cell.appendChild(field);
        row.appendChild(cell);
        table.appendChild(row);
        validateSap(id, required);
        propids += subasset_property_id + " ";
    }
    plist = document.createElement("input");
    plist.setAttribute("type", "hidden");
    plist.setAttribute("name", "subasset-" + asset_type_subasset_id + 
        "-propertylist");
    plist.setAttribute("value", propids);
    target.appendChild(plist);
    
    return asset_type_subasset_id;

}

function addOptionalSubasset(subasset)
{
}
function validateSap(subasset_property_id, required)
{
    box = document.getElementById("sap-" + subasset_property_id + "-value");
    if (!box) {
        return;
    }
    if (box.value == "" && required=="t") {
        setError("sap-" + subasset_property_id, 
            "You must enter a value for this property!");
        return;
    }    
    if (box.value.length > 64) {
        setError("sap-" + subasset_property_id, 
            "Property value must not be more than 64 characters");
        return;
    }
    clearError("sap-" + subasset_property_id);
}
function validateDescription()
{
    box = document.getElementById("description");
    if (box.value == "") {
        setError("description", "You must enter a description!");
        return;
    }    
    if (box.value.length > 64) {
        setError("description", 
            "Description must not be more than 64 characters");
        return;
    }
    clearError("description");
}
function validateSerialno()
{
    box = document.getElementById("serialno");
    if (box.value == "") {
        setWarning("serialno", "Please enter a serial number!");
        return;
    }
    if (box.value.length > 32) {
        setError("serialno", 
            "Serial number must not be more than 32 characters");
        return;
    }
    clearError("serialno");
    
}
function validatePrice()
{
    box = document.getElementById("price");
    if (!isNumeric(box.value)) {
        setError("price", "Invalid price entered! Must be numeric!");
        return;
    }
    if (box.value == 0) {
        setWarning("price", "Price should be greater than 0!");
        return;
    }
    clearError("price");

}
function validateSupplier()
{
    box = document.getElementById("supplier");
    if (box.value == "") {
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

    item = document.getElementById("instructions");
    ctext = item.firstChild;
    item.replaceChild(document.createTextNode(text), ctext);

}
