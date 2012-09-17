{* Copyright (C) 2006  The University of Waikato
 *
 * AMPlet Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - AMPlet"}
<form method="post" action="host.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$amplet.service_id}"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please enter the details for AMP on this host below.</div>
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
<table class="details" id="amplet-host-details">
{include file="mods/service/amplet-hostdetails.tpl"}
</table>
<br />
<ul>
<li><a href="/mods/host/host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
