/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
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
var toggleState=true;

function toggle(host_name) {
    if (Element.hasClassName("host-" + host_name, "loghidden")) {
        Element.removeClassName("host-" + host_name, "loghidden");
    } else {
        Element.addClassName("host-" + host_name, "loghidden");
    }
}
function updateAll() {
    boxes = document.getElementsByTagName("INPUT");
    for (i=0;i<boxes.length;i++) {
        box = boxes[i];
        /* Skip non checkboxes */
        if (box.type != "checkbox") {
            continue;
        }
        /* Skip checkboxes that don't start update- */
        if (box.name.substr(0, 6) != "update") {
            continue;
        }
        /* Check it */
        box.checked = toggleState;
    }
    toggleState = !toggleState;
}
