{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Static IP Pool
 *
 * Author:       Chris Browning <chris@rurallink.co.nz>
 * Version:      $Id: customerform.tpl 1604 2007-07-25 04:55:06Z ckb6 $
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
{include file="header.tpl" title="Add Static IP pool"}

<form method="post" action="static_ip.php">
<input type="hidden" name="process" value="yes">
<input type="hidden" name="do" value="add">

<table>
<tr>
    <th>Network</th>
    <td><input type="text" name="cidr" value="">In the form of 192.168.1.0/24</td>
</tr>
<tr>
    <th>Description</th>
    <td><input type="text" name="description" value="">Short description for the pool</td>
</tr>
</table>
<br>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="Add Pool &gt;&gt;">
</form>
<ul>
<li><a href="static_ip.php">Return to static ip pools</a>
</ul>
<br>
{include file="footer.tpl"}
