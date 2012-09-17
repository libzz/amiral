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
{include file="header.tpl" title="Authentication - Delete User"}

Are you sure you want to delete the following user?:<br>
<table>
<tr>
    <th width="100">Status</th>
    <td>{if $contact.status!=2}
    {if $contact.status == 1}Enabled{else}Disabled{/if}
    {else}First Login Pending{/if}
    </td>
</tr>
<tr>    
    <th>Username</th>
    <td>{$contact.username}</td>
</tr>
<tr>
    <th>First Name</th>
    <td>{$contact.givenname}</td>
</tr>
<tr>
    <th>Last Name</th>
    <td>{$contact.surname}</td>
</tr>
<tr>
    <th>Email Address</th>
    <td>{$contact.email}</td>
</tr>
<tr>
    <th>Account Type</th>
    <td>{$contact.type}</td>
</tr>
<tr>
    <th>User ID</th>
    <td>{$contact.uid}</td>
</tr>
</table>
<br>
This will permanently remove all information related to this user from the 
database. You may want to consider simply disabling the user account which
will prevent all usage while enabling you to keep a historical record of the
account.<br>
<br>
<a href="user.php?do=disable&contact_id={$contact.login_id}">
&lt;&lt;&nbsp;Disable&nbsp;User&nbsp;Account</a>
&nbsp;|&nbsp;
<a href="user.php">Cancel</a>
&nbsp;|&nbsp;

<a href="user.php?do=delete&confirm=yes&contact_id={$contact.login_id}">
Delete&nbsp;User&nbsp;&nbsp;Account&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
