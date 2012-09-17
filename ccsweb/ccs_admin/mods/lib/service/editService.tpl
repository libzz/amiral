{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Service configuration user interface template
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
{include file="header.tpl" title="Service Configuration - $service_name"}
<form method="post" action="service.php" id="editForm">
<input type="hidden" name="do" value="configure"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$service.service_id}"/>

<div id="instructions">
Please enter the network-wide details for this service below.</div>
<br/>
</form>
<br/>
<ul>
<li><a href="/mods/service/service.php">Return&nbsp;to&nbsp;service&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
