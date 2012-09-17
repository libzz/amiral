{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id: header.tpl 1527 2007-04-05 02:11:33Z ckb6 $
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
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <link rel="stylesheet" href="/css/crcnet.css" type="text/css"/>
{if $sheets != ""}
{foreach from=$sheets item=sheet}
    <link rel="stylesheet" href="{$sheet}" type="text/css"/>
{/foreach}
{/if}
    <script type="text/javascript">site="{$site_address}";</script>
    <script type="text/javascript" src="/js/prototype.js"></script>
    <script type="text/javascript" src="/js/behaviour.js"></script>
    <script type="text/javascript" src="/js/crcnet.js"></script>
{if $scripts != ""}
{foreach from=$scripts item=script}
    <script type="text/javascript" src="{$script}"></script>
{/foreach}
{/if}
    <title>Rurallink :: {$title}</title>
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
{if $refreshTime != 0}
    <meta http-equiv=Refresh content="{$RefreshTime}; URL={$smarty.request.page}"/>
{/if}
</head>
<body>
<div class="header">
<table cellspacing="0">
<tr>
<td class="title1">
<a href="http://www.wand.net.nz/"><img src="/img/wand-logo.png" alt="WAND Network Research Group"/></a>
</td><td class="title2">
<a href="http://www.waikato.ac.nz/"><img src="/img/uow-coa.jpg" alt="University
of Waikato Crest Of Arms"/></a>
</td></tr>
</table>
</div>
{include file="loginbar.tpl"}
{include file="notices.tpl"}
{if ! $no_page_layout}
<table><tr><td>
{include file="menubar.tpl"}
</td><td width="100%">
<div class="content">
<h1>{$title}</h1>
{/if}
