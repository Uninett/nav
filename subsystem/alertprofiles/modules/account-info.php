<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('My permissions'); ?></p>
</td></tr>

<tr><td>


<?php
include("loginordie.php");
loginOrDie();

session_set('lastaction', 'oversikt');
$brukernavn = session_get('bruker'); $uid = session_get('uid');

if (isset($subaction) && $subaction == 'settaktiv') {
	print "<p>" . gettext("Active profile changed.");
	$dbh->aktivProfil(session_get('uid'), $pid);
}



$brukerinfo = $dbh->brukerInfo( session_get('uid') );
$profiler = $dbh->listProfiler( session_get('uid'), 1);

//print "<p>Print din UID er " . session_get('uid');

$grupperettighet = $dbh->listUtstyrRettighet(session_get('uid'), 1);
$grupper = $dbh->listBrukersGrupper(session_get('uid'), 1);





if (sizeof($grupperettighet) < 1) {
		echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>' . gettext("You do not have permission to <b>any</b> alerts. Please ask your administrator to setup your alert permissions.") . '</td></tr></table>'; 	
} elseif ($brukerinfo[4] < 1) { 
		echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>' . gettext("No alert profile is active for the moment. That means no alerts will be sent.") . '</td></tr></table>'; 
} elseif (sizeof($profiler) < 1) {
	echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>' . gettext("You have not created any profiles. Consequently no profile is active, and no alerts is sent. Choose profiles from the menu at the left margin and create a new profile.") . '</td></tr></table>'; 
}
    


echo '<p>' . gettext('The NAV administrator may have limited the set of alarms that you may 
receive. The defined set that applies to you is shown in the
Permissions section below.');

echo '<table width="100%"><tr width="30%" valign="top"><td>';
echo '<h3>' . gettext('Account type') . '</h3>';

switch (session_get('admin') ) {
	case (100) :
		echo '<p><img alt="'. gettext('Administrator') . '" src="icons/person100.gif">&nbsp;';
		echo gettext('Administrator');
		break;
	case (1) :
		echo '<p><img alt="' . gettext('Regular user') . '" src="icons/person1.gif">&nbsp;';
		echo gettext('Regular user');
		break;
	default: 
		echo "<p>" . gettext("Uknown admin level.");
}

echo '</td><td width="70%" valign="top">';
echo '<h3>' . gettext("Access to SMS") . '</h3>';

if (access_sms($brukernavn) ) {
		echo '<p><img alt="' . gettext('Yes') . '" src="icons/ok.gif">&nbsp;';
		echo gettext('Yes, you have permission to setup SMS alerts.');
} else {
		echo '<p><img alt="Nei" src="icons/cancel.gif">&nbsp;';
		echo gettext('No, you do not have permission to setup SMS alerts.');
}

echo '</td></tr></table>';
#echo '<p>&nbsp;';

echo '<table width="100%"><tr>';
echo '<td width="50%" valign="top" class="oversikt">';


echo '<h2>' . gettext("Permissions") . '</h2>';

if (sizeof($grupperettighet) < 1) {
		echo gettext('<p>You have <b>not</b> permissions to any filter groups.');
} else {
		echo gettext('<p style="font-size:x-small">You have permissions to ') . sizeof($grupperettighet) . gettext(' filter groups:');
}
	
for ($i = 0; $i < sizeof($grupperettighet); $i++) {
		echo '<p class="nop"><img src="icons/chip.gif"><b>' . $grupperettighet[$i][1] . '</b></p>';
		echo '<p class="descr">' . $grupperettighet[$i][2]. '</p>';
}



echo '</td><td width="50%" valign="top" class="oversikt">';

echo '<h2>' . gettext("User groups") . '</h2>';


if (sizeof($grupper) < 1) {
		echo gettext('<p>You are <b>not</b> member of any user groups.');
} else {
		echo gettext('<p style="font-size:x-small">You are member of ') . sizeof($grupper) . gettext(' user groups:');
}

		
for ($i = 0; $i < sizeof($grupper); $i++) {
		echo '<p class=nop><img src="icons/gruppe.gif"><b>' . $grupper[$i][1] . '</b></p>';
		echo '<p class="descr">' . $grupper[$i][2]. '</p>';
}




echo '</td></tr></table>';

?>
</td></tr>
</table>
