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
{assign var="no_page_layout" value="1"}
{include file="header.tpl" title="Forgotten Password"}

<div class="content modal">
<h1>Configuration System Password Recovery</h1>

Please enter your username below and a new password will be emailed to you.
<br />
<br />
<div class="loginform">
<form method="post" action="/index.php">
<input type="hidden" name="function" value="forgotpass"/>
<input type="hidden" name="process" value="yes" />
<table cellpadding=0 cellspacing=2 border=0>
<tr>
    <th>Username</th>
    <td><input type="text" name="username" value="" /></td>
</tr>
<tr>
    <td colspan=2>&nbsp;</td>
</tr>
<tr>
    <td colspan=2>
    <input type="submit" value="Generate Password &gt;&gt;" name="change">
    </td>
</tr>
</table>
</form>
</div>
<br/>
</div>

{include file="footer.tpl"}
