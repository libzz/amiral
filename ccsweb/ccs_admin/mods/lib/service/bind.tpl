{* Copyright (C) 2006  The University of Waikato
 *
 * BIND Web Interface for the CRCnet Configuration System
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
 *}
{include file="header.tpl" title="Service Configuration - DNS Server"}
<form method="post" action="host.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$bind.service_id}"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please configure this DNS Server below.</div>
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
<tr>
    <th>DNS Master Server</th>
    <td><input type="checkbox" name="is_master" id="is_master" value="t"{if $bind.host.is_master=="t"} checked{/if} /></td>
</tr>
<tr>
    <th>DNS IP Address</th>
    <td>
        {if $bind.properties.dns_server_link.network_value != ""}
        <input type="text" name="dns_ip_address" id="dns_ip_address" value="{$bind.host.dns_ip_address}" /><br />
        <span class="note">You may leave this blank to use the host's loopback IP. If you wish to configure an explicit address, it must be within the range <strong>{$bind.dns_server_link_desc}</strong></span>
        {else}
        <span class="note">You must select a DNS server link before you can specify an explicit DNS server IP</span>
        <input type="hidden" name="dns_ip_address" id="dns_ip_address" value="" />
        {/if}
    </td>
</tr>

</table>
<ul>
<li><a href="/mods/host/host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
