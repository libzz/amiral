{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Customer list template.
 *
 * Author:       Matt Brown <matt@crc.net.nz>
				 Ivan Meredith <ivan@ivan.net.nz>
 * Version:      $Id: customerlist.tpl 1554 2007-06-25 03:40:31Z ckb6 $
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
{include file="header.tpl" title="Static IP Pool"}
<table>
<tr>
    <th>Network</th>
    <th>User</th>
    <th>Options</th>
</tr>
{foreach from=$pool item=itm}
<tr class="{cycle values="row1,row2"}">
    <td>{$itm.ip_address}</td>
	{if $itm.username}
    	<td>{$itm.username}@{$itm.domain}</td>
	{else}
		<td></td>
	{/if}
	{if $itm.username}
		<td><a href="static_ip.php?do=free&login_id={$itm.login_id}">[free]</a></td>
	{else}
		<td></td>
	{/if}
</tr>
{/foreach}
</table>
<ul>
<li><a href="static_ip.php">Return to Pools</a></li>
</ul>
{include file="footer.tpl"}
