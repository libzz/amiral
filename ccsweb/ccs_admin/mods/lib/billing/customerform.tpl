{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Billing Customer Management template.
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 *				 Ivan Meredith <ivan@ivan.net.nz>
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
{include file="header.tpl" title="Billing - $titlea Customer"}

<form method="post" action="customer.php">
<input type="hidden" name="customer_id" value="{$customer.customer_id}">
<input type="hidden" name="login_id" value="{$customer.login_id}">
<input type="hidden" name="do" value="{$action}">
<input type="hidden" name="process" value="yes">

{if $action=="add"}
Please enter the details of the new account below. An initial password will
be emailed to the address specified when the account is created.<br>
<br>
{assign var="bcaption" value="Add"}
{else}
{assign var="bcaption" value="Update"}
{/if}

{if $plain_password != ""}
<font color=blue>The inital password is {$plain_password}</font>
{/if}
<table id="contact_details">
<tr>
    <th width="120">Account Enabled?</th>
    <td><label name='enabled'>{if $customer.status!=2}<input type="checkbox" name="enabled" value="yes"{if $customer.status == 1 || $action == "add"} checked> True{else}> False{/if}
    </label>{else}&nbsp;(First Login Pending){/if}
    </td>
</tr>
<tr>
    <th>Account Charged?</th>
    <td><label name='charged'><input type="checkbox" name="charged" value="yes"{if $customer.charged == 't' || $action == "add"} checked> True{else}> False{/if}
    </label>
    </td>
</tr>
<tr>    
    <th>Username</th>
    <td>
    {if $action == "edit"}
    <input type="hidden" name="username" value="{$customer.username}">{$customer.username}@{$customer.domain}
    <input type="hidden" name="domain" value="{$customer.domain}">
    {else}
    <input type="text" name="username" value="{$customer.username}">@
    <select name="domain" id="domain">
    <!-- Full domain list
    {foreach from=$domains item=domain}
        <option value="{$domain.domain}" {if $domain.domain == $cdomain}selected="selected"{/if}>{$domain.domain}</option>
    {/foreach}
    -->
    <option value="no8wireless.co.nz" {if $domain.domain == $cdomain}selected="selected"{/if}>no8wireless.co.nz</option>
    <option value="lightwire.co.nz" {if $domain.domain == $cdomain}selected="selected"{/if}>lightwire.co.nz</option>
    <option value="tepahu.net" {if $domain.domain == $cdomain}selected="selected"{/if}>tepahu.net</option>
    <option value="unwire.co.nz" {if $domain.domain == $cdomain}selected="selected"{/if}>unwire.co.nz</option>
    </select>
    {/if}
    </td>
</tr>
<tr>
    <th>First Name</th>
    <td><input type="text" name="givenname" value="{$customer.givenname}"></td>
</tr>
<tr>
    <th>Last Name</th>
    <td><input type="text" name="surname" value="{$customer.surname}"></td>
</tr>
<tr>
	<th>Billing Name</th>
	<td>
    <input type="text" name="billing_name" value="{$customer.billing_name}">
    <span class="note">Only if different to first and last names</span>
    </td>
</tr>
<tr>
    <th>Email Address</th>
    <td><input type="text" name="email" value="{$customer.email}"></td>
</tr>
<tr>
    <th>Phone No.</th>
    <td>
    <input type="text" name="phone" value="{$customer.phone}">
    <span class="note">Format: +CC # ### #### (eg. +64 7 123 4567)</span>
    </td>
</tr>
<tr>
    <th valign="top">Physical Address</th>
    <td><textarea name="address" rows=5 cols=20>{$customer.address}</textarea></td>
</tr>
<tr>
	<th valign="top">Billing Address</th>
	<td>
    <textarea name="billing_address" rows=5 cols=20>{$customer.billing_address}</textarea>
    <span class="note" style="position:relative;top:-80px;">Only if different to the physical address</span>
</td>
</tr>
<tr>
	<th>Billing Plan</th>
	<td><select name="plan_id" id="plan_id">
	{foreach from=$plans item=plan}
	{if $plan.plan_id!=$customer.plan_id}
	<option label="{$plan.description} ({$plan.plan_name})" value="{$plan.plan_id}">{$plan.description} ({$plan.plan_name})</option>
	{else}
	<option label="{$plan.description} ({$plan.plan_name})" value="{$plan.plan_id}" selected="selected">{$plan.description} ({$plan.plan_name})</option>
	{/if}
	{/foreach}
	</select></td>
</tr>
{if $action == "edit"}
<tr>
	<th>Plan Activated</th>
	<td>
	{if $customer.activated}
	{$customer.activated}
	{else}
	<a href='customer.php?do=activate&login_id={$customer.login_id}&customer_id={$customer.customer_id}'>Activate</a>
	{/if}
    </td>
</tr>
{/if}
<tr>
	<th>Connection Method</th>
	<td>
        {html_options name="connection_method" id="connection_method" selected=$customer.connection_method values=$connection_methods output=$connection_methods}
    </td>
</tr>
{if $action=="edit"}
<tr>
    <th>Password</th><td>
    <span class="warn">Warning, changing this password will require changing the password on a CPE.
    </span><br>
    <input type="password" name="newpass" value="">
    <span class="note">NOTE: only complete this field if you wish to 
    change the password.</span>
    <br>
    <a href="customer.php?do=gen&customer_id={$customer.customer_id}&login_id={$customer.login_id}">Generate&nbsp;new&nbsp;password</a>
    </td>
</tr>
{/if}
{if $customer.uid != "" }
<tr>
    <th>Public Key</th>
    <td><textarea name="public_key">{$customer.public_key}</textarea></td>
</tr>
<tr>
    <th>Preferred Shell</th>
    <td><input type="text" name="shell" value="{$customer.shell}"></td>
</tr>
{/if}
</table>
<br>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$bcaption} Contact &gt;&gt;">
</form>
{if $action == "edit"}
<h3>Static IP:</h3>
<table>
<tr>
    <th width=200>Static IP</th>
	<td>{if $static_ip}{$static_ip}
		<a href='static_ip.php?do=free&login_id={$customer.login_id}&customer_id={$customer.customer_id}'>Remove</a>
		{else}
		<a href='static_ip.php?do=assign&login_id={$customer.login_id}&customer_id={$customer.customer_id}'>Assign</a>
		{/if}
	</td>
