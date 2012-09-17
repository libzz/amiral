{* Copyright (C) 2006  The University of Waikato
 *
 * Quagga Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - Create OSPF Area"}
<form method="post" action="service.php">
<input type="hidden" name="do" value="createOSPFArea"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$service_id}"/>

<div id="instructions">
Please enter the details for the area below.
</div>
<br />
<table class="details" id="quagga-details">
<tr>
    <th>Area No.</th>
    <td><input type="text" id="area_no" name="area_no" value="" /></td>
</tr>
<tr>
    <th>Link Class</th>
    <td>{html_options values=$link_class_ids output=$link_class_descs name="link_class_id" id="link_class_id"}</td>
</tr>
</table>
<br />
<input type="submit" id="submit" value="Create Area &gt;&gt;" />
<br />
<ul>
<li><a href="/mods/service/service.php?service_id={$service_id}&do=edit">Return&nbsp;to&nbsp;quagga&nbsp;properties</a></li>
</ul>
{include file="footer.tpl"}
