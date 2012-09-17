{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Network Map using zoomin.co.nz
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
{include file="header.tpl" title="Interactive Network Map"}
<script type="text/javascript">
var sites = new Array();
var links = new Array();

{foreach from=$hosts item=host}
{if $host.gps_lat==0||$host.gps_long==0}
//Bad coords for {$host.host_name}
{else}
{$host.host_key} = new GLatLng({$host.gps_lat}, {$host.gps_long});
sites.push(new Array({$host.host_key}, "{$host.host_name}", "{$host.description} at {$host.location}"));

{foreach from=$host.ifaces item=iface}
{if $iface.link_id != ""}
if (links[{$iface.link_id}] == null) {ldelim}
links[{$iface.link_id}] = new Array();
{rdelim}
links[{$iface.link_id}].push({$host.host_key});
{/if}
{/foreach}
{/if}

{/foreach}
</script>

<div id="mapview" style="margin: auto; width: 800px; height: 600px"></div>
<br />
<div id="co-ords"></div>
<div id="debug"></div>
<div class="hide">
{foreach from=$hosts item=host}
<div id="iwin-{$host.host_name}" class="iwin-content">
<h1>{$host.host_name} <span class="hardware">({$host.description})</span></h1>
{$host.location}<br />
<br />
More info here...
</div>
{/foreach}
</div>
<br />
<div id="hoverwin"></div>
<ul>
<li><a href="host.php">Return&nbsp;to&nbsp;host&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
