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
{assign var="sheets" value=()}
{assign var="scripts" value=()}
{include file="header.tpl" title="CRCnet Configuration System - Commit Changeset" sheets=$sheets scripts=$scripts}

Please enter a description of this changeset in the box below.
<br/>
{if $changesets > 0}
{if $changesets==1}
<b>WARNING</b> There is another active changeset 
{else}
<b>WARNING</b> There are {$changesets} other active changesets 
{/if}
currently accessing the configuration database. If you make changesets that
conflict with these changesets your changeset may be cancelled when you
commit it.<br\n>
<br\>
{/if}
<form action="{$page}" method="post">
<input type="hidden" name="confirm" value="yes">
<table cellpadding=0 cellspacing=2 border=0>
<tr>
    <th width="200">Changeset Description</th>
    <td>
    <textarea rows=5 name="description" cols=50>Please describe the changes here</textarea>
    </td>
</tr>
<tr>
    <td colspan=2>&nbsp;</td>
</tr>
<tr>
    <td colspan=2>
    <input type="submit" value="Commit Changeset &gt;&gt;" name="login">
    </td>
</tr>
</table>
</form>
</div>

{include file="footer.tpl"}
