/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of CRCnet Monitor
 *
 * Message of the day fetching and other homepage tasks
 * 
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless 
 * otherwise confirmed in writing by the copyright holder.
 *
 */
Behaviour.addLoadEvent(fetchMOTD);
function fetchMOTD() {
    motd=$("motd");
    if (motd) {
        new Ajax.Updater("motd", "/motd", {method:'get'});
        return;
    }
}
