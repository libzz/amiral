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
{include file="header.tpl" title="Authentication - Contact List"}

<table>
<tr>
    <th>Status</th>
    <th>Username</th>
    <th>First Name</th>
    <th>Last Name</th>
    <th>Email Address</th>
    <th>Account Type</th>
    <th>Unix User ID</th>
    <th>Actions</th>
</tr>
{foreach from=$contacts item=contact}
<tr class="{cycle values="row1,row2"}">
    <td>{if $contact.status == 1}Active
    {elseif $contact.status == 0}Disabled
    {elseif $contact.status == 2}Pending Login
    {else}Unknown{/if}</td>
    <td>{$contact.username}</td>
    <td>{$contact.givenname}</td>
    <td>{$contact.surname}</td>
    <td>{$contact.email}</td>
    <td>{$contact.type|capitalize}</td>
    <td>{$contact.uid}</td>
    <td>
    <a href="user.php?do=edit&contact_id={$contact.admin_id}">[edit]</a>
    &nbsp;
    <a href="user.php?do=delete&contact_id={$contact.admin_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="user.php?do=add">Create new contact</a></li>
</ul>
{include file="footer.tpl"}
