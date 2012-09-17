{* Copyright (C) 2006  The University of Waikato
 *
 * Amplet Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - Create AMPlet Group"}
<form method="post" action="service.php">
<input type="hidden" name="do" value="createAmpletGroup"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$service_id}"/>

<div id="instructions">
Please enter the details for the group below.
</div>
<br />
<table class="details" id="amplet-details">
<tr>
    <th>Group Name.</th>
    <td><input type="text" id="group_name" name="group_name" value="" /></td>
</tr>
<tr>
    <th>Group Description.</th>
    <td><input type="text" id="group_description" name="group_description" value="" /></td>
</tr>
</table>
<br />
<input type="submit" id="submit" value="Create Group &gt;&gt;" />
<br />
<ul>
<li><a href="/mods/service/service.php?service_id={$service_id}&do=edit">Return&nbsp;to&nbsp;amplet&nbsp;properties</a></li>
</ul>
{include file="footer.tpl"}
