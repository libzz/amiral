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
{if $statusError == ""}
<p class="uploadStatus">{$statusText}</p>
{else}
<p class="uploadStatusError">{$statusError}</p>
{/if}
<input type="hidden" value={$percent} name="percent" id="percent" />
<script>
updateProgressBar({$percent});
{if $percent==100 || $error==1}
    if (document.uploadStatus1)
        document.uploadStatus1.stop();
{/if}
</script>
{if $percent==100}
    {if count($errors) > 0}
<div class="error" style="font-weight:normal; margin-top: 5px; margin-bottom: 5px; text-align: left;">
The following errors occured while generating the configuration files,
        {if $changeset > 0}
the changeset has been left open for you to examine. If you are happy with the
changes you may manually commit the changeset, or if you do not wish to save
the changes at this time choose 'Cancel Changeset' from the menu bar.  
        {else}
please fix the errors and regenerate the configuration files.
        {/if}
<ul>
        {foreach from=$errors item=msg key=template}
<li><b>{$template}</b> - {$msg}</li>
        {/foreach}
</ul>
</div>
    {else}
<p>
        {if $revision!=-1}
The configuration files have been commited to the repository
as revision {$revision} which is displayed below for your convenience
        {else}
There were no changes to the configuration files.
        {/if}
</p>
    {/if}
    {if count($errors) <= 0 || $changeset > 0 }
<div id="configBrowser">
{include file="configListing.tpl" dir="$dir"}
</div>
    {/if}
{/if}
