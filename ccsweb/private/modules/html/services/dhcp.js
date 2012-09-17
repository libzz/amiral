/* Copyright (C) 2006  The University of Waikato
 *
 * DHCP Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless 
 * otherwise confirmed in writing by the copyright holder.
 */

errCount=0;
url = "https://" + site + "/mods/service/dhcp.php";
ifaceProps = new Array("pool_min", "pool_max", "router_ip");

// Register Rules
var myrules = {
    '#service_host_enabled' : function(element){
        element.onchange = hostEnabledChanged;
    },
    '#ns1' : function(element){
        element.onchange = hostPropertyChanged;
    },
	'#ns2' : function(element){
        element.onchange = hostPropertyChanged;
    },
	'#domain' : function(element){
        element.onchange = hostPropertyChanged;
    },
	'#default_lease_time' : function(element){
        element.onchange = hostPropertyChanged;
    },
	'#max_lease_time' : function(element){
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
        pars = "do=enableDHCPInterface&" + pars;
    } else {
        disableInterface(interface_id);
        pars = "do=disableDHCPInterface&" + pars;
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
        item = "iface-" + ifaceProps[i] + "-" + interface_id;
        ref = $(item + "-row");
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
    pars =  "do=updateDHCPHostProperty&service_id=" + service_id + 
        "&host_id=" + host_id + "&propName=" + name + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'dhcp-host-details'}, url, 
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
    pars =  "do=updateDHCPState&service_id=" + service_id + 
        "&host_id=" + host_id + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'dhcp-host-details'}, url, 
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

    // Validate properties
    if (parts[1] == "pool_min" || parts[1] == "pool_max") {
        if (val == "") {
            setError(name, "You must specify the extents of the allocation " +
                "pool!");
            return;
        } else {
            clearError(name);
        }
    }

    // Disable things while updating
    ref.disabled = true;

    // Update
    pars =  "do=updateDHCPInterface&service_id=" + service_id + 
        "&host_id=" + host_id + "&interface_id=" + interface_id +
        "&param=" + parts[1] + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'interface-' + interface_id}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function initForm()
{
    // Dynamically find all interface input elements
    attachEvents(document.getElementsByTagName("INPUT"));
}
function attachEvents(tagList)
{
    // Register Validation Rules
    var myrules = new Array();
    for (i=0;i<tagList.length;i++) {
        prop = tagList.item(i);
        if (prop.id.substr(0, 5) != "iface") {
            continue;
        }
        // Interface property, extract prop name
        parts = prop.id.split("-");
        if (parts.length < 3) {
            continue; // Bogus id
        }
        name = "#" + prop.id;
        // Setup appropriate validator
        if (parts[1] == "dhcp_enabled") {
            myrules[name] = function(element){
                element.onchange = interfaceStateChanged;
            }
        } else if (parts[1] == "pool_min") {
            myrules[name] = function(element){
                element.onchange = ifacePropChanged;
            }
        } else if (parts[1] == "pool_max") {
            myrules[name] = function(element){
                element.onchange = ifacePropChanged;
            }
        } else if (parts[1] == "router_ip") {
            myrules[name] = function(element){
                element.onchange = ifacePropChanged;
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
}
