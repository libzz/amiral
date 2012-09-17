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
<form method="post" action="service.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$rrdbot.service_id}"/>

<div id="instructions">
This is the configuration page for rrdbot. Below is a list of poller classes that will be used when doing snmp discovery.<br />
NOTE: Changing a class that has databases created off it will not change existing databases but will change new ones. For this reason it is most advisable to get the config for a class right and never modify it and if you do delete manually the databases the you want to be recreated with new parameters. Adding new classes is fine. Deleting a class will not cause any database deletion.
</div>
<br />
<br />
<table>
<tr>
    <th>Classname</th>
    <th>Depends</th>
    <th>Actions</th>
</tr>
{foreach from=$classes item=clas}
<tr class="{cycle values="row1,row2"}">
    <td{$class}>{$clas.class_name}</td>
    <td{$class}>{$clas.depends_name}</td>
    <td{$class}>
    <a href="service.php?do=editclass&class_id={$clas.class_id}&service_id={$service_id}">[edit]</a>
    &nbsp;
    <a href="service.php?do=delete&class_id={$clas.class_id}&service_id={$service_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<br />
<br />
<ul>
<li><a href="service.php?do=newclass&service_id={$service_id}">Add new class</a></li>
<li><a href="service.php">Return to services</a></li>
</ul>
{include file="footer.tpl"}
