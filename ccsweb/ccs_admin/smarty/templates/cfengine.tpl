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
<form action="/cfengine/" method="post">
<table cellspacing="0" id="cfrunlogs">
<tr>
    <th class="title">Hostname</th>
    <th class="title">Last Configuration Push</th>
    <th class="title" title="The revision currently operating on the host">
        Operating Revision
    </th>
    <th class="title" title="The revision currently active in CFengine and ready to be pushed out">
        Active Revision
    </th>
    <th class="title" title="The latest revision present in the configuration repository">
        Generated Revision
    </th>
    <th class="title">Push <a href="javascript:updateAll();">[All]</a></th>
</tr>
{assign var="dorefresh" value=0}
{foreach from=$cfrunLogs item=log}
    <tr>
        <th>&nbsp;
            {if $log.last_run != -1 && $log.error == "" && $log.run_status == ""}
            <a href="javascript:toggle('{$log.host_name}');">{/if}
            {$log.host_name}
            {if $log.last_run != -1 && $log.error == "" && $log.run_status == ""}
            </a>
            {/if}
        </th>
        <th>
        {if $log.run_status != ""}
            {assign var="dorefresh" value=1}
            <span class="normal" title="{$log.run_age}">
            {if $log.run_status == "pending"}
                New push currently queued
                (requested {$log.run_age_rounded} ago)
            {else}
                Push running now
                (started {$log.run_age_rounded} ago)
            {/if}
            </span>
        {elseif $log.last_run != -1}
            <span title="{$log.age}">
            {$log.age_rounded} ago&nbsp;
            ({$log.no_lines} lines of output)
            </span>
        {else}
            <span class="normal">
            {$log.host_name} has never had a configuration pushed to it!
            </span>
        {/if}
        </th>
        <th>
        <span class="status{$log.operating_rev_status}" title="{$log.operating_rev_hint}">
        {$log.operating_rev_text}
        {if $log.operating_rev != -1 && $log.operating_rev != ""}
        <a href="/configs/inputs/hosts/{$log.host_name}/?rev={$log.operating_rev}">[{$log.operating_rev}]</a>
        {/if}
        </span>
        </th>
        <th>
        {if $log.active_rev != -1}
        <a href="/configs/inputs/hosts/{$log.host_name}/?rev={$log.active_rev}">[{$log.active_rev}]</a>
        {else}<i class="normal">Unknown</i>{/if}
        </th>
        <th>
        {if $log.generated_rev != -1}
        <a href="/configs/inputs/hosts/{$log.host_name}/?rev={$log.generated_rev}">[{$log.generated_rev}]</a>
        {else}<i class="normal">Unknown</i>{/if}
        </th>
        <th>
        {if $session_state=="RW"}
            {if $log.run_status == ""}
        <input type="checkbox" name="update[{$log.host_name}]" value="yes" />
            {else}&nbsp;{/if}
        {else}
            <i class="normal">N/A</i>
        {/if}
        </th>
    </tr>
    <tr class="hostlog">
        <td colspan="6" class="hostlogc">
            <div class="loghidden" id="host-{$log.host_name}">
                {$log.contents|nl2br}
            </div>
        </td>
    </tr>
{/foreach}
</table>
<div id="pushconfigs">
{if $session_state == "RW"}
<div class="header">Push Options</div>
<table>
    <tr>
        <td>
            <label for="dist_upgrade">Upgrade Software</label>
        </td>
        <td>
    <input type="checkbox" name="dist_upgrade" id="dist_upgrade" value="yes" />
        </td>
    </tr>
    <tr>
        <td>
            <label for="delay_restart">Delay restarts</label>
        </td>
        <td>
    <input type="checkbox" name="delay_restart" id="delay_restart" value="yes" />
        </td>
    </tr>
    <tr>
        <td>
            <label for="classes">Define Classes (eg. A,B)</label>
        </td>
        <td>
            <input type="text" name="classes" id="classes" value="" />
        </td>
    </tr>
</table>
<input type="submit" value="Push Configuration(s)" />
{else}
Upgrade to a read-write session to push configurations
{/if}
</div>
{if $dorefresh>0}
<script type="text/javascript">
    var secs=5;
    // Refresh the cfrun log table in 5 seconds
    refresher = window.setInterval(countdown, 1000);
    function countdown() {ldelim}
        secs--;
        if (secs == 0) {ldelim}
            window.clearInterval(refresher);
            doupdate = new Ajax.Updater('cfruncontainer', '/cfengine/',
                {ldelim}asynchronous:true, evalScripts:true{rdelim});
            $("status").innerHTML = "Refreshing log information...";
        {rdelim} else {ldelim}
            $("countdown").innerHTML = secs;
        {rdelim} 
    {rdelim}
</script>
<span id="status">
Log information will refresh in <span id="countdown">5</span> seconds
</span>
{/if}
</div>
<div id="cfspacer">&nbsp;</div>
</form>
