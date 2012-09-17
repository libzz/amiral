{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Site manipulation user interface template
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
{include file="header.tpl" title="Site Configuration - $titea Site"}
<form method="post" action="site.php">
<input type="hidden" name="do" value="{$action}"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="site_id" value="{$site.site_id}"/>

<div id="instructions">
{if $action=="add"}
Please enter the details of the new site below. Once the site has been created
you will be able to add hosts and assets to it.<br>
<br>
{assign var="bcaption" value="Add"}
{else}
{assign var="bcaption" value="Update"}
{/if}
</div>
<br/>
<table id="sitedetails">
<tr>    
    <th width="200">Location</th>
    <td><input type="text" name="location" id="location" value="{$site.location}" /></td>
</tr>
<tr>
    <th>Admin Contact</th>
    <td>
    {html_options values=$contact_ids output=$contacts selected=$site.admin_contact_id name="admin_contact_id" id="admin_contact_id"}
    </td>
</tr>
<tr>
    <th>Technical Contact</th>
    <td>
    {html_options values=$contact_ids output=$contacts selected=$site.tech_contact_id name="tech_contact_id" id="tech_contact_id"}    
    </td>
</tr>
<tr>
    <th>GPS Latitude</th>
    <td><input type="text" name="gps_lat" id="gps_lat" value="{$site.gps_lat}" />
    </td>
</tr>
<tr>
    <th>GPS Longitude</th>
    <td>
    <input type="text" name="gps_long" id="gps_long" value="{$site.gps_long}" /> 
    </td>
</tr>
<tr>
    <th>Elevation</th>
    <td>
    <input type="text" name="elevation" id="elevation" value="{$site.elevation}" /> 
    </td>
</tr>
<tr>
    <th>Comments</th>
    <td>
    <textarea name="comments" rows=5>{$site.comments}</textarea>
    </td>
</tr>
<tr>
    <td colspan="2">&nbsp;</td>
</tr>
<tr>
    <td colspan="2">
    <input type="submit" name="submit" value="{$bcaption}" />
    </td>
</tr>
</table>
</form>
<br/>
<ul>
{if $action == "edit"}
<li><a href="host.php?do=add&site_id={$site.site_id}">Add new host at this site</a></li>
{/if}
<li><a href="site.php">Return to site list</a></li>
</ul>
