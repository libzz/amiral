{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
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
{if count($top_menu) > 0}
<div class="menu">
<h2>CRCnet Configuration</h2>
<ul>
{foreach from=$top_menu item=menuitem}
<li><a href="{$menuitem.href}">{$menuitem.label}</a></li>
{/foreach}
</ul>
<ul>
{foreach from=$top_funcs_menu item=menuitem}
<li><a href="{$menuitem.href}">{$menuitem.label}</a></li>
{/foreach}
<br />
<li><a href="/?function=changepass">Change my password</a></li>
</ul>
</div>
<br />
{/if}
{if count($bottom_menu) > 0 || count($bottom_menu_inc) > 0}
<div class="menu">
<h2>{$title|regex_replace:"/ - .*$/":""|strip}</h2>
<ul>
{foreach from=$bottom_menu item=menuitem}
<li><a href="{$menuitem.href}">{$menuitem.label}</a></li>
{/foreach}
</ul>
{foreach from=$bottom_menu_inc item=inc}
{include file=$inc}
{/foreach}
</div>
{/if}

{if $do_debug==1}
<table>
<tr>
<th>Function</th>
<th>Tot. Time</th>
<th>Curl Time</th>
</tr>
{foreach from=$rpctimes item=func}
<tr>
<td>{$func.function}</td>
<td>{$func.time|string_format:"%.3f"}</td>
<td>{$curltimes[$func.function]|string_format:"%.3f"}</td>
</tr>
{/foreach}
<tr>
<th>TOTALS</th>
<th>{$exec_time|string_format:"%.3f"}</th>
<th>&nbsp;</th>
</tr>
</table>
<small>All times in seconds</small>
{/if}
