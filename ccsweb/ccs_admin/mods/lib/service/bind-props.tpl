{* Copyright (C) 2006  The University of Waikato
 *
 * Bind Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
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
{include file="header.tpl" title="Service Configuration - DNS Servers"}
<form method="post" action="service.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$bind.service_id}"/>

<div id="instructions">
Please enter the global details for the network's DNS below.</div>
<br />
<table class="details" id="bind-details">
{include file="mods/service/bind-propdetails.tpl" bind=$bind}
</table>
<br />
<ul>
<li><a href="/mods/service/service.php">Return&nbsp;to&nbsp;service&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
