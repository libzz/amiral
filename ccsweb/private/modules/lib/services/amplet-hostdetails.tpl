{* Copyright (C) 2006  The University of Waikato
 *
 * Amplet Web Interface for the CRCnet Configuration System
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
    {include file="enabled-hierarchy-select.tpl" id="service_host_enabled" value=$amplet.service_host_enabled pvalue=$amplet.enabled}
    </td>
</tr>
<tr>
    <th>AMPlet Group</th>
    <td>
    {html_options values=$amplet_group_names output=$amplet_groups name="amplet_group" id="amplet_group" selected=$amplet.properties.amplet_group.value}
    </td>
</tr>
