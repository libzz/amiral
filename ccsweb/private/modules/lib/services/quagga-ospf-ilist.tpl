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
    <th>Enable OSPF on Interface?</th>
    <td>
    <input type="checkbox" id="iface-ospf_enabled-{$iface.interface_id}"{if $iface.ospf_enabled!="f"} checked{/if}>
    </td>
</tr>
{assign var="rclass" value=""}
{if $iface.ospf_enabled=="f"}
{assign var="rclass" value=' class="hidden"'}
{/if}
<tr id="iface-area_no-{$iface.interface_id}-row"{$rclass}>    
    <th>OSPF Area</th>
    <td>
    <select id="iface-area_no-{$iface.interface_id}">
    <option value="-1">Default Area (0)</option>
    {foreach from=$areas item=area}
    {assign var="sel" value=""}
    {if $iface.area_no == $area.area_no}
    <option value="{$area.area_no}" selected>{$area.link_class_desc} ({$area.area_no})</option>
    {else}
    <option value="{$area.area_no}">{$area.link_class_desc} ({$area.area_no})</option>
    {/if}    
    {/foreach}
    </select>
    </td>
</tr>
<tr id="iface-priority-{$iface.interface_id}-row"{$rclass}>    
    <th>Interface Priority</th>
    <td><input type="text" id="iface-priority-{$iface.interface_id}" value="{$iface.priority}">
    </td>
</tr>
<tr id="iface-md5_auth-{$iface.interface_id}-row"{$rclass}>    
    <th>Use MD5 Authentication?</th>
    <td>
    <input type="checkbox" id="iface-md5_auth-{$iface.interface_id}"{if $iface.md5_auth=="t"} checked{/if}>
    </td>
</tr>
{if $iface.ospf_enabled!="f" && $iface.md5_auth=="t"}
<tr id="iface-md5_key-{$iface.interface_id}-row">
{else}
<tr id="iface-md5_key-{$iface.interface_id}-row" class="hidden">
{/if}
    <th>Interface MD5 Key</th>
    <td><input type="text" id="iface-md5_key-{$iface.interface_id}" value="{$iface.md5_key}">
    </td>
</tr>
</table>
{/if}

