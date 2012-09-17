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
    <th>Area No.</th>
    <th>Link Class</th>
    <th>Actions</th>
</tr>
{foreach from=$quagga.areas item=area}
<tr>
    <td>{$area.area_no}</td>
    <td>{$area.link_class_desc}</td>
    <td><a href="service.php?service_id={$quagga.service_id}&do=deleteOSPFArea&area_no={$area.area_no}">[delete]</a></td>
</tr>
{/foreach}
