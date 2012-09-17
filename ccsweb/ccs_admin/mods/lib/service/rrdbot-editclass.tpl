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
<input type="hidden" name="do" value="editclass"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="class_id" id="class_id" value="{$classes[0].class_id}"/>

<div id="instructions">
Please enter the new details for this class below.</div>
<br/>
<table id="hostdetails">
<tr>    
    <th width="200" id="class_name-header">Classname</th>
    <td><input type="text" name="class_name" id="class_name" value="{$classes[0].class_name}"  />The name of the class</td>
</tr>
<tr>
    <th id="poll-header">Condition</th>
    <td><input type="text" name="poll" id="poll" value="{$classes[0].poll}"  ><br />The host snmp condition for this class to be used. If this class is not a subclass the format is oid:type where type is either count or exist. Count will create an instance of the class per number returned and exist will create one instance of the class if the oid exists. For a sub class however only a oid should be there as an exist condition is assumed.</td>
</tr>
<tr>
    <th id="interval-header">Interval</th>
    <td><input type="text" name="interval" id="interval" value="{$classes[0].interval}"  >The interval to poll at in seconds</td>
</tr>
<tr>
    <th>Consolidation function</th>
    <td>{html_options values=$cf_ids output=$cf_names selected=$classes[0].cf name="cf" id="cf"}The consolidation function used by rrdtool</td>
</tr>
<tr>
    <th id="archive-header">Archive</th>
    <td><input type="text" name="archive" id="archive" size=60 value="{$classes[0].archive}"  ><br />The archive function. This is a comma separated function starting at the smallest time step going sequentially to the largest. Each function is in the fromat of number/period (of the poll) * number period (time to keep). Period can be (Minute(s), Hour(s), Day(s), Month(s), Year(s)) eg. "12/Hour * 2" Days means keep 12 poll's an hour (one every five minutes) and keep them for 2 days. Please note that the interval must be set equal to or more often than the smallest time step otherwise this class will not be created</td>
</tr>
<tr>
    <th id="key-header">Key</th>
    <td><input type="text" name="key" id="key" value="{$classes[0].key}"  >If set, this oid will be probed for use as a unique key to identify the instance. NOTE: Subclasses will always inherit there parents keys</td>
</tr>
<tr>
    <th>Depends on</th>
    <td>{html_options values=$dependsids output=$dependsnames selected=$classes[0].depends name="depends" id="depends"}This means that the specified class must exist before this class is even checked for</td>
</tr>
<tr>
    <th id="upper_bound-header">Upper bound</th>
    <td><input type="text" name="upper_bound" id="upper_bound" size=60 value="{$classes[0].upper_bound}"  >This sets a bound that on an exist will reject any value greater than this value.
</tr>
<tr>
    <th id="lower_bound-header">Upper bound</th>
    <td><input type="text" name="lower_bound" id="lower_bound" size=60 value="{$classes[0].lower_bound}"  >This sets a bound that on an exist will reject any value less than this value.
</tr>
</table>
<br />
<br />
These are Options for automatic detection of interfaces and are best used when walking ipAdEntifIndex
<table>
<tr>
    <th width="200">Ip from oid</th>
    <td><input type="checkbox" name="ipfromoid" id="ipfromoid" value="yes"  {if $classes[0].ipfromoid=="1"} checked="checked"{/if} />Useful on classes doing a walk of a table where the ip is added after the supplied oid, this data is used to match an interface to a link.</td>
</tr>
<tr>
    <th>Skip software interfaces</th>
    <td><input type="checkbox" name="skip_software_loop" id="skip_software_loop" value="yes"  {if $classes[0].skip_software_loop=="1"} checked="checked"{/if} />Useful when you want do skip software interfaces (dummy, loopback)</td>
</tr>
<tr>    
    <td colspan=2>
    <input type="submit" name="submit" id="submit" value="Update Class &gt;&gt;">
    </td>
</tr>
</table>
<br/>
</form>
<br />
<br />
<table>
<tr>
    <th>Name</th>
    <th>Oid to collect</th>
    <th>Type</th>
    <th>Min</th>
    <th>Max</th>
    <th>Actions</th>

</tr>
Below is a list of data items that will be collected by rrdbot from a host if the host satisfies the class condition.
{foreach from=$parts item=part}
<tr class="{cycle values="row1,row2"}">
    <td{$class}>{$part.name}</td>
    <td{$class}>{$part.poll}</td>
    <td{$class}>{$part.type}</td>
    <td{$class}>{$part.min}</td>
    <td{$class}>{$part.max}</td>
    <td{$class}>
    <a href="service.php?do=editpart&class_id={$classes[0].class_id}&part_id={$part.part_id}&service_id={$service_id}">[edit]</a>
    &nbsp;
    <a href="service.php?do=deletepart&class_id={$classes[0].class_id}&part_id={$part.part_id}&service_id={$service_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="service.php?do=newpart&class_id={$classes[0].class_id}&service_id={$service_id}">Add&nbsp;part</a></li>
<li><a href="service.php?do=edit&service_id={$service_id}">Return&nbsp;to&nbsp;rrdbot</a></li>
</ul>
{include file="footer.tpl"}
