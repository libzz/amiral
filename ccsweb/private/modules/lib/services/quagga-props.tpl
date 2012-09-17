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
{include file="header.tpl" title="Service Configuration - Routing (Quagga)"}
<form method="post" action="service.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$quagga.service_id}"/>

<div id="instructions">
Please enter the global details for the Quagga routing service below. These
values will be used network wide unless they are overriden on a specific host.
</div>
<br />
<table class="details" id="quagga-details">
{include file="mods/service/quagga-propdetails.tpl" quagga=$quagga}
</table>
<br />
<h3>OSPF Areas</h3><br />
The following areas are available for use on the network.
<table class="details" id="quagga-ospf-areas">
{include file="mods/service/quagga-areas.tpl" quagga=$quagga}
</table>
<br />
<ul>
<li><a href="/mods/service/service.php?service_id={$quagga.service_id}&do=createOSPFArea">Create new OSPF area &gt;&gt;</a></li>
</ul>
<br />
<ul>
<li><a href="/mods/service/service.php">Return&nbsp;to&nbsp;service&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
