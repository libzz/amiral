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
{include file="header.tpl" title="Asset Management - Delete Asset Property"}

Are you sure you want to delete the following asset property?:<br>
<table>
<tr>    
    <th width="120">Description</th>
    <td>{$description}</td>
</tr>
</table>
<br>
This will permanently remove all information related to this property from
the  database. Asset properties cannot be deleted if they are still 
referenced by Subassets . Please ensure you have removed all information that
references this property from the system before continuing.<br>
<br>
<a href="properties.php">Cancel</a>
&nbsp;|&nbsp;
<a href="properties.php?do=delete&confirm=yes&asset_property_id={$asset_property_id}">
Delete&nbsp;Asset&nbsp;Property&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
