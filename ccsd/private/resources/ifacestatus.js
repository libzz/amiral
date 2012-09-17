/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of CRCnet Monitor
 *
 * Interface Status Updating
 * 
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless 
 * otherwise confirmed in writing by the copyright holder.
 *
 */
updater = null;
function startUpdater() {
    freq = parseInt($F("frequency"));
    if (freq <= 0) {
        freq=2;
    }
    if (!updater) {
        updater = new Ajax.PeriodicalUpdater("ifaceinfo", 
            '/status/iface_ajax', {method: 'get', asynchronous:true, 
            onComplete: function empty() {}, frequency: freq});
    } else {
        updater.stop();
        updater.frequency = freq;
        updater.start();
    }
    // Setup the status box
    Element.removeClassName("updatestatus", "statuscritical")
    Element.addClassName("updatestatus", "statusok")
    Element.update("updatestatus", "Active");
    Element.update("updatelink", "Disable Updates");
}
function updateFrequency() {
    freq = parseInt($F("frequency"));
    if (freq < 1) {
        Element.addClassName("frequency", "statuscritical");
        return;
    }
    Element.removeClassName("frequency", "statuscritical");

    if (updater) {
        updater.frequency = freq;
    }
}
function toggleUpdates() {
    if (Element.hasClassName("updatestatus", "statuscritical")) {
        // Enabling
        startUpdater();
    } else {
        // Disabling - kill updater
        updater.stop();
        // Update captions and links
        Element.update("updatestatus", "Disabled");
        Element.removeClassName("updatestatus", "statusok");
        Element.addClassName("updatestatus", "statuscritical");
        Element.update("updatelink", "Enable Updates");
    }
    $("updatelink").blur();
    return false;
}

window.onload = function loader() {
    startUpdater();
    // Load the event handler for the change button
    link = $("updatelink")
    link.onclick = toggleUpdates;
    link.onmouseover = function() {window.status="";}
}
