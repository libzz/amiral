{* Copyright (C) 2006  The University of Waikato
 *
 * Firewall Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - Firewall"}
<form method="post" action="host.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$firewall.service_id}"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please enter the details for this host's firewall below.</div>
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
<table class="details" id="firewall-host-details">
{include file="mods/service/firewall-hostdetails.tpl" firewall=$firewall}
</table>
<br />
<div id="interfaces">
<h2>Interfaces</h2>
You may set the firewall class that is assigned to each interface 
using the sections below.<br />
{foreach from=$firewall.interfaces item=iface}
<span id="interface-{$iface.interface_id}">
{include file="mods/service/firewall-ilist.tpl" iface=$iface firewall_classes_select=$firewall.firewall_classes_select}
</span>
{/foreach}
{if count($firewall.interfaces)<=0}
<br ><i>There are no interfaces defined on the host!</i><br />
{/if}
</div>
<br />
<ul>
<li><a href="/mods/host/host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
