/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Asset Management Interface - Host Addition / Modification
 * 
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id: map.js 899 2006-07-27 11:09:35Z mglb1 $
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
map = false;
Behaviour.addLoadEvent(setupMap);
function siteHover(e) {
    this.openInfoWindowHtml($("iwin-" + this.crcnet_host));
}
function siteHoverOff(e) {
    win = map.getInfoWindow();
    win.hide();
}
function mapClick(marker, point) {
    // Ignore clicks on markers
    if (marker)
        return;
    // Print out the co-ordinates of other clicks
    $("co-ords").innerHTML = point.x + " " + point.y;
}
function setupMap() {
    if (GBrowserIsCompatible()) {
        map = new GMap2($("mapview"));
        //map.addMapType(new Zoomin.NZTM);
        map.addControl(new GLargeMapControl());
        map.addControl(new GMapTypeControl());
        map.setCenter(new GLatLng(-37.878, 175.211), 12);
        GEvent.addListener(map, "click", mapClick);
        sites.each(function foo(t) { 
            var marker = new GMarker(t[0]);
            marker.crcnet_host = t[1];
            GEvent.addListener(marker, "mouseover", siteHover);
            GEvent.addListener(marker, "mouseout", siteHoverOff);
            map.addOverlay(marker);
        });
        links.each(function foo(t) {
            if (!t) return;
            if (t.length < 2) return;
            var line = new GPolyline(t, "#ff0000", "2", "0.6");
            map.addOverlay(line);
        });
    }
}
function debug(msg) {
    d= $("debug");
    ts = new Date();
    d.innerHTML = d.innerHTML + ts +": " + msg + "<br />";
}
