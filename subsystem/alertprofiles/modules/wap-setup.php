<?php
/* $Id$
 *
 * Copyright 2002-2004 UNINETT AS
 * 
 * This file is part of Network Administration Visualized (NAV)
 *
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *
 * Authors: Andreas Aakre Solberg <andreas.solberg@uninett.no>
 *
 */
?><table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("WAP setup"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>";
echo gettext('Here you can setup and deactivate WAP access for your Alert profiles account.
Remember to keep your wap key secret. If compromised, you can generate a new key here or deactivate WAP access. When generating a new WAP key you have to remember to update your bookmark on your mobile telephone or PDA.');



$uid = session_get('uid');

if (isset($subaction) && $subaction == 'nykey') {
	$nk = chr (rand(0, 25) + ord('A')) .
		chr (rand(0, 25) + ord('A')) .
		rand(0, 9) . rand(0,9) .
		chr (rand(0, 25) + ord('A'));

	$dbh->settwapkey(session_get('uid'), $nk);
}
if (isset($subaction) && $subaction == 'slettkey') {
	$dbh->slettwapkey($uid);
}

;


$k = $dbh->hentwapkey($uid);
print "<h2>" . gettext("WAP key") . "</h2>";

if ($k[0] == null) {
	print "<p>" . gettext("You have no WAP key. One must be generated to access Alert Profiles from WAP.");
	print "<p>[ <a href=\"index.php?action=wap&subaction=nykey\">" . gettext("Generate WAP key") . "</a> ]";	
} else {
	print "<p>" . gettext("Your WAP key is: ") ."<b>" . $k[0] . "</b>.";
	print "<p>" . gettext("You can now access Alert profiles from this WAP page :") . "<br>";
	print '<pre>http://' . $_SERVER['SERVER_NAME'] . '/alertprofiles/wap/?k=' . $k[0] . '</pre>';

	print "<p>[ <a href=\"index.php?action=wap&subaction=nykey\">" . gettext("Generate a new key") . "</a> | 
<a href=\"index.php?action=wap&subaction=slettkey\">" . gettext("Deactivate WAP access") . "</a> ]";

}
?>

</td></tr>
</table>
