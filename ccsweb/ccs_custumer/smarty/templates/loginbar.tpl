{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id: loginbar.tpl 1527 2007-04-05 02:11:33Z ckb6 $
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
{if $update>0}
<script>Element.removeClassName("loginbar", "lbcsmopen");</script>
<script>Element.removeClassName("loginbar", "lbcsopen");</script>
{/if}
{if $online=="yes" && $changeset > 0}
    {if $changesets > 0}
        {assign var="classes" value='class="lbcsmopen"'}
        {if $update>0}
<script>Element.addClassName("loginbar", "lbcsmopen");</script>
        {/if}
    {else}
        {assign var="classes" value='class="lbcsopen"'}
        {if $update>0}
<script>Element.addClassName("loginbar", "lbcsopen");</script>
        {/if}
    {/if}
{/if}
{if $update!=1}
<div {$classes} id="loginbar">
{/if}
<div id="lblogin">
{if $session_state != "NO"}
Logged in as:&nbsp;<b>{$username}</b>&nbsp;
{if $changeset > 0}
<form method="post" action="/">
<input type="hidden" name="function" value="commitChangeset" />
<input type="submit" value="Commit Changeset &gt;&gt;" class="submit" />
</form>
{else}
<form method="post" action="/">
<input type="hidden" name="function" value="logout" />
<input type="submit" value="Logout &gt;&gt;" class="submit" />
</form>
{/if}
{else}
{if ! $no_page_layout}
<form method="post" action="/">
<input type="hidden" name="function" value="login"/>
<input type="hidden" name="persist" value="yes"/>
Username:&nbsp;<input name="username"/>&nbsp;
Password:<input name="password" type="password" />&nbsp;
<input type="submit" value="Login &gt;&gt;" class="submit"/>
</form>
{else}
Please login using the form below.&nbsp;&nbsp;
{/if}
{/if}
</div>
<div id="lbstatusfield">
&nbsp;{$smarty.now|date_format:"%H:%M %a %d %b %Z %Y"} 
</div>
&nbsp;
{if $update!=1}
</div>
{/if}
