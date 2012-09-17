/* Copyright (C) 2006  The University of Waikato
 *
 * HostAPd Web Interface for the CRCnet Configuration System
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
url = "https://" + site + "/mods/service/hostapd.php";

// Register Rules
Behaviour.addLoadEvent(initForm);

function interfaceStateChanged(e)
{
    name = e.target.id;
    parts = name.split("-");
	e.target.disabled = true;
    if (parts.length < 2) {
        return; // Bogus id
    }

    val = $F(name);
    host_id = $F("host_id");
    service_id = $F("service_id");
    interface_id = parts[1];


    pars =  "&service_id=" + service_id + "&host_id=" + host_id + 
        "&interface_id=" + interface_id;
    pars = "do=updateHostAPdInterface&val=" + val + pars;
    myAjax = new Ajax.Updater({}, url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        evalScripts:true});
}
function initForm()
{
    // Dynamically find all interface input elements
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
        if (parts.length < 2) {
            continue; // Bogus id
        }
        name = "#" + prop.id;
        if (parts[0] == "hostapd") {
            myrules[name] = function(element){
                element.onchange = interfaceStateChanged;
            }
        }
    }
    Behaviour.register(myrules);
    Behaviour.apply();
}
