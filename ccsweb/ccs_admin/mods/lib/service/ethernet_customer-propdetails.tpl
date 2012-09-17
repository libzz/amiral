{* Copyright (C) 2006  The University of Waikato
 *
 * Ethernet Customer Web Interface for the CRCnet Configuration System
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
<tr>
    <th>Property</th>
    <th>Network-wide Value</th>
    <th>Default Value</th>
</tr>
<tr>
    <th>IP Allocation Link</th>
    <td>{html_options id="ethernet_customer_link" name="ethernet_customer_link" values=$link_ids output=$links selected=$ethernet_customer.properties.ethernet_customer_link.network_value}</td>
    <td>None</td>
</tr>
<tr>
    <th>Firewall Class</th>
    <td>{html_options id="ethernet_customer_firewall" name="ethernet_customer_firewall" options=$firewall.firewall_classes_select selected=$ethernet_customer.properties.ethernet_customer_firewall.network_value}</td>
    <td>None</td>
</tr>
