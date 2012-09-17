/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Asset Management Interface - Asset Property Manipulation
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

function setRequired(subasset_property_id, required)
{
    // Trigger the update
    if (required == 1)
        oreq = 0;
    else
        oreq = 1;
    default_value = getDefaultValue(subasset_property_id, oreq);
    url = "https://" + site + "/mods/asset/properties.php?do=" +
        "updateSubassetProperty&subasset_property_id=" + 
        subasset_property_id + "&required=" + required + 
        "&default_value=" + default_value +
        "&callback=processRequired";
    loadXMLDoc(url, null);
    // Wait until all requests have completed
    if (req != null) {
        setTimeout("complete()", 100);
    } else {
        complete();
    }

}
function editSubassetProperty(subasset_property_id, required)
{
    // Get a default value
    default_value = prompt("Please enter the new default value for this " +
        "property");
    
    // Trigger the update
    url = "https://" + site + "/mods/asset/properties.php?do=" +
        "updateSubassetProperty&subasset_property_id=" + 
        subasset_property_id +  "&default_value=" + 
        default_value + "&required=" + required + 
        "&callback=processUpdate";
    loadXMLDoc(url, null);
    // Wait until all requests have completed
    if (req != null) {
        setTimeout("complete()", 100);
    } else {
        complete();
    }

}

