/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Graph manipulation user interface
 *
 * Author:       Chris Browning <ckb6@cs.waikato.ac.nz>
 * Version:      $Id: hosteditform.tpl 1067 2006-10-05 22:55:17Z mglb1 $
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

url = "https://" + site + "/mods/graphs/graphs.php";

// Register Validation Rules
var myrules = {
    '#host_id' : function(element){
        element.onchange = host_selected;
    },
    '#host' : function(element){
        element.onchange = toggle;
    },
    '#link' : function(element){
        element.onchange = toggle;
    },
    '#target' : function(element){
        element.onchange = toggle;
    }        
};

Behaviour.register(myrules);

// When a new host is selected update the available graphs
function host_selected()
{
    if (document.getElementById('group_id').disabled == true)
        return;
    host_id = group_id = -1;
    if (document.getElementById('host_id').disabled == false)
    {
        host_ido = $("host_id");
        if (host_ido)
            host_id = $F("host_id");
    }
    group_ido = $("group_id");
    if (group_ido)
        group_id = $F("group_id")
    // Retrieve the list of available graphs for this host
    pars = "do=listgraphs&host_id=" + host_id + "&group_id=" + group_id;
    myAjax = new Ajax.Updater({success: 'group_id-cell'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion: insertList});
}

// Insert new infomation into a list
function insertList(object, string) 
{
    object.innerHTML = string;
    Behaviour.apply();
}

// This is done to change an image when its time has changed
function change_img(server, host, time_idel, graph_id, num, ip, force, imgel, refl) {
    image = document.getElementById(imgel);
    referance = document.getElementById(refl);
    time_id = document.getElementById(time_idel).value;
    src = "http://" + server + "/graphs/" + host + "/" + time_id + "/" + graph_id + "?";
    ref = "http://" + server + "/graphs/" + host + "/" + time_id + "/" + graph_id + "?" + "big=1&";
    if (num != "" && num != "0"){
        src += "interface=" + num;
        ref += "interface=" + num;
    }
    if (ip != ""){
        src += "&ip=" + ip;
        ref += "&ip=" + ip;
    }
    if (force == "on"){
        src += "&force=1";
        ref += "&force=1";
    }
        
    image.src = src;
    referance.href = ref;
}

// This handles enableing and disabling of elements when radio's are changed
function toggle() {
    // First fetch elements
    mhost = document.getElementById('host');
    mlink = document.getElementById('link');
    mtarget = document.getElementById('target');
    mirror = document.getElementById('mirror');
    host = document.getElementById('host_id');
    link = document.getElementById('link_id');
    type = document.getElementById('group_id');
    target = document.getElementById('target_id');
    if(mhost.checked) {  //host is checked
        mirror.disabled = false;
        type.disabled = false;
        host.disabled = false;
        link.disabled = true;
        target.disabled = true;
    } else if(mlink.checked) {   //link is checked
        mirror.disabled = true;
        mirror.checked = false;
        type.disabled = false;
        host.disabled = true; 
        link.disabled = false;
        target.disabled = true;

    } else if(mtarget.checked) {   //target is checked
        mirror.disabled = true;
        mirror.checked = false;
        type.disabled = true;
        host.disabled = true; 
        link.disabled = true;
        target.disabled = false;

    }
    // Update the graphs list
    host_selected();
}
