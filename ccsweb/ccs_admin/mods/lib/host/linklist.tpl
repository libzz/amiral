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
{include file="header.tpl" title="Host Configuration"}
Select a link from the list below.
<table>
<tr>
    <th>Description</th>
    <th>Link Class</th>
    <th>Network Address</th>
    <th>Mode / Channel</th>
    <th>Number Interfaces</th>
    <th>Actions</th>
</tr>
{foreach from=$links item=link}
<tr class="{cycle values="row1,row2"}">
    <td>{$link.description}</td>
    <td>{$link.class_desc}</td>
    <td>{$link.network_address}</td>
    <td>{$link.mode_desc}{if $link.channel!=""} on Channel {$link.channel}{/if}</td>
    <td>{$link.no_interfaces}</td>
    <td>
    <a href="link.php?do=edit&link_id={$link.link_id}">[edit]</a>
    &nbsp;
    <a href="link.php?do=delete&link_id={$link.link_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="link.php?do=add">Create new link</a></li>
</ul>

{include file="footer.tpl"}
