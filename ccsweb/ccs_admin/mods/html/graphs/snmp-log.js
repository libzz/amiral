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
function warn(host_id, host_name)
{
    res = confirm("Warning, you are about to remove all entries containing the host " + host_name + ".");
    if (res)
        window.location ="snmp-log.php?do=deletehost&host_id=" + host_id;
}
function flush()
{
    res = confirm("Warning, you are about to remove all entries from the table.");
    if (res)
        window.location ="snmp-log.php?do=flush";
}
Behaviour.addLoadEvent(ActivateCountDown);
var _countDowncontainer=0;
var _currentSeconds=0;
var _running=true;

function ActivateCountDown() {
    strContainerID="Counter";
    initialValue=$F("counttimer");
    if (initialValue==0)
        initialValue = 30;
    _countDowncontainer = document.getElementById(strContainerID);

    if (!_countDowncontainer) {
        alert("count down error: container does not exist: "+strContainerID+
            "\nmake sure html element with this ID exists");
        return;
    }

    SetCountdownText(initialValue);
    window.setTimeout("CountDownTick()", 1000);
}

function CountDownTick() {
    if (_currentSeconds <= 0) {
        //alert("your time has expired!");
        window.location = "snmp-log.php";
        return;
    }

    if (_running == true)
        SetCountdownText(_currentSeconds-1);
        window.setTimeout("CountDownTick()", 1000);
}
function StopCountDown(){
    _running = false;
    _countDowncontainer.innerHTML = "Auto-refreash disabled";
}
function SetCountdownText(seconds) {
    //store:
    _currentSeconds = seconds;

    //get minutes:
    var minutes=parseInt(seconds/60);

    //shrink:
    seconds = (seconds%60);

    //get hours:
    var hours=parseInt(minutes/60);

    //shrink:
    minutes = (minutes%60);

    //build text:
    var strText = "<a href=\"javascript:StopCountDown();\">" + AddZero(hours) + ":" + AddZero(minutes) + ":" + AddZero(seconds) + "</a>";

    //apply:
    _countDowncontainer.innerHTML = strText;
}

function AddZero(num) {
    return ((num >= 0)&&(num < 10))?"0"+num:num+"";
}
