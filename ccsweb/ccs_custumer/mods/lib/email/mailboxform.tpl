{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Email management interface
 *
 * Author:       Chris Browning <chris.ckb@gmail.com>
 * Version:      $Id: mailboxform.tpl 1562 2007-06-26 21:43:38Z ckb6 $
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
{include file="header.tpl" title="Email - $titlea Email Mailbox"}

<form method="post" action="email.php">
<input type="hidden" name="email" value="{$mailbox.email}">
<input type="hidden" name="domain" value="{$mailbox.domain}">
<input type="hidden" name="do" value="{$action}">
<input type="hidden" name="type" value="mailbox">
<input type="hidden" name="process" value="yes">

{if $action=="add"}
Please enter the details of the new Mailbox below. 
<br>
<br>
{assign var="bcaption" value="Add"}
{else}
{assign var="bcaption" value="Update"}
{/if}
{if $plain_password != ""}
<font color=blue>The inital password is {$plain_password}</font>
{/if}
<table>
<input type="hidden" name="customer_id" value={$mailbox.customer_id}>
<input type="hidden" name="login_id" value={$mailbox.login_id}>
<input type="hidden" name="domain" value="{$mailbox.domain}">
<tr>
    <th>Email</th>
    <td>
    {if $action == "edit"}
    <input type="hidden" name="email" value="{$mailbox.email}">{$mailbox.email}
    <input type="hidden" name="username" value="{$mailbox.username}">
    {else}
    <input type="text" name="username" value="{$mailbox.username}">@
    <select name="domain" id="domain">
    {foreach from=$domains item=domain}
        <option value="{$domain.domain}" {if $domain.domain == $cdomain}selected="selected"{/if}>{$domain.domain}</option>
    {/foreach}
    </select>
    
    {/if}
    </td>
</tr>
<!-- 
<tr>
    <th>Quota</th>
    <td>{$mailbox.quota}</td>
</tr>
-->
<tr>
    <th>Forward To</th>
    <td><input type="text" name="fwdto" value="{$mailbox.fwdto}">
    <span class="note">If this is set any emails that are recieved by this account will forwarded to the email address set here.</span></td>
</tr>
<tr>
    {if $mailbox.restrict != 1}
    <th>Password</th>
    <td><input type="password" name="passwd" value="">
    <span class="note">NOTE: only complete this field if you wish to 
    change the password.</span>
    </td>
    {/if}
</tr>

</table>
<br>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$bcaption} Mailbox &gt;&gt;">
</form>

<ul>
<li><a href="email.php">Return&nbsp;to&nbsp;mailbox&nbsp;list</a>
</ul>
<br>
{include file="footer.tpl"}
