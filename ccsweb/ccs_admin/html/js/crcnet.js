/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Common Javascript Functions
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

/* How many errors are on the form */
var errCount;

/* Global variable to track the request, note this means that you can't have
 * more than one active request at a time... 
 */
var req = null;
var req_timeout_id = -1;

/* Refresh the login bar every 2 seconds */
Behaviour.addLoadEvent(initLoginBarUpdates);

function initLoginBarUpdates() {
    document.updateStatusBar = new Ajax.PeriodicalUpdater({success:'loginbar'},
        '/?function=loginbarUpdate', Object.extend({asynchronous:true,
        evalScripts:true, method:'GET'},{frequency:5.0}));
}

/*
 * Create a XMLHTTPRequest Object in a browser safe fashion
 *
 * Parameters:
 * url      Fully qualified URL of the document to load 
 * data     String containing any data to send
 *
 * Returns:
 * 0 on success
 */
function loadXMLDoc(url, data) 
{

    // Cannot initiate a request when one is already active!
    if (req != null) {
        return -1;
    }
    
    // branch for native XMLHttpRequest object
    if (window.XMLHttpRequest) {
        req = new XMLHttpRequest();
        req.onreadystatechange = processReqChange;
        req.open("POST", url, true);
        req.send(data);
    // branch for IE/Windows ActiveX version
    } else if (window.ActiveXObject) {
        req = new ActiveXObject("Microsoft.XMLHTTP");
        if (req) {
            req.onreadystatechange = processReqChange;
            req.open("POST", url, true);
            req.send(data);
        }
    }

    // Set timeout handler
    req_timeout_id = setTimeout("cancelXMLRequest()", 15000);
    
    return 0;
    
}

function cancelXMLRequest()
{
    alert("CancelXMLRequest");
    if (req==null) {
        return;
    }
    req_timeout_id = -1;
    req.abort();
    alert("Request timed out!");
    req = null;

}

/* 
 * Process an XMLHttpRequest as it's state changes
 *
 * This function expects the result of the request to be an XML document
 * containing two nodes, method and result. Method must be a valid function
 * name that this function can call, result will be passed to the function
 *
 * Parameters:
 * req      Global variable containing state of the request
 *
 * Returns:
 * Calls the requested function
 */
function processReqChange() {
    
    // It's a bad day if we get called with no request set!
    if (req == null) {
        return;
    }

    // Only process if the request has completed
    if (req.readyState != 4) {
        return;
    }

    // Cancel timeout handled
    clearTimeout(req_timeout_id);
    req_timeout_id = -1;
    
    // Only process if the request completed successfully
    if (req.status != 200) {
        alert("Unable to process request: " + req.statusText);
        req = null;
        start = 0;
        return;
    }

    // Parse the request
    response  = req.responseXML.documentElement;
    method = response.getElementsByTagName('method')[0].firstChild.data;
    result =  response.getElementsByTagName('result')[0].firstChild.data;
    if (result == null) {
        result = response.getElementsByTagName('result');
    }
    // Validate sanity
    if (method == "") {
        alert("Unable to process request: Invalid method returned!");
        req = null;
        start = 0;
        return;
    }

    // Tidyup
    start = 0;
    req = null;

    // Call the method
    eval(method + "(result)");

    
}

/* Searches the specified select list and returns the option with the 
 * specified value.
 */
function findItem(select, value)
{
    // Check input sanity
    opts = select.options;
    if (opts == null) {
        return -1;
    }
    if (value == "") {
        return -1;
    }
    // Loop to find item
    nopts = opts.length;
    for (i=0;i<nopts;i++) {
        item = opts.item(i);
        if (item.value == value) {
            return i;
        }
    }

    // End of list
    return -1;
    
}

/ * Clears a combo box */
function clearCombo(combo)
{
    length = combo.childNodes.length;
    for (i=0;i<length;i++) {
        combo.removeChild(combo.childNodes.item(0));
    }
}
/* Creates an HREF DOM Object */
function makeHref(href, caption) {
    
    n_href = document.createElement("a");
    n_href.setAttribute("href", href);
    n_href.appendChild(document.createTextNode(caption));

    return n_href;
}
/* Checks if the specified string is numeric */
function isNumeric(sText)
{
   var validChars = "0123456789.";
   var isNumber=true;
   var tchar;

 
   for (i = 0; i < sText.length && isNumber == true; i++) { 
        tchar = sText.charAt(i);
        if (validChars.indexOf(tchar) == -1) {
            isNumber = false;
        }
    }
    
    return isNumber;
    
}

function complete()
{
    // Wait until requests has completed
    if (req != null) {
        setTimeout("complete()", 100);
        return;
    } 
}

/* Miscellaneous functions for extracting data from responses */
function getFromTagName(item, name)
{
    // Get status
    t = item.getElementsByTagName(name)[0];
    if (!t) {
        return "";
    }      
    if (t.childNodes.length > 0) {
        return t.firstChild.data;
    } else {
        return "";
    }
}
function getTextValue(item)
{
    if (item.childNodes.length <= 0)
        return ""
    return item.firstChild.data;
}
function reportError(request) {
    alert("An error occured!");
}
/* Form validation functions 
 * These make use of a global variable called errCount which tracks how many
 * errors are on the form. The form may not be submitted unless this count is
 * 0. 
 *
 * These functions also assume that input fields have an id field set and that
 * the corresponding header element for each input field has an id of the input
 * field with -header suffixed.
 *
 */
function setTextDefault(id, value)
{
    item = document.getElementById(id);
    if (item) {
        item.value = value;
    }
}
function enableControl(id)
{
    item = document.getElementById(id);
    if (item) {
        item.disabled = false;
    }
}
function disableControl(id)
{
    item = document.getElementById(id);
    if (item) {
        item.disabled = true;
    }
}
function setWarning(name, reason) 
{
    item = $(name + "-header");
    if (!item) 
        return;
    if (Element.hasClassName(item, "error")) {
        Element.removeClassName(item, "error");
        errCount--;
    }
    Element.addClassName(item, "warning");
    item.title = reason;
    if (errCount == 0) {
        enableSubmit();
    }
}
function setError(name, reason) 
{
    item = $(name + "-header");
    if (!item) 
        return;
    if (Element.hasClassName(item, "warning")) {
        Element.removeClassName(item, "warning");
    }
    if (!Element.hasClassName(item, "error")) {
        Element.addClassName(item, "error");
        errCount++;
    }
    item.title = reason;

    disableSubmit();
    
}
function clearError(name) 
{
    item = $(name + "-header");
    if (!item)
        return;
    if (Element.hasClassName(item, "error")) {
        if (errCount > 0)
            errCount--;
        Element.removeClassName(item, "error");
    }
    if (Element.hasClassName(item, "warning")) {
        Element.removeClassName(item, "warning");
    }
    item.title = "";
    
    if (errCount == 0) {
        enableSubmit();
    }
}
function disableSubmit()
{
    submit = document.getElementById("submit");
    if (!submit)
        return;
    submit.disabled = true;
}
function enableSubmit()
{
    submit = document.getElementById("submit");
    if (!submit)
        return;
    submit.disabled = false;
}
function setInstructionText(text)
{
    item = $("instructions");
    ctext = item.firstChild;
    item.replaceChild(document.createTextNode(text), ctext);
}
