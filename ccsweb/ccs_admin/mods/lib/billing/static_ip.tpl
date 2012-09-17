{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Static Ip Pools
 *
 * Author:       Chris Browning <chris@rurallink.co.nz>
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
    <th>Description</th>
    <th>Used addresses</th>
    <th>Remaining addresses</th>
    <th>Total addresses</th>
    <th>Options</th>
</tr>
{foreach from=$pools item=pool}
<tr class="{cycle values="row1,row2"}">
    <td>{$pool.network}</td>
    <td>{$pool.description}</td>
    <td>{$pool.used}</td>
    <td>{$pool.total-$pool.used}</td>
    <td>{$pool.total}</td>
	<td><a href="static_ip.php?do=show&pool_id={$pool.pool_id}">[show]</a>
	<a href="static_ip.php?do=del&pool_id={$pool.pool_id}&cidr={$pool.network}&description={$pool.description}">[delete]</a></td>
</tr>
{/foreach}
</table>
{$smarty.capture.pagenav}
<ul>
<li><a href="static_ip.php?do=add">Create new IP pool</a></li>
</ul>
{include file="footer.tpl"}
