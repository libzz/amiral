{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Adding plans template.
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 *               Ivan Meredith <ivan@ivan.net.nz>
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
{include file="header.tpl" title="Billing - $titlea plan"}
<form method="post" action="plan.php" id="planForm">
<input type="hidden" name="plan_id" value="{$plan.plan_id}"/>
<input type="hidden" name="do" value="{$action}"/>
<input type="hidden" name="process" value="yes"/>

<div id="instructions">
Please enter the details for the plan you would like to create below.
</div>
<br/>
<table id="plandetails">
<tr>    
    <th width="200" id="plan_name-header">Plan name</th>
    <td><input type="text" name="plan_name" id="plan_name" value="{$plan.plan_name}" /></td>
</tr>
<tr>
    <th>Description</th>
    <td><input type="text" name="description" id="description" value="{$plan.description}" /></td>
    
<tr>
    <th>Price</th>
    <td><input type="text" name="price" id="price" value="{$plan.price|string_format:"%.2f"}"/></td>
</tr>
<tr>
    <th>Radius Plan</th>
    <td><select name="radius_plan" id="radius_plan">
    {foreach from=$radius_plans item=rp}
    {if $plan.radius_plan==$rp.plan_id}
    <option label="{$rp.plan_name}" value="{$rp.plan_id}" selected="selected">{$rp.plan_name} ({$rp.upstream_kbps}UP/{$rp.downstream_kbps}DOWN)</option>
    {else}
    <option label="{$rp.plan_name}" value="{$rp.plan_id}">{$rp.plan_name} ({$rp.upstream_kbps}UP/{$rp.downstream_kbps}DOWN)</option>
    {/if}
    {/foreach}
    </select></td>
</tr>
<tr>
    <th>Included mb</th>
    <td><input type="text" name="included_mb" id="included_mb" value="{$plan.included_mb}"/></td>
</tr>
<tr>
    <th>Cap Period</th>
    <td><input type="text" name="cap_period" id="cap_period" value="{$plan.cap_period}"/></td>
</tr>
<tr>
    <th>Cap Action</th>
    <td><input type="text" name="cap_action" id="cap_action" value="{$plan.cap_action}"/></td>
</tr>
<tr>
    <th>Cap Parameter</th>
    <td><input type="text" name="cap_param" id="cap_param" value="{$plan.cap_param}"/></td>
</tr>
<tr>
    <th>Cap Price(if needed)</th>
    <td><input type="text" name="cap_price" id="cap_price" value="{$plan.cap_price}"/></td>
</tr>


</table>
<br/>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$titlea} Plan &gt;&gt;">
</form>
<ul>
<li><a href="plan.php">Return&nbsp;to&nbsp;host&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
