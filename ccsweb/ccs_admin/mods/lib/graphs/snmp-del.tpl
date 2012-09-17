{include file="header.tpl" title="Graphs"}
{if $host_name != ""}
Are you sure you want to delete the following entry?<br />
<br />
<table>
<tr>    
    <th width="200">Hostname</th>
    <td>{$host_name}</td>
</tr>
{if $class_name != ""}
<tr>
    <th>Class</th>
    <td>{$class_name}</td>
</tr>
<tr>
    <th>ifIndex</th>
    <td>{$num}</td>
</tr>
{/if}
</table>
{else}
<font color=red> WARNING: You are about to disable all graphing ability. DO NOT CONTINUE unless you know what you are doing!!</font>
{/if}
<br>
<a href="snmp-log.php">Cancel</a>
&nbsp;|&nbsp;
{if $host_name == ""}
<a href="snmp-log.php?do=flush&confirm=yes">
Flush&nbsp;&gt;&gt;</a>
{else}{if $class_name != ""}
<a href="snmp-log.php?do=delete&class_id={$class_id}&host_id={$host_id}&num={$num}&confirm=yes">
Delete&nbsp;Entries&nbsp;&gt;&gt;</a>
{else}
<a href="snmp-log.php?do=deletehost&host_id={$host_id}&confirm=yes">
Delete&nbsp;Entry&nbsp;&gt;&gt;</a>
{/if}
{/if}
<br><br>
{include file="footer.tpl"}
