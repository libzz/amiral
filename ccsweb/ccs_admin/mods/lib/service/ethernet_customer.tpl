{* Copyright (C) 2006  The University of Waikato
 *
 * Ethernet Customer Web Interface for the CRCnet Configuration System
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
{include file="header.tpl" title="Service Configuration - Ethernet Customers"}
<form method="post" action="host.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$ethernet_customer.service_id}"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please select the customers assigned to each interface below.</div>
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
<br />
<div id="interfaces">
<h2>Interfaces</h2>
You may select the customer that is assigned to each interface using the
sections below.<br />
{foreach from=$ethernet_customer.interfaces item=iface}
<span id="interface-{$iface.interface_id}">
{include file="mods/service/ethernet_customer-ilist.tpl" iface=$iface ethernet_customers_select=$ethernet_customer.ethernet_customers_select}
</span>
{/foreach}
{if count($ethernet_customer.interfaces)<=0}
<br ><i>There are no interfaces defined on the host!</i><br />
{/if}
</div>
<br />
<ul>
<li><a href="/mods/host/host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
