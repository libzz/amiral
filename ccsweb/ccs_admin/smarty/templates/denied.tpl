{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id: error.tpl 741 2006-06-20 00:27:30Z mglb1 $
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
{include file="header.tpl" title="Access Denied!"}

Sorry, you have been denied access to this page:<br />
<br />
<div class="error">
{if $reason == 4}
Your account does not have the appropriate permissions enabled.
{elseif $reason == 5}
The username and/or password you provided could not be verified.
{elseif $reason == 7}
Your account is not of the appropriate type to access this page.
{else}
{$reason}
{/if}
</div>
<br />
{include file="footer.tpl"}
