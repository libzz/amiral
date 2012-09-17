{* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Author:       Matt Brown <matt@crc.net.nz>
 * Version:      $Id: index.tpl 1527 2007-04-05 02:11:33Z ckb6 $
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
{include file="header.tpl" title="Welcome"}
<table><td>
<table>
<tr><th width='120'>Username:</th><td>{$details.username}@{$details.domain}</td></tr>
<tr><th>First Name:</th><td>{$details.givenname}</td></tr>
<tr><th>Last Name:</th><td>{$details.surname}</td></tr>
<tr><th>Address:</th><td>{$details.address}</td></tr>
<tr><th>Billing Name:</th><td>{$details.billing_name}</td></tr>
<tr><th>Billing Address:</th><td>{$details.billing_address}</td></tr>
{if $modules.details}
<tr><td><a href="mods/details/">Change my details</a></td></tr>
{/if}
{if $modules.email}
<tr><td><a href="mods/email/">Email Settings</a></td></tr>
{/if}
{if $modules.invoices}
<tr><td><a href="mods/invoices/">Veiw Invoices</a></td></tr>
{/if}
</table></td><td>
<table>
<tr><th width='120'>Plan:</th><td>{$details.description}</td></tr>
<tr><th>Speed:</th><td>{$details.downstream_kbps}kbps down, {$details.upstream_kbps}kbps up</td></tr>
<tr><th>Data Cap:</th><td>{$details.included_mb/1024}GB ({$details.included_mb}MB) per week</td></tr>
{if $modules.plans}
<tr><td><a href="mods/plans/">Change my plan</a></td></tr>
{/if}
<tr><td><br></td></tr>
{if $details.percent > 100}
    {assign var="uclass" value="critical"}
{elseif $customer.cap_usage_int > 80}
    {assign var="uclass" value="warning"}
{else}
    {assign var="uclass" value="ok"}
{/if}

<tr><th>Data Usage:</th><td><span class="status{$uclass}">{$details.used_mb}MB ({$details.percent}%)</span></td></tr>
{if $details.cap_action == 'purchase'}
<tr><th>Purchases:</th><td>{$details.purchase_number} x {$details.cap_param}MB packs, total ${$details.purchase_cost} + GST</td></tr>
<tr><th>New Cap:</th><td>{$details.cap_at_mb}MB</td></tr>
{/if}
<tr><th>Rollover:</th><td>Midnight {$details.cap_period}</td></tr>
{if $modules.history}
<!--<tr><td colspan="2"><a href="mods/history/purchases.php">View data purchases this week</a></td></tr>-->
<tr><td colspan="2"><a href="mods/history/usage.php">View usage by day</a></td></tr>
{/if}
</table>
</td><table>
{include file="footer.tpl"}
