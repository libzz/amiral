{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Graph manipulation interface
 *
 * Author:       Chris Browning <ckb6@cs.waikato.ac.nz>
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
{include file="header.tpl" title="Graphs"}
<div id="instructions">
Graphs are grouped into groups of similar graphs for ease of viewing.
<br />
<br />
</div>
<table>
<tr>
    <th>Name</th>
    <th>Options</th>
</tr>
{foreach from=$entries item=entry}
<tr class="{cycle values="row1,row2"}">
    <td{$class}>{$entry.group_name}</td>
    <td>
    <a href="config-graphs.php?do=editgroup&group_id={$entry.group_id}">[edit]</a>
    &nbsp;
    <a href="config-graphs.php?do=deletegroup&group_id={$entry.group_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="config-graphs.php?do=newgroup">New&nbsp;Group</a></li>
</ul>
{include file="footer.tpl"}
