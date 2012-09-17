{* Copyright (C) 2006  The University of Waikato
 *
 * Firewall Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - Firewall"}
<form method="post" action="service.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$firewall.service_id}"/>

<div id="instructions">
Please enter the global details for Firewalls below. These
values will be used network wide unless they are overriden on a specific host.
</div>
<br />
<table class="details" id="firewall-details">
{include file="mods/service/firewall-propdetails.tpl" firewall=$firewall}
</table>
<br />
<h3>Firewall Classes</h3><br />
The following classes are available to be assigned to interfaces.
<table class="details" id="firewall-classes">
{include file="mods/service/firewall-classes.tpl" firewall=$firewall}
</table>
<br />
<ul>
<li><a href="/mods/service/service.php?service_id={$firewall.service_id}&do=createFirewallClass">Create new firewall class &gt;&gt;</a></li>
</ul>
<br />
<ul>
<li><a href="/mods/service/service.php">Return&nbsp;to&nbsp;service&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
