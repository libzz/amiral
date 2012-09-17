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
{include file="header.tpl" title="Site Configuration - Delete Site"}

Are you sure you want to delete the following site?:<br>
<table>
<tr>    
    <th width="150">Location</th>
    <td>{$site.location}</td>
</tr>
<tr>
    <th>Admin Contact</th>
    <td>{$site.admin_contact_desc}</td>
</tr>
<tr>
    <th>Technical Contact</th>
    <td>{$site.tech_contact_desc}</td>
</tr>
<tr>
    <th>GPS Latitude</th>
    <td>{$site.gps_lat}</td>
</tr>
<tr>
    <th>GPS Longitude</th>
    <td>{$site.gps_long}</td>
</tr>
<tr>
    <th>Comments</th>
    <td>{$site.comments}</td>
</tr>
</table>
<br>
NOTE: You will not be able to remove this site if it is still set as the 
location of any hosts or assets. Please ensure that you have reconfigured all
hosts and reassigned all assets before attempting to remove this site.<br>
<br>
<a href="site.php">Cancel</a>
&nbsp;|&nbsp;

<a href="site.php?do=delete&confirm=yes&site_id={$site.site_id}">
Delete&nbsp;Site&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
