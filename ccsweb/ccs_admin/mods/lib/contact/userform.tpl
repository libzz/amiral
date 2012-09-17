{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Authentication interface template
 *
 * Author:       Matt Brown <matt@crc.net.nz>
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
{include file="header.tpl" title="Authentication - $titlea User"}

<form method="post" action="user.php">
<input type="hidden" name="admin_id" value="{$contact.admin_id}">
<input type="hidden" name="login_id" value="{$contact.login_id}">
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
<font color=blue>A new password has been emailed to {$contact.email}. They will be prompted to set a new password when they login</font>
{/if}
<table>
<tr>
    <th width="120">Account Enabled?</th>
    <td><label name='enabled'>{if $contact.status!=2}<input type="checkbox" name="enabled" value="yes"{if $contact.status == 1 || $action == "add"} checked> True{else}> False{/if}
    </label>{else}&nbsp;(First Login Pending){/if}
    </td>
</tr>
<tr>    
    <th>Username</th>
    <td>
    {if $action == "edit"}
    <input type="hidden" name="username" value="{$contact.username}">{$contact.username}@{$contact.domain}
    <input type="hidden" name="domain" value="{$contact.domain}">
    {else}
    <input type="text" name="username" value="{$contact.username}">@
    <input type="text" name="domain" value="{$contact.domain}">
    {/if}
    </td>
</tr>
<tr>
    <th>First Name</th>
    <td><input type="text" name="givenname" value="{$contact.givenname}"></td>
</tr>
<tr>
    <th>Last Name</th>
    <td><input type="text" name="surname" value="{$contact.surname}"></td>
</tr>
<tr>
    <th>Email Address</th>
    <td><input type="text" name="email" value="{$contact.email}"></td>
</tr>
<tr>
    <th>Phone No.</th>
    <td><input type="text" name="phone" value="{$contact.phone}"></td>
</tr>
<tr>
    <th>Postal Address</th>
    <td><input type="text" name="address" value="{$contact.address}"></td>
</tr>
{if $action=="edit"}
<tr>
    <th>Password</th>
    <td><input type="password" name="newpass" value="">
    <span class="note">NOTE: only complete this field if you wish to 
    change the password.</span>
    <br>
    <a href="user.php?do=gen&admin_id={$contact.admin_id}&login_id={$contact.login_id}">Generate&nbsp;new&nbsp;password</a>
    </td>
</tr>
{/if}
<tr>
    <th>Account Type</th>
    <td><select name="type">
    {if $action=="add"}
	{html_options options=$contact_types selected="user"}
    {else}
	{html_options options=$contact_types selected=$contact.type}
    {/if}
    </select></td>
</tr>
{if $contact.type == "user" && $action != "add"} 
<tr>
    <th>Unix User ID</th>
    <td>{if $contact.uid != ""}{$contact.uid}{else}
    <a href="user.php?do=assignuid&contact_id={$contact.contact_id}">Assign UID</a>
    {/if}
    </td>
</tr>
{/if}
{if $contact.uid != "" }
<tr>
    <th>Public Key</th>
    <td><textarea name="public_key">{$contact.public_key}</textarea></td>
</tr>
<tr>
    <th>Preferred Shell</th>
    <td><input type="text" name="shell" value="{$contact.shell}"></td>
</tr>
{/if}
</table>
<br>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$bcaption} Contact &gt;&gt;">
</form>
<ul>
<li><a href="user.php">Return&nbsp;to&nbsp;contact&nbsp;list</a>
</ul>
<br>
{include file="footer.tpl"}
