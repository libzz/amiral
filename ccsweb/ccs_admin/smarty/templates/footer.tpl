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
{if ! $no_page_layout}
</div>
</td></tr></table>
{/if}
<div class="footer"></div>
{* Display any warning messages *}
{if count($warning_msgs) > 0}
<div class="warnings"><br/>
<b>WARNINGS:</b>
<ul>
{foreach from=$warning_msgs item=msg}
<li>{$msg}</li>
{/foreach}
</ul>
</div><br/>
{/if}

{* Display any debug messages *}
{if count($debug_msgs) > 0 && $do_debug==1}
<div class="debug"><br/>
<b>DEBUG:</b>
<ul>
{foreach from=$debug_msgs item=msg}
<li>{$msg}</li>
{/foreach}
</ul>
</div><br/>
{/if}
<!-- Page Execution Time: {$exec_time} seconds -->
</body>
</html>
