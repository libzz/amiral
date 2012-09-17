/* Copyright (C) 2006  The University of Waikato
 *
 * Quagga Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
errCount=0;
url = "https://" + site + "/mods/service/quagga.php";
ifaceProps = new Array("ospf_enabled", "area_no", "priority", "md5_auth",
    "md5_key");

// Register Rules
var myrules = {
    '#service_host_enabled' : function(element){
        element.onchange = hostEnabledChanged;
    },
    '#telnet_password' : function(element){
        element.onchange = hostPropertyChanged;
    },
	'#enable_password' : function(element){
        element.onchange = hostPropertyChanged;
    },
	'#redistribute_static' : function(element){
        element.onchange = hostPropertyChanged;
    },
	'#redistribute_connected' : function(element){
        element.onchange = hostPropertyChanged;
    }
};
Behaviour.register(myrules);
Behaviour.addLoadEvent(initForm);

function interfaceStateChanged(e)
{
    name = e.target.id;
    parts = name.split("-");
    if (parts.length < 3) {
        return; // Bogus id
    }

    val = $F(name);
    host_id = $F("host_id");
    service_id = $F("service_id");
    interface_id = parts[2];


    pars =  "service_id=" + service_id + "&host_id=" + host_id + 
        "&interface_id=" + interface_id;
    if (val) {
        showInterface(interface_id);
        disableInterface(interface_id);
        pars = "do=enableOSPFInterface&" + pars;
    } else {
        disableInterface(interface_id);
        pars = "do=disableOSPFInterface&" + pars;
    }
    myAjax = new Ajax.Updater({success: 'interface-' + interface_id}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function disableInterface(interface_id)
{
    for (i=0;i<ifaceProps.length;i++) {
        item = "iface-" + ifaceProps[i] + "-" + interface_id;
        ref = $(item);
        ref.disabled = true;
    }
}
function showInterface(interface_id)
{
    for (i=0;i<ifaceProps.length;i++) {
        item = "iface-" + ifaceProps[i] + "-" + interface_id + "-row";
        ref = $(item);
        Element.removeClassName(ref, "hidden");
    }
}
function hostPropertyChanged(e)
{
    name = e.target.id;
    ref = $(name);
    val = ref.value;
    host_id = $F("host_id");
    service_id = $F("service_id");

    // Disable things while updating
    ref.disabled = true;

    // Update
    pars =  "do=updateQuaggaHostProperty&service_id=" + service_id + 
        "&host_id=" + host_id + "&propName=" + name + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'quagga-host-details'}, url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function hostEnabledChanged(e)
{
    name = e.target.id;
    ref = $(name);
    val = escape(ref.value);
    host_id = $F("host_id");
    service_id = $F("service_id");

    // Disable things while updating
    ref.disabled = true;

    // Update
    pars =  "do=updateQuaggaState&service_id=" + service_id + 
        "&host_id=" + host_id + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'quagga-host-details'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function md5StateChanged(e)
{
    name = e.target.id;
    parts = name.split("-");
    if (parts.length < 3) {
        return; // Bogus id
    }
    ref = $(name);
    val = $F(name);
    host_id = $F("host_id");
    service_id = $F("service_id");
    interface_id = parts[2];

    // Disable things while updating
    item = "iface-md5_key-" + interface_id;
    ref2 = $(item);
    ref.disabled = true;
    ref2.disabled = true;
    ref2 = $(item + "-row");

    // Update
    pars =  "do=updateOSPFInterface&service_id=" + service_id + 
        "&host_id=" + host_id + "&interface_id=" + interface_id +
        "&param=md5_auth&value=";
    if (val) {
        pars += "t";
        Element.removeClassName(ref2, "hidden");
    } else {
        pars += "f";
        Element.addClassName(ref2, "hidden");
    }
    myAjax = new Ajax.Updater(
        {success: 'interface-' + interface_id}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function ifacePropChanged(e)
{
    name = e.target.id;
    parts = name.split("-");
    if (parts.length < 3) {
        return; // Bogus id
    }
    ref = $(name);
    val = $F(name);
    host_id = $F("host_id");
    service_id = $F("service_id");
    interface_id = parts[2];

    // Disable things while updating
    ref.disabled = true;

    // Update
    pars =  "do=updateOSPFInterface&service_id=" + service_id + 
        "&host_id=" + host_id + "&interface_id=" + interface_id +
        "&param=" + parts[1] + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'interface-' + interface_id}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function staticPropChanged(e)
{
    name = e.target.id;
    parts = name.split("-");
    if (parts.length < 3) {
        return; // Bogus id
    }
    ref = $(name);
    val = $F(name);
    host_id = $F("host_id");
    service_id = $F("service_id");
    static_id = parts[2];

    // Validate if necessary
    if (parts[1] != "metric") {
        if (val == "") {
            Element.addClassName(ref, "error");
            return;
        } else {
            Element.removeClassName(ref, "error");
        }
    }

    if (static_id == "NEW") {
        // If this was the last field to be cleared of errors do the add
        a = Element.hasClassName($("static-description-NEW"), "error");
        b = Element.hasClassName($("static-prefix-NEW"), "error");
        c = Element.hasClassName($("static-next_hop-NEW"), "error");
        if (a || b || c) {
            return;
        } else {
            // Add
            disableStatic("NEW");
            Element.addClassName($("static-remove-NEW"), "disabled");
            pars = "do=createStatic&service_id=" + service_id + 
                "&host_id=" + host_id + "&description=" + 
                $F("static-description-NEW") + "&prefix=" + 
                $F("static-prefix-NEW") + "&next_hop=" +
                $F("static-next_hop-NEW");
        }
    } else {
        // Disable things while updating
        ref.disabled = true;

        // Update
        pars =  "do=updateStatic&service_id=" + service_id + 
            "&host_id=" + host_id + "&static_id=" + static_id +
            "&param=" + parts[1] + "&value=" + val;
    }
    myAjax = new Ajax.Updater(
        {success: 'statics'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function addStatic()
{
    
    // Check that there is not already an addition active
    if ($("static-description-NEW")) {
        $("static-description-NEW").focus();
        return;
    }

    // Insert a row for the addition
    pars =  "do=newStatic";
    myAjax = new Ajax.Updater(
        {success: 'statics'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:appendStaticRow});

}
function disableStatic(static_id)
{
    $("static-description-" + static_id).disabled = true;
    $("static-prefix-" + static_id).disabled = true;
    $("static-next_hop-" + static_id).disabled = true;
    $("static-metric-" + static_id).disabled = true;
}
function removeStatic(static_id)
{
    host_id = $F("host_id");
    service_id = $F("service_id");

    if (static_id == "NEW") {
        // Easy to delete NEW row, no need to talk to server
        row = $("static-row-NEW");
        row.parentNode.removeChild(row);
        Element.removeClassName($("add-static-button"), "disabled");
        return;
    }

    disableStatic(static_id);
    pars =  "do=removeStatic&service_id=" + service_id + 
            "&static_id=" + static_id + "&host_id=" + host_id;
    myAjax = new Ajax.Updater(
        {success: 'statics'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:updateDiv});  
}
function initForm()
{
    // Dynamically find all interface input elements
    attachEvents(document.getElementsByTagName("INPUT"));
    // Dynamically find all interface select elements
    attachEvents(document.getElementsByTagName("SELECT"));
}
function attachEvents(tagList)
{
    // Register Validation Rules
    var myrules = new Array();
    for (i=0;i<tagList.length;i++) {
        prop = tagList.item(i);
        // Interface property, extract prop name
        parts = prop.id.split("-");
        if (parts.length < 3) {
            continue; // Bogus id
        }
        name = "#" + prop.id;
        if (parts[0] == "iface") {
            // Setup appropriate validator for interface properties
            if (parts[1] == "ospf_enabled") {
                myrules[name] = function(element){
                    element.onchange = interfaceStateChanged;
                }
            } else if (parts[1] == "md5_auth") {
                myrules[name] = function(element){
                    element.onchange = md5StateChanged;
                }
            } else if (parts[1] == "md5_key") {
                myrules[name] = function(element){
                    element.onchange = ifacePropChanged;
                }
            } else if (parts[1] == "area_no") {
                myrules[name] = function(element){
                    element.onchange = ifacePropChanged;
                }
            } else if (parts[1] == "priority") {
                myrules[name] = function(element){
                    element.onchange = ifacePropChanged;
                }
            }
        } else if (parts[0] == "static") {
            // Setup validators for static routes
            if (parts[1] == "description") {
                myrules[name] = function(element){
                    element.onchange = staticPropChanged;
                }
            } else if (parts[1] == "prefix") {
                myrules[name] = function(element){
                    element.onchange = staticPropChanged;
                }
            } else if (parts[1] == "next_hop") {
                myrules[name] = function(element){
                    element.onchange = staticPropChanged;
                }
            } else if (parts[1] == "metric") {
                myrules[name] = function(element){
                    element.onchange = staticPropChanged;
                }
            }
        }
    }
    Behaviour.register(myrules);
    Behaviour.apply();
}
function updateDiv(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
    Element.removeClassName($("add-static-button"), "disabled");
}
function appendStaticRow(object, string)
{
    new Insertion.Bottom(object, string);
    Behaviour.apply();
    attachEvents(document.getElementsByTagName("INPUT"));
    Element.addClassName($("static-description-NEW"), "error");
    Element.addClassName($("static-prefix-NEW"), "error");
    Element.addClassName($("static-next_hop-NEW"), "error");
    $("static-description-NEW").focus();
    Element.addClassName($("add-static-button"), "disabled");
}
