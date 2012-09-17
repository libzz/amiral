{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Discount deletion template
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
{include file="header.tpl" title="Billing Configuration - Delete Discount"}

Are you sure you want to delete the following discount?<br />
<br />
This will cause all related configuration information to be removed from the
database.<br />
You may wish to simply prevent the host from being autoconfigured, or remove
it from
a site.<br />
<br />
<table>
<tr>    
    <th width="200">Discount name</th>
    <td>{$discount.discount_name}</td>
</tr>
<tr>
    <th>Desciption</th>
    <td>{$discount.description}</td>
</tr>
<tr>
    <th>Amount</th>
    <td>${$discount.amount}</td>
</tr>
</table>
<br>
<a href="discounts.php">Cancel</a>
&nbsp;|&nbsp;

<a href="discounts.php?do=deleteBillingDiscount&confirm=yes&discount={$discount.discount_id}">
Delete&nbsp;Discount&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