function removeSubassetProperty(subasset_property_id, required)
{
    // Trigger the add
    url = "https://" + site + "/mods/asset/properties.php?do=" +
        "removeSubassetProperty&subasset_property_id=" + 
        subasset_property_id + "&required=" + required + 
        "&callback=processRemove";
    loadXMLDoc(url, null);
    // Wait until all requests have completed
    if (req != null) {
        setTimeout("complete()", 100);
    } else {
        complete();
    }

}
function addSubassetProperty(subasset_type_id, asset_property_id, required)
{
    
    // Get a default value
    default_value = prompt("Please enter a default value for this property");

    // Trigger the add
    url = "https://" + site + "/mods/asset/properties.php?do=" +
        "addSubassetProperty&subasset_type_id=" + subasset_type_id + 
        "&asset_property_id=" + asset_property_id +  "&default_value=" + 
        default_value + "&required=" + required + 
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
    t = result[0].getElementsByTagName("subasset_property_id")[0];
    subasset_property_id = t.firstChild.data;
    // Get optional
    t = result[0].getElementsByTagName("required")[0];
    required = t.firstChild.data;
    // Get new default value
    t = result[0].getElementsByTagName("default_value")[0];
    if (t.childNodes.length > 0) {
        default_value = t.firstChild.data;
    } else {
        default_value = "";
    }    
    if (required == 1) {
        list = "required-properties";
        idstr = "rproprow-";
    } else {;
        list = "optional-properties";
        idstr = "oproprow-";
    }
    type = "";
    name = "";
    // Find row to modify
    rlist = document.getElementById(list);
    rows = rlist.rows;
    search = idstr + subasset_property_id;
    for (i=0;i<rows.length;i++) {
        row = rows.item(i);
        if (row.id == search) {
            cell = row.cells.item(1);
            if (cell.childNodes.length > 0) {
                row.cells.item(1).firstChild.data = default_value;
            } else {
                cell.appendChild(document.createTextNode(default_value));
            }
            return;
        }
    }
    
    // Could not find the appropriate row!
    window.location = window.location + "&reload=1";
    return;
    
}
function processRequired(result)
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
    t = result[0].getElementsByTagName("subasset_property_id")[0];
    subasset_property_id = t.firstChild.data;
    // Get optional
    t = result[0].getElementsByTagName("required")[0];
    required = t.firstChild.data;       
    // Get new default value
    t = result[0].getElementsByTagName("default_value")[0];
    if (t.childNodes.length > 0) {
        default_value = t.firstChild.data;
    } else {
        default_value = "";
    }    
    if (required != 1) {
        list = "required-properties";
        idstr = "rproprow-";
    } else {;
        list = "optional-properties";
        idstr = "oproprow-";
    }
    type = "";
    name = "";
    // Find row to modify
    rlist = document.getElementById(list);
    rows = rlist.rows;
    search = idstr + subasset_property_id;
    for (i=0;i<rows.length;i++) {
        row = rows.item(i);
        if (row.id == search) {
            name = rows.item(i).cells.item(0).firstChild.data;
            rlist.deleteRow(i);
            recolourRows(rows);
            addRow(name, default_value, required, subasset_property_id);
            return;
        }
    }

    // Could not find the appropriate row!
    window.location = window.location + "&reload=1";
    return;
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
    t = result[0].getElementsByTagName("subasset_property_id")[0];
    subasset_property_id = t.firstChild.data;
    // Get optional
    t = result[0].getElementsByTagName("required")[0];
    required = t.firstChild.data;       
    if (required == 0) {
        list = "optional-properties";
        idstr = "oproprow-";
    } else {
        list = "required-properties";
        idstr = "rproprow-";
    }
    
    // Find row to delete
    rlist = document.getElementById(list);
    rows = rlist.rows;
    search = idstr + subasset_property_id;
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
    // Get Subasset Type ID
    t = result[0].getElementsByTagName("subasset_type_id")[0];
    subasset_type_id = t.firstChild.data;
    // Get Property ID
    t = result[0].getElementsByTagName("asset_property_id")[0];
    asset_property_id = t.firstChild.data;
    // Get Subasset Property ID
    t = result[0].getElementsByTagName("subasset_property_id")[0];
    subasset_property_id = t.firstChild.data;
    // Get Default Value
    t = result[0].getElementsByTagName("default_value")[0];
    if (t.childNodes.length > 0) {
        default_value = t.firstChild.data;
    } else {
        default_value = "";
    }
    // Get required
    t = result[0].getElementsByTagName("required")[0];
    required = t.firstChild.data;       

    // Insert the row
    name = getPropertyName(asset_property_id);
    addRow(name, default_value, required, subasset_property_id);
    
}
function addRow(name, default_value, required, subasset_property_id)
{
    if (required == 0) {
        list = "optional-properties";
        idstr = "oproprow-";
        makestr = "Required";  
    } else {
        list = "required-properties";
        idstr = "rproprow-";
        makestr = "Optional";     
    }
    // Find insert position
    rlist = document.getElementById(list);
    rows = rlist.rows;
    for (i=0;i<rows.length;i++) {
        cname = rows.item(i).cells.item(0).firstChild.data;
        if (cname > name) {
            break;
        }
    }
    // Insert the row
    nrow = rlist.insertRow(i);
    nrow.setAttribute("id", idstr + subasset_property_id);
    cell = nrow.insertCell(-1);
    t=document.createTextNode(name);
    cell.appendChild(t);    
    cell = nrow.insertCell(-1);
    t=document.createTextNode(default_value);
    cell.appendChild(t);   
    cell = nrow.insertCell(-1);
    cell.appendChild(makeHref("javascript:editSubassetProperty(" + 
        subasset_property_id + ", " + required + ");", 
        "[Change Default Value]"));
    cell.appendChild(document.createTextNode("\u00A0\u00A0"));
    if (allowModify()) {
        if (required ==1)
            rv=0;
        else
            rv=1;
        cell.appendChild(makeHref("javascript:setRequired(" + 
            subasset_property_id + ", " + rv + ");", "[Make " + makestr + 
            "]"));
        cell.appendChild(document.createTextNode("\u00A0\u00A0"));
    }
    if (allowModify() || required==0) {
        cell.appendChild(makeHref("javascript:removeSubassetProperty(" + 
            subasset_property_id + ", " + required + ");", "[Remove]"));
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

function getPropertyName(asset_property_id)
{

    row = document.getElementById("proprow-" + asset_property_id);
    if (!row) {
        return "";
    }
    pname = row.cells.item(0).firstChild.data;

    return pname;
}
function getDefaultValue(subasset_property_id, required) 
{
    if (required == 0) {
        idstr = "oproprow-" + subasset_property_id;
    } else {
        idstr = "rproprow-" + subasset_property_id;  
    }
    row = document.getElementById(idstr);
    if (!row) {
        return "";
    }
    if (row.cells.item(1).childNodes.length > 0) {
        dv = row.cells.item(1).firstChild.data;
    } else {
        dv = "";
    }
    return dv; 
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
