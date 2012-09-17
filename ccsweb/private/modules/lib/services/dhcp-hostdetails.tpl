{* Copyright (C) 2006  The University of Waikato
 *
 * DHCP Web Interface for the CRCnet Configuration System
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
    {include file="enabled-hierarchy-select.tpl" id="service_host_enabled" value=$dhcp.service_host_enabled pvalue=$dhcp.enabled}
    </td>
</tr>
<tr>
    <th>Primary Nameserver</th>
    <td><input type="text" id="ns1" value="{$dhcp.properties.ns1.value}"></td>
</tr>
<tr>
    <th>Secondary Nameserver</th>
    <td><input type="text" id="ns2" value="{$dhcp.properties.ns2.value}"></td>
</tr>
<tr>
    <th>Domain</th>
    <td><input type="text" id="domain" value="{$dhcp.properties.domain.value}"></td>
</tr>
<tr>
    <th>Default Lease Time</th>
    <td><input type="text" id="default_lease_time" value="{$dhcp.properties.default_lease_time.value}"></td>
</tr>
<tr>
    <th>Maximum Lease Time</th>
    <td><input type="text" id="max_lease_time" value="{$dhcp.properties.max_lease_time.value}"></td>
</tr>
