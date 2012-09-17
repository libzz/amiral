{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
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
{include file="header.tpl" title="CFengine Management - Configuration Status"}
<ul>
<li>Click a hostname to view the last update log for that host.</li>
{if $session_state=="RW"}
<li>Select a checkbox (or multiple checkboxes) and click 'Push Configuration(s)'
to push the active configuration out to those hosts.</li>
{else}
<li>Upgrade to a read-write session to push new configurations out to a host</li>
{/if}
</ul>
<div id="cfruncontainer">
{include file="cfengine.tpl" cfrunLogs=$cfrunLogs}
</div>
{include file="footer.tpl"}