</tr>
</table>
<h3>Discounts:</h3>
<table>
<tr>
    <th>Name</th>
    <th>Amount</th>
    <th>Start</th>
    <th>End</th>
    <th>Recurring</th>
    <th>Actions</th>
{foreach from=$discounts item=discount}
<tr class="{cycle values="row1,row2"}">
    <td>{$discount.discount_name}</td>
    <td>${$discount.amount}</td>
    <td>{$discount.start_date}</td>
    <td>{$discount.end_date}</td>
    <td>{$discount.recurring}</td>
    <td><a href="discounts.php?do=deleteCustomerDiscount&contact_id={$customer.customer_id}&customer_discount_id={$discount.customer_discount_id}">[delete]</a>
        <a href="discounts.php?do=editCustomerDiscount&contact_id={$customer.customer_id}&customer_discount_id={$discount.customer_discount_id}">[edit]</a>
    </td>
</tr>
{/foreach}
    
</tr>
</table>
{/if}
<ul><input type="hidden" name="contact_id" value="{$customer.contact_id}">

{if $action=="edit"}
<li><a href="discounts.php?do=addCustomerDiscount&contact_id={$customer.customer_id}">Add&nbsp;discount</a>
{/if}
<li><a href="customer.php">Return&nbsp;to&nbsp;customer&nbsp;list</a>
</ul>
<br>
{include file="footer.tpl"}
