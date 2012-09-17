{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Customer list template.
 *
 * Author:       Matt Brown <matt@crc.net.nz>
				 Ivan Meredith <ivan@ivan.net.nz>
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
{include file="header.tpl" title="Customer List"}
<form action="/mods/billing" method="get" id="searchform">
Display {html_options name=num id=num options=$num_results selected=$num} customers per page whose {html_options name=field options=$searchfields selected=$field} matches <input type=text name=search value="{$search}"/>
<input type=submit value="Search">
<input type=reset name=reset id=reset>
</form>

{capture name="pagenav"}
{if $max_page > 1}
<div class="pagenav">
{if $current_page != 1}
    <a href="customer.php?page={$current_page-1}&field={$field}&search={$search}">&lt;&lt; Prev</a>
{/if} 
{foreach from=$pagenum item=page}
    {if $current_page == $page}
        <span class="currentpage">{$page}</span>
    {else}
        <a href="customer.php?page={$page}&field={$field}&search={$search}">{$page}</a>
    {/if}
{/foreach}
{if $current_page != $max_page}
    <a href="customer.php?page={$current_page+1}&field={$field}&search={$search}">Next &gt;&gt;</a>
{/if}
</div>
{/if}
{/capture}
{$smarty.capture.pagenav}

<table>
<tr>
	<th>ID</th>
    <th>Username</th>
    <th>First name</th>
    <th>Last name</th>
    <th>Billing Plan</th>
	<th>Cap Started</th>
    <th>Cap Usage</th>
    <th>Cap Rollover</th>
    <th>Active Plan</th>
    <th>Options</th>
</tr>
{foreach from=$customers item=customer}
<tr class="{cycle values="row1,row2"}">
	<td>{$customer.customer_id}</td>
    <td>{$customer.username}</td>
    <td>{$customer.givenname}</td>
    <td>{$customer.surname}</td>
    <td title="{$customer.billing_plan_desc}">{$customer.billing_plan_desc|truncate:28:"...":true}</td>
    <td>{$customer.plan_start}</td>
    {if $customer.cap_usage_int > 100}
        {assign var="uclass" value="critical"}
    {elseif $customer.cap_usage_int > 80}
        {assign var="uclass" value="warning"}
    {else}
        {assign var="uclass" value="ok"}
    {/if}
    <td title="Used {$customer.total_mb}MB out of {$customer.cap_at_mb}MB" class="usage">
        <span class="status{$uclass}">{$customer.cap_usage}</span>
        ({$customer.total_mb}MB used)
    </td>
    <td>{$customer.cap_period}</td>
    <td>{$customer.radius_plan_desc|capitalize}</td>
	<td><a href="customer.php?do=edit&contact_id={$customer.customer_id}">[edit]</a>
	<a href="customer.php?do=history&contact_id={$customer.customer_id}">[history]</a>
    </td>
</tr>
{/foreach}
</table>
{$smarty.capture.pagenav}
<ul>
<li><a href="customer.php?do=add">Create new customer</a></li>
</ul>
{include file="footer.tpl"}
