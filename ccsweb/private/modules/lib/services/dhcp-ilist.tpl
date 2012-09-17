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
{if $iface.interface_active=="f"}
<h3 class="disabled">Inferface '{$iface.name}' Is Disabled</h3>
{else}
<h3>Interface '{$iface.name}'</h3>
<table class="details">
<tr>    
    <th>IP Address</th>
    <td>{$iface.ip_address}</td>
</tr>
<tr>    
    <th>Enable DHCP on Interface?</th>
    <td>
    <input type="checkbox" id="iface-dhcp_enabled-{$iface.interface_id}"{if $iface.dhcp_enabled!="f"} checked{/if}>
    </td>
</tr>
{assign var="rclass" value=""}
{if $iface.dhcp_enabled=="f"}
{assign var="rclass" value=' class="hidden"'}
{/if}
<tr id="iface-pool_min-{$iface.interface_id}-row"{$rclass}>    
    <th id="iface-pool_min-{$iface.interface_id}-header">Allocation Pool Min. IP</th>
    <td><input type="text" id="iface-pool_min-{$iface.interface_id}" value="{$iface.pool_min}">
    </td>
</tr>
<tr id="iface-pool_max-{$iface.interface_id}-row"{$rclass}>    
    <th id="iface-pool_max-{$iface.interface_id}-header">Allocation Pool Max. IP</th>
    <td><input type="text" id="iface-pool_max-{$iface.interface_id}" value="{$iface.pool_max}">
    </td>
</tr>
<tr id="iface-router_ip-{$iface.interface_id}-row"{$rclass}>    
    <th id="iface-router_ip-{$iface.interface_id}-header">Router Address</th>
    <td><input type="text" id="iface-router_ip-{$iface.interface_id}" value="{$iface.router_ip}">
    </td>
</tr>
</tr>
</table>
{/if}

