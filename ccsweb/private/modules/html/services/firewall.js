/* Copyright (C) 2006  The University of Waikato
 *
 * Firewall Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
errCount=0;
url = "https://" + site + "/mods/service/firewall.php";

// Register Rules
var myrules = {
    '#service_host_enabled' : function(element){
        element.onchange = hostEnabledChanged;
    }
};
Behaviour.register(myrules);
Behaviour.addLoadEvent(initForm);

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
    pars =  "do=updateFirewallState&service_id=" + service_id + 
        "&host_id=" + host_id + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'firewall-host-details'}, url, 
        {method: 'post', parameters: pars, onFailure: reportError,
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
    firewall_class_id = $F(name);
    host_id = $F("host_id");
    service_id = $F("service_id");
    interface_id = parts[2];

    // Disable things while updating
    ref.disabled = true;

    // Update
    pars =  "do=updateFirewallInterface&service_id=" + service_id + 
        "&host_id=" + host_id + "&interface_id=" + interface_id +
        "&firewall_class_id=" + firewall_class_id;
    myAjax = new Ajax.Updater(
        {success: 'interface-' + interface_id}, url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function initForm()
{
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
        if (parts[0] != "iface") {
            continue;
        }
        // Setup appropriate validator for interface properties
        if (parts[1] == "firewall_class_id") {
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
