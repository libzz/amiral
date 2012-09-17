{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Host manipulation user interface template
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
<input type="hidden" name="asset_id-orig" id="asset_id-orig" value="{$host.asset_id}">
<select id="asset_id" name="asset_id">
    {if $host.asset_id==""}
    <option value="-1">Please select an asset...</option>
    {else}
    <option value="-1">No Asset</option>
    <option id="selectedasset" value="{$host.asset_id}" selected>[{$host.asset_id}] {$host.asset_desc}</option>
    {/if}
    {if count($site_assets)>0}
    <optgroup label="Unassigned Assets at Site" id="site_assets">
    {foreach from=$site_assets item=asset}
    <option value="{$asset.asset_id}">[{$asset.asset_id}] {$asset.description}</option>
    {/foreach}
    </optgroup>
    {/if}
    {if count($stock_assets)>0}
    <optgroup label="Unassigned Assets in Stock" id="stock_assets">
    {foreach from=$stock_assets item=asset}
    <option value="{$asset.asset_id}">[{$asset.asset_id}] {$asset.description}</option>
    {/foreach}
    </optgroup>
    {/if}
</select>
