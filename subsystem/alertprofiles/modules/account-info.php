<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('Account info'); ?></p>
</td></tr>

<tr><td>


<?php
include("loginordie.php");
loginOrDie();

session_set('lastaction', 'oversikt');
$brukernavn = session_get('bruker'); $uid = session_get('uid');

if ($subaction == 'settaktiv') {
	print "<p>" . gettext("Active profile changed.");
	$dbh->aktivProfil(session_get('uid'), $pid);
}



$brukerinfo = $dbh->brukerInfo( session_get('uid') );
$profiler = $dbh->listProfiler( session_get('uid'), 1);


// Lag en dropdown meny for å velge aktiv profil
print '<form name="form1" method="post" action="index.php?action=oversikt&subaction=settaktiv">';

print gettext('Active profile') . ': <select name="pid" id="selectprof" onChange="this.form.submit()">';


if ($brukerinfo[4] < 1) { 
	echo '<option value="0">' . gettext("Choose alert profile") . '</option>'; 
}
for ($i = 0; $i < sizeof($profiler); $i++) {
	print '<option value="' . $profiler[$i][0] . '" '; 
	if ($brukerinfo[4] == $profiler[$i][0]) echo 'selected'; 
	echo '>' . $profiler[$i][1] . '&nbsp;&nbsp;</option>';
}

if (sizeof($profiler) < 1) {
	echo '<option value="0">' . gettext("No profiles exists...") . '</option>';
}
echo '</select>';

if ($brukerinfo[4] < 1) { 
	echo "<p>" . gettext("No alert profile is active. Activate a profile from the menu above."); 
}
echo '</form>';



    
if ($brukerinfo[4] < 1) { 
		echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>' . gettext("No alert profile is active for the moment. That means no alerts will be sent.") . '</td></tr></table>'; 
}
    
if (sizeof($profiler) < 1) {
	echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>' . gettext("You have not created any profiles. Consequently no profile is active, and no alerts is sent. Choose profiles from the menu at the left margin and create a new profile.") . '</td></tr></table>'; 
}
    


echo '<p>&nbsp;';

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

echo '<h2>' . gettext("User groups") . '</h2>';

$grupper = $dbh->listBrukersGrupper(session_get('uid'), 1);

		
for ($i = 0; $i < sizeof($grupper); $i++) {
		echo '<p class=nop><img src="icons/gruppe.gif"><b>' . $grupper[$i][1] . '</b></p>';
		echo '<p class="descr">' . $grupper[$i][2]. '</p>';
}

if (sizeof($grupper) < 1) {
		echo gettext('<p>You are <b>not</b> member of any user groups.');
} else {
		echo gettext('<p>You are member of ') . sizeof($grupper) . gettext(' user groups.');
}

echo '</td><td width="50%" valign="top" class="oversikt">';

echo '<h2>' . gettext("Permissions") . '</h2>';
$grupper = $dbh->listUtstyrRettighet(session_get('uid'), 1);

		
for ($i = 0; $i < sizeof($grupper); $i++) {
		echo '<p class="nop"><img src="icons/chip.gif"><b>' . $grupper[$i][1] . '</b></p>';
		echo '<p class="descr">' . $grupper[$i][2]. '</p>';
}

if (sizeof($grupper) < 1) {
		echo gettext('<p>You have <b>not</b> permissions to any equipment groups.');
} else {
		echo gettext('<p>You have permissions to ') . sizeof($grupper) . gettext(' equipment groups.');
}

echo '</td></tr></table>';

?>
</td></tr>
</table>
