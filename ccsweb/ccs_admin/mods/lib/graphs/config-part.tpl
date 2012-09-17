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
<input type="hidden" name="do" id="do" value="{$action}"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="class_id" id="class_id" value="{$class_id}"/>
<input type="hidden" name="group_id" id="group_id" value="{$group_id}"/>
<input type="hidden" name="graph_id" id="graph_id" value="{$graph_id}"/>
<input type="hidden" name="part_id" id="part_id" value="{$part_id}"/>
<div id="instructions">
Please enter the new details for this graph below.</div>
<br/>
<table id="part-div">

{include file="mods/graphs/config-part-div.tpl"}

</table>
<br/>
</form>
<ul>
<li><a href="config-graphs.php?do=edittype&group_id={$group_id}&graph_id={$graph_id}">Return&nbsp;to&nbsp;Graph</a></li>
<li><a href="config-graphs.php?do=editgroup&group_id={$group_id}">Return&nbsp;to&nbsp;Group</a></li>
<li><a href="config-graphs.php">Return&nbsp;to&nbsp;Group&nbsp;list</a></li>
</ul>

{include file="footer.tpl"}
