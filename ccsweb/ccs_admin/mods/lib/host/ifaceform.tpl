{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Interface manipulation user interface template
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
{include file="header.tpl" title="$action Interface"}
<form method="post" action="interface.php" onsubmit="return validateForm();">
<input type="hidden" name="do" id="do" value="{$action}"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>
<input type="hidden" name="interface_id" id="interface_id" value="{$iface.interface_id}"/>

<div id="instructions">
{if $action=="add"}
Please enter the new details for this interface below.
{else}
Please enter the updated details for this interface below.
{/if}
</div>
<br/>
<table class="ifacedetails">
<tr>    
    <th width="200">Hostname</th>
    <td>{$host.host_name}</td>
</tr>
<tr>
    <td colspan=2>&nbsp;</td>
</tr>
<tr>
    <th id="interface_type-header">Interface Type</th>
    <td>
    {if $interface_type!=""}
    <input type="hidden" name="interface_type" id="interface_type" value="{$interface_type}" />
    {$interface_type_desc}
    {else}
    {html_options values=$interface_type_ids output=$interface_types selected=$iface.interface_type name="interface_type" id="interface_type"}
    {/if}
    </td>
</tr>
<tr>
    <th id="link_id-header">Link</th>
    <td>
    <input type="hidden" name="link_id-orig" id="link_id-orig" value="{$interface.link_id}" />
    {html_options values=$link_ids output=$links selected=$iface.link_id name="link_id" id="link_id"}
    </td>
</tr>
<tr id="subasset_id-row">
    <th id="subasset_id-header">Interface Hardware</th>
    <td id="subasset_id-cell">
    {if $subasset_id != ""}
    <input type="hidden" name="subasset_id" id="subasset_id" value="{$subasset_id}" />
    {$subasset_desc}
    {else}
    {html_options values=$subasset_ids output=$subassets selected=$iface.subasset_id name="subasset_id" id="subasset_id"}
    {/if}
</td>
</tr>
<tr id="raw_interface-row">
    <th id="raw_interface-header">Base Interface</th>
    <td id="raw_interface-cell">
    {html_options values=$raw_interface_ids output=$raw_interfaces selected=$iface.raw_interface name="raw_interface" id="raw_interface"}
</td>
</tr>
<tr id="ifname-row">
    <th id="ifname-header">Interface Name</th>
    <td>
    <input type="hidden" name="ifname-orig" id="ifname-orig" value="{$interface.name}" />
    <input type="text" name="ifname" id="ifname" value="{$iface.name}" />
    </td>
</tr>
<tr id="vid-row">
    <th id="vid-header">VLAN ID</th>
    <td>
    <input type="hidden" name="vid-orig" id="vid-orig" value="{$interface.vid}" />
    <input type="text" name="vid" id="vid" value="{$iface.vid}" />
    </td>
</tr>
<tr>    
    <th id="interface_active-header">Interface Active?</th>
    <td>
    <input type="hidden" name="interface_active-orig" value="{if $iface.interface_active!="f"}yes{/if}"/>
    <input type="checkbox" name="interface_active" id="interface_active" value="yes"{if $iface.interface_active!="f"} checked="checked"{/if} />
    </td>
</tr>
<tr id="spacer-row">
    <td colspan=2>&nbsp;</td>
</tr>
<tr id="toggle-row">
    <td colspan=2><a href="javascript:toggleAdvanced();" id="expandLink">+ Expand Advanced Configuration</a></td>
</tr>
<tr id="driver-row">
    <th>Interface Driver</th>
    <td>{html_options values=$module_ids output=$modules selected=$interface.module_id name="module_id" id="module_id"}
</td>
</tr>
<tr id="ip_address-row">    
    <th>IP Address</th>
    <td>
    <input type="hidden" name="ip_address-orig" id="ip_address-orig" value="{$iface.ip_address}" />
    <input type="hidden" name="ip_address-orig2" id="ip_address-orig2" value="{$iface.ip_address}" />
    <div id="ip_address-cell">
    <input type="text" name="ip_address" id="ip_address" value="{$iface.ip_address}" />
    </div>
    </td>
</tr>
<tr id="alias_netmask-row">    
    <th>Alias Netmask (eg. /32)</th>
    <td>
    <input type="hidden" name="alias_netmask-orig" id="alias_netmask-orig" value="{$iface.alias_netmask}" />
    <div id="alias_netmask-cell">
    <input type="text" name="alias_netmask" id="alias_netmask" value="{$iface.alias_netmask}" /><span class="note">Use this to override the default netmask for the link when aliasing a single IP to an interface.</span>
    </div>
    </td>
</tr>
<tr id="bridge_interface-row">
    <th>Bridge Destination</th>
    <td>
    <input type="hidden" name="bridge_interface-orig" value="{if $iface.bridge_interface==""}-1{else}{$iface.bridge_interface}{/if}"/>
    {html_options values=$bridge_interfaces output=$bridge_interface_descs selected=$iface.bridge_interface name="bridge_interface" id="bridge_interface"}
    </td>
</tr>
<tr id="master_interface-row">
    <th>Act as Access Point?</th>
    <td>
    <input type="hidden" name="master_interface-orig" value="{$iface.master_interface}"/>
    <input type="checkbox" name="master_interface" id="master_interface" value="yes"{if $iface.master_interface=="t"} checked="checked"{/if}/>
    </td>
</tr>
<tr id="master_channel-row">    
    <th>AP Mode/Channel</th>
    <td>
    <input type="hidden" name="master_mode-orig" value="{if $iface.master_mode==""}{else}{$iface.master_mode}{/if}"/>
    {html_options values=$link_modes output=$link_mode_descs selected=$iface.master_mode name="master_mode" id="master_mode" style="width=\"50px;\""}
    &nbsp;&nbsp;
    <input type="hidden" name="master_channel-orig" id="master_channel-orig"  value="{if $iface.master_channel==""}-1{else}{$iface.master_channel}{/if}"/>
    <span id="master_channel-cell">
    {html_options values=$channels output=$channel_descs name="master_channel" id="master_channel" selected=$iface.master_channel}
    </span>
    </td>
</tr>
<tr id="monitor_interface-row">
    <th>Use as Monitor Interface?</th>
    <td>
    <input type="hidden" name="monitor_interface-orig" value="{if $iface.monitor_interface=="t"}yes{/if}"/>
    <input type="checkbox" name="monitor_interface" id="monitor_interface" value="yes"{if $iface.monitor_interface=="t"} checked="checked"{/if}/>
    </td>
</tr>
<tr id="use_gateway-row">
    <th>Use link gateway?</th>
    <td>
    <input type="hidden" name="use_gateway-orig" value="{if $iface.use_gateway=="t"}yes{/if}"/>
    <input type="checkbox" name="use_gateway" id="use_gateway" value="yes"{if $iface.use_gateway=="t"} checked="checked"{/if}/>
    </td>
</tr>
</table>
<br />
{if $action=="add"}
<input type="submit" name="submit" id="submit" value="Add Interface &gt;&gt;">
{else}
<input type="submit" name="submit" id="submit" value="Update Interface &gt;&gt;">
{/if}
</form>
 <br/>
<ul>
<li><a href="host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
