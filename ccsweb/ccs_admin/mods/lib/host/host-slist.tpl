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
<h2>Configured Services</h2>
<table id="services-list">
<tr>    
    <th width="210">Service Name</th>
    <th>Status</th>
    <th>Actions</th>
</tr>
{foreach from=$cservices item=serv}
<tr>
    <td>{$serv.service_name}</td>
    <td class="status{$serv.statuscode}">{$serv.status}</td>
    <td><a href="/mods/service/service.php?do=configure&host_id={$host_id}&service_id={$serv.service_id}">[configure]</a>&nbsp;&nbsp;<a href="javascript:removeServiceFromHost({$serv.service_id});">[remove]</a></td>
</tr>
{/foreach}
</table>
<br />
<h2>Unconfigured Services</h2>
<table id="uservices-list">
<tr>    
    <th width="210">Service Name</th>
    <th>Status</th>
    <th>Actions</th>
</tr>
{foreach from=$services item=serv}
<tr id="serv-{$service_id}">
    <td>{$serv.service_name}</td>
    <td class="status{$serv.statuscode}">{$serv.status}</td>
    <td><a href="javascript:addServiceToHost({$serv.service_id});">[add to host]</a></td>
</tr>
{/foreach}
</table>
