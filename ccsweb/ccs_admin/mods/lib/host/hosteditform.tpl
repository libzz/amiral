{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Host manipulation user interface template
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
{include file="header.tpl" title="Host Configuration - Edit Host"}
<form method="post" action="host.php" id="editForm">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please enter the new details for this host below.</div>
<br/>
<table id="hostdetails">
<tr>    
    <th width="200" id="host_name-header">Hostname</th>
    <td><input type="text" name="host_name" id="host_name" value="{$host.host_name}" onchange="validateHostname();" /></td>
    <td rowspan="9">
    <div id="hoststatus">
    <h2>Host Status</h2>
    {if $status}
    <table>
    <tr>
        <th width="100">State</th>
        {if $status.reachable}
            {assign var="c" value="statusok"}
            {assign var="t" value="Last checked at $status.lastCheckedAt"}
            {assign var="s" value=" Up"}
        {else}
            {assign var="c" value="statuscritical"}
            {assign var="t" value="Not seen since $status.infoUpdatedAt"}
            {assign var="s" value=" Down"}
        {/if}
        <td id="hoststate" class="{$c}" title="{$t}">{$host.ip_address}{$s}</td>
    </tr>
    <tr>
        <th valign="top">SSH Keys</th>
        <td id="sshkeystate" class="status{$status.ssh_key_status}">
        <span title="{$status.ssh_key_text}">{$status.ssh_key_status|upper}</span>
        {if $status.ssh_key_status!="ok"}&nbsp;&nbsp;
        <a href="host.php?do=generateSSHKeys&host_id={$host.host_id}">[regenerate]</a>
        {/if}
        </td>
    </tr>
    <tr>
        <th valign="top">CFengine Keys</th>
        <td id="cfenginekeystate" class="status{$status.cfengine_key_status}">
        <span title="{$status.cfengine_key_text}">{$status.cfengine_key_status|upper}</span>
        {if $status.cfengine_key_status!="ok"}&nbsp;&nbsp;
        <a href="host.php?do=generateCFengineKeys&host_id={$host.host_id}">[regenerate]</a>
        {/if}
        </td>
    </tr>
    <tr>
        <th valign="top">Config Revision</th>
        <td title="O/A/G Revs: {$status.operating_rev_text} - {$status.operating_rev_hint}">
        {if $status.operating_rev!=-1 && $status.operating_rev!=""}
        <a href="/configs/inputs/hosts/{$host.host_name}?rev={$status.operating_rev}" class="status{$status.operating_rev_status}">[{$status.operating_rev}]</a>
        {else}
        ??
        {/if}
        /
        {if $status.active_rev!=-1 && $status.active_rev!=""}
        <a href="/configs/inputs/hosts/{$host.host_name}?rev={$status.active_rev}">[{$status.active_rev}]</a>
        {else}
        ??
        {/if}
        /
        {if $status.generated_rev!=-1 && $status.generated_rev!=""}
        <a href="/configs/inputs/hosts/{$host.host_name}?rev={$status.generated_rev}">[{$status.generated_rev}]</a>
        {else}
        ??
        {/if}
        <a href="host.php?do=generateHostConfig&host_name={$host.host_name}"><b>[regenerate]</b></a>
        </td>
    </tr>
    <tr>
        <th>Traffic Load</th>
        <td id="trafficload"></td>
    </tr>
    <tr>
        <th>Uptime</th>
        <td id="uptime"></td>
    </tr>
    </table>
    {else}
    <br>There is not status information available for this host!
    {/if}
    </div>
    </td>
</tr>
<tr>
    <th id="site_id-header">Current Location</th>
    <td><input type="hidden" name="site_id-orig" id="site_id-orig" value="{$host.site_id}">
    {html_options values=$site_ids output=$site_descs selected=$host.site_id name="site_id" id="site_id"}
    </td>
</tr>
<tr>
    <th id="asset_id-header">Asset Hardware</th>
    <td id="asset_id-cell">{include file="mods/host/host-assetlist.tpl"}</td>
</tr>
<tr>
    <th id="distribution-header">Distribution</th>
    <td>
    {html_options values=$distribution_ids output=$distributions selected=$host.distribution_id name="distribution_id" id="distribution_id"}
    </td>
</tr>
<tr>
    <th id="kernel-header">Kernel</th>
    <td>
    {html_options values=$kernel_ids output=$kernels selected=$host.kernel_id name="kernel_id" id="kernel_id"}    
    </td>
</tr>
<tr>    
    <th id="is_gateway-header">Act as an Internet Gateway?</th>
    <td>
    <input type="hidden" name="is_gateway-orig" value="{$host.isgateway}"/>
    <input type="checkbox" name="is_gateway" id="is_gateway" value="yes"{if $host.is_gateway=="t"} checked="checked"{/if} />
    </td>
</tr>
<tr>    
    <th id="host_active-header">Configure Automatically?</th>
    <td>
    <input type="hidden" name="host_active-orig" value="{$host.host_active}"/>
    <input type="checkbox" name="host_active" id="host_active" value="yes"{if $host.host_active=="t"} checked="checked"{/if} />
    </td>
</tr>
<tr>    
    <td colspan=2>&nbsp;</td>
</tr>
<tr>    
    <td colspan=2>
    <input type="submit" name="submit" id="submit" value="Update Host &gt;&gt;">
    </td>
</tr>
</table>
<br/>
</form>

<div id="interfaces">
<h2>Interfaces</h2>
<table>
<tr>    
    <th>Interface Name</th>
    <th>Status</th>
    <th>IP Address</th>
    <th>Subasset</th>
    <th>Link</th>
    <th>Actions</th>
</tr>
{foreach from=$host.interfaces item=iface}
<tr class="{cycle values="row1,row2"}">
    {if $iface.statuscode=="OK"}
        {assign var="class" value=""}
    {else}
        {assign var="class" value=" class=\"disabled\""}
    {/if}
    <td{$class}>
    {if $iface.interface_type == 4}
        <span class="disabled">{$iface.name}</span>
    {else}
        {$iface.name}
    {/if}
    {if $iface.master_mode!=""}
    <b>&nbsp;&nbsp;(802.11{$iface.master_mode} on ch{$iface.master_channel})</b>
    {/if}
    </td>
    <td{$class}>{$iface.status}</td>
    <td{$class}>
    {if $iface.bridge_interface != ""}{$iface.bridge_desc}{else}{$iface.ip_address}{/if}{if $iface.alias_netmask != ""}{$iface.alias_netmask}{/if}
    </td>
    <td{$class}>{$iface.subasset_desc}</td>
    <td{$class}>{$iface.link_desc}</td>
    <td>
    {if $iface.statuscode!="UNCONFIGURED"}
    <a href="interface.php?do=edit&host_id={$host.host_id}&interface_id={$iface.interface_id}">[reconfigure]</a>&nbsp;&nbsp;
    <a href="interface.php?do=remove&host_id={$host.host_id}&interface_id={$iface.interface_id}">[remove]</a>
    {else}
    <a href="interface.php?do=add&host_id={$host.host_id}&subasset_id={$iface.subasset_id}">[configure]</a>
    {/if}
    </td>
</tr>
{/foreach}
</table>
<br/>
</div>
<ul>
<li><a href="interface.php?do=add&host_id={$host.host_id}">Add new interface</a></li>
</ul>
<br />
<div id="services">
{include file="mods/host/host-slist.tpl" cservices=$host.services services=$services host_id=$host.host_id}
</div>
<br/>
<ul>
<li><a href="host.php">Return&nbsp;to&nbsp;host&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
