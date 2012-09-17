{* Copyright (C) 2006  The University of Waikato
 *
 * HostAPd Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - HostAPd"}
<form method="post" action="host.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$hostapd.service_id}"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please select the interfaces that you wish to enable HostAP on below.</div>
<br/>
<table class="details">
<tr>    
    <th>Hostname</th>
    <td>{$host.host_name}</td>
</tr>
<tr>
    <th>Current Location</th>
    <td>{$host.location}</td>
</tr>
</table>

{foreach from=$hostapd.interfaces item=iface}
<br /><h2>Interface - {$iface.name}</h2>
<!--
Check the box below if you wish to enable HostAP on this interface.<br />

<input type="checkbox" id="hostapd-{$iface.interface_id}"{if $iface.hostapd_enabled!="f"} checked{/if}> -->
Please choose select what you want hostapd to do.
<select id="hostapd-{$iface.interface_id}" />
        <option value=0 {if $iface.hostapd_enabled==0}selected="selected"{/if}>Disabled</option>
        <option value=1 {if $iface.hostapd_enabled==1}selected="selected"{/if}>Radius AUTH</option>
        <option value=2 {if $iface.hostapd_enabled==2}selected="selected"{/if}>Local Cert AUTH</option>
</select>

<br />
{/foreach}
{if count($hostapd.interfaces)<=0}
<br ><i>There are no AP interfaces configured for this host!</i><br />
{/if}

<ul>
<li><a href="/mods/host/host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
