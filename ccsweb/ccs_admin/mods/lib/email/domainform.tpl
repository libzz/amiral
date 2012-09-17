{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Domain managment interface
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
{include file="header.tpl" title="Email - $titlea Email Domain"}

<form method="post" action="email.php">
<input type="hidden" name="domain" value="{$domain.domain}">
<input type="hidden" name="do" value="{$action}">
<input type="hidden" name="type" value="domain">
<input type="hidden" name="process" value="yes">

{if $action=="add"}
Please enter the details of the new Domain below. 
<br>
<br>
{assign var="bcaption" value="Add"}
{else}
{assign var="bcaption" value="Update"}
{/if}
<table>
<tr>    
    <th width=120>Owner</th>
    <td>
    <select name="customer_id" id="customer_id">
    {foreach from=$owners key=key item=domaini}
        <optgroup label="{$key}">
        {foreach from=$domaini key=cus_id item=owner}
            <option value="{$cus_id}" {if $cus_id == $domain.customer_id}selected="selected"{/if}>{$owner}</option>
        {/foreach}
        </optgroup>
    {/foreach}
    </select>
    </td>
</tr>
<tr>
    <th>Domain Name</th>
    <td>
    {if $action == "edit"}
    {assign var="utype" value="hidden"}
    {assign var="ustr" value=$domain.domain}
    {else}
    {assign var="utype" value="text"}
    {assign var="ustr" value=""}
    {/if}
    <input type="{$utype}" name="domain" value="{$domain.domain}">{$ustr}
    </td>
</tr>
<tr>
    <th>Catchall Address</th>
    <td><input type="text" name="catchall" value="{$domain.catchall}"></td>
</tr>
<tr>
    <th>Redirect domain</th>
    <td><input type="text" name="redirect" value="{$domain.redirect}"></td>
</tr>
</table>
<br>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$bcaption} Domain &gt;&gt;">
</form>
{if $action=="edit"}
Select a mailbox from the list below.
<table>
<tr>
    <th>Box name</th>
    <th>Box owner</th>
    <th>Quota</th>
    <th>Forward</th>
    <th>Actions</th>
</tr>
{foreach from=$mailboxes item=mailbox}
<tr class="{cycle values="row1,row2"}">
    <td>{$mailbox.email}</td>
    <td>{$mailbox.owner}</td>
    <td>{$mailbox.quota}</td>
    <td>{$mailbox.fwdto}</td>
    <td>
    <a href="email.php?do=edit&type=mailbox&mailbox={$mailbox.login_id}">[edit]</a>
    &nbsp;
    <a href="email.php?do=delete%type=mailbox&mailbox={$mailbox.login_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
{/if}
<ul>
{if $action=="edit"}
<li><a href="email.php?do=add&type=mailbox&domain={$domain.domain}">Create new mailbox</a>
{/if}
<li><a href="email.php">Return&nbsp;to&nbsp;domain&nbsp;list</a>
</ul>
<br>
{include file="footer.tpl"}
