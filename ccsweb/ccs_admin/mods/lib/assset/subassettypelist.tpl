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
{include file="header.tpl" title="Asset Management - Subasset Types"}

<table>
<tr>
    <th>Description</th>
    <th>No. Types Used By</th>
    <th>No. Properties</th>
    <th>Actions</th>
</tr>
{foreach from=$subasset_types item=type}
<tr class="{cycle values="row1,row2"}">
    <td>{$type.description}</td>
    <td>{$type.no_asset_types}</td>
    <td>{$type.no_properties}</td>
    <td>
    <a href="types.php?type=subasset&do=edit&subasset_type_id={$type.subasset_type_id}">[edit]</a>
    &nbsp;
    <a href="types.php?type=subasset&do=delete&subasset_type_id={$type.subasset_type_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="types.php?type=subasset&do=add">Create new subasset type</a></li>
</ul>
{include file="footer.tpl"}
