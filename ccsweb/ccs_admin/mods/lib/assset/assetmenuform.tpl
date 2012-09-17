{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Asset manipulation template
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
<b>View Asset By</b><br>

ID #:&nbsp;&nbsp;
<form method="post" action="asset.php" name="enterAssetForm" style="display: inline">
<input type="hidden" name="do" value="edit">
<input type="text" name="asset_id" size=15>
<input type="submit" name="view" value="View">
</form><br>
or<br>
MAC:&nbsp;&nbsp;
<form method="post" action="asset.php" name="enterMACForm" style="display: inline">
<input type="hidden" name="do" value="edit">
<input type="text" name="find_asset_mac" size=15>
<input type="submit" name="view" value="Find">
</form>
