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
{assign var="titlea" value=$action|capitalize}
{include file="header.tpl" title="Asset Management - Add Wireless Asset"}

<form method="post" action="asset.php" onsubmit="return validateForm();">
<input type="hidden" name="do" value="addwireless">
<input type="hidden" name="process" value="yes">

<div id="instructions">
Please select the type of asset you would like to add from the list
below. You will then be able to enter the remaining details for the asset.</div>
<br>
<table id="assetdetails">
<tr>    
    <th width="200">Asset Type</th>
    <td>
    <select name="asset_type" id="asset_type" class="assetdetails">
    <option value="-1" selected>Select an asset type...</option>
    {foreach from=$asset_types item=asset_type}
    <option value="{$asset_type.asset_type_id}">{$asset_type.description}</option>
    {/foreach}
    </select>    
    </td>
</tr>
<tr>    
    <th>Enabled</th>
    <td><input type="checkbox" name="enabled" id="enabled" value="yes" checked disabled /></td>
</tr>
<tr>    
    <th id="description-header">Description</th>
    <td><input type="text" name="description" id="description" value="" size=32 class="assetdetails" disabled /></td>
</tr>
<tr>    
    <th>Date Purchased</th>
    <td>{html_select_date prefix="date_purchased_" start_year="2000" end_year="+0" all_extra="disabled" month_extra='id="date_purchased_Month"' day_extra='id="date_purchased_Day"' year_extra='id="date_purchased_Year"'}</td>
</tr>
<tr>    
    <th id="price-header">Price</th>
    <td>
    {html_options values=$cur_codes output=$cur_codes selected="NZD" name="currency" disabled="" id="currency"}
    &nbsp;<b>$</b>&nbsp;
    <input type="text" id="price" name="price" value="0" disabled /></td>
</tr>
<tr>    
    <th id="supplier-header">Supplier</th>
    <td><input type="text" id="supplier" name="supplier" value="" size=32 class="assetdetails" disabled /></td>
</tr>
<tr>    
    <th>Notes</th>
    <td><textarea name="notes" id="notes" cols=28 rows=5 disabled></textarea></td>
</tr>
</table>
<br>
<h2>Invididual Wireless Card Details</h2>
<table>
<tr>    
    <th width="200">No. Cards to add:</th>
    <td>
    <input type="text" id="no_cards" name="no_cards" value="1" size=32 class="assetdetails" /> 
    </td>
</tr>
</table>
<br />
Enter the details for each card below
<table id="icard-table">
<tr>
    <th>Card No.</th>
    <th>Serial No.</th>
    <th>Mac Address</th>
</tr>
</table>
<br /><br />
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" id="submit" value="Add Wireless Assets &gt;&gt;" disabled>
</form>
<ul>
<br>
<li><a href="asset.php">Return&nbsp;to&nbsp;asset&nbsp;list</a></li>
</ul>
{include file="footer.tpl"}
