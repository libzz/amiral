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
{include file="header.tpl" title="Host Configuration"}
Select a host from the list below.
<table>
<tr>
    <th>Hostname</th>
    <th>Location</th>
    <th>Asset</th>
    <th>Status</th>
    <th>Actions</th>
</tr>
{foreach from=$hosts item=host}
<tr class="{cycle values="row1,row2"}">
    {if $host.host_active=="t"}
        {assign var="class" value=""}
    {else}
        {assign var="class" value=" class=\"disabled\""}
    {/if}
    <td{$class}>{$host.host_name}</td>
    <td{$class}>
    {if $host.location==""}<i>In Stock</i>{else}{$host.location}{/if}
    </td>
    <td{$class}>
    {if $host.asset_id==""}
        <i>No Asset Assigned</i>
    {else}
        [{$host.asset_id}]&nbsp;{$host.description}
    {/if}
    </td>
    <td{$class}>
    {if $host.host_active=="f"}
    Disabled
    {else}
    <span class="status{$host.status}" title="{$host.status_hint}">
    {$host.status_text}
    </span>
    {/if}
    </td>
    <td{$class}>
    <a href="host.php?do=edit&host_id={$host.host_id}">[edit]</a>
    &nbsp;
    <a href="host.php?do=delete&host_id={$host.host_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="host.php?do=add">Create new host</a></li>
</ul>

{include file="footer.tpl"}
