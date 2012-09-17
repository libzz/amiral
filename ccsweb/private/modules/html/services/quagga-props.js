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

// Register Rules
var myrules = {
    '#telnet_password' : function(element){
        element.onchange = propertyChanged;
    },
	'#enable_password' : function(element){
        element.onchange = propertyChanged;
    },
	'#md5_key' : function(element){
        element.onchange = propertyChanged;
    },
	'#redistribute_static' : function(element){
        element.onchange = propertyChanged;
    },
	'#redistribute_connected' : function(element){
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
    pars =  "do=updateQuaggaProperty&service_id=" + service_id + 
        "&propName=" + name + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'quagga-details'}, url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function updateDiv(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
}
