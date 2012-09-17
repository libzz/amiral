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
{include file="header.tpl" title="Administration"}

<b>Note:</b> This site is SSL secured, you should always ensure that you are
accessing this site over a secured connection.<br>
<br>
If your browser is warning you about the certificate not being signed by a 
known authority you can install the appropriate CA certificate from the link
below.<br>
<br>
<b>Choose your browser</b>
<ul>
<li><a href="/certs/cacert.pem">Mozilla / Netscape</a></li>
<li><a href="/certs/cacert.der">Internet Explorer</a></li>
</ul>
{include file="footer.tpl"}
