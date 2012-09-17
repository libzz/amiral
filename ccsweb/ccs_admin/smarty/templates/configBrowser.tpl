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
{if $keeprev==1}
{assign var="pageq" value="?rev=$revision"}
{assign var="pageqa" value="&amp;rev=$revision"}
{else}
{assign var="pageq" value=""}
{assign var="pageqa" value=""}
{/if}
<div id="configBrowser">
<div id="ctxtnav" class="nav">
 <ul>
  <li class="last"><a href="/configs/log">Revision Log</a></li>
 </ul>
</div>
<h1><a class="first" title="Go to root directory" href="/configs/{$pageq}">root</a>
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
    <form action="" method="get">
    <div>
        <label for="rev">View revision:</label>
        <input type="text" id="rev" name="rev" value="" size="4" />
    </div>
    </form>
</div>

<table id="info" summary="Revision info">
    <tr>
        <th scope="row">
            Revision <a href="/configs/changeset/{$file.created_rev.number}">{$file.created_rev.number}</a>
     (checked in by {$file.last_author}, {$file.age_rounded} ago)
        </th>
        <td class="message">
            <p>{$file.created_rev.log|nl2br}</p>
        </td>
    </tr>
    {if count($file.props) > 0}
    <tr>
        <td colspan="2">
            <ul class="props">
                {foreach from=$file.props key=prop item=value}
                <li>
                Property <strong>{$prop}</strong> set 
                {if $value != ""}to <em><code>{$value}</code></em>{/if}
                </li>
                {/foreach}
            </ul>
        </td>
    </tr>
    {/if}
</table>
<div id="preview">
<table class="code">
<thead>
    <tr>
        <th class="lineno">Line</th>
        <th class="content">&nbsp;</th>
    </tr>
</thead>
<tbody>
    {foreach from=$file.contents item=line name=lines}
    {assign var="no" value=$smarty.foreach.lines.iteration}
    <tr>
        <th id="L{$no}"><a href="#L{$no}">{$no}</a></th>
        <td>{$line}</td>
    </tr>
    {/foreach}
</tbody>
</table>

</div>
