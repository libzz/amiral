{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Domain management interface
 *
 * Author:       Chris Browning <chris.ckb@gmail.com>
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
{include file="header.tpl" title="Email Domain Configuration"}
Select a domain from the list below.
<table>
<tr>
    <th>Domain Name</th>
    <th>Owner</th>
    <th>Catchall</th>
    <th>Redirect</th>
    <th>Actions</th>
</tr>
{foreach from=$domains item=domain}
<tr class="{cycle values="row1,row2"}">
    <td>{$domain.domain}</td>
    <td>{$domain.owner}</td>
    <td>{$domain.catchall}</td>
    <td>{$domain.redirect}</td>
    <td>
    <a href="email.php?do=edit&type=domain&domain={$domain.domain}">[edit]</a>
    &nbsp;
    <a href="email.php?do=delete&type=domain&domain={$domain.domain}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="email.php?do=add&type=domain">Create new domain</a></li>
</ul>

{include file="footer.tpl"}
