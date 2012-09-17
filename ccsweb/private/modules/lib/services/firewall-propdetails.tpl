{* Copyright (C) 2006  The University of Waikato
 *
 * Firewall Web Interface for the CRCnet Configuration System
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
    <th>Default Interface Class</th>
    <td>{html_options id="default_class" name="default_class" options=$firewall.firewall_classes_select selected=$firewall.properties.default_class.network_value}</td>
    <td>{$firewall.firewall_classes[$firewall.properties.default_class.default_value].firewall_class_name}</td>
</tr>
