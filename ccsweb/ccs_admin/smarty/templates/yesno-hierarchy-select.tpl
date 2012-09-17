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
{if $defaulttxt == ""}
{assign var="defaulttxt" value="Use global status"}
{/if}
<input type="hidden" name="{$id}-orig" value="{$value}" />
<select name="{$id}" id="{$id}">
  <option value=""{if $value==""} selected{/if}>{$defaulttxt} ({if $pvalue=="t"}Yes{else}No{/if})</option>
  <option value="t"{if $value=="t"} selected{/if}>Yes</option>
  <option value="f"{if $value=="f"} selected{/if}>No</option>
</select>
