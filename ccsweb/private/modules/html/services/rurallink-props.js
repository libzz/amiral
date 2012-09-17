/* Copyright (C) 2006  The University of Waikato
 *
 * Rural Link Service Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 */
errCount=0;
url = "https://" + site + "/mods/service/rurallink.php";
v = 0;

// Register Rules
var myrules = {
    '#rl_root_pw' : function(element){
        element.onmouseover = showPassword;
        element.onmouseout = hidePassword;
        element.onfocus = selectPassword;
        element.onblur = hidePassword;
        element.onchange = passwordChanged;
    },
};
Behaviour.register(myrules);

function showPassword(e) {
    ref=$("rl_root_pw");
    if (ref.value != "<password hidden>")
        return;
    $("rl_root_pw").value = $F("rl_root_pw_val");
    v++;
}
function selectPassword(e) {
    $("rl_root_pw").select();
    v++;
}
function hidePassword(e) {
    ref = $("rl_root_pw");
    if (e && e.type == "mouseout" && v>1)
        return;
    if (ref.disabled)
        return;
    v=0;
    ref.value = "<password hidden>";
}
function passwordChanged(e)
{
    ref = $("rl_root_pw");
    val = ref.value;
    service_id = $F("service_id");
    
    if (val == $F("rl_root_pw_val") || val == "<password hidden>" || val=="") {
        hidePassword();
        return;
    }

    // Disable things while updating
    ref.disabled = true;
    ref.value = "Updating password..."

    // Update
    pars =  "do=updateRurallinkProperty&service_id=" + service_id + 
        "&propName=rl_root_pw&value=" + val;
    myAjax = new Ajax.Updater(
        {success: 'rurallink-details'}, url, 
        {method: 'post', parameters: pars, onFailure: reportError,
        insertion:updateDiv});
}
function updateDiv(object, string)
{
    object.innerHTML = string;
    Behaviour.apply();
    v=0;
}
