{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Graph manipulation user interface template
 *
 * Author:       Chris Browning <ckb6@cs.waikato.ac.nz>
 * Version:      $Id: hosteditform.tpl 1067 2006-10-05 22:55:17Z mglb1 $
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
{include file="header.tpl" title="Graphs"}
<h3>Select a from the options below and click Refresh to view graphs.</h3>
<form method="get" action="graphs.php" id="selectgraphForm">
<input type="hidden" name="do" value="getgraph"/>
<form name="filter" method="get" action="graph.php">
  <table>
    <tr><td class="bodyText"><input type="radio" name="main" value="host" id="host" {if $main=="host" || $main==""}checked{/if} /> Host:</td><td> 
      <select id="host_id" name="host_id"{if !($main=="host" || $main=="")} DISABLED {/if} />
      <option value=-1>--ALL--</option>
      {foreach from=$hosts item=host}
      <option value="{$host.host_id}" {if $host.host_id == $host_id}selected="selected"{/if}>{$host.host_name}</option>
      {/foreach}
    
</td>
    <tr><td class="bodyText"><input type="radio" name="main" value="link" id="link" {if $main=="link"}checked{/if}/> Link:</td><td>
      {if $main=="link"}
      {html_options values=$link_ids output=$link_names selected=$link_id name="link_id" id="link_id"}
      {else}
      {html_options values=$link_ids output=$link_names selected=$link_id name="link_id" id="link_id" disabled=true}
      {/if}
</td></tr>
    <tr><td class="bodyText"><input type="radio" name="main" value="target" id="target" {if $main=="target"}checked{/if}/> Target:</td><td>
      {if $main=="target"}
      {html_options values=$target_ids output=$target_names selected=$target_id name="target_id" id="target_id"}
      {else}
      {html_options values=$target_ids output=$target_names selected=$target_id name="target_id" id="target_id" disabled=true}
      {/if}
      
</td></tr>
    <tr><td class="bodyText">Type:</td><td id = 'group_id-cell'>{include file="mods/graphs/graphs-list.tpl"}
</td></tr>
    <tr><td class="bodyText">Period: </td><td>
    <select id="time_id" name="time_id" />
    {foreach from=$times item=time}
    <option value="{$time.time_id}" {if $time.time_id == $time_id}selected="selected"{/if}>{$time.name}</option>
    {/foreach}
</select>    
</td></tr>
    <tr><td class="bodyText">Mirror:</td><td><input type="checkbox" name="mirror" id="mirror" {if $mirror=="on"}checked{/if} {if $main!="host" && $main!=''}disabled{/if}/></td></tr>
    <tr><td class="bodyText">Force Redraw:</td><td><input type="checkbox" name="force" id="force" {if $force=="on"}checked{/if} /></td></tr>
</table>
<input type="submit" value="Refresh" class="inputbox"/>
</form>    
<table>
    {assign var='i' value=0}
    {foreach from=$vgraphs item=graph}
    <tr><td>
        <select id="time_id{$i}" onChange="change_img('{$server}', '{$graph.host_name}','time_id{$i}','{$graph.graph_id}','{$graph.num}', '{$graph.ip_address}', '{$force}','img{$i}','ref{$i}')">
        {foreach from=$times item=time}
            <option value="{$time.time_id}" {if $time.time_id == $time_id}selected="selected"{/if}>{$time.name}</option>
        {/foreach}
        </select>
        <br /><a id="ref{$i}" href="http://{$server}/graphs/{$graph.host_name}/{$time_id}/{$graph.graph_id}?big=1&{if $graph.num != '0'}interface={$graph.num}&{/if}{if $graph.ip_address != ''}ip={$graph.ip_address}&{/if}{if $force=="on"}force=1{/if}"><img id="img{$i++}" src="http://{$server}/graphs/{$graph.host_name}/{$time_id}/{$graph.graph_id}?{if $graph.num != '0'}interface={$graph.num}&{/if}{if $graph.ip_address != ''}ip={$graph.ip_address}&{/if}{if $force=="on"}force=1{/if}"></a><br />
    </td><td>
        {if $graph.num2 != ''}
            <select id="time_id{$i}" onChange="change_img('{$server}', '{$graph.host_name2}','time_id{$i}','{$graph.graph_id}','{$graph.num2}', '{$graph.ip_address2}', '{$force}', 'img{$i}','ref{$i}')">
            {foreach from=$times item=time}
                <option value="{$time.time_id}" {if $time.time_id == $time_id}selected="selected"{/if}>{$time.name}</option>
            {/foreach}
            </select>        
            <br /><a id="ref{$i}" href="http://{$server}/graphs/{$graph.host_name2}/{$time_id}/{$graph.graph_id}?big=1&{if $graph.num2 != '0'}interface={$graph.num2}&{/if}{if $graph.ip_address2 != ''}ip={$graph.ip_address2}&{/if}{if $force=="on"}force=1{/if}"><img id="img{$i++}" src="http://{$server}/graphs/{$graph.host_name2}/{$time_id}/{$graph.graph_id}?{if $graph.num2 != '0'}interface={$graph.num2}&{/if}{if $graph.ip_address2 != ''}ip={$graph.ip_address2}&{/if}{if $force=="on"}force=1{/if}"></a><br />
        {/if}
    </td></tr>
    {/foreach}
</table>
{include file="footer.tpl"}
