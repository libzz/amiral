{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Link manipulation user interface template
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
{include file="header.tpl" title="Link Configuration - Delete Link"}

Are you sure you want to delete the following link?<br />
<br />
This will cause all related configuration information to be removed from the
database.<br />
<br />
<table>
<tr>    
    <th width="200">Description</th>
    <td>{$link.description}</td>
</tr>
<tr>
    <th>Type</th>
    <td>{$link.type}</td>
</tr>
<tr>
    <th>Mode</th>
    <td>{$link.mode_desc}</td>
</tr>
{if $link.type=="Managed" || $link.type=="Ad-Hoc"}
<tr>
    <th>ESSID</th>
    <td>{$link.essid}</td>
</tr>
{/if}
<tr>
    <th>Network Address</th>
    <td>{$link.network_address}</td>
</tr>
<tr>
    <th>Shared Network?</th>
    <td>{if $link.shared_network=='t'}Yes{else}No{/if}</td>
</tr>
</table>
<br>
<a href="link.php">Cancel</a>
&nbsp;|&nbsp;

<a href="link.php?do=delete&confirm=yes&link_id={$link.link_id}">
Delete&nbsp;Link&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
