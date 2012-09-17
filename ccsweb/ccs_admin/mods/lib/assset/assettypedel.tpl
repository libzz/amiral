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
{include file="header.tpl" title="Asset Management - Delete Asset Type"}

Are you sure you want to delete the following asset type?:<br>
<table>
<tr>    
    <th width="120">Description</th>
    <td>{$description}</td>
</tr>
</table>
<br>
This will permanently remove all information related to this asset type from
the  database. Asset types cannot be deleted if they are still referenced by
Subasset Types or Assets. Please ensure you have removed all information that
references this asset type from the system before continuing.<br>
<br>
<a href="types.php">Cancel</a>
&nbsp;|&nbsp;
<a href="types.php?do=delete&confirm=yes&asset_type_id={$asset_type_id}">
Delete&nbsp;Asset&nbsp;Type&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
