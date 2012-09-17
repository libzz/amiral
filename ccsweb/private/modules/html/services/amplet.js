/* Copyright (C) 2006  The University of Waikato
 *
 * Amplet Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
errCount=0;
url = "https://" + site + "/mods/service/amplet.php";

// Register Rules
var myrules = {
    '#service_host_enabled' : function(element){
        element.onchange = hostEnabledChanged;
    },
    '#amplet_group' : function(element){
        element.onchange = hostPropertyChanged;
    }
};
Behaviour.register(myrules);

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
    pars =  "do=updateAmpletHostProperty&service_id=" + service_id + 
        "&host_id=" + host_id + "&propName=" + name + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'amplet-host-details'}, url, 
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
    pars =  "do=updateAmpletState&service_id=" + service_id + 
        "&host_id=" + host_id + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'amplet-host-details'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function updateDiv(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
}

