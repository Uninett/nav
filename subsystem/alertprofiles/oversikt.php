<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('Oversikt'); ?></p>
</td></tr>

<tr><td>


<?php

function helgdescr($helg) {
	switch($helg) {
		case 1 : return gettext('Hele uken');
		case 2 : return gettext('Man-Fre');
		case 3 : return gettext('Lør-Søn');
		default: return gettext('Ukjent');
	}
}




function showTimeTable($dbh, $brukerinfo, $listofhelg) {

	echo '<table class="timetable" border="0" cellpadding="0" cellspacing="0">';
	echo '<tr class="header"><td class="clock">Klokke</td><td class="helg">Ukedag</td>' .
		'<td class="eqg">Varsling til utstyrsgruppe</td></tr>';
	$t_per = $dbh->listPerioder($brukerinfo[4], 0);
	$rc = 0;
	$alt[0] = 'even'; $alt[1] = 'odd';
	foreach ($t_per AS $t_p) {

		if (! in_array($t_p[1], $listofhelg ) ) continue;

		if ($t_p[0] == 1068) { // active
			echo '<tr class="period active ' . $alt[++$rc % 2] . '">';
		} else {
			echo '<tr class="period ' . $alt[++$rc % 2] . '">';
		}

		echo '<td class="clock">';
		echo '<a class="tt" href="?action=periode&amp;subaction=endre&amp;tid=' . $t_p[0] . '&amp;pid=' . $brukerinfo[4] . '#endre">';
		echo leading_zero($t_p[2],2) . ":" . leading_zero($t_p[3],2) . 
			'</a><br><img src="http://jimmac.musichall.cz/ikony/i12/appointment-reminder.png">' . "</td>";
			
		echo '<td class="helg">' . helgdescr($t_p[1]) . '</td>'; // <br><small>(' . $t_p[0] . ')</small>
		echo '<td class="eqg">';
		
		$t_utg = $dbh->listUtstyrPeriode(session_get('uid'), $t_p[0], 0);

		echo '<table class="eqgroup" border="0" cellpadding="0" cellspacing="0">';
		$rrc = 0; $ecount = 0;
		foreach ($t_utg AS $t_u) {
			$estring = '<td class="eqname">';
			$estring .= '<img src="icons/equipment.png">&nbsp;';
			if ($t_u[4]) $estring .= '<a class="tt" href="?action=utstyrgrp&amp;gid=' . $t_u[0] . '">';
				else $estring .= '<a class="tt" href="?action=utstyr">';
			$estring .= $t_u[1];
			$estring .= "</a></td>"; 
			$estring .= '<td class="eqaddress">';
			
			$p_adr = $dbh->listVarsleAdresser(session_get('uid'), $t_p[0], $t_u[0], 0);
			$estring .= '<ul>';
			$vcount = 0;
			foreach ($p_adr AS $p_a) {
				if (!is_null($p_a[3]) ) {
					$vcount++;
					$vstr = '<a class="tt" href="?action=adress">' . $p_a[1] . '</a>';
					if ($p_a[3] == 0) {
						$estring .= '<li class="direct">' . $vstr . "</li>";
					} else if ($p_a[3] == 1) {
						$estring .= '<li class="queue">' . $vstr . " (Daglig kø)</li>";
					} else if ($p_a[3] == 2) {
						$estring .= '<li class="queue">' . $vstr . " (Ukentlig kø)</li>";
					} else if ($p_a[3] == 3) {
						$estring .= '<li class="queue">' . $vstr . " (Kø til profilbytte)</li>";
					} else if ($p_a[3] == 4) {
						$estring .= '<li class="direct">' . $vstr . " (Ingen varsling)</li>";
					} else {
						$estring .= '<li class="queue">' . $vstr . " (Ukjent køtype)</li>";
					}
				}
			}

			$estring .= '</ul>';
			$estring .= '</td></tr>';
			
			if ($vcount > 0) { 
				$ecount++; 
				echo '<tr class="eqrow ' . $alt[++$rrc % 2] . '">';
				echo $estring; 
			}
		}
		if ($ecount == 0) { 
			echo '<tr class="eqrow ' . $alt[++$rrc % 2] . '"><td><p>';
			echo '<img src="icons/cancel.gif">&nbsp;Ingen varsling';
			echo '</td></tr>'; 
		}
		echo '</table>';

		echo "</td></tr>";
	}
	echo "</table>";
	
}

if ($subaction == 'settaktiv') {
	print "<p>" . gettext("Aktiv profil er endret.");
	$dbh->aktivProfil(session_get('uid'), $pid);
}



$brukerinfo = $dbh->brukerInfo( session_get('uid') );
$profiler = $dbh->listProfiler( session_get('uid'), 1);

if (get_exist('vis') )
	session_set('visoversikt', get_get('vis') );
	
if (get_exist('tview') )
	session_set('tview', get_get('tview') );	

if (session_get('visoversikt') == 0) {
	echo '<p style="text-align: right; font-size: small">[ <a href="index.php?vis=1">' . gettext("Vis mer info...") . '</a> ]</p>';
} else {
	echo '<p style="text-align: right; font-size: small">[ <a href="index.php?vis=0">' . gettext("Vis mindre info...") . '</a> ]</p>';
}





// Lag en dropdown meny for å velge aktiv profil
print '<form name="form1" method="post" action="index.php?action=oversikt&subaction=settaktiv">';

print 'Aktiv profil: <select name="pid" id="selectprof" onChange="this.form.submit()">';


if ($brukerinfo[4] < 1) { 
	echo '<option value="0">' . gettext("Velg varslingsprofil") . '</option>'; 
}
for ($i = 0; $i < sizeof($profiler); $i++) {
	print '<option value="' . $profiler[$i][0] . '" '; 
	if ($brukerinfo[4] == $profiler[$i][0]) print 'selected'; 
	print '>' . $profiler[$i][1] . '&nbsp;&nbsp;</option>';
}

