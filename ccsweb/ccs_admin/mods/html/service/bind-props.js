/* Copyright (C) 2006  The University of Waikato
 *
 * Bind Web Interface for the CRCnet Configuration System
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
    '#dns_server_link' : function(element){
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
    pars =  "do=updateBindProperty&service_id=" + service_id + 
        "&propName=" + name + "&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'bind-details'}, url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function updateDiv(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
}
