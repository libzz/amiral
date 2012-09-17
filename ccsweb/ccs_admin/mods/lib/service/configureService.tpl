{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Service configuration user interface template
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
{include file="header.tpl" title="Service Configuration - $service_name"}
<form method="post" action="service.php" id="editForm">
<input type="hidden" name="do" value="configure"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$service.service_id}"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please enter the new details for this service below.</div>
<br/>
<table id="hostdetails">
<tr>    
    <th width="200">Hostname</th>
    <td>{$host.host_name}</td>
</tr>
<tr>
    <th>Current Location</th>
    <td>{$host.location}</td>
</tr>
<tr>
    <th>Service Name</th>
    <td>{$service.service_name}</td>
</tr>
<tr>
    <th id="service_host_enabled-header">Service Enabled on Host</th>
    <td>
    {include file="enabled-hierarchy-select.tpl" id="service_host_enabled" value=$service.service_host_enabled pvalue=$service.enabled}
    </td>
</tr>
</table>
<br/>
<table>
<tr>    
    <th width="200">Property Name</th>
    <th>Type</th>
    <th>Value</th>
    <th>Default Value</th>
</tr>
{assign var="properties" value=""}
{foreach from=$service.properties item=prop}
<tr class="{cycle values="row1,row2"}">
    <td id="{$prop.prop_name}-header"{if $prop.required=="t"} class="required"{/if}>{$prop.prop_name}</td>
    <td id="{$prop.prop_name}-type">{$prop.prop_type}</td>
    <td id="{$prop.prop_name}-cell"><input type="hidden" name="{$prop.prop_name}-orig" value="{$prop.value}" /><input type="text" name="{$prop.prop_name}" id="{$prop.prop_name}" value="{$prop.value}" class="service-property" size="50" /></td>
    <td>{$prop.default_value}</td>
</tr>
{assign var="name" value=$prop.prop_name}
{assign var="properties" value="$properties $name"}
{/foreach}
</table>
<input type="hidden" name="properties" value="{$properties}" />
<small><b>Note:</b>&nbsp;You may leave the value blank to use the default value for
parameters that are not required.</small><br />
<br />
<input type="submit" id="submit" value="Update Service &gt;&gt;" />
</form>
<br/>
<ul>
<li><a href="/mods/host/host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
