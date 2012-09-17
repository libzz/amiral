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
{include file="header.tpl" title="Service Configuration"}
Select a service from the list below.
<table>
<tr>
    <th>Service Name</th>
    <th>Status</th>
    <th>Actions</th>
</tr>
{foreach from=$services item=service}
<tr class="{cycle values="row1,row2"}">
    {if $service.enabled=="f"}
        {assign var="class" value=" class=\"disabled\""}
    {else}
        {assign var="class" value=""}
    {/if}
    <td{$class}>{$service.service_name}</td>
    <td{$class}>
    {if $service.enabled=="f"}
    Disabled
    {else}
    Enabled
    {/if}
    </td>
    <td{$class}>
    <a href="service.php?do=edit&service_id={$service.service_id}">[edit]</a>
    &nbsp;
    {if $service.enabled=="f"}
    <a href="service.php?do=enable&service_id={$service.service_id}">[enable]</a>
    {else}
    <a href="service.php?do=disable&service_id={$service.service_id}">[disable]</a>
    {/if}
    </td>
</tr>
{/foreach}
</table>
{include file="footer.tpl"}
