{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Discount list template
 *
 * Author:       Chris Browning <chris.ckb@gmail.com>
 *
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

{include file="header.tpl" title="Billing Configuration - Discount Management"}
	
<table>
<tr>
    <th>Name</th>
    <th>Description</th>
    <th>Amount</th>
    <th>Actions</th>
</tr>
{foreach from=$discounts item=discount}
<tr class="{cycle values="row1,row2"}">
    <td>{$discount.discount_name}</td>
    <td>{$discount.description}</td>
    <td><div align=right>${$discount.amount}</div></td>
    <td><a href="discounts.php?do=editBillingDiscount&discount_id={$discount.discount_id}">[edit]</a>
		<a href="discounts.php?do=deleteBillingDiscount&discount_id={$discount.discount_id}">[delete]</a>
	</td>
</tr>
{/foreach}
</table>
<br/>
<li><a href="discounts.php?do=addBillingDiscount">Create a new discount</a></li>
{include file="footer.tpl"}
