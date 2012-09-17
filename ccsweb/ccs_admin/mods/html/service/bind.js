/* Copyright (C) 2006  The University of Waikato
 *
 * BIND Web Interface for the CRCnet Configuration System
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
url = "https://" + site + "/mods/service/bind.php";

// Register Rules
var myrules = {
    '#service_host_enabled' : function(element){
        element.onchange = hostEnabledChanged;
    },
    '#is_master' : function(element){
        element.onchange = hostPropertyChanged;
    },
    '#dns_ip_address' : function(element){
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
    is_master = $F("is_master");
    dns_ip_address = $F("dns_ip_address");

    // Disable things while updating
    $("is_master").disabled = true;
    $("dns_ip_address").disabled = true;

    // Update
    pars =  "do=updateDNSServer&service_id=" + service_id + 
        "&host_id=" + host_id + "&is_master=" + is_master + 
        "&dns_ip_address=" + dns_ip_address;
    myAjax = new Ajax.Request(url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        onSuccess:reloadPage});
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
    pars =  "do=updateBindState&service_id=" + service_id + 
        "&host_id=" + host_id + "&value=" + val;
    myAjax = new Ajax.Request(url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        onSuccess:reloadPage});
}
function reloadPage()
{
    window.location = window.location;
}
