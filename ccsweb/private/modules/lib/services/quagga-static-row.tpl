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
<tr id="static-row-{$static.static_id}">
    <td><input type="text" id="static-description-{$static.static_id}" value="{$static.description}" class="description" /></td>
    <td><input type="text" id="static-prefix-{$static.static_id}" value="{$static.prefix}" class="prefix" /></td>
    <td><input type="text" id="static-next_hop-{$static.static_id}" value="{$static.next_hop}" class="next_hop" /></td>
    <td><input type="text" id="static-metric-{$static.static_id}" value="{$static.metric}" class="metric" /></td>
    <td><a href="javascript:removeStatic('{$static.static_id}');" id="static-remove-{$static.static_id}">[Remove]</a></td>
</tr>
