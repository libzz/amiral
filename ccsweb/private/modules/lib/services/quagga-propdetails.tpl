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
    <th>Property</th>
    <th>Network-wide Value</th>
    <th>Default Value</th>
</tr>
<tr>
    <th>Telnet Password</th>
    <td><input type="text" id="telnet_password" value="{$quagga.properties.telnet_password.network_value}"></td>
    <td>{$quagga.properties.telnet_password.default_value}</td>
</tr>
<tr>
    <th>Enable Password</th>
    <td><input type="text" id="enable_password" value="{$quagga.properties.enable_password.network_value}"></td>
    <td>{$quagga.properties.enable_password.default_value}</td>
</tr>
<tr>
    <th>MD5 Key</th>
    <td><input type="text" id="md5_key" value="{$quagga.properties.md5_key.network_value}"></td>
    <td>{$quagga.properties.md5_key.default_value}</td>
</tr>
<tr>
    <th valign="top">Redistribute Static Routes</th>
    <td>
    {include file="yesno-hierarchy-select.tpl" id="redistribute_static" value=$quagga.properties.redistribute_static.network_value pvalue=$quagga.properties.redistribute_static.default_value defaulttxt="Use Default"}
    </td>
    <td>{if $quagga.properties.redistribute_static.default_value=="t"}Yes{else}No{/if}</td>
</tr>
<tr>
    <th valign="top">Redistribute Connected Routes</th>
    <td>
    {include file="yesno-hierarchy-select.tpl" id="redistribute_connected" value=$quagga.properties.redistribute_connected.network_value pvalue=$quagga.properties.redistribute_connected.default_value defaulttxt="Use Default"}
    </td>
    <td>{if $quagga.properties.redistribute_connected.default_value=="t"}Yes{else}No{/if}</td>
</tr>

