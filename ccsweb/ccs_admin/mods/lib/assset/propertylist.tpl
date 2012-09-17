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
{include file="header.tpl" title="Asset Management - Asset Properties"}

<table>
<tr>
    <th width="20%">Description</th>
    <th width="20%">No. Subassets Used By</th>
    <th>Actions</th>
</tr>
{foreach from=$properties item=prop}
<tr class="{cycle values="row1,row2"}">
    <td>{$prop.description}</td>
    <td>{$prop.no_subasset_properties}</td>
    <td>
    <a href="properties.php?do=edit&asset_property_id={$prop.asset_property_id}">[edit]</a>
    &nbsp;
    <a href="properties.php?do=delete&asset_property_id={$prop.asset_property_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="properties.php?do=add">Create new asset property</a></li>
</ul>
{include file="footer.tpl"}
