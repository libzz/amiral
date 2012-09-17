/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Interface manipulation
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

url = "https://" + site + "/mods/host/interface.php";
errCount=0;

// XXX: These should probably be included from somewhere else...
INTERFACE_TYPE_PHYSICAL=1
INTERFACE_TYPE_VAP=2
INTERFACE_TYPE_VLAN=3
INTERFACE_TYPE_ALIAS=4

// Register Rules
var myrules = {
    '#interface_type' : function(element){
        element.onchange = typeSelected;
    },
    '#link_id' : function(element){
        element.onchange = linkSelected;
    },
	'#subasset_id' : function(element){
        element.onchange = validateSubasset;
    },
	'#raw_interface' : function(element){
        element.onchange = validateRawInterface;
    },
	'#bridge_interface' : function(element){
        element.onchange = validateBridge;
    },
	'#ifname' : function(element){
        element.onchange = validateIfName;
    },
	'#interface_active' : function(element){
        element.onchange = validateInterfaceActive;
    },
	'#master_interface' : function(element){
        element.onchange = masterChanged;
    },
	'#monitor_interface' : function(element){
        element.onchange = monitorChanged;
    },
    '#master_mode' : function(element){
        element.onchange = modeChanged;
    },
};
Behaviour.register(myrules);
Behaviour.addLoadEvent(initForm);

var allRows = new Array("subasset_id", "raw_interface", "ifname", "vid", "spacer", 
    "toggle", "driver", "ip_address", "alias_netmask", "bridge_interface",
    "master_interface", "master_channel", "monitor_interface", "use_gateway");
var advancedRows = new Array("driver", "ip_address", "alias_netmask", 
    "bridge_interface", "master_interface", "master_channel", 
    "monitor_interface", "use_gateway");
// XXX: INTERFACE_TYPE constants don't work in the array below... annoying
var typeRows = {
    1:new Array("subasset_id", "ifname", "spacer", "toggle", "driver", 
        "ip_address", "bridge_interface", "master_interface",
        "master_channel", "monitor_interface", "use_gateway"),
    2:new Array("subasset_id", "ifname", "spacer", "toggle", "driver", 
        "ip_address", "bridge_interface", "master_interface", 
        "master_channel", "monitor_interface", "use_gateway"),
    3:new Array("raw_interface", "vid", "spacer", "toggle",  "ip_address"),
    4:new Array("raw_interface", "ip_address", "alias_netmask")
};

