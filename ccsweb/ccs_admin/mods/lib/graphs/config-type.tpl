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
<input type="hidden" name="graph_id" id="graph_id" value="{$graph_id}"/>

<div id="instructions">
Please enter the new details for this graph below.</div>
<br/>
<table id="hostdetails">
<tr>    
    <th width="200" id="title-header">Title</th>
    <td><input type="text" name="title" id="title" value="{$graph.title}"/>Title of Graph</td>
</tr>
<tr>    
    <th width="200">Class</th><td>
        <select id="class_id" name="class_id" {if $action=="edittype"}disabled{/if}>
        {foreach from=$classes item=clas}
            <option value="{$clas.class_id}" {if $clas.class_id == $graph.class_id}selected="selected"{/if}>{$clas.class_name}</option>
        {/foreach}
        </select>
</td></tr>
<tr>    
    <th width="200" id="label-header">Vertical Label</th>
    <td><input type="text" name="virtical_label" id="virtical_label" value="{$graph.virtical_label}"/>Label normally containing units</td>
</tr>
<tr>    
    <th width="200" id="upper-header">Upper graph limit</th>
    <td><input type="text" name="upper" id="upper" value="{$graph.upper}"/>Specifies the top of the graphs Y axis</td>
</tr>
<tr><th width='200' id='rigid-header'>Rigid</th><td><input type="checkbox" name="rigid" id="rigid" {if $graph.rigid=="t"}checked{/if} />If checked then the upper limit set above will be enforced even if there is larger values to be drawn</td></tr>
<tr><th width='200' id='auto_comment-header'>Auto-comment</th><td><input type="checkbox" name="auto_comment" id="auto_comment" {if $graph.auto_comment=="t"}checked{/if} />Enables auto printing of Last, Average and Max as a comment at the bottom of the graph</td></tr>
<tr>    
    <td colspan=2>
    <input type="submit" name="submit" id="submit" value="Update Graph Type &gt;&gt;">
    </td>
</tr>
</table>
<br/>
</form>
{if $action=="edittype"}
<div id="instructions">
This is a list of graph components. The order they are here is the order they will be used to draw the graph.
<br />
<br />
</div>
<table>
<tr>
    <th>Type</th>
    <th>More</th>
    <th>Variable</th>
    <th>Order</th>
    <th>Options</th>
</tr>
{foreach from=$entries item=entry}
<tr class="{cycle values="row1,row2"}">
    <td{$class}>{$entry.type}</td>
    <td{$class}>{$entry.text}</td>
    <td{$class}>{$entry.varname}</td>
    <td{$class}>{$entry.graph_order}</td>
    <td>
    <a href="config-graphs.php?do=editpart&group_id={$group_id}&graph_id={$entry.graph_id}&part_id={$entry.part_id}&class_id={$graph.class_id}">[edit]</a>
    &nbsp;
    <a href="config-graphs.php?do=deletepart&group_id={$group_id}&graph_id={$entry.graph_id}&part_id={$entry.part_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
{/if}
<ul>
{if $action=="edittype"}<li><a href="config-graphs.php?do=newpart&group_id={$group_id}&graph_id={$graph_id}&class_id={$graph.class_id}">New&nbsp;part</a></li>{/if}
<li><a href="config-graphs.php?do=editgroup&group_id={$group_id}">Return&nbsp;to&nbsp;Group</a></li>
<li><a href="config-graphs.php">Return&nbsp;to&nbsp;Group&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
