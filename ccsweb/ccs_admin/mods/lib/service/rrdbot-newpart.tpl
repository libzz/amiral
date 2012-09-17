{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * rrdbot Web Interface for the CRCnet Configuration System
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
{include file="header.tpl" title="Service Configuration - rrdbot"}
<form method="post" action="service.php?service_id={$service_id}" id="editForm">
<input type="hidden" name="do" value="newpart"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="part_id" id="part_id" value="{$parts[0].part_id}"/>
<input type="hidden" name="class_id" id="class_id" value="{$class_id}"/>

<div id="instructions">
Please enter the new details for this part below.</div>
<br/>
<table id="classdetails">
<tr>    
    <th width="200" id="name-header">Name</th>
    <td><input type="text" name="name" id="name"/>Name of variable in the rrd file</td>
</tr>
<tr>
    <th id="poll-header">Oid to collect</th>
    <td><input type="text" name="poll" id="poll">The oid for the poller to collect</td>
</tr>
<tr>
    <th id="type-header">Type</th>
    <td>{html_options values=$type_ids output=$type_names selected="GAUGE" name="type" id="type"}The variable type</td>
</tr>
<tr>
    <th id="min-header">Min</th>
    <td><input type="text" name="min" id="min">The minimal value for a GAUGE, leave blank for no minimal</td>
</tr>
<tr>
    <th id="max-header">Max</th>
    <td><input type="text" name="max" id="max">The maximum value for a GAUGE, leave blank for no maximum</td>
</tr>
<tr>    
    <td colspan=2>
    <input type="submit" name="submit" id="submit" value="Create Class Part &gt;&gt;">
    </td>
</tr>
</table>
<br/>
</form>
<br />
<br />
<ul>
<li><a href="service.php?do=editclass&class_id={$class_id}&service_id={$service_id}">Return&nbsp;to&nbsp;class</a></li>
</ul>
{include file="footer.tpl"}
