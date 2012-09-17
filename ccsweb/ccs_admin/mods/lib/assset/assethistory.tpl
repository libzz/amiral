{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Asset manipulation template
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
{include file="header.tpl" title="Asset Management - Asset History"}

<table>
<tr>    
    <th width="200">Asset ID</th>
    <td>{$asset.asset_id}</td>
</tr>
<tr>    
    <th width="200">Asset Type</th>
    <td>{$asset.asset_type_description}</td>
</tr>
<tr>
    <th>Current Location</th>
    <td>{$asset.location}</td>
</tr>
<tr>    
    <th>Enabled</th>
    <td>{if $asset.enabled=="t"}Yes{else}No{/if}</td>
</tr>
<tr>    
    <th id="description-header">Description</th>
    <td>{$asset.description}</td>
</tr>
</table>
<br/>
The following events are recorded in the history for this asset.
<br/><br/>
<table>
<tr>
    <th>Date</th>
    <th>User</th>
    <th>Event Type</th>
    <th>Details</th>
</tr>
{foreach from=$history item=hist}
<tr class="{cycle values="row1,row2"}">
    <td>{$hist.timestamp|date_format:"%d %b %Y %H:%M:%S %z"}</td>
    <td>{$hist.username}</td>
    <td>{$hist.description}</td>
    <td>{$hist.event_desc}</td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="asset.php">Return to asset list</a></li>
<li><a href="asset.php?do=edit&asset_id={$asset.asset_id}">Edit Asset</a></li>
</ul>

{include file="footer.tpl"}
