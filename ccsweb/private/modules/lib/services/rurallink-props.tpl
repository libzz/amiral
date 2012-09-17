{* Copyright (C) 2006  The University of Waikato
 *
 * RuralLink Service Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - Rural Link"}
<form method="post" action="service.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$rurallink.service_id}"/>

<div id="instructions">
Please enter the root password for the Rural Link devices below. This password
is not used directly on any device, but is used as a key when generating device
specific passwords.
</div>
<br />
<table class="details" id="rurallink-details">
{include file="mods/service/rurallink-propdetails.tpl" rurallink=$rurallink}
</table>
<br />
<ul>
<li><a href="/mods/service/service.php">Return&nbsp;to&nbsp;service&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
