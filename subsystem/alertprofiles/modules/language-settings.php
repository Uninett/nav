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
<?php
echo '<p>' . gettext("Language settings") . '</p>';


?>

</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();

echo "<p>" . gettext("Here you can choose in which language alert should be sent to you.");

$brukernavn = session_get('bruker'); $uid = session_get('uid');




echo '<h2>' . gettext("Choose language") . '</h2>';

echo '<div style="margin: 5px; padding: 1em; border: thin solid #ccc; font-size: large">';
if ($language == 'en') {
	print '<img src="icons/gbr.png" alt"' . gettext("English") . '">&nbsp;' . gettext('English') . ' (Selected)';
} else {
	if ($login) { 
		print '<a href="?action=language&langset=en">';
	}
	print '<img src="icons/gbrg.png" alt"' . gettext("English") . '">&nbsp;' . gettext('English');
	if ($login) { 
		print '</a>';
	}

}
echo '</div><div style="margin: 5px; padding: 1em; border: thin solid #ccc; font-size: large">';
if ($language == 'no') {
	print '<img src="icons/nor.png" alt"' . gettext("Norwegian") . '">&nbsp;'.  gettext('Norwegian') . ' (Selected)';
} else {
	if ($login) { 
		print '<a href="?action=language&langset=no">';
	}
	print '<img src="icons/norg.png" alt"' . gettext("Norwegian") . '">&nbsp;'.  gettext('Norwegian');
	if ($login) { 
		print '</a>';
	}
}
echo '</div>';

if (isset($langset) && $langset) {
	echo gettext("<p>Your language of choice is saved, but at the moment it will only work for alert messages.");
}

?>

</td></tr>
</table>
