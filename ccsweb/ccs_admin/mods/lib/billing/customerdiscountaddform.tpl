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
<input type="hidden" name="customer_discount_id" value="{$discount.customer_discount_id}"/>
<input type="hidden" name="customer_id" value="{$contact_id}"/>
<input type="hidden" name="do" value="{$action}"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="amounts" value="{$discounts}"/>

<div id="instructions">
Please enter the details for the discount you would like to create below.
</div>
<br/>
<table id="discountdetails">
<tr>    
    <th width="200" id="discount_name-header">Discount name</th>
    
    <td>
    <select id="discount_id" name="discount_id" />
    {foreach from=$discounts item=d}
    <option value="{$d.discount_id}" {if $discount.discount_id == $d.discount_id}SELECTED{/if}>{$d.discount_name} - ${$d.amount}</option>
    {/foreach}
    </td>
</tr>
<tr>
    <th>Start date</th>
    <td><input type="text" name="start_date" id="start_date" value="{$discount.start_date}" /></td>
</tr>    
<tr>
    <th>End date</th>
    <td><input type="text" name="end_date" id="end_date" value="{$discount.end_date}" /></td>
</tr>    
<tr>
    <th>Recurring</th>
    <td><input type="checkbox" name="recurring" id="recurring" {if $discount.recurring=="t"}checked{/if} /></td>
</tr>    
</table>
<br/>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$titlea} Discount &gt;&gt;">
</form>
<ul>
<li><a href="customer.php?do=edit&contact_id={$contact_id}">Return&nbsp;to&nbsp;customer</a></li>
</ul>
{include file="footer.tpl"}
