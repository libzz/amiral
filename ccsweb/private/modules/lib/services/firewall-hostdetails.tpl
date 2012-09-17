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
    <th id="service_host_enabled-header">Firewall Enabled on Host</th>
    <td>
    {include file="enabled-hierarchy-select.tpl" id="service_host_enabled" value=$firewall.service_host_enabled pvalue=$firewall.enabled}
    </td>
</tr>
