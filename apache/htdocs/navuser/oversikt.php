<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p>Oversikt</p>
</td></tr>

<tr><td>


<?php

$brukerinfo = $dbh->brukerInfo( session_get('uid') );

if (get_exist('vis') )
	session_set('visoversikt', get_get('vis') );

print '<table width="100%"><tr><td>';
print '<h2>' . $brukerinfo[1] . '</h2>';
print '<p>Du er logget inn på NAV med brukernavn <b>' . $brukerinfo[0] . '</b>.<br>';
print '</td><td>';
if (session_get('visoversikt') == 0) {
	print '<p>[ <a href="index.php?vis=1">Vis mer info...</a> ]';
} else {
	print '<p>[ <a href="index.php?vis=0">Vis mindre info...</a> ]';
}
print '</td></tr></table>';

if (session_get('visoversikt') == 1) {

print '<p>&nbsp;';

print '<table width="100%"><tr width="30%" valign="top"><td>';
print '<h3>Kontotype</h3>';

switch ($brukerinfo[2]) {
	case (100) :
		print '<p><img alt="Administrator" src="icons/person100.gif">&nbsp;';
		print 'Administrator';
		break;
	case (1) :
		print '<p><img alt="Vanlig bruker" src="icons/person1.gif">&nbsp;';
		print 'Vanlig bruker';
		break;
	default: 
		print "<p>Ukjent administrator nivå.";
}

print '</td><td width="70%" valign="top">';
print '<h3>Tilgang til SMS</h3>';

if ($brukerinfo[3] == 't') {
	print '<p><img alt="Ja" src="icons/ok.gif">&nbsp;';
	print 'Ja, du har tilgang til å sette opp SMS alarmer.';
} else {
	print '<p><img alt="Nei" src="icons/cancel.gif">&nbsp;';
	print 'Nei, du har ikke lov til å sette opp SMS alarmer.';
}

print '</td></tr></table>';
#print '<p>&nbsp;';

print '<table width="100%"><tr>';
print '<td width="50%" valign="top" class="oversikt">';

print '<h2>Brukergrupper</h2>';

$grupper = $dbh->listBrukersGrupper(session_get('uid'), 1);

	
for ($i = 0; $i < sizeof($grupper); $i++) {
	print '<p class=nop><img src="icons/gruppe.gif"><b>' . $grupper[$i][1] . '</b></p>';
	print '<p class="descr">' . $grupper[$i][2]. '</p>';
}

if (sizeof($grupper) < 1) {
	print '<p>Du er <b>ikke</b> medlem av noen brukergrupper.';
} else {
	print '<p>Du er medlem av ' . sizeof($grupper) . ' brukergrupper.';
}

print '</td><td width="50%" valign="top" class="oversikt">';

print '<h2>Rettigheter</h2>';
$grupper = $dbh->listUtstyrRettighet(session_get('uid'), 1);

	
for ($i = 0; $i < sizeof($grupper); $i++) {
	print '<p class="nop"><img src="icons/chip.gif"><b>' . $grupper[$i][1] . '</b></p>';
	print '<p class="descr">' . $grupper[$i][2]. '</p>';
}

if (sizeof($grupper) < 1) {
	print '<p>Du har <b>ikke</b> rettighet til noen utstyrsgrupper.';
} else {
	print '<p>Du har rettighet til ' . sizeof($grupper) . ' utstyrsgrupper.';
}

print '</td></tr></table>';

print '<h2>Aktiv profil</h2>';

if ($subaction == 'settaktiv') {
	print "<p>Aktiv profil er endret til : ";
	$dbh->aktivProfil(session_get('bruker'), $pid);

}


print '<form name="form1" method="post" action="index.php?action=oversikt&subaction=settaktiv">';


$profiler = $dbh->listProfiler( session_get('uid'), 1);
print '<select name="pid" id="selectprof" onChange="this.form.submit()">';
	

$brukerinfo = $dbh->brukerInfo( session_get('uid') );
for ($i = 0; $i < sizeof($profiler); $i++) {
	print '<option value="' . $profiler[$i][0] . '" '; 
	if ($brukerinfo[4] == $profiler[$i][0]) print 'selected'; 
	print '>' . $profiler[$i][1] . '&nbsp;&nbsp;</option>';
}

if (sizeof($profiler) < 1) {
	print '<option value="0">Ingen profiler opprettet...</option>';
}
print '</select>';

print '</form>';

}

?>
</td></tr>
</table>
