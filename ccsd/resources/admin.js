/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of CRCnet Monitor
 *
 * CPE Administration
 * 
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * crcnetd is free software; you can redistribute it and/or modify it under 
 * the terms of the GNU General Public License version 2 as published by the 
 * Free Software Foundation.
 *
 * crcnetd is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * crcnetd; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 */
var updateWindowTimer = false;
var updateWindowDots=0;
var updateWindowTimeout=35;
// Change this to one to output debug messages to the page. It should never be
// committed as 1 however.
var dodebug=0;

// Register Rules
var myrules = {
    '#password' : function(element){
        element.onchange = updatePassword;
    },
    '#factory_reset' : function(element){
        element.onclick = resetDevice;
    },
};
Behaviour.register(myrules);

function updatePassword(e) {

    pars =  "password=" + $F("password");
    $("password").disabled = true;
    myAjax = new Ajax.Request("/admin", {method: 'post', postBody: pars, 
        onSuccess:passwordChanged, onFailure:passwordChangeFailed});
}
function passwordChanged(obj) {
    $("password").disabled = false;
}
function passwordChangeFailed(obj) {
    alert("Failed to update password! - " + obj.statusText);
    $("password").disabled = false;
}
function resetDevice(e) {

    // Double check the user wants to reset
    rv = confirm("Are you sure you want to reset the device? This will loose" +
        " all your settings!");
    if (!rv)
        return;

    // Send the request
    myAjax = new Ajax.Request("/admin", {method: 'post', 
        postBody: "reset=true", onSuccess:deviceResetSuccess, 
        onFailure:deviceResetFailed});

    // Setup the waiting page
    Element.removeClassName("reset", "hidden");
    Element.addClassName("admin", "hidden");
    $("resetstatus").innerHTML = "Resetting Device Configuration...";
    /* Setup timer to update the dots */
    updateWindowDots=0;
    updateWindowTimer = window.setInterval(resetUpdateWindow, 1000);

}
function deviceResetSuccess(obj) {
    // Trigger the device restart
    myAjax = new Ajax.Request("/admin", {method: 'post', 
        postBody: "restart=true"});
    // Make the user wait 10 seconds and then reload the page
    $("resetstatus").innerHTML = "Configuration Updated! Rebooting Device...";
    updateWindowDots=20;
}
function deviceResetFailed(obj) {
    window.clearInterval(updateWindowTimer);
    alert("Device failed to reset!");
    Element.addClassName("reset", "hidden");
    Element.removeClassName("admin", "hidden");
}
function resetUpdateWindow() {
    if (updateWindowDots == 30) {
        window.clearInterval(updateWindowTimer);
        // Go to the 'homepage'
        window.location.replace(window.location.href.slice(0, -5));
        return;
    }
    updateWindowDots++;
    obj = $("resetstatus");
    obj.innerHTML = obj.innerHTML + ".";
}
function debug(msg) {
    if (dodebug) {
        d = new Date();
        str = d.getTime() + ": " + msg;
        node = document.createElement("div");
        node.appendChild(document.createTextNode(str));
        document.body.appendChild(node);
    }
}
