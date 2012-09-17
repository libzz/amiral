/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Asset Management Interface - Link Addition / Modification
 * 
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id: link.js 502 2006-02-14 05:08:09Z mglb1 $
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
 */

errCount=0;

Behaviour.addLoadEvent(initForm);

function initForm()
{
    // Focus on the location field
    $("location").select();
}