if (sizeof($profiler) < 1) {
	print '<option value="0">' . gettext("Ingen profiler opprettet...") . '</option>';
}
print '</select>';

if ($brukerinfo[4] < 1) { 
	echo "<p>" . gettext("Ingen brukerprofil er aktiv. Aktiviser en profil ved å velge den fra menyen over."); 
}
print '</form>';



    
if ($brukerinfo[4] < 1) { 
		echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>' . gettext("Ingen brukerprofil er for øyeblikket aktiv. Det betyr at du ikke vil bli varslet om noen alarmer.") . '</td></tr></table>'; 
}
    
if (sizeof($profiler) < 1) {
	echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>' . gettext("Du har ikke opprettet noen profiler. Dermed vil du heller ikke få noe varsling. Gå til menyvalget Profiler i venstremargen og opprett en ny profil der.") . '</td></tr></table>'; 
}
    
    
/*
 * TIMEPLAN OVERSIKT OVER AKTIV PROFIL
 
<li style="margin: 1px; list-style-image: url(http://jimmac.musichall.cz/ikony/i12/appointment-reminder.png)"> 
 <li style="border: thin solid black; background: #ebb; margin: 1px;
		list-style-image: url(http://jimmac.musichall.cz/ikony/i12/appointment-reminder-excl.png)">
		echo '<li style="list-style-image: url(http://jimmac.musichall.cz/ikony/i5/16_ethernet.png)">';		
				echo '<li style="list-style-image: url(http://jimmac.musichall.cz/ikony/i43/stock_jump-to-16.png)">';		
 */

//echo '<div style="border: thin #999 solid; margin: 2px; padding: 2px; background: ddd">';

if ($brukerinfo[4] > 0) {
	if (session_get('tview') == 2) {
		echo '<p style="font-size: small">Vis timeplan for [ <a href="?tview=1">ukedag og helg</a> | hele uken samlet ]';
		echo "<h3>Timeplan hele uken</h3>";
		showTimeTable($dbh, $brukerinfo, array(1,2,3) );
	} else {
		echo '<p style="font-size: small">Vis timeplan for [ ukedag og helg | <a href="?tview=2">hele uken samlet</a> ]';
		echo "<h3>Timeplan Mandag - Fredag</h3>";

		showTimeTable($dbh, $brukerinfo, array(1,2) );
		
		echo "<h3>Timeplan Lørdag - Søndag</h3>";
		showTimeTable($dbh, $brukerinfo, array(1,3) );
	}
}







if (session_get('visoversikt') == 1) {
    
    print '<p>&nbsp;';
    
    print '<table width="100%"><tr width="30%" valign="top"><td>';
    print '<h3>' . gettext('Kontotype') . '</h3>';
    
    switch (session_get('admin') ) {
            case (100) :
                    print '<p><img alt="'. gettext('Administrator') . '" src="icons/person100.gif">&nbsp;';
                    print gettext('Administrator');
                    break;
            case (1) :
                    print '<p><img alt="' . gettext('Vanlig bruker') . '" src="icons/person1.gif">&nbsp;';
                    print gettext('Vanlig bruker');
                    break;
            default: 
                    print "<p>" . gettext("Ukjent administrator nivå.");
    }
    
    print '</td><td width="70%" valign="top">';
    print '<h3>' . gettext("Tilgang til SMS") . '</h3>';
    
    if ($brukerinfo[3] == 't') {
            print '<p><img alt="' . gettext('Ja') . '" src="icons/ok.gif">&nbsp;';
            print gettext('Ja, du har tilgang til å sette opp SMS alarmer.');
    } else {
            print '<p><img alt="Nei" src="icons/cancel.gif">&nbsp;';
            print gettext('Nei, du har ikke lov til å sette opp SMS alarmer.');
    }
    
    print '</td></tr></table>';
    #print '<p>&nbsp;';
    
    print '<table width="100%"><tr>';
    print '<td width="50%" valign="top" class="oversikt">';
    
    print '<h2>' . gettext("Brukergrupper") . '</h2>';
    
    $grupper = $dbh->listBrukersGrupper(session_get('uid'), 1);
    
            
    for ($i = 0; $i < sizeof($grupper); $i++) {
            print '<p class=nop><img src="icons/gruppe.gif"><b>' . $grupper[$i][1] . '</b></p>';
            print '<p class="descr">' . $grupper[$i][2]. '</p>';
    }
    
    if (sizeof($grupper) < 1) {
            print gettext('<p>Du er <b>ikke</b> medlem av noen brukergrupper.');
    } else {
            print gettext('<p>Du er medlem av ') . sizeof($grupper) . gettext(' brukergrupper.');
    }
    
    print '</td><td width="50%" valign="top" class="oversikt">';
    
    print '<h2>' . gettext("Rettigheter") . '</h2>';
    $grupper = $dbh->listUtstyrRettighet(session_get('uid'), 1);
    
            
    for ($i = 0; $i < sizeof($grupper); $i++) {
            print '<p class="nop"><img src="icons/chip.gif"><b>' . $grupper[$i][1] . '</b></p>';
            print '<p class="descr">' . $grupper[$i][2]. '</p>';
    }
    
    if (sizeof($grupper) < 1) {
            print gettext('<p>Du har <b>ikke</b> rettighet til noen utstyrsgrupper.');
    } else {
            print gettext('<p>Du har rettighet til ') . sizeof($grupper) . gettext(' utstyrsgrupper.');
    }
    
    print '</td></tr></table>';
    



    
}
?>
</td></tr>
</table>
