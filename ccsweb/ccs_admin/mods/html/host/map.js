/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Asset Management Interface - Host Addition / Modification
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
Behaviour.addLoadEvent(setupMap);
function siteHover(e) {
    b = document.getElementById("debug");
    w = document.getElementById("hoverwin");
    parts = e.target.id.split("_");
    c = document.getElementById("crcnet_container_" + parts[2]);
    m = document.getElementById("mapview");
    i = document.getElementById("theInsideLayer");
    bb = document.getElementById("__base__");
    w.innerHTML = sites[parts[2]][2];
    w.style.display = "block";
    w.style.top = (c.offsetTop+m.offsetTop+i.offsetTop) + "px";
    w.style.left = (c.offsetLeft+i.offsetLeft+m.offsetLeft+35) + "px";
    b.innerHTML = c.offsetLeft + " " + i.offsetLeft + " " + bb.offsetLeft;
}
function siteHoverOff(e) {
    w = document.getElementById("hoverwin");
    w.style.display = "none";
}
var CRCnetMarker = function (sitename, point, icon)
{
    var marker = new GMarker(point, icon);
    marker.icon.id = "crcnet_container_" + i;
    marker.icon.firstChild.id = "crcnet_icon_" + i;
    
    marker.addEventListener = function (eventname, handler) {
        b = document.getElementById(marker.icon.firstChild.id);
        b.addEventListener(eventname, handler, false);
    }
    return marker;
}
function setupMap() {
    if (GBrowserIsCompatible()) {
        var map = new GMap2($("mapview"));
        map.addMapType(new Zoomin.NZTM);
        map.addControl(new GSmallMapControl());
        map.addControl(new GMapTypeControl());
        map.setCenter(new GLatLng(5814955.93,1804019.12), 8);
        sites.each(function foo(t) { 
            var marker = new GMarker(t[0]);
            map.addOverlay(marker);
        });
        links.each(function foo(t) {
            if (!t) return;
            if (t.length < 2) return;
            var line = new GPolyline(t, "#ff0000", "2", "0.6");
            map.addOverlay(line);
            //debug(t);
        });
    }
}
function debug(msg) {
    d= $("debug");
    ts = new Date();
    d.innerHTML = d.innerHTML + ts +": " + msg + "<br />";
}