function hideRow(row) {
    Element.addClassName($(row + "-row"), "hidden");
    clearError(row);
}
function showRow(row) {
    // Display the specified row if it is valid for the currently 
    // selected interface type
    if (!typeRows[$F("interface_type")].include(row)) return;
    Element.removeClassName($(row + "-row"), "hidden");
}
function showNormalRow(row) {
    // Display the specified row if it is valid for the currently
    // selected interface type and is not normally hidden
    if (!typeRows[$F("interface_type")].include(row)) return;
    if (advancedRows.include(row)) return;
    Element.removeClassName($(row + "-row"), "hidden");
}
function toggleAdvanced()
{
    // Get link
    link = $("expandLink");

    // If expanded, contract and vice versa  
    if (Element.hasClassName($("ip_address-row"), "hidden")) {
        advancedRows.each(showRow);
        link.replaceChild(document.createTextNode("- Hide Advanced " +
            "Configuration"), link.firstChild);
    } else {
        advancedRows.each(hideRow);
        link.replaceChild(document.createTextNode("+ Expand Advanced " +
            "Configuration"), link.firstChild);
    }
}
function typeSelected()
{
    validateType();
    interface_type = $F("interface_type");
    host_id = $F("host_id");

    // Hide everything
    allRows.each(hideRow);
    // Display those that match the selected type
    typeRows[interface_type].each(showNormalRow);

    // Force showing alias rows even if they would be normally hidden
    if (interface_type == INTERFACE_TYPE_ALIAS) {
        typeRows[interface_type].each(showRow);
    }

    // Fetch required data 
    if (interface_type == INTERFACE_TYPE_VLAN ||
            interface_type == INTERFACE_TYPE_ALIAS) {
        // Get list of interfaces
        Form.Element.disable("raw_interface");
        pars = "do=listRawInterfaces&host_id=" + host_id + 
            "&interface_type=" +  interface_type;
        myAjax = new Ajax.Updater({success: 'raw_interface-cell'}, url, 
            {method: 'get', parameters: pars, onFailure: reportError,
            insertion:updateList});
    }

}
function linkSelected()
{
    validateLink();
    
    link_id = $F("link_id");
    if (link_id==-1)
        return;
    host_id = $F("host_id");
    if ($("interface_id")) {
        interface_id = $F("interface_id");
    } else {
        interface_id = -1;
    }
    interface_type_box = $("interface_type");
    interface_type = interface_type_box.value;
    subasset_id = $F("subasset_id");

    // Retrieve the list of assets that could be used for this interface
    if ((interface_type == INTERFACE_TYPE_PHYSICAL || 
            interface_type == INTERFACE_TYPE_VAP) &&
            (interface_type_box.tagName=="SELECT" || subasset_id=="")) {
        pars = "do=listInterfaceAssets&host_id=" + host_id + "&link_id=" + 
            link_id + "&interface_type=" + interface_type;
        if (interface_id != -1)
            pars += "&interface_id=" + interface_id;
        Form.Element.disable("subasset_id");
        myAjax = new Ajax.Updater({success: 'subasset_id-cell'}, url, 
            {method: 'get', parameters: pars, onFailure: reportError,
            insertion:updateList});
    } else {
        suggestIP();
    }
       
}
function updateList(object, string)
{
    updateDiv(object, string);
    suggestIP();
    validateSubasset();
    validateRawInterface();
}
function suggestIP()
{  
    validateLink();
    
    // Get the select box
    box = $("link_id");
    link_id = $F("link_id");
    if (link_id==-1)
        return;
    host_id = $F("host_id");
    if (host_id == -1)
        return;
    master_if=0;
    if ($F("master_interface"))
        master_if=1;
    
    // Query for a suggested IP
    Form.Element.disable("ip_address");
    pars = "do=getSuggestedIP&link_id=" + link_id + "&host_id=" + host_id +
        "&master_if=" + master_if;
    myAjax = new Ajax.Updater({success: 'ip_address-cell'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function masterChanged() {

    if ($F("master_interface")) {
        // Make sure master channel is visible
        Element.removeClassName($("master_channel-row"), "hidden");
        modeChanged();
    } else {
        // Hide the master channel option
        Element.addClassName($("master_channel-row"), "hidden");
    }

}
function modeChanged()
{
    // Get the selected type
    mode = $F("master_mode");
    if ($F("do")=="edit") {
        oldchannel = $F("master_channel-orig");
        pars = "do=getChannelList&mode=" + mode + "&oldchannel=" + oldchannel;
    } else {
            pars = "do=getChannelList&mode=" + mode;
    }
    // Retrieve the list of modes
    myAjax = new Ajax.Updater({success: 'master_channel-cell'}, url, 
        {method: 'get', parameters: pars, onFailure: reportError});

}
function monitorChanged() {

    if ($F("monitor_interface")) {
        // Monitor interfaces preclude everything else
        Element.addClassName($("master_interface-row"), "hidden");
        Element.addClassName($("master_channel-row"), "hidden");
        Element.addClassName($("bridge_interface-row"), "hidden");
        Element.addClassName($("ip_address-row"), "hidden");
        Element.addClassName($("use_gateway-row"), "hidden");
    } else {
        // Hide the master channel option
        Element.removeClassName($("master_interface-row"), "hidden");
        if ($F("master_interface"))
            Element.removeClassName($("master_channel-row"), "hidden");
        Element.removeClassName($("bridge_interface-row"), "hidden");
        if ($F("bridge_interface")==-1)
            Element.removeClassName($("ip_address-row"), "hidden");
            Element.removeClassName($("use_gateway-row"), "hidden");
    }

}

function validateBridge()
{
    if ($F("bridge_interface")!=-1) {
        Element.addClassName($("ip_address-row"), "hidden");
        Element.addClassName($("use_gateway-row"), "hidden");
        return;
    }
    Element.removeClassName($("ip_address-row"), "hidden");
    Element.removeClassName($("use_gateway-row"), "hidden");
}
function validateType()
{
    b = $("interface_type");

    // Exit immediately if interface type is not changeable
    if (b.tagName != "SELECT")
        return;

    if (b.value == -1) {
        setError("interface_type", "You must select a valid interface type!");
        return;
    }
    clearError("interface_type");
}
function validateLink()
{
    if ($F("link_id") == -1) {
        setError("link_id", "You must select a valid link for this interface!");
        return;
    }
    clearError("link_id");
}
function validateSubasset()
{
    combo = $("subasset_id");
    // Exit immediately if disabled, hidden or not changeable
    if (combo.disabled || 
            Element.hasClassName($("subasset_id-row"), "hidden") ||
            combo.tagName!="SELECT") {
        clearError("subasset_id");
        return;
    }
    if (combo.value == -1) {
        conf = $("interface_active");
        if (conf.checked) {
            setError("subasset_id", "You must select valid hardware if you " +
                "wish to enable this interface!");
        } else {
            setWarning("subasset_id", "It is recommended that you select " +
                "some hardware for this interface it will be disabled!");
        }
        return;
    }
    clearError("subasset_id");
}
function validateRawInterface() {
    combo = $("raw_interface");
    if (combo.disabled || 
            Element.hasClassName($("raw_interface-row"), "hidden")) {
        clearError("raw_interface");
        return;
    }
    if (combo.value == -1) {
        conf = $("interface_active");
        if (conf.checked) {
            setError("raw_interface", "You must select a base interface " +
                "if you wish to enable this interface!");
        } else {
            setWarning("raw_interface", "It is recommended that you select " +
                "some hardware for this interface it will be disabled!");
        }
        return;
    }
    clearError("raw_interface");

}
function validateIfName()
{
    name=$F("ifname");
    if (name == "") {
        setError("ifname", "Interface name must be specified!");
        return;
    }
    if (name.length > 8) {
        setError("ifname", "Interface name must not be more than 8 " +
            "characters!");
        return;
    }
    clearError("ifname");
}
function validateInterfaceActive()
{
    /* Don't need to validate anything here per. se, but could cause state of
     * interface hardware to change.
     */
    validateSubasset();
    validateRawInterface();
}
function initForm()
{
    action = $F("do");

    toggleAdvanced();
    validateForm();

    typeSelected();
    if (action != "add") {
        if ($F("subasset_id") == "") {
            linkSelected();
        }
        validateBridge();
        modeChanged();
    }

}
function validateForm()
{
    validateType();
    validateLink();
    validateSubasset();
    validateRawInterface();
    validateIfName();
}
function updateDiv(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
}
