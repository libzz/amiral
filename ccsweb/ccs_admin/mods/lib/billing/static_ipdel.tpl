{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * IP pool deletion template
 *
 * Author:       Chris Browning <chris@rurallink.co.nz>
 * Version:      $Id: discountdel.tpl 1547 2007-05-21 03:42:40Z ckb6 $
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

Are you sure you want to delete the following IP pool?<br />
<br />
<table>
<tr>    
    <th width="200">Pool</th>
    <td>{$cidr}</td>
</tr>
<tr>    
    <th width="200">Description</th>
    <td>{$description}</td>
</tr>
</table>
<br>
<a href="static_ip.php">Cancel</a>
&nbsp;|&nbsp;

<a href="static_ip.php?do=del&confirm=yes&pool_id={$pool_id}">
Delete&nbsp;Pool&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
