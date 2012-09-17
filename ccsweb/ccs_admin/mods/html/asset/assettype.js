/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Asset Management Interface - Asset Type/Subasset Type Manipulation
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

function setRequired(asset_type_subasset_id, required)
{
    // Trigger the update
    url = "https://" + site + "/mods/asset/types.php?do=updateSubassetLink&" +
        "asset_type_subasset_id=" + asset_type_subasset_id + 
        "&required=" + required + "&callback=processUpdate";
    loadXMLDoc(url, null);
    // Wait until all requests have completed
    if (req != null) {
        setTimeout("complete()", 100);
    } else {
        complete();
    }

}

function removeSubasset(asset_type_subasset_id, required)
{
    // Trigger the add
    url = "https://" + site + "/mods/asset/types.php?do=removeSubassetLink&" +
        "asset_type_subasset_id=" + asset_type_subasset_id + 
        "&required=" + required + "&callback=processRemove";
    loadXMLDoc(url, null);
    // Wait until all requests have completed
    if (req != null) {
        setTimeout("complete()", 100);
    } else {
        complete();
    }

}
function addSubasset(asset_type_id, subasset_type_id, required)
{
    new_members = "";
    
    // Get a descriptive Name
    name = prompt("Please enter a descriptive name for this subasset type");
    if (name == "") {
        alert("Invalid name!");
        return;
    }

    // Trigger the add
    url = "https://" + site + "/mods/asset/types.php?do=addSubassetLink&" +
        "asset_type_id=" + asset_type_id + "&subasset_type_id=" +
        subasset_type_id +  "&name=" + name + "&required=" + required + 
        "&callback=processAdd";
    loadXMLDoc(url, null);
    // Wait until all requests have completed
    if (req != null) {
        setTimeout("complete()", 100);
    } else {
        complete();
    }
}
function complete()
{

    // Wait until requests has completed
    if (req != null) {
        setTimeout("complete()", 100);
        return;
    }
    
}
function processUpdate(result)
{
    if (result.length < 1) {
        alert("Invalid result received!");
        // Force a page reload
        window.location = window.location + "&reload=1";
        return;
    }
    
    // Get status
    t = result[0].getElementsByTagName("success")[0];
    if (!t) {
        alert("Invalid result!");
        // Force a page reload
        window.location = window.location + "&reload=1";
        return;
    }       
    success = t.firstChild.data;
    if (success != 0) {
        t = result[0].getElementsByTagName("errMsg")[0];
        errMsg = t.firstChild.data;
        alert(errMsg);
        return;
    }
    // Get id
    t = result[0].getElementsByTagName("asset_type_subasset_id")[0];
    asset_type_subasset_id = t.firstChild.data;
    // Get optional
    t = result[0].getElementsByTagName("required")[0];
    required = t.firstChild.data;       
    if (required == 0) {
        list = "required-subassets";
        idstr = "rsatrow-";
    } else {;
        list = "optional-subassets";
        idstr = "osatrow-";
    }
    type = "";
    name = "";
    // Find row to delete
    rlist = document.getElementById(list);
    rows = rlist.rows;
    search = idstr + asset_type_subasset_id;
    for (i=0;i<rows.length;i++) {
        row = rows.item(i);
        if (row.id == search) {
            type = row.cells.item(0).firstChild.data;
            name = row.cells.item(1).firstChild.data;
            rlist.deleteRow(i);
            recolourRows(rows);
        }
    }
    if (type == "" || name == "") {
        // Could not find the appropriate row!
        window.location = window.location + "&reload=1";
        return;
    }

    // Add new row
    addRow(type, name, required, asset_type_subasset_id);
    
}
function processRemove(result)
{
    if (result.length < 1) {
        alert("Invalid result received!");
        // Force a page reload
        window.location = window.location + "&reload=1";
        return;
    }
    
    // Get status
    t = result[0].getElementsByTagName("success")[0];
    if (!t) {
        alert("Invalid result!");
        // Force a page reload
        window.location = window.location + "&reload=1";
        return;
    }       
    success = t.firstChild.data;
    if (success != 0) {
        t = result[0].getElementsByTagName("errMsg")[0];
        errMsg = t.firstChild.data;
        alert(errMsg);
        return;
    }
    // Get id
    t = result[0].getElementsByTagName("asset_type_subasset_id")[0];
    asset_type_subasset_id = t.firstChild.data;
    // Get optional
    t = result[0].getElementsByTagName("required")[0];
    required = t.firstChild.data;       
    if (required == 0) {
        list = "optional-subassets";
        idstr = "osatrow-";
    } else {
        list = "required-subassets";
        idstr = "rsatrow-";
    }
    
    // Find row to delete
    rlist = document.getElementById(list);
    rows = rlist.rows;
    search = idstr + asset_type_subasset_id;
    for (i=0;i<rows.length;i++) {
        row = rows.item(i);
        if (row.id == search) {
            rlist.deleteRow(i);
            recolourRows(rows);
            return;
        }
    }

    // Could not find the appropriate row!
    window.location = window.location + "&reload=1";
    return;
}
function processAdd(result)
{
    if (result.length < 1) {
        alert("Invalid result received!");
        // Force a page reload
        window.location = window.location + "&reload=1";
        return;
    }
    
    // Get status
    t = result[0].getElementsByTagName("success")[0];
    if (!t) {
        alert("Invalid result!");
        // Force a page reload
        window.location = window.location + "&reload=1";
        return;
    }       
    success = t.firstChild.data;
    if (success != 0) {
        t = result[0].getElementsByTagName("errMsg")[0];
        errMsg = t.firstChild.data;
        alert(errMsg);
        return;
    }
    // Get Asset/Subasset Type ID
    t = result[0].getElementsByTagName("asset_type_id")[0];
    asset_type_id = t.firstChild.data;    
    t = result[0].getElementsByTagName("subasset_type_id")[0];
    subasset_type_id = t.firstChild.data;
    t = result[0].getElementsByTagName("asset_type_subasset_id")[0];
    asset_type_subasset_id = t.firstChild.data;
    // Get Name
    t = result[0].getElementsByTagName("name")[0];
    name = t.firstChild.data;    
    // Get optional
    t = result[0].getElementsByTagName("required")[0];
    required = t.firstChild.data;       

    // Insert the row
    type = getSubassetTypeName(subasset_type_id);
    addRow(type, name, required, asset_type_subasset_id);
    
}
function addRow(type, name, required, asset_type_subasset_id)
{
    if (required == 0) {
        list = "optional-subassets";
        idstr = "osatrow-";
        makestr = "Required";  
    } else {
        list = "required-subassets";
        idstr = "rsatrow-";
        makestr = "Optional";     
    }
    // Find insert position
    rlist = document.getElementById(list);
    rows = rlist.rows;
    for (i=0;i<rows.length;i++) {
        cname = rows.item(i).cells.item(1).firstChild.data;
        if (cname > name) {
            break;
        }
    }
    // Insert the row
    nrow = rlist.insertRow(i);
    nrow.setAttribute("id", idstr + asset_type_subasset_id);
    cell = nrow.insertCell(-1);
    t=document.createTextNode(type);
    cell.appendChild(t);    
    cell = nrow.insertCell(-1);
    t=document.createTextNode(name);
    cell.appendChild(t);   
    cell = nrow.insertCell(-1);
    if (allowModify()) {
        if (required ==1)
            rv=0;
        else
            rv=1;
        cell.appendChild(makeHref("javascript:setRequired(" + 
            asset_type_subasset_id + ", " + rv + ");", "[Make " + 
            makestr + "]"));
        cell.appendChild(document.createTextNode("\u00A0\u00A0"));
        cell.appendChild(makeHref("javascript:removeSubasset(" + 
            asset_type_subasset_id + ", " + required + ");", "[Remove]"));
    }
    // Recolour the rows
    recolourRows(rows);
}

function allowModify() {
    
    mod = document.getElementById("allowmod");
    if (mod) {
        return 1;
    }
    
    return 0;

}

function getSubassetTypeName(subasset_type_id)
{

    row = document.getElementById("satrow-" + subasset_type_id);
    if (!row) {
        return "";
    }
    tname = row.cells.item(0).firstChild.data;

    return tname;
}
function debug() {
    row = document.getElementById("rsatrow-1");
    if (!row) {
        return "";
    }
    for (i=0;i<row.cells.item(2).childNodes.length;i++) {
        n = row.cells.item(2).childNodes.item(i);
        alert(n + " " + n.nodeName);
    }

    return tname;

}
function recolourRows(rows) {

    // Fix row colouring
    t = "row1";
    for (i=0;i<rows.length;i++) {
        row = rows.item(i);
        row.className = t;
        if (t == "row1") {
            t = "row2";
        } else {
            t = "row1";
        }
    }

}
