{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Asset manipulation template
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
{include file="header.tpl" title="Asset Management - Edit Asset"}
<form method="post" action="asset.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="edit"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="asset_id" value="{$asset.asset_id}"/>

<div id="instructions">
Please enter the new details for this asset below.</div>
<br/>
<table id="assetdetails">
<tr>    
    <th width="200">Asset ID</th>
    <td>{$asset.asset_id}</td>
    <td rowspan=10>
    <div id="assethistory">
    <h2>Asset History</h2>
    <table>
    <tr>
        <th width="50">Date</th>
        <th width="80">Event</th>
        <th width="100">Details</th>
    </tr>
    {if count($history)>0}
    {foreach from=$history item=hist name=histloop}
    {if $smarty.foreach.histloop.iteration<=5}
    <tr>
        <td title="{$hist.timestamp|date_format:"%d %b %Y %H:%M:%S %z"}">{$hist.timestamp|date_format:"%d %b %Y"}</td>
        <td title="{$hist.description} by {$hist.username}">{$hist.description}</td>
        <td title="{$hist.event_desc} by {$hist.username}" class="histentry-details"><a href="asset.php?do=history&asset_id={$asset.asset_id}">{$hist.event_desc|truncate:28:"...":true}</a></td>
    </tr>
    {/if}
    {/foreach}
    {/if}
    </table>
    {if count($history)>5}<a href="asset.php?do=history&asset_id={$asset.asset_id}">View more history &gt;&gt;</a><br>{/if}
    <span class="note">(Hovering or clicking on an item will display more information if available)</span>
    </div>
    {if count($asset.attached_assets)>0}
    <br />
    <div id="attachedassets">
    <h2>Attached Assets</h2>
    <table>
    <tr>
        <th width="50">Asset ID</th>
        <th width="180">Description</th>
    </tr>
    {foreach from=$asset.attached_assets item=aasset name=aaloop}
    <tr>
        <td style="text-align:center;"><a href="asset.php?do=edit&asset_id={$aasset.asset_id}">{$aasset.asset_id}</a></td>
        <td title="{$aasset.description}"><a href="asset.php?do=edit&asset_id={$aasset.asset_id}">{$aasset.description|truncate}</a></td>
    </tr>
    {/foreach}
    </table>
    </div>
    {/if}
    {if $asset.parent_asset}
    <br />
    <div id="parentasset">
    <h2>Parent Asset</h2>
    <table>
    <tr>
        <th width="80">Asset ID</th>
        <td width="210"><a href="asset.php?do=edit&asset_id={$asset.parent_asset.asset_id}">{$asset.parent_asset.asset_id}</a></td>
    </tr>
    <tr>
        <th>Description</th>
        <td><a href="asset.php?do=edit&asset_id={$asset.parent_asset.asset_id}">{$asset.parent_asset.description}</a></td>
    </tr>
    <tr>
        <th>Location</th>
        <td>{$asset.parent_asset.location}</td>
    </tr>
    <tr>
        <th>State</th>
        <td>{if $asset.parent_asset.enabled=="t"}Enabled{else}Disabled{/if}</td>
    </tr>
    </table>
    </div>
    {/if}
    </td>
</tr>
<tr>    
    <th width="200">Asset Type</th>
    <td>{$asset.asset_type_description}</td>
</tr>
<tr>
    <th>Current Location</th>
    <td>{$asset.location} <a href="asset.php?do=assign&asset_id={$asset.asset_id}&back=1">[change location]</a></td>
</tr>
<tr>    
    <th>Enabled</th>
    <td>
    <input type="hidden" name="enabled-orig" value="{$asset.enabled}"/>
    <input type="checkbox" name="enabled" id="enabled" value="yes"{if $asset.enabled=="t"} checked="checked"{/if}/>
    </td>
</tr>
<tr>    
    <th id="description-header">Description</th>
    <td>
    <input type="hidden" name="description-orig" value="{$asset.description}"/>
    <input type="text" name="description" id="description" value="{$asset.description}" size="32" class="assetdetails" onchange="validateDescription();"/>
    </td>
</tr>
<tr>    
    <th id="serial_no-header">Serial No.</th>
    <td>
    <input type="hidden" name="serial_no-orig" value="{$asset.serial_no}"/>
    <input type="text" name="serial_no" id="serial_no" value="{$asset.serial_no}" size="32" class="assetdetails" onchange="validateSerialNo();"/>
    </td>
</tr>
<tr>    
    <th>Date Purchased</th>
    <td>
    <input type="hidden" name="date_purchased-orig" value="{$asset.date_purchased}"/>
    {html_select_date prefix="date_purchased_" start_year="2000" end_year="+0" month_extra='id="date_purchased_Month"' day_extra='id="date_purchased_Day"' year_extra='id="date_purchased_Year"' time=$asset.date_purchased_ts}
    </td>
</tr>
<tr>    
    <th id="price-header">Price</th>
    <td>
    <input type="hidden" name="currency-orig" value="{$asset.currency}"/>
    {html_options values=$cur_codes output=$cur_codes selected="NZD" name="currency" id="currency" selected=$asset.currency}
    &nbsp;<b>$</b>&nbsp;
    <input type="hidden" name="price-orig" value="{$asset.price}"/>
    <input type="text" name="price" id="price" value="{$asset.price}" onchange="validatePrice();"/></td>
</tr>
<tr>    
    <th id="supplier-header">Supplier</th>
    <td>
    <input type="hidden" name="supplier-orig" value="{$asset.supplier}"/>
    <input type="text" name="supplier" id="supplier" value="{$asset.supplier}" size="32" class="assetdetails" onchange="validateSupplier();"/>
    </td>
</tr>
<tr>    
    <th>Notes</th>
    <td>
    <input type="hidden" name="notes-orig" value="{$asset.notes}"/>
    <textarea name="notes" id="notes" cols="28" rows="5">{$asset.notes}</textarea>
    </td>
</tr>
</table>
<br/>
<div id="active-subassets">
{foreach from=$asset.subassets item=subasset}
<div id="subasset-{$subasset.subasset_id}">
<h2>{$subasset.description} - {$subasset.name}</h2>
<input type="hidden" name="subasset-{$subasset.subasset_id}-properties" value="{$subasset.property_list}"/>
<table>
<tr>    
    <th width="200" >Enabled</th>
    <td>
    <input type="hidden" name="subasset-{$subasset.subasset_id}-enabled-orig" value="{$subasset.enabled}"/>
    <input type="checkbox" name="subasset-{$subasset.subasset_id}-enabled" value="yes"{if $subasset.enabled=="t"} checked="checked"{/if}/>
    </td>
</tr>
{foreach from=$subasset.properties item=prop}
<tr>    
    <th width="200" id="subasset-{$subasset.subasset_id}-property-{$prop.subasset_property_id}-header">
    {$prop.description}
    </th>
    <td>
    <input type="hidden" name="subasset-{$subasset.subasset_id}-property-{$prop.subasset_property_id}-orig" value="{$prop.value}"/>
    <input type="text" name="subasset-{$subasset.subasset_id}-property-{$prop.subasset_property_id}-value" id="subasset-{$subasset.subasset_id}-property-{$prop.subasset_property_id}-value" value="{$prop.value}" onchange="validateSap('subasset-{$subasset.subasset_id}-property-{$prop.subasset_property_id}','{$prop.required}');" class="assetdetails"/>
    </td>
</tr>
{/foreach}
</table>
<br/>
</div>
{/foreach}
<input type="hidden" name="subassets" value="{$asset.subasset_list}"/>
</div>
<div id="optional-subassets">
{if count($asset.optionalsubassets)>0}
<h2>Optional Subassets</h2>
The following subassets are optional. If you would like to add one to the
asset simply click on its name.<br/>
<ul id="optional-subasset-list">
{foreach from=$asset.optionalsubassets item=osubasset}
<li id="optional-subasset-{$osubasset.asset_type_subasset_id}"><a href="javascript:addNewSubasset({$osubasset.subasset_type_id}, {$osubasset.asset_type_subasset_id}, '{$osubasset.name}', '{$osubasset.description}', 'f');">{$osubasset.description} - {$osubasset.name}</a></li>
{/foreach}
</ul>
<input type="hidden" name="new-subassets" id="new-subassets" value=""/>
<br/>
{/if}
</div>
<input type="reset" name="reset" value="Reset Form"/>&nbsp;
<input type="submit" name="submit" id="submit" value="Update Asset &gt;&gt;"/>
</form>
<br/>
<ul>
<li><a href="asset.php">Return&nbsp;to&nbsp;asset&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
