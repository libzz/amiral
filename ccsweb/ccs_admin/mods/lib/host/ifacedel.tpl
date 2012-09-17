{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Interface manipulation user interface template
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
{include file="header.tpl" title="Host Configuration - Remove Interface"}

Are you sure you want to remove the following interface?<br />
<br />
This will cause all related configuration information to be removed from the
database.<br />
You may wish to simply disable the interface.<br />
<br />
<table>
<tr>    
    <th width="200">Hostname</th>
    <td>{$host.host_name}</td>
</tr>
<tr>
    <th>Interface Name</th>
    <td>{$interface.name}</td>
</tr>
<tr>
    <th>Link</th>
    <td>{$interface.link_desc}</td>
</tr>
<tr>
    <th>IP Address</th>
    <td>{$interface.ip_address}</td>
</tr>
</table>
<br>
<a href="host.php?do=edit&host_id={$host.host_id}">Cancel</a>
&nbsp;|&nbsp;

<a href="interface.php?do=remove&confirm=yes&host_id={$host.host_id}&interface_id={$interface.interface_id}">
Remove&nbsp;Interface&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
