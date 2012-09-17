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
url = "https://" + site + "/mods/service/amplet.php";

// Register Rules
var myrules = {
    '#ping_perturb' : function(element){
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
    pars =  "do=updateAmpletProperty&service_id=" + service_id + 
        "&propName=" + name + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'amplet-details'}, url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function updateDiv(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
}
