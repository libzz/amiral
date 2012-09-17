{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Adding discounts template.
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
 {assign var="titlea" value=$action|capitalize}
{include file="header.tpl" title="Billing - $titlea discount"}
<form method="post" action="discounts.php" id="discountForm">
<input type="hidden" name="discount_id" value="{$discount.discount_id}"/>
<input type="hidden" name="do" value="{$action}"/>
<input type="hidden" name="process" value="yes"/>

<div id="instructions">
Please enter the details for the discount you would like to create below.
</div>
<br/>
<table id="discountdetails">
<tr>    
    <th width="200" id="discount_name-header">Discount name</th>
    <td><input type="text" name="discount_name" id="discount_name" value="{$discount.discount_name}" /></td>
</tr>
<tr>
    <th>Description</th>
    <td><input type="text" name="description" id="description" value="{$discount.description}" /></td>
    
<tr>
    <th>Amount</th>
    <td><input type="text" name="amount" id="amount" value="{$discount.amount}"/></td>
</tr>
</table>
<br/>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$titlea} Discount &gt;&gt;">
</form>
<ul>
<li><a href="discounts.php">Return&nbsp;to&nbsp;host&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
