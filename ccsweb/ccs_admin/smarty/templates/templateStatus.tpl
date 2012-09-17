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
{include file="header.tpl" title="Template Generation"}
<br />
<input type="hidden" id="statsKey" value="{$statsKey}" />
{strip}
<div id="status-win">
    <div class="progressBar" id="UploadProgressBar1">
        <div class="border">
            <div class="background">
                <div class="foreground"></div>
            </div>
        </div>
    </div>
    <div id="UploadStatus1">
    {include file="templateStatusUpdate.tpl" included=1}    
    </div>
</div>
{/strip}
{include file="footer.tpl"}
