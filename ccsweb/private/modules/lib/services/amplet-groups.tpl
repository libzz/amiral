{* Copyright (C) 2006  The University of Waikato
 *
 * AMPlet Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
<tr>
    <th>Group Name</th>
    <th>Group Description</th>
    <th>Actions</th>
</tr>
{foreach from=$amplet.groups item=group}
<tr>
    <td>{$group.group_name}</td>
    <td>{$group.group_description}</td>
    <td><a href="service.php?service_id={$amplet.service_id}&do=deleteAmpletGroup&amplet_group_id={$group.amplet_group_id}">[delete]</a></td>
</tr>
{/foreach}
