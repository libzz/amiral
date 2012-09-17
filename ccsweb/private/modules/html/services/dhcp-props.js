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

// Register Rules
var myrules = {
    '#ns1' : function(element){
        element.onchange = propertyChanged;
    },
	'#ns2' : function(element){
        element.onchange = propertyChanged;
    },
	'#domain' : function(element){
        element.onchange = propertyChanged;
    },
	'#default_lease_time' : function(element){
        element.onchange = propertyChanged;
    },
	'#max_lease_time' : function(element){
        element.onchange = propertyChanged;
    }
};
Behaviour.register(myrules);

function propertyChanged(e)
{
    name = e.target.id;
    ref = $(name);
    val = ref.value;
    service_id = $F("service_id");

    // Disable things while updating
    ref.disabled = true;

    // Update
    pars =  "do=updateDHCPProperty&service_id=" + service_id + 
        "&propName=" + name + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'dhcp-details'}, url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function updateDiv(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
}
