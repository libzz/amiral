{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Host manipulation user interface template
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
{include file="header.tpl" title="Host Configuration - Add Host"}
<form method="post" action="host.php" id="hostForm">
<input type="hidden" name="do" value="add"/>
<input type="hidden" name="process" value="yes"/>

<div id="instructions">
Please enter the details for the host you would like to create below. Once the
host has been created you will be given the opportunity to add interfaces and
services to it.
</div>
<br/>
<table id="hostdetails">
<tr>    
    <th width="200" id="host_name-header">Hostname</th>
    <td><input type="text" name="host_name" id="host_name" value="{$host.host_name}" /></td>
</tr>
<tr>
    <th id="site_id-header">Location</th>
    <td>
    {html_options values=$site_ids output=$site_descs selected=$host.site_id name="site_id" id="site_id"}
    </td>
</tr>
<tr>
    <th id="asset_id-header">Asset Hardware</th>
    <td id="asset_id-cell">{include file="mods/host/host-assetlist.tpl"}</td>
</tr>
<tr>
    <th id="distribution_id-header">Distribution</th>
    <td>
    {html_options values=$distribution_ids output=$distributions selected=$host.distribution name="distribution_id" id="distribution_id"}
    </td>
</tr>
<tr>
    <th id="kernel_id-header">Kernel</th>
    <td>
    {html_options values=$kernel_ids output=$kernels selected=$host.kernel name="kernel_id" id="kernel_id"}    
    </td>
</tr>
<tr>
    <th id="loopback_id-header">Loopback Range</th>
    <td>
    {html_options values=$loopback_ids output=$loopbacks selected=$host.loopback name="link_class_id" id="link_class_id"}    
    </td>
</tr>
<tr>    
    <th id="is_gateway-header">Act as an Internet Gateway?</th>
    <td>
    <input type="checkbox" name="is_gateway" id="is_gateway" value="yes"{if $host.isgateway=="t"} checked="checked"{/if} />
    </td>
</tr>
<tr>    
    <th id="host_active-header">Configure Automatically?</th>
    <td>
    <input type="checkbox" name="host_active" id="host_active" value="yes"{if $host.host_active!="f"} checked="checked"{/if} />
    </td>
</tr>
<tr>
    <td colspan="2">&nbsp;</td>
</tr>
<tr>
    <td colspan="2">
    <input type="submit" name="submit" id="submit" value="Add Host &gt;&gt;" disabled>
    </td>
</tr>
</table>
<br/>
</form>
<ul>
<li><a href="host.php">Return&nbsp;to&nbsp;host&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
