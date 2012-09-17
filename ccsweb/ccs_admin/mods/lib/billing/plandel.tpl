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
{include file="header.tpl" title="Billing Configuration - Delete Plan"}

Are you sure you want to delete the following plan?<br />
<br />
This will cause all related configuration information to be removed from the
database.<br />
You may wish to simply prevent the host from being autoconfigured, or remove
it from
a site.<br />
<br />
<table>
<tr>    
    <th width="200">Plan name</th>
    <td>{$plan.plan_name}</td>
</tr>
<tr>
    <th>Desciption</th>
    <td>{$plan.description}</td>
</tr>
<tr>
    <th>Price</th>
    <td>{$plan.price}</td>
</tr>
</table>
<br>
<a href="plan.php">Cancel</a>
&nbsp;|&nbsp;

<a href="plan.php?do=delete&confirm=yes&plan={$plan.plan_id}">
Delete&nbsp;Plan&nbsp;&gt;&gt;</a>
<br><br>
{include file="footer.tpl"}
