{* Copyright (C) 2006  The University of Waikato
 *
 * AMPlet Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - AMPlet"}
<form method="post" action="service.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$amplet.service_id}"/>

<div id="instructions">
Please enter the global details for the AMPlet service below. These
values will be used network wide unless they are overriden on a specific host.
</div>
<br />
<br />
<h3>AMPlet Groups</h3><br />
The following groups are available for use with AMP. Each group can be
configured with a separate test schedule template.
<table class="details" id="amplet-groups">
{include file="mods/service/amplet-groups.tpl"}
</table>
<br />
<ul>
<li><a href="/mods/service/service.php?service_id={$amplet.service_id}&do=createAmpletGroup">Create new AMPlet group &gt;&gt;</a></li>
</ul>
<br />
<ul>
<li><a href="/mods/service/service.php">Return&nbsp;to&nbsp;service&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
