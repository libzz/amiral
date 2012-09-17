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
{include file="header.tpl" title="Asset Management - Change Location"}
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

{if ! $can_change}
You cannot update the location of this asset at the present time as it is
marked as in use by the following things.<br/>
<br/>
If you wish to move this asset to a new location you will first have to 
change the configuration of the devices listed below so that they do not 
refer to it anymore.<br/>
<br/>
{else}
Please select the site that you would like to assign this asset to from the
list below.<br/>
<form method="POST" action="asset.php">
<input type="hidden" name="do" value="assign">
<input type="hidden" name="process" value="yes">
<input type="hidden" name="type" value="site">
<input type="hidden" name="asset_id" value="{$asset.asset_id}">
<input type="hidden" name="from" value="{$from}">

<b>Available Sites</b><br/>
{html_options values=$site_ids output=$site_descs selected="$location.site_id" name="new_site" id="new_site" selected=$location.site_id class="assetdetails"}
<br/>
<br/>
<input type="submit" name="submit" value="Move to Site &gt;&gt;">
</form>
<br/>
OR, you can choose to attach this asset to another asset. This may be useful
for a wireless card that is inside a BiscuitPC for example.<br/>
<br/>
<form method="POST" action="asset.php">
<input type="hidden" name="do" value="assign">
<input type="hidden" name="process" value="yes">
<input type="hidden" name="type" value="asset">
<input type="hidden" name="asset_id" value="{$asset.asset_id}">
<input type="hidden" name="from" value="{$from}">

<b>Available Assets</b><br/>
{html_options values=$asset_ids output=$asset_descs selected="$location.attached_to" name="new_asset" id="new_asset" selected=$location.attached_to class="assetdetails"}
<br/>
<br/>
<input type="submit" name="submit" value="Attach to Asset &gt;&gt;">
</form>
<br/>
OR, finally you can assign the asset to a named 'thing' (usually a person).<br/>
<br/>
<form method="POST" action="asset.php">
<input type="hidden" name="do" value="assign">
<input type="hidden" name="process" value="yes">
<input type="hidden" name="type" value="thing">
<input type="hidden" name="asset_id" value="{$asset.asset_id}">
<input type="hidden" name="from" value="{$from}">

<b>Assign To:</b>
<input type="text" name="thing_name" id="thing_name" value="" size="32" />
<br/>
<br/>
<input type="submit" name="submit" value="Assign Asset &gt;&gt;">
</form>
{/if}
<br/>
<br/>
<ul>
<li><a href="asset.php">Return to asset list</a></li>
</ul>

{include file="footer.tpl"}
