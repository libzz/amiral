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
    <th>Property</th>
    <th>Network-wide Value</th>
    <th>Default Value</th>
</tr>
<tr>
    <th>Primary Nameserver</th>
    <td><input type="text" id="ns1" value="{$dhcp.properties.ns1.network_value}"></td>
    <td>{$dhcp.properties.ns1.default_value}</td>
</tr>
<tr>
    <th>Secondary Nameserver</th>
    <td><input type="text" id="ns2" value="{$dhcp.properties.ns2.network_value}"></td>
    <td>{$dhcp.properties.ns2.default_value}</td>
</tr>
<tr>
    <th>Domain</th>
    <td><input type="text" id="domain" value="{$dhcp.properties.domain.network_value}"></td>
    <td>{$dhcp.properties.domain.default_value}</td>
</tr>
<tr>
    <th>Default Lease Time</th>
    <td><input type="text" id="default_lease_time" value="{$dhcp.properties.default_lease_time.network_value}"></td>
    <td>{$dhcp.properties.default_lease_time.default_value}</td>
</tr>
<tr>
    <th>Maximum Lease Time</th>
    <td><input type="text" id="max_lease_time" value="{$dhcp.properties.max_lease_time.network_value}"></td>
    <td>{$dhcp.properties.max_lease_time.default_value}</td>
</tr>

