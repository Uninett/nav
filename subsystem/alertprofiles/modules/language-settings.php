<table width="100%" class="mainWindow">
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

if ($langset) {
	echo gettext("<p>Your language of choice is saved, but at the moment it will only work for alert messages.");
}

?>

</td></tr>
</table>
