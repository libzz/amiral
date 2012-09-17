{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Authentication interface template
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
{include file="header.tpl" title="Authentication - Delete Group"}

Are you sure you want to delete the following group?:<br>
<table>
<tr>    
    <th width="120">Group Name</th>
    <td>{$group.group_name}</td>
</tr>
<tr>
    <th>Unix Group ID</th>
    <td>{$group.gid}</td>
</tr>
</table>
<br>
This will permanently remove all information related to this group from the 
database, including information about which contacts are members of the group.
You may want to consider simply removing all privileges from this group, 
instead of deleting it.<br>
<br>
<a href="group.php">Cancel</a>
&nbsp;|&nbsp;
<a href="group.php?do=delete&confirm=yes&group_id={$group.admin_group_id}">
Delete&nbsp;Group&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
