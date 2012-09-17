/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of CRCnet Monitor
 *
 * RuralLink Administration
 * 
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless 
 * otherwise confirmed in writing by the copyright holder.
 *
 */
var wizardStep = 1;
var canProgress = true;
var updateWindowTimer = false;
var updateWindowDots=0;
var updateWindowTimeout=35;
var myAjax;
var lock=0;
var processing=0;
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
    '#ap0_channel' : function(element){
        element.onchange = updateChannel;
    },
    '#internal_policy' : function(element){
        element.onchange = policySelected;
    },
    '#ap0_policy' : function(element){
        element.onchange = policySelected;
    },
    '#isptype' : function(element){
        element.onchange = ISPSelected;
    },
    '#ethmode': function(element){
        element.onchange = ethModeChanged;
    },
    '#wizard_hostname' : function(element){
        element.onchange = wizardHostnameUpdated;
    },
    '#wizard_password' : function(element){
        element.onchange = wizardPasswordUpdated;
    },
    '#wizard_essid': function(element){
        element.onchange = wizardESSIDUpdated;
    },
    '#wizard_isptype': function(element){
        element.onchange = wizardISPUpdated;
    },
    '#wizard_ethmode': function(element){
        element.onchange = wizardEthModeChanged;
    },
    '#wizard_ispusername': function(element){
        element.onchange = wizardISPUpdated;
    },
    '#wizard_isppassword': function(element){
        element.onchange = wizardISPUpdated;
    }
};
Behaviour.register(myrules);

