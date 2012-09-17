{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Adding plans template.
 *
 * Author:       Ivan Meredith <ivan@ivan.net.nz>
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

{include file="header.tpl" title="Billing - Customer History"}
<form method="get" action="customer.php">
    <input type=hidden name="do" value="history" />
    Username: <input type=text name="username" value="{$customer.username}"/>
    <input type=submit value="View History" />
</form>
<h4>Traffic Usage History for {$customer.givenname} {$customer.surname} - Username: {$customer.username}</h4>
<form method="get" action="customer.php">

<select name="monthkey">
    {foreach from=$history_dates key=tmonthkey item=tmonth}
    {if $monthkey==$tmonthkey}
    <option label="{$tmonth}" value="{$tmonthkey}" selected>{$tmonth}</option>
    {else}
    <option label="{$tmonth}" value="{$tmonthkey}">{$tmonth}</option>
    {/if}
    {/foreach}
</select>
<input type="hidden" name="contact_id" value="{$contact_id}"/>
<input type="hidden" name="do" value="history" />
<input type="submit" name="sumbit" value="Go" />
<form>
<table>
<tr>
    <th>Day of Month</th>
    <th>Uploads (mb)</th>
    <th>Downloads (mb)</th>
    <th>Total (mb)</th>
</tr>
{assign var="total" value=0}
{foreach from=$history key=day item=i}
<tr class="{cycle values="row1,row2"}">
    <td>{$day}</td>
    <td>{$i.input}</td>
    <td>{$i.output}</td>
    <td>{$i.input+$i.output}</td>
</tr>
{assign var="total" value=$total+$i.input+$i.output}
{/foreach}
<tr class="total">
    <td><b>Total data for month (mb)</b></td>
    <td></td>
    <td></td>
    <td><b>{$total}</b></td>
</tr>
</table>

<a href=customer.php>Return to Customer List</a>
{include file="footer.tpl"}
