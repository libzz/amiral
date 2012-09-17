{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Billing Customer Management template.
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 *				 Ivan Meredith <ivan@ivan.net.nz>
 * Version:      $Id: customerform.tpl 1586 2007-07-04 04:55:24Z ckb6 $
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
{include file="header.tpl" title="Details"}

<form method="post" action="index.php">
<input type="hidden" name="customer_id" value="{$customer.customer_id}">
<input type="hidden" name="login_id" value="{$customer.login_id}">
<input type="hidden" name="do" value="edit">
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
    <th>Username</th>
    <td>
    <input type="hidden" name="username" value="{$customer.username}">{$customer.username}@{$customer.domain}
    <input type="hidden" name="domain" value="{$customer.domain}">
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
</table>
<br>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$bcaption} Contact &gt;&gt;">
</form>
<ul><input type="hidden" name="contact_id" value="{$customer.contact_id}">

<li><a href="/">Home</a>
</ul>
<br>
{include file="footer.tpl"}
