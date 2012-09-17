{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Email management interface
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
<tr>    
    <th width=120>Owner</th>
    <td>
    {if $action == "edit"}
    <input type="hidden" name="customer_id" value={$mailbox.customer_id}>
    <input type="hidden" name="login_id" value={$mailbox.login_id}>
    <input type="hidden" name="owner" value="{$mailbox.owner}">{$mailbox.owner}
    <input type="hidden" name="domain" value="{$mailbox.domain}">
    {else}
    <select name="customer_id" id="customer_id">
    {foreach from=$owners key=key item=domaini}
        <optgroup label="{$key}">
        {foreach from=$domaini key=cus_id item=owner}
            <option value="{$cus_id}" {if $cus_id == $domain.customer_id}selected="selected"{/if}>{$owner}</option>
        {/foreach}
        </optgroup>
    {/foreach}
    </select>
    {/if}
    </td>
</tr>
<tr>
    <th>Email</th>
    <td>
    {if $action == "edit"}
    <input type="hidden" name="email" value="{$mailbox.email}">{$mailbox.email}
    <input type="hidden" name="username" value="{$mailbox.username}">
    {else}
    <input type="text" name="username" value="{$mailbox.username}">@{$mailbox.domain}
    {/if}
    </td>
</tr>
<tr>
    <th>Quota</th>
    <td><input type="text" name="quota" value="{$mailbox.quota}"></td>
</tr>
<tr>
    <th>Forward To</th>
    <td><input type="text" name="fwdto" value="{$mailbox.fwdto}"></td>
</tr>
<tr>
    <th>Password</th><td>
    {if $mailbox.restrict == 1}
    <span class="warn">Warning, changing this password will require changing the password on a CPE.
    </span><br>{/if}
    <input type="password" name="passwd" value="">
    <span class="note">NOTE: only complete this field if you wish to 
    change the password.</span>
    {if $action == "edit"}
    <br>
    <a href="email.php?do=gen&owner_id={$mailbox.owner_login_id}&mailbox={$mailbox.login_id}">Generate&nbsp;new&nbsp;password</a>
    {/if}
    </td>
</tr>

</table>
<br>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$bcaption} Mailbox &gt;&gt;">
</form>

<ul>
<li><a href="email.php?do=edit&type=domain&domain={$mailbox.domain}">Return&nbsp;to&nbsp;domain</a>
<li><a href="email.php">Return&nbsp;to&nbsp;domain&nbsp;list</a>
</ul>
<br>
{include file="footer.tpl"}
