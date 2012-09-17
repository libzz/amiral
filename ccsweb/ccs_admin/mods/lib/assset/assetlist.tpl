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
{include file="header.tpl" title="Asset Management"}

<form name="filter" action="index.php" method="get">
Show&nbsp;Only:&nbsp;{html_options values=$asset_type_ids output=$asset_type_descs selected=$asset_type_id name="asset_type_id" id="asset_type_id"}
<input type="submit" value="Filter List &gt;" />
&nbsp;&nbsp;or&nbsp;&nbsp;
<input type="submit" value="Reset Filter" onclick="$('asset_type_id').value=-1;" />
</form>
<br />
<table>
{foreach from=$asset_types item=asset_type}
{if $asset_type_id==$asset_type.asset_type_id or ($asset_type.no_assets != 0 and $asset_type_id==-1)}
<tr>
    <th colspan="4" class="atheader">{$asset_type.description}</th>
</tr>
{if $asset_type.no_assets == 0}
<tr>
    <td colspan="2">There are no assets in this category!<br /></td>
</tr>
{else}
<tr>
    <th>Asset ID</th>
    <th>Description</th>
    <th>Current Location</th>
    <th>Actions</th>
</tr>
{assign var="atid" value=$asset_type.asset_type_id}
{foreach from=$assets.$atid item=asset}
<tr class="{cycle values="row1,row2"}">
    <td>{$asset.asset_id}</td>
    <td>{$asset.description}</td>
    <td title="At site '{$asset.location}' since {$asset.location_updated|date_format:"%d %b %Y"}">{$asset.location}</td>
    <td>
    <a href="asset.php?do=edit&asset_id={$asset.asset_id}">[edit]</a>
    &nbsp;
    <a href="asset.php?do=assign&asset_id={$asset.asset_id}">[change location]</a>
    &nbsp;
    <a href="asset.php?do=history&asset_id={$asset.asset_id}">[view history]</a>    </td>
</tr>
{/foreach}
{/if}
<tr>
    <td colspan="4">&nbsp;</td>
</tr>
{/if}
{/foreach}
</table>
<ul>
<li><a href="asset.php?do=add">Create new asset</a></li>
<li><a href="asset.php?do=addsoekris">Create new soekris asset(s)</a></li>
<li><a href="asset.php?do=addwireless">Create new wireless card asset(s)</a></li>
</ul>

{include file="footer.tpl"}
