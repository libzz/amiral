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
    <th>Class Name</th>
    <th>Description</th>
    <th>Actions</th>
</tr>
{foreach from=$firewall.firewall_classes item=details}
<tr>
    <td>{$details.firewall_class_name}</td>
    <td>{$details.description}</td>
    <td><a href="service.php?service_id={$firewall.service_id}&do=updateFirewallClass&firewall_class_id={$details.firewall_class_id}">[edit]</a>&nbsp;&nbsp;<a href="service.php?service_id={$firewall.service_id}&do=deleteFirewallClass&firewall_class_id={$details.firewall_class_id}">[delete]</a></td>
</tr>
{/foreach}
