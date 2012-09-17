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
<tr>
    <th id="service_host_enabled-header">Service Enabled on Host</th>
    <td>
    {include file="enabled-hierarchy-select.tpl" id="service_host_enabled" value=$quagga.service_host_enabled pvalue=$quagga.enabled}
    </td>
</tr>
<tr>
    <th>Telnet Password</th>
    <td><input type="text" id="telnet_password" value="{$quagga.properties.telnet_password.value}"></td>
</tr>
<tr>
    <th>Enable Password</th>
    <td><input type="text" id="enable_password" value="{$quagga.properties.enable_password.value}"></td>
</tr>
<tr>
    <th valign="top">Redistribute Static Routes</th>
    <td>
    {if $quagga.properties.redistribute_static.network_value==""}
        {assign var="pvalue" value=$quagga.properties.redistribute_static.default_value}
    {else}
        {assign var="pvalue" value=$quagga.properties.redistribute_static.network_value}
    {/if}
    {include file="yesno-hierarchy-select.tpl" id="redistribute_static" value=$quagga.properties.redistribute_static.value pvalue=$pvalue}
    </td>
</tr>
<tr>
    <th valign="top">Redistribute Connected Routes</th>
    <td>
    {if $quagga.properties.redistribute_connected.network_value==""}
        {assign var="pvalue" value=$quagga.properties.redistribute_connected.default_value}
    {else}
        {assign var="pvalue" value=$quagga.properties.redistribute_connected.network_value}
    {/if}
    {include file="yesno-hierarchy-select.tpl" id="redistribute_connected" value=$quagga.properties.redistribute_connected.value pvalue=$pvalue}
    </td>
</tr>
