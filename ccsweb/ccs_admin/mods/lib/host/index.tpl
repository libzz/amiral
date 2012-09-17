{include file="header.tpl" title="Host Configuration"}
Select a host from the list below.
<table>
<tr>
    <th>Hostname</th>
    <th>Location</th>
    <th>Status</th>
    <th>Actions</th>
</tr>
{foreach from=$hosts item=host}
<tr class="{cycle values="row1,row2"}">
    <td>{$host.hostname}</td>
    <td>{$host.location}</td>
    <td>{$host.status}</td>
    <td>
    <a href="host.php?do=edit&host_id={$host.host_id}">[edit]</a>
    &nbsp;
    <a href="host.php?do=delete&host_id={$host.host_id}">[delete]</a>
    </td>
</tr>
{/foreach}
</table>
<ul>
<li><a href="host.php?do=add">Create new host</a></li>
</ul>

{include file="footer.tpl"}
