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
{include file="header.tpl" title="Asset Management - $titlea Asset Property"}

<form method="post" action="properties.php">
<input type="hidden" name="asset_property_id" value="{$asset_property_id}">
<input type="hidden" name="do" value="{$action}">
<input type="hidden" name="process" value="yes">
{if $referer!=""}<input type="hidden" name="go" value="{$referer}">{/if}

{if $action=="add"}
Please enter the details of the new asset property below. Once the property 
has been created you will be able to link it to assets.<br>
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
<input type="submit" name="submit" value="{$bcaption} Asset Property &gt;&gt;">
</form>
<br>
<ul>
<br>
<li><a href="properties.php">Return&nbsp;to&nbsp;asset&nbsp;property&nbsp;list</a>
</ul>
{include file="footer.tpl"}
