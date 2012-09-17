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

{if $part.type != ""}
Are you sure you want to delete the following entry?<br />
<br />
<table>
<tr>    
    <th width="200">Type</th>
    <td>{$part.type}</td>
</tr>
<tr>
    <th>More</th>
    <td>{$part.text}</td>
</tr>
<tr>
    <th>Number</th>
    <td>{$part.graph_order}</td>
</tr>
</table>
<br>
<a href="config-graphs.php?do=edittype&group_id={$group_id}&graph_id={$part.graph_id}">Cancel</a>
&nbsp;|&nbsp;
<a href="config-graphs.php?do=deletepart&group_id={$group_id}&graph_id={$part.graph_id}&part_id={$part.part_id}&confirm=yes">
Delete&nbsp;Part&nbsp;&gt;&gt;</a>

{else}{if $graph.title != ""}
Are you sure you want to delete the following graph?<br />
<br />
<table>
<tr>    
    <th width="200">Title</th>
    <td>{$graph.title}</td>
</tr>
<tr>
    <th>Class</th>
    <td>{$classes.class_name}</td>
</tr>
</table>
<br>
<a href="config-graphs.php?do=editgroup&group_id={$group_id}">Cancel</a>
&nbsp;|&nbsp;
<a href="config-graphs.php?do=deletetype&group_id={$group_id}&graph_id={$graph.graph_id}&confirm=yes">
Delete&nbsp;Graph&nbsp;&gt;&gt;</a>
{else}
Are you sure you want to delete the following group?<br />
<br />
<table>
<tr>    
    <th width="200">Name</th>
    <td>{$group.group_name}</td>
</tr>
</table>
<br>
<a href="config-graphs.php">Cancel</a>
&nbsp;|&nbsp;
<a href="config-graphs.php?do=deletegroup&group_id={$group.group_id}&confirm=yes">
Delete&nbsp;Group&nbsp;&gt;&gt;</a>

{/if}
{/if}
<br><br>
{include file="footer.tpl"}
