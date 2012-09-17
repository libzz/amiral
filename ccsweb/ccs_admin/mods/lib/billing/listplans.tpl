{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Plan list template
 *
 * Author:		 Matt Brown <matt@crc.net.nz>
 *				 Ivan Meredith <ivan@ivan.net.nz>
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
{include file="header.tpl" title="Billing Configuration - Plan Management"}
	
<table>
<tr>
    <th>Name</th>
    <th>Description</th>
    <th>Price</th>
    <th>Speed up/down (kbps)</th>
    <th>Data cap</th>
    <th>Actions</th>
</tr>
{foreach from=$plans item=p}
<tr class="{cycle values="row1,row2"}">
    <td>{$p.plan_name}</td>
    <td>{$p.description}</td>
    <td><div align=right>${$p.price|string_format:"%.2f"}</div></td>
    <td><div align=center>{$p.upstream_kbps}/{$p.downstream_kbps} kbps</div></td>
    <td><div align=center>{$p.included_mb} mb</div></td>
    <td><a href="plan.php?do=edit&plan_id={$p.plan_id}">[edit]</a>
		<a href="plan.php?do=delete&plan_id={$p.plan_id}">[delete]</a>
	</td>
</tr>
{/foreach}
</table>
<br/>
<li><a href="plan.php?do=add">Create a new plan</a></li>
{include file="footer.tpl"}
