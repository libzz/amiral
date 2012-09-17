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
{if $iface.interface_active=="f"}
<h3 class="disabled">Inferface '{$iface.name}' Is Disabled</h3>
{else}
<h3>Interface '{$iface.name}'</h3>
<table class="details">
<tr>    
    <th>Customer IP Address</th>
    <td>{$iface.customer.ip_address}</td>
</tr>
<tr id="iface-firewall_class_id-{$iface.interface_id}-row">    
    <th>Customer</th>
    <td>
    {assign var="iid" value=$iface.interface_id}
    {if $iface.customer == ""}{assign var="cid" value=-1}{else}{assign var="cid" value=$iface.customer.customer_id}{/if}
    {html_options id="iface-customer_id-$iid" name="iface-customer_id-$iid" options=$ethernet_customers_select selected=$cid}
    </td>
</tr>
</table>
{/if}
