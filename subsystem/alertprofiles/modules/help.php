<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("Help"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();
echo '<h1>User Manual</h1>';
echo '<p><img src="icons/pdf_icon.png" alt="PDF format">';
echo '[ <a href="documents/alert-profiles-manual.pdf">' . gettext("Download") . '</a> ] ' . gettext("user manual in PDF format.");

?>
</td></tr>
<tr><td>

<h1 style="margin-top: 2em">Icon legend</h1>

<table width="100%" cellpadding="0" cellspacing="5" border="0">
<tr><td colspan="2"><h2>Overview and account info</h2></td></tr>
<tr>
	<td width="32"><img alt="icon" src="icons/equipment.png"></td>
	<td><p>Filter group.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/gruppe.gif"></td>
	<td><p>Account group.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/person0.gif"></td>
	<td><p>Your account is disabled.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/person1.gif"></td>
	<td><p>Your account is a standard user account.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/person100.gif"></td>
	<td><p>Your account is an administration account.</p></td>
</tr>

<tr>
	<td width="32"><img alt="icon" src="icons/direct.png"></td>
	<td><p>Alert will be delivered immidiately.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/queue.png"></td>
	<td><p>Alert will be enqueued.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/cancel.gif"></td>
	<td><p>No alerts will be sent during this time period.</p></td>
</tr>

<tr><td colspan="2"><h2>Address types</h2></td></tr>
<tr>
	<td width="32"><img alt="icon" src="icons/mail.gif"></td>
	<td><p>Email.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/mobil.gif"></td>
	<td><p>SMS.</p></td>
</tr>


<tr><td colspan="2"><h2>Filter groups</h2></td></tr>
<tr>
	<td width="32"><img alt="icon" src="icons/person1.gif"></td>
	<td><p>Equipment group is private.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/person100.gif"></td>
	<td><p>Equipment group is owned by the administrators and shared among user groups.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/pluss.gif"></td>
	<td><p>Filter is added to group.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/minus.gif"></td>
	<td><p>Filter is subtracted from the group.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/plussinverse.gif"></td>
	<td><p>Alerts which not match the filter is added to the group.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/and.gif"></td>
	<td><p>Alerts has to match this filter to be in the group.</p></td>
</tr>

<tr><td colspan="2"><h2>Setting up addresses, profiles and equipment groups</h2></td></tr>
<tr>
	<td width="32"><img alt="icon" src="icons/stop.gif"></td>
	<td><p>No references. Shows that an item do not have any references. In example this icon could mean that a equipment group is not in use in any profiles.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/open2.gif"></td>
	<td><p>Open and edit item. Item composition will be shown in a new page.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/edit.gif"></td>
	<td><p>Edit simple properties of this item. Changable fields will be shown inline at the same page.</p></td>
</tr>
<tr>
	<td width="32"><img alt="icon" src="icons/delete.gif"></td>
	<td><p>Delete item.</p></td>
</tr>

</table>

</td></tr>
<tr><td>

<h1 style="margin-top: 2em">FAQ</h1>
<p>Coming soon...</p>

</td></tr>


</table>
