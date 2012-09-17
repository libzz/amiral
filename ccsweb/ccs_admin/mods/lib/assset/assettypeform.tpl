{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Asset manipulation template
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
{include file="header.tpl" title="Authentication - $titlea Asset Type"}
{if $allowmod==1}<span id="allowmod"></span>{/if}
<form method="post" action="types.php">
<input type="hidden" name="asset_type_id" value="{$asset_type_id}">
<input type="hidden" name="do" value="{$action}">
<input type="hidden" name="process" value="yes">

{if $action=="add"}
Please enter the details of the new asset type below. Once the asset type has
been created you will be able to add subasset types and properties to it.<br>
<br>
{assign var="bcaption" value="Add"}
{else}
{assign var="bcaption" value="Update"}
{/if}
<table>
<tr>    
    <th width="120">Description</th>
    <td><input type="text" name="description" value="{$description}"></td>
</tr>
</table>
<br>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$bcaption} Asset Type &gt;&gt;">
</form>
{if $action != "add"}
<br>
<h2>Subasset types associated with {$description}</h2><br>
<table border=0>
<tr>
<th width="20%">Required Subasset Type</th>
<th width="15%">Name</th>
<th>Actions</th>
</tr>
<tbody id="required-subassets">
{foreach from=$linked_subassets item=subasset}
{if $subasset.required=='t'}
<tr class="{cycle name="1" values="row1,row2"}" id="rsatrow-{$subasset.asset_type_subasset_id}">
    <td>{$subasset.description}</td>
    <td>{$subasset.name}</td>
    <td>{if $allowmod==1}<a href="javascript:setRequired({$subasset.asset_type_subasset_id}, 0);">[Make Optional]</a>&nbsp;&nbsp;<a href="javascript:removeSubasset({$subasset.asset_type_subasset_id}, 1);">[Remove]</a>{/if}</td>
</tr>
{/if}
{/foreach}
</tbody>
<tr>
<th width="20%">Optional Subasset Type</th>
<th width="15%">Name</th>
<th>Actions</th>
</tr>
<tbody id="optional-subassets">
{foreach from=$linked_subassets item=subasset}
{if $subasset.required!='t'}
<tr class="{cycle name="2" values="row1,row2"}" id="osatrow-{$subasset.asset_type_subasset_id}">
    <td>{$subasset.description}</td>
    <td>{$subasset.name}</td>
    <td>{if $allowmod==1}<a href="javascript:setRequired({$subasset.asset_type_subasset_id}, 1);">[Make Required]</a>&nbsp;&nbsp;<a href="javascript:removeSubasset({$subasset.asset_type_subasset_id}, 0);">[Remove]</a>{/if}</td>
</tr>
{/if}
{/foreach}
</tbody>
</table>
<br>
<h2>Available Subasset types</h2><br>
<table border=0>
<tr>
<th width="20%">Subasset Type</th>
<th>Actions</th>
</tr>
{foreach from=$subasset_types item=subasset}
<tr class="{cycle name="3" values="row1,row2"}" id="satrow-{$subasset.subasset_type_id}">
    <td>{$subasset.description}</td>
    <td>{if $allowmod==1}<a href="javascript:addSubasset({$asset_type_id},{$subasset.subasset_type_id},1);">[Add as Required]</a>&nbsp;&nbsp;{/if}<a href="javascript:addSubasset({$asset_type_id},{$subasset.subasset_type_id},0);">[Add as Optional]</a></td>
</tr>
{/foreach}
</table>

{/if}
<ul>
<br>
<li><a href="types.php?type=subasset&do=add">Add&nbsp;a&nbsp;new&nbsp;subasset&nbsp;type</a></li>
<li><a href="types.php">Return&nbsp;to&nbsp;asset&nbsp;type&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
