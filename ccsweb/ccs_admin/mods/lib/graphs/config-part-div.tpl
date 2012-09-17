{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Graph manipulation interface
 *
 * Author:       Chris Browning <ckb6@cs.waikato.ac.nz>
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

<tr> 
    <th width="200">Type</th><td>
        <select id="type" name="type" />
            <option value="DEF" {if $part.type == "DEF"}selected="selected"{/if}>DEF</option>
            <option value="CDEF" {if $part.type == "CDEF"}selected="selected"{/if}>CDEF</option>
            <option value="PRINT" {if $part.type == "PRINT"}selected="selected"{/if}>PRINT</option>
            <option value="GPRINT" {if $part.type == "GPRINT"}selected="selected"{/if}>GPRINT</option>
            <option value="COMMENT" {if $part.type == "COMMENT"}selected="selected"{/if}>COMMENT</option>
            <option value="VRULE" {if $part.type == "VRULE"}selected="selected"{/if}>VRULE</option>
            <option value="HRULE" {if $part.type == "HRULE"}selected="selected"{/if}>HRULE</option>
            <option value="LINE1" {if $part.type == "LINE1"}selected="selected"{/if}>LINE1</option>
            <option value="LINE2" {if $part.type == "LINE2"}selected="selected"{/if}>LINE2</option>
            <option value="LINE3" {if $part.type == "LINE3"}selected="selected"{/if}>LINE3</option>
            <option value="STACK" {if $part.type == "STACK"}selected="selected"{/if}>STACK</option>
            <option value="AREA" {if $part.type == "AREA"}selected="selected"{/if}>AREA</option>
        </select></td>   
</tr>
<tr>    
    <th width="200" id="order-header">Order</th>
    <td><input type="text" name="graph_order" id="graph_order" value="{$part.graph_order}"/>This field controls the order in which they are used during rendering. If two numbers are the same it is undefined what order they will be used.</td>
</tr>
{if $part.type == "LINE1" || $part.type == "LINE2" || $part.type == "LINE3" || $part.type == "AREA" || $part.type == "STACK"}
<tr>    
    <th width="200" id="varname-header">Variable</th><td>
        <select name="varname" id="varname">
        {foreach from=$vars item=var}
            <option value="{$var.varname}" {if $var.varname == $part.varname}selected="selected"{/if}>{$var.varname}</option>
        {/foreach}
        </select>
</td></tr>
<tr>    
    <th width="200" id="colour-header">Colour</th>
    <td><input type="text" name="colour" id="colour" value="{$part.colour}"/>The draw colour in hex (RRGGBB eg FF0000 is red)</td>
</tr>
<tr>    
    <th width="200">Legend</th>
    <td><input type="text" name="text" id="text" value="{$part.text}"/></td>
</tr>

{/if}
{if $part.type == "HRULE"}
<tr>    
    <th width="200" id="varname-header">Value</th>
    <td><input type="text" name="varname" id="varname" value="{$part.varname}"/></td>
</tr>
<tr>    
    <th width="200" id="colour-header">Colour</th>
    <td><input type="text" name="colour" id="colour" value="{$part.colour}"/>The draw colour in hex (RRGGBB eg FF0000 is red)</td>
</tr>
<tr>    
    <th width="200">Legend</th>
    <td><input type="text" name="text" id="text" value="{$part.text}"/></td>
</tr>
{/if}
{if $part.type == "VRULE"}
<tr>    
    <th width="200" id="varname-header">Time</th>
    <td><input type="text" name="varname" id="varname" value="{$part.varname}"/>In seconds since 1 Jan 1970</td>
</tr>
<tr>    
    <th width="200" id="colour-header">Colour</th>
    <td><input type="text" name="colour" id="colour" value="{$part.colour}"/>The draw colour in hex (RRGGBB eg FF0000 is red)</td>
</tr>
<tr>    
    <th width="200">Legend</th>
    <td><input type="text" name="text" id="text" value="{$part.text}"/></td>
</tr>

{/if}
{if $part.type == "PRINT" || $part.type == "GPRINT"}
<tr>    
    <th width="200" id="varname-header">Variable</th><td>
        <select name="varname" id="varname">
        {foreach from=$vars item=var}
            <option value="{$var.varname}" {if $var.varname == $part.varname}selected="selected"{/if}>{$var.varname}</option>
        {/foreach}
        </select>
</td></tr>
<tr>    
    <th width="200">CF</th><td>
        <select id="cf" name="cf" />
            <option value="AVERAGE" {if $part.cf == "AVERAGE"}selected="selected"{/if}>AVERAGE</option>
            <option value="LAST" {if $part.cf == "LAST"}selected="selected"{/if}>LAST</option>
            <option value="MAX" {if $part.cf == "MAX"}selected="selected"{/if}>MAX</option>
            <option value="MIN" {if $part.cf == "MIN"}selected="selected"{/if}>MIN</option>
        </select></td>       
</tr>
<tr>    
    <th width="200" id="text-header">Statement</th>
    <td><input type="text" name="text" id="text" value="{$part.text}"/></td>
</tr>
{/if}
{if $part.type == "COMMENT"}
<tr>    
    <th width="200" id="text-header">Comment</th>
    <td><input type="text" name="text" id="text" value="{$part.text}"/></td>
</tr>
{/if}
{if $part.type == "DEF"}
<tr>    
    <th width="200" id="varname-header">Variable</th>
    <td><input type="text" name="varname" id="varname" value="{$part.varname}"/>The variable name</td>
</tr>
<tr>    
    <th width="200">RRD Item</th><td>
        <select name="text" id="text">
        {foreach from=$items item=item}
            <option value="{$item.name}" {if $part.text == $item.name}selected="selected"{/if}>{$item.name}</option>
        {/foreach}
        </select>
</td></tr>    
<tr>    
    <th width="200">CF</th><td>
        <select id="cf" name="cf" />
            <option value="AVERAGE" {if $part.cf == "AVERAGE"}selected="selected"{/if}>AVERAGE</option>
            <option value="LAST" {if $part.cf == "LAST"}selected="selected"{/if}>LAST</option>
            <option value="MAX" {if $part.cf == "MAX"}selected="selected"{/if}>MAX</option>
            <option value="MIN" {if $part.cf == "MIN"}selected="selected"{/if}>MIN</option>
        </select></td>       
</tr>

{/if}
{if $part.type == "CDEF"}
<tr>    
    <th width="200" id="varname-header">Variable</th>
    <td><input type="text" name="varname" id="varname" value="{$part.varname}"/>The variable name</td>
</tr>
<tr>    
    <th width="200" id="text-header">Chain</th>
    <td><input type="text" name="text" id="text" value="{$part.text}"/></td>
</td></tr>  
{/if}
<tr>    
    <td colspan=2>
    <input type="submit" name="submit" id="submit" value="Update Part Type &gt;&gt;">
    </td>
</tr>
