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
{include file="header.tpl" title="Asset Management - $titlea Subasset Type"}
{if $allowmod==1}<span id="allowmod"></span>{/if}
<form method="post" action="types.php">
<input type="hidden" name="type" value="subasset">
<input type="hidden" name="subasset_type_id" value="{$subasset_type_id}">
<input type="hidden" name="do" value="{$action}">
<input type="hidden" name="process" value="yes">

{if $action=="add"}
Please enter the details of the new subasset type below. Once the subasset 
type has been created you will be able to link it to asset types and add 
properties to it.<br>
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
<input type="submit" name="submit" value="{$bcaption} Subasset Type &gt;&gt;">
</form>
{if $action != "add"}
<br>
<h2>Properties of {$description}</h2>

<table border=0>
<tr>
<th width="20%">Required Property</th>
<th width="15%">Default Value</th>
<th>Actions</th>
</tr>
<tbody id="required-properties">
{foreach from=$linked_properties item=property}
{if $property.required=='t'}
<tr class="{cycle name="1" values="row1,row2"}" id="rproprow-{$property.subasset_property_id}">
    <td>{$property.description}</td>
    <td>{$property.default_value}</td>
    <td><a href="javascript:editSubassetProperty({$property.subasset_property_id}, 1);">[Change Default Value]</a>&nbsp;&nbsp;{if $allowmod==1}<a href="javascript:setRequired({$property.subasset_property_id}, 0);">[Make Optional]</a>&nbsp;&nbsp;<a href="javascript:removeSubassetProperty({$property.subasset_property_id}, 1);">[Remove]</a>{/if}</td>
</tr>
{/if}
{/foreach}
</tbody>
<tr>
<th width="20%">Optional Property</th>
<th width="15%">Default Value</th>
<th>Actions</th>
</tr>
<tbody id="optional-properties">
{foreach from=$linked_properties item=property}
{if $property.required!='t'}
<tr class="{cycle name="2" values="row1,row2"}" id="oproprow-{$property.subasset_property_id}">
    <td>{$property.description}</td>
    <td>{$property.default_value}</td>
    <td><a href="javascript:editSubassetProperty({$property.subasset_property_id}, 0);">[Change Default Value]</a>&nbsp;&nbsp;{if $allowmod==1}<a href="javascript:setRequired({$property.subasset_property_id}, 1);">[Make Required]</a>&nbsp;&nbsp;{/if}<a href="javascript:removeSubassetProperty({$property.subasset_property_id}, 0);">[Remove]</a></td>
</tr>
{/if}
{/foreach}
</tbody>
</table>
<br>
<h2>Available Properties</h2><br>
<table border=0>
<tr>
<th width="20%">Description</th>
<th>Actions</th>
</tr>
{foreach from=$properties item=property}
<tr class="{cycle name="3" values="row1,row2"}" id="proprow-{$property.asset_property_id}">
    <td>{$property.description}</td>
    <td>{if $allowmod==1}<a href="javascript:addSubassetProperty({$subasset_type_id},{$property.asset_property_id},1);">[Add as Required]</a>&nbsp;&nbsp;{/if}<a href="javascript:addSubassetProperty({$subasset_type_id},{$property.asset_property_id},0);">[Add as Optional]</a></td>
</tr>
{/foreach}
</table>

{/if}
<ul>
<br>
<li><a href="properties.php?do=add&back=true">Add&nbsp;new&nbsp;property</a></li>
<li><a href="types.php?type=subasset">Return&nbsp;to&nbsp;subasset&nbsp;type&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
