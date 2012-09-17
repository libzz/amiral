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
<form method="post" action="config-graphs.php" id="editForm">
<input type="hidden" name="do" value="{$action}"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="group_id" id="group_id" value="{$group_id}"/>

<div id="instructions">
Please enter the new name for this group below.</div>
<br/>
<table>
<tr>    
    <th width="200" id="name-header">Name</th>
    <td><input type="text" name="group_name" id="group_name" value="{$group.group_name}"/>Name of group</td>
</tr>
<tr>    
    <td colspan=2>
    <input type="submit" name="submit" id="submit" value="Update Group &gt;&gt;">
    </td>
</tr>
</table>
<br/>
</form>
{if $action=="editgroup"}
<div id="instructions">
This is a list of groups that graphs are grouped in.
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
    <td{$class}>{$entry.title}</td>
    <td>
    <a href="config-graphs.php?do=edittype&group_id={$group_id}&graph_id={$entry.graph_id}">[edit]</a>
    &nbsp;
    <a href="config-graphs.php?do=deletetype&group_id={$group_id}&graph_id={$entry.graph_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
{/if}
<ul>
{if $action=="editgroup"}<li><a href="config-graphs.php?do=newtype&group_id={$group_id}">New&nbsp;Graph</a></li>{/if}
<li><a href="config-graphs.php">Return&nbsp;to&nbsp;Group&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
