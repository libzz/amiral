{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
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
{strip}
{if $keeprev==1}
{assign var="pageq" value="?rev=$revision"}
{assign var="pageqa" value="&amp;rev=$revision"}
{else}
{assign var="pageq" value=""}
{assign var="pageqa" value=""}
{/if}
{assign var="nameclass" value=""}
{assign var="sizeclass" value=""}
{assign var="dateclass" value=""}
{assign var="nameorder" value=""}
{assign var="sizeorder" value=""}
{assign var="dateorder" value=""}
{if $order!=""}
    {if $desc==1}
        {assign var="`$order`class" value=" desc"}
        {assign var="`$order`order" value="&amp;desc=0"}
    {else}
        {assign var="`$order`class" value=" asc"}
        {assign var="`$order`order" value="&amp;desc=1"}
    {/if}
{/if}
{/strip}
<div id="configBrowser">
<div id="ctxtnav" class="nav">
 <ul>
  <li class="last"><a href="/configs/log">Revision Log</a></li>
 </ul>
</div>

<h1><a class="first" title="Go to root directory" href="/configs/">root</a>
{assign var="prev" value=""}
{assign var="parent" value=""}
{foreach from=$path item=part}
{if $part!=""}
<span class="sep">/</span>
<a title="View {$part}" href="/configs{$prev}/{$part}{$pageq}">{$part}</a>
{assign var="parent" value=$prev}
{assign var="prev" value="$prev/$part"}
{/if}
{/foreach}
{assign var="pageurl" value="$prev"}
</h1>

<div id="jumprev">
    <form action="/configs{$pageurl}" method="get">
    <div>
        <label for="rev">View revision:</label>
        <input type="text" id="rev" name="rev" value="{if $revision!=-1}{$revision}{/if}" size="4" />
    </div>
    </form>
</div>

<table class="listing" id="dirlist">
<thead>
<tr>
    <th class="name{$nameclass}">
        <a title="Sort by name (descending)" 
            href="/configs{$pageurl}?order=name{$nameorder}{$pageqa}">Name</a>
    </th>
    <th class="size{$sizeclass}">
        <a title="Sort by size" 
            href="/configs{$pageurl}?order=size{$sizeorder}{$pageqa}">Size</a>
    </th>
    <th class="rev">Rev</th>
    <th class="date{$dateclass}">
        <a title="Sort by date" 
            href="/configs{$pageurl}?order=date{$dateorder}{$pageqa}">Age</a>
    </th>
    <th class="change">Last Change</th>
</tr>
</thead>
<tbody>
{if $pageurl!=""}
<tr class="even">
    <td class="name" colspan="5">
        <a class="parent" title="Parent Directory" 
            href="/configs{$parent}{$pageq}">../</a>
    </td>
</tr>
{/if}
{foreach from=$entries item=entry}
<tr class="{cycle values="odd,even"}">
    <td class="name">
        <a class="{$entry.kind_desc}" title="View {$entry.kind_desc}" 
            href="/configs{$pageurl}/{$entry.name}{$pageq}">{$entry.name}</a>
    </td>
    <td class="size">
        {assign var="kbs" value=$entry.size/1024}
        {if $entry.size>0}{$kbs|string_format:"%.1f"}&nbsp;kB{/if}
    </td>
    <td class="rev">
        <a title="View Revision Log" 
            href="/configs/log{$pageurl}">{$entry.created_rev.number}</a>
    </td>
    <td class="age">
        <span title="{$entry.age}">{$entry.age_rounded}</span>
    </td>
    <td class="change">
        <span class="author">{$entry.last_author}:</span>
        <span class="change">{$entry.created_rev.log}</span>
    </td>
</tr>
{/foreach}
</tbody>
</table>

</div>
