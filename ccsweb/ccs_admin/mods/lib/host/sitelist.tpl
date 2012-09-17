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
{include file="header.tpl" title="Site Configuration"}
Select a site from the list below.
<table>
<tr>
    <th>Site Name</th>
    <th>Admin Contact</th>
    <th>Technical Contact</th>
    <th>GPS Latitude</th>
    <th>GPS Longitude</th>
    <th>No. Hosts at Site</th>
    <th>No. Assets Assigned to Site</th>
    <th>Actions</th>
</tr>
{foreach from=$sites item=site}
<tr class="{cycle values="row1,row2"}">
    <td>{$site.location}</td>
    <td>{$site.admin_contact_desc}</td>
    <td>{$site.tech_contact_desc}</td>
    <td>{$site.gps_lat}</td>
    <td>{$site.gps_long}</td>
    <td>{$site.no_hosts}</td>
    <td>
        {$site.no_assets}
        &nbsp;
        <a href="/mods/asset/index.php?site_id={$site.site_id}">[view assets]</a>
    </td>
    <td>
    <a href="site.php?do=edit&site_id={$site.site_id}">[edit]</a>
    &nbsp;
    <a href="site.php?do=delete&site_id={$site.site_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="site.php?do=add">Create new site</a></li>
</ul>

{include file="footer.tpl"}
