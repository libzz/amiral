{* Copyright (C) 2006  The University of Waikato
 *
 * Quagga Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - Routing (Quagga)"}
<form method="post" action="host.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$quagga.service_id}"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please enter the details for this host's routing below. Text fields may be
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
<table class="details" id="quagga-host-details">
{include file="mods/service/quagga-hostdetails.tpl" quagga=$quagga}
</table>
<br />
<div id="interfaces">
<h2>OSPF Interfaces</h2>
You may set the status and configuration for OSPF on each interface of the
host using the sections below.<br />
{foreach from=$quagga.interfaces item=iface}
<span id="interface-{$iface.interface_id}">
{include file="mods/service/quagga-ospf-ilist.tpl" iface=$iface areas=$quagga.areas}
</span>
{/foreach}
{if count($quagga.interfaces)<=0}
<br ><i>There are no interfaces defined on the host!</i><br />
{/if}
</div>
<br />
<div id="statics-container">
<h2>Static Routes</h2>
<table id="statics">
{include file="mods/service/quagga-static.tpl" statics=$quagga.statics}
</table>
<br />
<a href="javascript:addStatic();" id="add-static-button">Add new Static Route &gt;&gt;</a><br />
<br />
</div>
<br />
<!--<div id="bgp">
<h2>BGP Configuration</h2>
<table>
<tr>    
    <th width="210">Peer Name</th>
    <th>Peer IP</th>
    <th>Peer AS</th>
    <th>Actions</th>
</tr>
<tr>
    <td>Murray's Server</td>
    <td>10.1.1.1</td>
    <td>65489</td>
    <td><a href="#">[configure]</a>&nbsp;&nbsp;<a href="#">[remove]</a></td>
</tr>
</table>
<br/>
</div>-->
<ul>
<li><a href="/mods/host/host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
