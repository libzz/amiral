{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Domain management interface
 *
 * Author:       Chris Browning <chris.ckb@gmail.com>
 * Version:      $Id: domainlist.tpl 1567 2007-06-27 05:49:49Z ckb6 $
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
{include file="header.tpl" title="Email Configuration"}
This is a list of your mailboxes that we host for you.
<table>
<tr>
    <th>Email</th>
    <!--
    <th>Quota</th>
    -->
    <th>Forward To</th>
    <th>Actions</th>
</tr>
{foreach from=$mailboxes item=mailbox}
<tr class="{cycle values="row1,row2"}">
    <td>{$mailbox.email}</td>
    <!--
    <td>{$mailbox.quota}</td>
    -->
    <td>{$mailbox.fwdto}</td>
    <td>
    <a href="email.php?do=edit&type=mailbox&mailbox={$mailbox.login_id}">[edit]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="email.php?do=add&type=mailbox">Create new mailbox</a></li>
<li><a href="/">Home</a></li>
</ul>

{include file="footer.tpl"}
