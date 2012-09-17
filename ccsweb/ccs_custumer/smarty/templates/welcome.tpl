{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id: welcome.tpl 1527 2007-04-05 02:11:33Z ckb6 $
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
{include file="header.tpl" title="Login"}

<div class="modal content">
<h1>Customer Login</h1>
{if $errMsg!=""}
<div class="error">{$errMsg}</div>
{/if}
{if $reason != ""}
{if $reason==3}
You must reauthenticate to enable read-write privileges on this session 
before proceeding.<br /><br />
{elseif $reason == 6}
<span class="error">Sorry, your session has timed out.</span>
{/if}
{/if}
<div id="loginform">
Please enter your authentication details below.<br />
<br />
<form method="post" action="/index.php">
<input type="hidden" name="function" value="login"/>
<input type="hidden" name="from" value="{$from}"/>

<table cellpadding=1 cellspacing=2 border=0 align="center">
{if count($networks)>0}
<tr>
    <th>Network</th>
    <td>{html_options values=$networks output=$networks name="network" id="network" selected=$network}</td>
</tr>
{else}
<input type="hidden" name="network" value="{$networks[0]}" />
{/if}
<tr>
    <th>Username</th>
    <td><input type="text" name="username" value="{$username}"/></td>
</tr>
<tr>
    <th>Password</th>
    <td><input type="password" name="password" value=""/></td>
</tr>
<tr>
    <th>Persist</th>
    <td><label><input type="checkbox" name="persist" value="yes" checked/>
    &nbsp;Use cookies to save my login details</label>
    </td>
</tr>
<tr>
    <td colspan=2>&nbsp;</td>
</tr>
<tr>
    <td colspan=2>
    <input type="submit" value="Login &gt;&gt;" name="login">
    </td>
</tr>
</table>
</form>
<br/>
</div>
</div>

{include file="footer.tpl"}
