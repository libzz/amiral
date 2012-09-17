{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Link manipulation user interface template
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
{include file="header.tpl" title="Link Configuration - Edit Link"}
<form method="post" action="link.php">
<input type="hidden" name="do" value="edit" />
<input type="hidden" name="process" value="yes" />
<input type="hidden" name="link_id" id="link_id" value="{$link.link_id}" />
<div id="instructions">
Please enter the updated details for this link below. 
</div>
<br/>
<table id="linkdetails">
<tr>    
    <th width="200" id="description-header">Description</th>
    <td><input type="text" name="description" id="description" value="{$link.description}" /></td>
</tr>
<tr>
    <th id="type-header">Link Type</th>
    <td>
    {html_options values=$link_types output=$link_type_descs selected=$link.type name="type" id="type"}
    </td>
</tr>
<tr>
    <th id="mode-header">Link Mode</th>
    <td id="mode-cell">
    {html_options values=$link_modes output=$link_mode_descs selected=$link.mode name="mode" id="mode"}
    </td>
</tr>
{if $link.type=="Managed" || $link.type=="Ad-Hoc" }
{assign var="wclass" value=""}
{else}
{assign var="wclass" value=" class=\"hidden\""}
{/if}
<tr id="essid-row"{$wclass}>    
    <th id="essid-header">ESSID</th>
    <td><input type="text" name="essid" id="essid" value="{$link.essid}" /></td>
</tr>
<tr id="channel-row"{$wclass}>
    <th id="channel-header">Link Channel</th>
    <td id="channel-cell">
    {html_options values=$channels output=$channel_descs selected=$link.channel name="channel" id="channel"}
    </td>
</tr>
<tr id="key-row"{$wclass}>    
    <th id="key-header">WEP Key</th>
    <td><input type="text" name="key" id="key" value="{$link.key}" /></td>
</tr>
<tr>
    <th id="class_id-header">Network Class</th>
    <td>
    {html_options values=$link_class_ids output=$link_class_descs selected=$link.class_id name="class_id" id="class_id"}    
    </td>
</tr>
<tr>    
    <th width="200" id="network_address-header">Network Address</th>
    <td id="network_address-cell">{include file="inputbox.tpl" name="network_address" value=$link.network_address}</td>
</tr>
<tr>    
    <th id="shared_network-header">Shared Network?</th>
    <td>
    <input type="checkbox" name="shared_network" id="shared_network" value="yes"{if $link.shared_network=="t"} checked="checked"{/if} />
    </td>
</tr>
<tr>
    <td colspan="2">&nbsp;</td>
</tr>
<tr>
    <td colspan="2">
    <input type="submit" name="submit" id="submit" value="Update Link &gt;&gt;">
    </td>
</tr>
</table>
<br/>
</form>
<ul>
<li><a href="link.php">Return&nbsp;to&nbsp;link&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
