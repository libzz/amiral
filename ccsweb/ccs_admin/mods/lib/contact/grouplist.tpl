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
{include file="header.tpl" title="Authentication - Group List"}

<table>
<tr>
    <th>Group Name</th>
    <th>Unix Group ID</th>
    <th>No. Members</th>
    <th>Actions</th>
</tr>
{foreach from=$groups item=group}
<tr class="{cycle values="row1,row2"}">
    <td>{$group.group_name}</td>
    <td>{$group.gid}</td>
    <td>{$group.nmembers}</td>
    <td>
    <a href="group.php?do=edit&group_id={$group.admin_group_id}">[edit]</a>
    &nbsp;
    <a href="group.php?do=delete&group_id={$group.admin_group_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="group.php?do=add">Create new group</a></li>
</ul>
{include file="footer.tpl"}
