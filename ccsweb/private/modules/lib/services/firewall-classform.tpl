{* Copyright (C) 2006  The University of Waikato
 *
 * Firewall Web Interface for the CRCnet Configuration System
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id$
 *
 * No usage or redistribution rights are granted for this file unless
 * otherwise confirmed in writing by the copyright holder.
 *}
{assign var='adisplay' value=$action|capitalize}
{include file="header.tpl" title="Service Configuration - $adisplay Firewall Class"}
<form method="post" action="service.php">
<input type="hidden" name="do" value="{$action}FirewallClass"/>
<input type="hidden" name="process" value="yes"/>
<input type="hidden" name="service_id" id="service_id" value="{$service_id}"/>
{if $action == "update"}<input type="hidden" name="firewall_class_id" id="firewall_class_id" value="{$firewall_class_id}"/>{/if}

<div id="instructions">
Please enter the rules for this class below.
</div>
<br />
<table class="details" id="firewall-class-details">
<tr>
    <th>Class Name</th>
    <td>
    <input type="text" id="firewall_class_name" name="firewall_class_name" value="{$firewall_class_name}" />
    </td>
</tr>
<tr>
    <th>Description</th>
    <td>
    <input type="text" id="description" name="description" value="{$description}" />
    </td>
</tr>
<tr>
    <th>Rules</th>
    <td>
    <textarea id="contents" name="contents">{if $contents==""}
# Firewall Class Template

# Load rules on boot
on_startup

# Default policies
policy in ACCEPT 
policy out ACCEPT 
policy forward-in ACCEPT
policy forward-out ACCEPT 

# Interface features
if_feature rp_filter 1           # Enable Reverse Router Filtering
if_feature accept_redirects 1    # Accept Redirects
if_feature accept_source_route 1 # Accept Source Routes
if_feature bootp_relay 0         # Dont forward bootp requests
if_feature forwarding 1          # forward packets arriving at this interface
if_feature log_martians 0        # log martians?
if_feature send_redirects 1      # Send redirects?
{else}{$contents}{/if}</textarea>
    </td>
</tr>
</table>
<br />
<input type="submit" id="submit" value="{$adisplay} Class &gt;&gt;" />
<br />
<ul>
<li><a href="/mods/service/service.php?service_id={$service_id}&do=edit">Return&nbsp;to&nbsp;firewall&nbsp;properties</a></li>
</ul>
{include file="footer.tpl"}
