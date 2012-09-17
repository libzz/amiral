{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Authentication interface template
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
{include file="header.tpl" title="Authentication - $titlea Group"}
{assign var="sentinel" value='<option value="zzzz" disabled class="iehide">&nbsp;</option>'}

<form method="post" action="group.php">
<input type="hidden" name="group_id" value="{$group.admin_group_id}">
<input type="hidden" name="do" value="{$action}">
<input type="hidden" name="process" value="yes">

{if $action=="add"}
Please enter the details of the new group below. Once the group has been
created you will be able to add admins to it.<br>
<br>
{assign var="bcaption" value="Add"}
{else}
{assign var="bcaption" value="Update"}
{/if}
<table>
<tr>    
    <th width="120">Group Name</th>
    <td><input type="text" name="group_name" value="{$group.group_name}"></td>
</tr>
{if $action != "add"}
<tr>
    <th>Unix Group ID</th>
    <td>{if $group.gid != ""}{$group.gid}{else}
    <a href="group.php?do=assigngid&group_id={$group.admin_group_id}">Assign GID</a>
    {/if}
    </td>
</tr>
{/if}
</table>
<br>
<input type="reset" name="reset" value="Reset Form">&nbsp;
<input type="submit" name="submit" value="{$bcaption} Group &gt;&gt;">
</form>
{if $action != "add"}
<br>
<h2>Group Membership</h2>
Use the form below to update the group membership in real time, no page 
reloads are required.<br>
<br>
<table cellpadding="0" cellspacing="2" border="0">
<tr>
<td style="text-align:center;">
<div class="ielistheading">Current Members</div>
<select size="10" multiple id="group_members" class="ielist">
<optgroup label="Groups">
{assign var="cogstarted" value="0"}
{foreach from=$members item=admin}
{if $admin.group_id != ""}
    <option value="{$admin.group_name};g{$admin.group_id}">{$admin.group_name|capitalize}</option>
{else if $admin.admin_id != ""}
{if $cogstarted==0}
    {$sentinel}
</optgroup>
<optgroup label="Users">
{assign var="cogstarted" value="1"}{/if}
    <option value="{$admin.username};u{$admin.admin_id}">{$admin.username} ({$admin.givenname} {$admin.surname})</option>
{/if}
{/foreach}
{if $cogstarted==0}
    {$sentinel}
</optgroup>
<optgroup label="Users">
{/if}
    {$sentinel}
</optgroup>
</select>
</td>
<td class="ielistbuttons">
<input type="button" name="addmember" value="&lt;&lt;&nbsp;Add To Group" class="ielistbutton" onclick="addMember({$group.admin_group_id});"><br>
<br>
<input type="button" name="delmember" value="Remove From Group&nbsp;&gt;&gt;" class="ielistbutton" onclick="delMember({$group.admin_group_id});"><br>
<br>
<span class="ienotice" id="ienotice">&nbsp;</span>
</td>
<td style="text-align:center;">
<div class="ielistheading">Possible Members</div>
<select size="10" multiple id="avail_users" class="ielist">
<optgroup label="Groups">
{assign var="cogstarted" value="0"}
{foreach from=$avail item=admin}
{if $admin.admin_group_id != ""}
    <option value="{$admin.group_name};g{$admin.admin_group_id}">{$admin.group_name|capitalize}</option>
{else if $admin.admin_id != ""}
{if $cogstarted==0}
    {$sentinel}
</optgroup>
<optgroup label="Users">
{assign var="cogstarted" value="1"}{/if}
    <option value="{$admin.username};u{$admin.admin_id}">{$admin.username} ({$admin.givenname} {$admin.surname})</option>
{/if}
{/foreach}
{if $cogstarted==0}
    {$sentinel}
</optgroup>
<optgroup label="Users">
{/if}
    {$sentinel}
</optgroup>
</select>
</td>
</tr>
</table>
{/if}
<ul>
<br>
<li><a href="group.php">Return&nbsp;to&nbsp;group&nbsp;list</a>
</ul>
{include file="footer.tpl"}
