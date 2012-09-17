{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Billing Customer Management template.
 *
 * Author:       Chris Browning <chris@rurallink.co.nz>
 * Version:      $Id: customerform.tpl 1654 2008-02-05 02:25:06Z ckb6 $
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
{assign var="titlea" value=$action|capitalize}
{include file="header.tpl" title="Billing - $titlea Customer"}

<form method="post" action="customer.php">
<input type="hidden" name="customer_id" value="{$customer_id}">
<input type="hidden" name="login_id" value="{$login_id}">
<input type="hidden" name="do" value="activate">
<input type="hidden" name="process" value="yes">

<table id="contact_details">
<tr>
    <th width="120">Month activated</th>
    <td>
	{$month}
    </td>
    <td>
    </td>
</tr>
<tr>
    <th width="120">Day activated</th>
    <td>
	<input type="text" name="day" value="{$today}">
    </td>
    <td>
	Day this month that the account is to be activated on
    </td>
</tr>
</table>
<input type="submit" name="submit" value="Activate Customer &gt;&gt;">
</form>
{include file="footer.tpl"}
