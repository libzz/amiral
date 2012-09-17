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
{if $iface.interface_active=="f"}
<h3 class="disabled">Inferface '{$iface.name}' Is Disabled</h3>
{else}
<h3>Interface '{$iface.name}'</h3>
<table class="details">
<tr>    
    <th>IP Address</th>
    <td>{$iface.ip_address}</td>
</tr>
<tr id="iface-firewall_class_id-{$iface.interface_id}-row">    
    <th>Firewall Class</th>
    <td>
    {assign var="iid" value=$iface.interface_id}
    {html_options id="iface-firewall_class_id-$iid" name="iface-firewall_class_id-$iid" options=$firewall_classes_select selected=$iface.firewall_class_id}
    </td>
</tr>
</table>
{/if}
