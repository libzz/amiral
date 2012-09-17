/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Service Configuration 
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
url = "https://" + site + "/mods/service/service.php";

// Register Validation Rules
var myrules = {
    '.service-property' : function(element){
        element.onchange = validatePropertyHandler;
    },
    '#service_host_enabled' : function(element){
        element.onchange = validateAllProperties;
    },
    '#editForm' : function(element){
        element.onsubmit = checkForm;
    },
};
Behaviour.register(myrules);
Behaviour.addLoadEvent(initForm);

function validatePropertyHandler(e)
{
    validateProperty(e.target);
}
function validateProperty(prop)
{
    name = prop.id;
    header = $(name + "-header");
    if (Element.hasClassName(header, "required")) {
        if (prop.value == "") {
            if (getServiceState() == "t") {
                setError(name, name + " is a required service property and " +
                    "must be specified!");
            } else {
                setWarning(name, name + " is a required service property "+
                    "and must be specified before the service can be " +
                    "enabled!");
            }
            return;
        }
    }

    clearError(name);

}
function validateAllProperties()
{
    // Get all property input elements
    props = document.getElementsByTagName("INPUT");
    for (i=0;i<props.length;i++) {
        prop = props.item(i);
        if (Element.hasClassName(prop, "service-property")) {
            validateProperty(prop);
        }
    }

}
function getServiceState()
{
    global_state = $F("enabled");
    host_state = $F("service_host_enabled");

    // If explicitly set use that
    if (host_state=="f" || host_state=="t") {
        return host_state;
    }
    
    // Otherwise use global state
    return global_state;
}
function initForm()
{
    // Always perform initial validation.
    validateAllProperties();
}
function checkForm()
{
    do_alert = 1;
    if (arguments.length > 0) {
        do_alert = arguments[0];
    }
    warncount = 0;
    
    // Get all TD elements
    headers = document.getElementsByTagName("TD");
    for (i=0;i<headers.length;i++) {
        td = headers.item(i);
        if (td.id.indexOf("-header") == -1)
            continue;
        if (Element.hasClassName(td, "error")) {
            name = getTextValue(td);
            if (do_alert) {
                alert("You must specify a value for the '" + name + 
                    "' field!");
            }
            return false;
        }
        if (Element.hasClassName(td, "warning")) {
            warncount++;
        }
    }

    if (warncount > 0 && do_alert) {
        rv = confirm("There are some warnings present on the form. Do you " +
            "want to continue? This may cause problems later on.");
        if (rv != 1) {
            return false;
        }
    }

    return true;

}
