/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Authentication Display Interface - Group manipulation
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

var processed = 0;
var errFlag = 0;

function getType(str)
{
    if (str == "zzzz") {
        return "z";
    }

    t = str.split(";");
    if (t.length <= 1) {
        return "";
    }
    return t[1].substr(0,1);
}

function addMember(group_id)
{
    new_members = "";
    
    // Retrieve necessary page elements
    avail = document.getElementById("avail_users");
    if (avail == null) {
        displayIeNoticeError("Unable to add member, page components missing!");
        return;
    }
    
    // Retrieve the selected users in the available list
    opts = avail.options;
    if (opts == null) {
        displayIeNoticeError("Unable to add member, page components missing!");
        return;
    }
    nopts = opts.length;
    processsed = 0;
    n=0
    for (i=0;i<nopts;i++) {
        item = opts.item(i);
        if (item == null) {
            continue;
        }
        // If the item is not selected skip it
        if (item.selected == 0) {
            continue;
        }
        // Add to the list of members
        if (n>0) {
            new_members += ",";
        }
        t = item.value.split(";");
        new_members += t[1];
        n++;
    }
    url = "https://" + site + "/mods/contact/group.php?do=addmember&" +
        "group_id=" + group_id + "&new_members=" + new_members + 
        "&callback=processAddResult";
    loadXMLDoc(url, null);
    // Wait until all requests have completed
    if (req != null) {
        setTimeout("addMemberComplete()", 100);
    } else {
        addMemberComplete();
    }
}
function addMemberComplete()
{

    // Wait until all requests have completed
    if (req != null) {
        setTimeout("addMemberComplete()", 100);
        return;
    }
    if (processed == 0 && errFlag == 0) {
        displayIeNoticeError("No users selected!");
    }
    
}
function processAddResult(result)
{
    added = result.split("*");
    len = added.length
    for (c=0;c<len;c++) {
        addToMemberList(added[c]);
    }
    
}
function addToMemberList(result)
{
    // Retrieve necessary page elements
    avail = document.getElementById("avail_users");
    members = document.getElementById("group_members");
    notice = document.getElementById("ienotice");

    // Expand the result
    t = result.split(",");
    status = t[0];
    value = t[1];
    message = t[2];
    type = getType(value);

    // Check the request was successfull
    if (status != "success") {
        displayIeNoticeError("Could not add user to group! - " + message);
        errFlag = 1;
        return;
    }
    
    // Update display
    itemIdx = findItem(avail, value);
    if (itemIdx == -1) {
        // Force a page reload
        window.location = window.location + "&reload=1";
        return;
    }  
    item = avail.options.item(itemIdx);
    before = findIeInsertPoint(members, item);
    item.selected = 0;
    members.add(item, before);

    // Update number of members added
    processed++;
    
    return;
}
function delMember(group_id)
{

    // Retrieve necessary page elements
    members = document.getElementById("group_members");
    if (members == null) {
        displayIeNoticeError("Unable to delete member, page " +
            "components missing!");
        return;
    }
    
    // Retrieve the selected members in the members list
    opts = members.options;
    if (opts == null) {
        displayIeNoticeError("Unable to delete member, page " +
            "components missing!");
        return;
    }
    nopts = opts.length;
    processsed = 0;
    old_members = "";
    n = 0;
    for (i=0;i<nopts;i++) {
        item = opts.item(i);
        if (item == null) {
            continue;
        }
        // If the item is not selected skip it
        if (item.selected == 0) {
            continue;
        }
        // Add the user to the list to be removed
        if (n>0) {
            old_members += ",";
        }
        t = item.value.split(";");
        old_members += t[1];
        n++;

    }
    url = "https://" + site + "/mods/contact/group.php?do=delmember&" +
        "group_id=" + group_id + "&old_members=" + old_members + "&" +
        "callback=processDelResult";
    loadXMLDoc(url);    // Wait until all requests have completed
    if (req != null) {
        setTimeout("delMemberComplete()", 100);
    } else {
        delMemberComplete();
    }
}
function delMemberComplete()
{

    // Wait until all requests have completed
    if (req != null) {
        setTimeout("delMemberComplete()", 100);
        return;
    }
    if (processed == 0 && errFlag == 0) {
        displayIeNoticeError("No users selected!");
    } 

}
function processDelResult(result)
{
    mems = result.split("*");
    for (c=0;c<mems.length;c++) {
        addToAvailList(mems[c]);
    }

}
function addToAvailList(result)
{
    // Retrieve necessary page elements
    avail = document.getElementById("avail_users");
    members = document.getElementById("group_members");

    // Expand the result
    t = result.split(",");
    status = t[0];
    value = t[1];
    
    // Check the request was successfull
    if (status != "success") {
        displayIeNoticeError("Could not delete user from group! - " + t[2]);
        errFlag = 1;
        return;
    }
    
    // Update display
    itemIdx = findItem(members, value);
    if (itemIdx == -1) {
        // Force a page reload to ensure consistent state
        window.location = window.location + "&reload=1";
        return;
    }  
    item = members.options.item(itemIdx);
    before = findIeInsertPoint(avail, item);
    item.selected = 0;
    avail.add(item, before);

    // Update number of members added
    processed++;
    
    return;
}

/* Searches the specified select list and returns the option at the position
 * after which the specified item should be inserted. 
 *
 * The comparison takes into account the group and user sections of the list.
 */
function findIeInsertPoint(select, item)
{

    type = getType(item.value);
    ctype = "g";
    before = null;
    for (i=0;i<select.options.length;i++) {
        titem = select.options.item(i);
        if (titem == null) {
            continue;
        }
        ttype = getType(titem.value);
        if (ttype == "z") {
            if (ctype == type) {
                return titem;
            } else {
                ctype = "u";
                continue
            }
        }
        if (ttype != type) {
            continue;
        }
        if (titem.text > item.text) {
            return titem;
        }
    }

    return null;
}

function clearIeNotice()
{
    notice = document.getElementById("ienotice");

    if (notice == null) {
        return;
    }
    notice.innerHTML = "&nbsp;"
    notice.className = "ienotice";
    errFlag = 0;
}
function displayIeNotice(msg)
{
    notice = document.getElementById("ienotice");

    if (notice == null) {
        return;
    }
    notice.innerHTML = "msg"
    notice.className = "ienotice";
    setTimeout("clearIeNotice()", 10000);
}
function displayIeNoticeError(msg)
{
    notice = document.getElementById("ienotice");

    if (notice == null) {
        return;
    }
    notice.innerHTML = msg;
    notice.className = "ienotice-error";
    setTimeout("clearIeNotice()", 10000);
    errFlag = 1;

}

