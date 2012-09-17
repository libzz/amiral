/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Asset Management Interface - Host Addition / Modification
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
url = "https://" + site + "/mods/host/host.php";

// Register Validation Rules
var myrules = {
    '#host_name' : function(element){
        element.onchange = validateHostname;
    },
    '#site_id' : function(element){
        element.onchange = site_selected;
    },
    '#asset_id' : function(element){
        element.onchange = validateAsset;
    },
	'#distribution_id' : function(element){
        element.onchange = validateDistribution;
    },
	'#kernel_id' : function(element){
        element.onchange = validateKernel;
    },
	'#host_active' : function(element){
        element.onchange = validateHostActive;
    },
    '#editForm' : function(element){
        element.onsubmit = checkForm;
    }
};
Behaviour.register(myrules);
Behaviour.addLoadEvent(validateForm);

function removeServiceFromHost(service_id)
{
    host_id = $F("host_id");

    // Retrieve the suggested network address
    pars = "do=removeServiceFromHost&host_id=" + host_id + "&service_id=" + 
        service_id;
    myAjax = new Ajax.Updater({success: 'services'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion: processServiceList});
}
function addServiceToHost(service_id)
{
    host_id = $F("host_id");

    // Retrieve the suggested network address
    pars = "do=addServiceToHost&host_id=" + host_id + "&service_id=" + 
        service_id;
    myAjax = new Ajax.Updater({success: 'services'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion: processServiceList});
}
function processServiceList(object, resString) {
    object.innerHTML = resString;
    Behaviour.apply();
}
function site_selected()
{
    site_id = host_id = -1;
    site_ido = $("site_id");
    if (site_ido)
        site_id = $F("site_id")
    host_ido = $("host_id");
    if (host_ido)
        host_id = $F("host_id")

    // Retrieve the list of available assets at this site
    pars = "do=listSiteAssets&site_id=" + site_id + "&host_id=" + host_id;
    myAjax = new Ajax.Updater({success: 'asset_id-cell'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion: insertAssetList});

}
function insertAssetList(object, string) 
{
    object.innerHTML = string;
    Behaviour.apply();
    validateSite();
    validateAsset();
}
function validateHostname()
{
    box = document.getElementById("host_name");
    if (box.value == "") {
        setError("host_name", "Hostname must be specified!");
        return;
    }
    if (box.value.length > 64) {
        setError("host_name", "Hostname must not be more than 64 characters!");
        return;
    }
    clearError("host_name");
    
}
function validateSite()
{
    combo = document.getElementById("site_id");
    if (!combo)
        return;
    if (combo.value == -1) {
        conf = document.getElementById("host_active");
        if (conf.checked) {
            setError("site_id", "You must select a valid site if you wish " +
                "to automatically configure this host!");
        } else {
            setWarning("site_id", "It is recommended that you select a " +
                "location for this host!");
        }
        return;
    }
    clearError("site_id");    
}
function validateAsset()
{
    combo = document.getElementById("asset_id");
    if (!combo)
        return;
    if (combo.value == -1) {
        conf = document.getElementById("host_active");
        if (conf.checked) {
            setError("asset_id", "You must select a valid asset if you wish " +
                "to automatically configure this host!");
        } else {
            setWarning("asset_id", "It is recommended that you select an " +
                "asset for this host!");
        }
        return;
    }
    clearError("asset_id");
}
function validateDistribution()
{
    combo = document.getElementById("distribution_id");
    if (combo.value == -1) {
        setError("distribution_id", "You must select a valid distribution!");
        return;
    }
    clearError("distribution_id");
}
function validateKernel()
{
    combo = document.getElementById("kernel_id");
    if (combo.value == -1) {
        setError("kernel_id", "You must select a valid kernel!");
        return;
    }
    clearError("kernel_id");
}
function validateHostActive()
{
    /* Don't need to validate anything here perse, but coudl cause state of
     * asset / side to change.
     */
    validateAsset();
    validateSite();
}
function validateForm()
{
    validateHostname();
    validateSite();
    validateAsset();
    validateDistribution();
    validateKernel();
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
        rv = confirm("Warning you have not specified either a location " +
            "or an asset for this host. This host will not be usable, " + 
            "continue?");
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