function doAjaxWizard() {
    // If there is an object called postWizard on the page
    // the the AJAX wizard is disabled
    if ($("postWizard")) {
        return false;
    } else {
        return true;
    }
}
function nextStep() {
    debug("nextStep");
    if (lock)
        return;
    if (!doAjaxWizard()) {
        d = $("direction");
        d.value = "next";
        $("wizardForm").submit();
        return;
    }
    if (!processStep())
         return;
    progress();
}
function progress() {
    debug("progress");    
    if (!canProgress)
        return;
    if (wizardStep==5) {
        alert("No more steps!");
        return;
    }
    debug("progress allowed");
    // Hide the current step
    Element.hide("step" + wizardStep);
    // Show the next step
    wizardStep++;
    $("step" + wizardStep).style.display="block";
    // Don't progress until the form has been completed
    initialiseStep();
}
function prevStep() {
    debug("prevStep");
    if (lock)
        return;
    if (!doAjaxWizard()) {
        d = $("direction");
        d.value = "previous";
        $("wizardForm").submit();
        return;
    }
    if (wizardStep==1) {
        alert("No more steps!");
        return;
    }
    // Hide the current step
    Element.hide("step" + wizardStep);
    // Show the next step
    wizardStep--;
    $("step" + wizardStep).style.display="block";
    // Don't progress until the form has been completed
    canProgress = false;
    initialiseStep();
}
function initialiseStep() {
    id="";
    if (wizardStep == 1) {
        canProgress = true;
    } else if (wizardStep == 2) {
        id="wizard_hostname";
        canProgress = true;
    } else if (wizardStep == 3) {
        id="wizard_password";
        canProgress = false;
    } else if (wizardStep == 4) {
        canProgress = false;
        obj = $("wizard_ispusername");
        if (obj) {
            id = obj.id;
        }
    } else if (wizardStep == 5) {
        canProgress = false;
    }
    if (id != "") {
        $(id).select();
        $(id).focus();
    }
}
function processStep() {
    debug("processStep");
    // If we're already processing signal that we should quit
    if (processing)
        return false;
    debug("process allowed");
    // Otherwise note that we're processing
    processing=1;

    // Do the processing for the current step
    if (wizardStep == 3) {
        wizardPasswordUpdated(null);
    } else if (wizardStep == 4) {
        if (!$("wizard_isptype")) {
            // Client node
            if ($("wizard_essid"))
                wizardESSIDUpdated(null);
        } else {
            // Master node
            wizardISPUpdated(null);
        }
    }

    // Finished processing
    processing=0;
    return canProgress;    
}
function showUpdateWindow(text) {
    debug("showing update window");
    obj = $("updatewindow");
    step = $("step" + wizardStep);
    step.style.opacity = 0.2;
    obj.innerHTML = text + "...";
    obj.style.top = 110+step.offsetTop + 
        ((step.offsetHeight/2)-(obj.offsetHeight/2)) + "px";
    obj.style.left = step.offsetLeft + ((step.offsetWidth/2)-150) + "px";
    obj.style.display = "block";
    /* Disable next links */
    list = document.getElementsByClassName("next");
    for (link in list) {
        link.disabled = true;
    }
    /* Setup timer to update the dots */
    updateWindowDots=0;
    updateWindowTimer = window.setInterval(wizardUpdateWindow, 1000);
}
function hideUpdateWindow() {
    debug("hiding update window");
    /* Hide window, stop updating dots */
    obj = $("updatewindow");
    obj.style.display = "none";
    window.clearInterval(updateWindowTimer);
    /* Enable next links */
    list = document.getElementsByClassName("next");
    for (link in list) {
        link.disabled = false;
    }
    /* Set step opacity back to normal */
    step = $("step" + wizardStep);
    step.style.opacity = 1;
    /* Try and proceed if possible */
    lock=0;
    progress();
}
function wizardUpdateSuccess(r) {
    debug("AJAX call succeeded: (" + r.status + ") " + r.statusText);
    obj = $("updatewindow");
    obj.innerHTML = obj.innerHTML + " <span class=\"statusok\">OK.</span>";
    window.clearInterval(updateWindowTimer);
    window.setTimeout(hideUpdateWindow, 1000);
    canProgress = true;
}
function wizardUpdateFailure(r) {
    debug("AJAX call failed: (" + r.status + ") " + r.statusText);
    obj = $("updatewindow");
    obj.innerHTML = obj.innerHTML + " <span class=\"error\">FAILED!</span>" +
        "<br />" + r.statusText;
    window.clearInterval(updateWindowTimer);
    window.setTimeout(hideUpdateWindow, 3000);
    canProgress = false;
} 
function wizardUpdateWindow() {
    obj = $("updatewindow");
    if (updateWindowDots==updateWindowTimeout) { 
        debug("timeout");
        myAjax.transport.abort()
        debug("AJAX aborted");
        wizardUpdateFailure({status:500,statusText:"Timeout!"});
    } else { 
        obj.innerHTML = obj.innerHTML + "."; 
        updateWindowDots++; 
    } 
}
function wizardHostnameUpdated(e) {
    if (!doAjaxWizard())
        return;
    debug("wizardHostnameUpdated");
    lock=1;
    showUpdateWindow("Saving Hostname");
    pars =  "wizard_hostname=" + $F("wizard_hostname");
    myAjax = new Ajax.Request("/", {method: 'post', postBody: pars, 
        onSuccess:wizardUpdateSuccess, onFailure:wizardUpdateFailure});
}
function wizardPasswordUpdated(e) {
    if (!doAjaxWizard())
        return;
    debug("wizardPasswordUpdated");
    lock=1;
    showUpdateWindow("Saving Password");
    pars =  "wizard_password=" + $F("wizard_password");
    myAjax = new Ajax.Request("/", {method: 'post', postBody: pars, 
        onSuccess:wizardUpdateSuccess, onFailure:wizardUpdateFailure});
}
function wizardESSIDUpdated(e) {
    if (!doAjaxWizard())
        return;
    debug("wizardESSIDUpdated");
    lock=1;
    showUpdateWindow("Selecting Upstream Device");
    pars =  "wizard_essid=" + $F("wizard_essid");
    myAjax = new Ajax.Request("/", {method: 'post', postBody: pars, 
        onSuccess:wizardUpdateSuccess, onFailure:wizardUpdateFailure});
}
function wizardISPUpdated(e) {
    debug("wizardISPUpdated");
    lock=1;
    type = $F("wizard_isptype");
    docred=true;
    if (type == "eth") {
        // Hide username / password and note
        Element.hide("wizard_ispusername_row");
        Element.hide("wizard_isppassword_row");
        Element.show("wizard_ethmode_row");
        if ($("eth-note"))
            Element.show("eth-note");
        if ($("home-note"))
            Element.hide("home-note");
        docred=false;
        // Bail out now, never update automatically because the user may
        // want to change DHCP/Static choices
        if (e) {
            lock=0;
            return;
        }
        // Retrieve the other ethernet parameters
        ethmode = $F("wizard_ethmode");
        ethip = $F("wizard_ethip");
        ethnetmask = $F("wizard_ethnetmask");
        ethgw = $F("wizard_ethgw");
    } else {
        Element.show("wizard_ispusername_row");
        Element.show("wizard_isppassword_row");
        Element.hide("wizard_ethmode_row");
        Element.hide("wizard_ethip_row");
        Element.hide("wizard_ethnetmask_row");
        Element.hide("wizard_ethgw_row");
        if ($("eth-note"))
            Element.hide("eth-note");
        if ($("home-note"))
            Element.show("home-note");
        // Check username / password are specified 
        username = $F("wizard_ispusername");
        password = $F("wizard_isppassword");
        if (username=="" || password=="") {
            // Not all fields are complete
            lock=0;
            return;
        }
    }
    if (!doAjaxWizard()) {
        lock=0;
        return;
    }
    showUpdateWindow("Configuring ISP");
    if (docred) {
        // Update the ISP Type
        pars =  "wizard_isptype=" + type;
        myAjax = new Ajax.Request("/", {method: 'post', postBody: pars});
        // Then update the authentication details
        pars =  "wizard_ispusername=" + username + "&wizard_isppassword=" + 
            password;
        myAjax = new Ajax.Request("/", {method: 'post', postBody: pars, 
            onSuccess:wizardUpdateSuccess, onFailure:wizardUpdateFailure});
    } else {
        // Just update the ISP type
        pars =  "wizard_isptype=" + type + "&wizard_ethmode=" + ethmode + 
            "&wizard_ethip=" + ethip + "&wizard_ethnetmask=" + ethnetmask + 
            "&wizard_ethgw=" + ethgw;
        myAjax = new Ajax.Request("/", {method: 'post', postBody: pars, 
            onSuccess:wizardUpdateSuccess, onFailure:wizardUpdateFailure});
    }
}   
function wizardEthModeChanged(e) {
    mode = $F("wizard_ethmode");
    if (mode == "dhcp") {
        /* Hide static info */
        Element.hide("wizard_ethip_row");
        Element.hide("wizard_ethnetmask_row");
        Element.hide("wizard_ethgw_row");
    } else {
        /* Show static info */
        Element.show("wizard_ethip_row");
        Element.show("wizard_ethnetmask_row");
        Element.show("wizard_ethgw_row");
    }
}
function wizardRefreshBackhaul() {
    href = window.location.href;
    if (href.indexOf("step") != -1) {
        window.location.replace(href);
    } else if (href.indexOf("?") != -1)  {
        window.location.replace(href + "&step=4");
    } else {
        window.location.replace(href + "?step=4")
    }
    return;
}
function ISPSelected(e){
    type = $F("isptype");
    if (type != "eth") {
        Element.show("username_row");
        Element.show("auth_link");
    } else {
        Element.hide("username_row");
        Element.hide("auth_link");
    }
    if (!doAjaxWizard())
        return;
    e.target.form.submit();
}
function ethModeChanged(e) {
    mode = $F("ethmode");
    if (mode == "dhcp") {
        /* Hide static info */
        Element.hide("ethip_row");
        Element.hide("ethnetmask_row");
        Element.hide("ethgw_row");
    } else {
        /* Show static info */
        Element.show("ethip_row");
        Element.show("ethnetmask_row");
        Element.show("ethgw_row");
    }
}
function policySelected(e) {

    id = e.target.id;
    parts = id.split("_");
    if (parts.length != 2) {
        // Bogus name
        return;
    }

    url = "/traffic/policy/" + parts[0] ;
    
    pars =  "policy=" + $F(id);
    $(id).disabled = true;
    myAjax = new Ajax.Request(url, {method: 'post', postBody: pars, 
        onSuccess:policyUpdateComplete, onFailure:policyUpdateFailed});
}

