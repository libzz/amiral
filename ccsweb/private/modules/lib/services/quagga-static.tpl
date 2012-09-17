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
    <th width="210">Description</th>
    <th width="180">Prefix</th>
    <th width="180">Next Hop</th>
    <th width="150">Metric</th>
    <th>Actions</th>
</tr>
{foreach from=$statics item=static}
{include file="mods/service/quagga-static-row.tpl" static=$static}
{/foreach}
