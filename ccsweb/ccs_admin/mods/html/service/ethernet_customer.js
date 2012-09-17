/* Copyright (C) 2006  The University of Waikato
 *
 * Ethernet Customer Web Interface for the CRCnet Configuration System
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
url = "https://" + site + "/mods/service/ethernet_customer.php";
Behaviour.addLoadEvent(initForm);

function ifacePropChanged(e)
{
    name = e.target.id;
    parts = name.split("-");
    if (parts.length < 3) {
        return; // Bogus id
    }
    ref = $(name);
    customer_id = $F(name);
    host_id = $F("host_id");
    service_id = $F("service_id");
    interface_id = parts[2];

    // Disable things while updating
    ref.disabled = true;

    // Update
    pars =  "do=updateCustomerInterface&service_id=" + service_id + 
        "&host_id=" + host_id + "&interface_id=" + interface_id +
        "&customer_id=" + customer_id;
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
        if (parts[1] == "customer_id") {
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
    attachEvents(object.getElementsByTagName("SELECT"));
}
