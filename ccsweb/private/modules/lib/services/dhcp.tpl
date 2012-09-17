{* Copyright (C) 2006  The University of Waikato
 *
 * DHCP Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - DHCP"}
<form method="post" action="host.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$dhcp.service_id}"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please enter the details for DHCP on this host below. Text fields may be
left blank if you wish to use the default values defined for the service.</div>
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
<table class="details" id="dhcp-host-details">
{include file="mods/service/dhcp-hostdetails.tpl" dhcp=$dhcp}
</table>
<br />
<div id="interfaces">
<h2>Interfaces</h2>
You may set the status and configuration for DHCP on each interface of the
host using the sections below.<br />
{foreach from=$dhcp.interfaces item=iface}
<span id="interface-{$iface.interface_id}">
{include file="mods/service/dhcp-ilist.tpl" iface=$iface}
</span>
{/foreach}
{if count($dhcp.interfaces)<=0}
<br ><i>There are no interfaces defined on the host!</i><br />
{/if}
</div>
<br />
<div id="statics">
<h2>Static Hosts</h2>
<table>
<tr>    
    <th width="210">Description</th>
    <th>Prefix</th>
    <th>Next Hop</th>
    <th>Metric</th>
    <th>Actions</th>
</tr>
{foreach from=$dhcp.statics item=static}
<tr>
    <td>{$static.description}</td>
    <td>{$static.mac}</td>
    <td>{$static.ip_address}</td>
    <td><a href="">[Edit]</a>&nbsp;&nbsp;<a href="">[Remove]</a></td>
</tr>
{/foreach}
</table>
<br /><a href="">Add new Static Host&gt;&gt;</a><br />
<br/>
</div>
<br />
<ul>
<li><a href="/mods/host/host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