function updateChannel(e) {

    url = "/rladmin";
    obj = e.target.id;
    alert(obj);
    pars =  obj + "=" + $F(obj);
    $(obj).disabled = true;
    myAjax = new Ajax.Request(url, {method: 'post', postBody: pars, 
        onSuccess:channelChanged, onFailure:channelChangeFailed});
}
function channelChanged(obj) {
    $("ap0_channel").disabled = false;
    $("ap0_channel").value = obj.responseText;
}
function channelChangeFailed() {
    alert("Failed to update channel!");
    $("ap0_channel").disabled = false;
}
function updatePassword(e) {

    url = "/rladmin";
    
    pars =  "password=" + $F("password");
    $("password").disabled = true;
    myAjax = new Ajax.Request(url, {method: 'post', postBody: pars, 
        onSuccess:passwordChanged, onFailure:passwordChangeFailed});
}
function passwordChanged(obj) {
    parts = obj.responseText.split(":");
    if (parts.length!=3) {
	window.location.reload();
        return;
    }
    $("password").disabled = false;
    b = $("password");
    b.value = parts[0];
    b = $("wephex")
    b.innerHTML = parts[1];
    b = $("wep")
    b.innerHTML = parts[2];
}
function passwordChangeFailed(obj) {
    alert("Failed to update password! - " + obj.statusText);
    $("password").disabled = false;
}
function policyUpdateComplete() {
    $("internal_policy").disabled = false;
    $("ap0_policy").disabled = false;
}
function policyUpdateFailed() {
    alert("Failed to update settings!");
    $("internal_policy").disabled = false;
    $("ap0_policy").disabled = false;
}
function resetDevice(e) {

    // Double check the user wants to reset
    rv = confirm("Are you sure you want to reset the device? This will loose" +
        " all your settings!");
    if (!rv)
        return;

    // Send the request
    myAjax = new Ajax.Request("/rladmin", {method: 'post', 
        postBody: "reset=true", onSuccess:deviceResetSuccess, 
        onFailure:deviceResetFailed});

    // Setup the waiting page
    Element.removeClassName("reset", "hidden");
    Element.addClassName("rladmin", "hidden");
    $("resetstatus").innerHTML = "Resetting Device Configuration...";
    /* Setup timer to update the dots */
    updateWindowDots=0;
    updateWindowTimer = window.setInterval(resetUpdateWindow, 1000);

}
function deviceResetSuccess(obj) {
    // Trigger the device restart
    myAjax = new Ajax.Request("/rladmin", {method: 'post', 
        postBody: "restart=true"});
    // Make the user wait 30 seconds and then reload the page
    $("resetstatus").innerHTML = "Configuration Updated! Rebooting Device...";
    updateWindowDots=4955;
}
function deviceResetFailed(obj) {
    window.clearInterval(updateWindowTimer);
    alert("Device failed to reset!");
    Element.addClassName("reset", "hidden");
    Element.removeClassName("rladmin", "hidden");
}
function resetUpdateWindow() {
    if (updateWindowDots == 5000) {
        window.clearInterval(updateWindowTimer);
        // Go to the 'homepage'
        window.location.replace(window.location.href.slice(0, -7));
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
