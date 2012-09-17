{* Copyright (C) 2006  The University of Waikato
 *
 * Rlac Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id: rlac.tpl 1627 2007-11-12 20:48:53Z ckb6 $
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{include file="header.tpl" title="Service Configuration - Rlac"}
<form method="post" action="host.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$rlac.service_id}"/>
<input type="hidden" name="host_id" id="host_id" value="{$host.host_id}"/>

<div id="instructions">
Please select the interfaces that you wish to enable Rlac on below.</div>
<br/>
<table class="details">
<tr>    
    <th>Hostname</th>
    <td>{$host.host_name}</td>
</tr>
<tr>
    <th>Current Location</th>
    <td>{$host.location}</td>
</tr>
<tr>
    <th>LNS</th>
    <td>
		<select id="rlac-host" />
			{foreach from=$lnss item=ls}
        	<option value={$ls.lns_id} {if $rlac.lns[0].lns_id==$ls.lns_id}selected="selected"{/if}>{$ls.lns_name}</option>
			{if $ls.lns_id == $rlac.network_default}
				{assign var='network_default' value=$ls.lns_name}
			{/if}
			{/foreach}
        	<option value=0 {if $rlac.lns[0].lns_id==0}selected="selected"{/if}>Network Default ({$network_default})</option>
		</select>
	</td>
</tr>
</table>

{foreach from=$rlac.interfaces item=iface}
<br /><h2>Interface - {$iface.name}</h2>
Check the box below if you wish to enable Rlac on this interface.<br />

<input type="checkbox" id="rlac-{$iface.interface_id}"{if $iface.rlac_enabled!="f"} checked{/if}>
<br />
{/foreach}
{if count($rlac.interfaces)<=0}
<br ><i>There are no AP interfaces configured for this host!</i><br />
{/if}

<ul>
<li><a href="/mods/host/host.php?do=edit&host_id={$host.host_id}">Return&nbsp;to&nbsp;host</a></li>
</ul>
{include file="footer.tpl"}
