<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('My active profile'); ?></p>
</td></tr>

<tr><td>


<?php

session_set('lastaction', 'oversikt');
$brukernavn = session_get('bruker'); $uid = session_get('uid');

if (get_exist('vis') )
	session_set('visoversikt', get_get('vis') );

if (get_exist('tview') )
	session_set('tview', get_get('tview') );

function helgdescr($helg) {
	switch($helg) {
		case 1 : return gettext('All week');
		case 2 : return gettext('Mon-Fri');
		case 3 : return gettext('Sat-Sun');
		default: return gettext('Uknown');
	}
}


/*
 * the function easysetup() prints an easy form to create a default alert profile.
 *
 */
function easysetup($dbh) {

	# Check users addresses
	$adr = $dbh->listAdresser(session_get('uid'), 0);
	for ($i = 0; $i < sizeof($adr); $i++) {
		$atype[$adr[$i][2]]++;
	}
	echo '<p>
	<table width="100%">
		<tr><td>
			<img alt="Warning" align="top" src="images/warning.png">
		</td><td>' . gettext("You have not created any profiles. Consequently no profile is active, and no alerts will be sent. 
						You may use the initial setup for your first profile.");
	echo '</td></tr>';
	echo '<tr><td colspan="2">';
	
	echo '<div class="newelement"><h2>Easy setup your first alert profile</h2>';
	echo '<form method="post" action="index.php?action=oversikt&subaction=easysetup">';
	echo '<p>Enter a profile name: <input name="name" size="35" value="Standard">';
	echo '<br>Choose a default profile template:<br><select name="template">';
	echo '
		<option value="1">Empty profile, no time periods</option>	
		<option value="2">One timeperiod, all week</option>
		<option value="3" selected>Three timeperiods, workhours (8-16), evening and weekend</option>
		<option value="4">Five timeperiods, Weekdays (work,evening,night), Weekend (day,night)</option>

	';
	echo '</select>';
	if ($atype[1] < 1 or $atype[2] < 1) {
		echo '<h3>Add alert addresses to your account</h3>';
		if ($atype[1] < 1) {
			echo '<p><img alt="mail" src="icons/mail.gif" border=0>&nbsp;' . gettext("Email") . '&nbsp;';
			echo '<input name="address-1" size="30">';
		}
		if ($atype[2] < 1) {
			echo '<p><img alt="sms" src="icons/mobil.gif" border=0>&nbsp;' . gettext("SMS") . '&nbsp;';
			echo '<input name="address-2" size="8">';
		}

	}
	echo '<p><input type="submit" value="Create profile">';
	echo '</form></div></td></tr>	
	</table>'; 
	
}

if (isset($subaction) && $subaction == 'easysetup') {
	

	$profilid = $dbh->nyProfil(post_get('name'), session_get('uid'), 0, "09", "00", "07", "30" );

	switch(post_get('template') ) {
		case 2: 
			$tidsid = $dbh->nyTidsperiode(1, '08:00', $profilid);
		break;
		case 3:
			$tidsid = $dbh->nyTidsperiode(2, '08:00', $profilid);
			$tidsid = $dbh->nyTidsperiode(2, '16:00', $profilid);

			$tidsid = $dbh->nyTidsperiode(3, '09:00', $profilid);
		break;		
		case 4:
			$tidsid = $dbh->nyTidsperiode(2, '08:00', $profilid);
			$tidsid = $dbh->nyTidsperiode(2, '16:00', $profilid);
			$tidsid = $dbh->nyTidsperiode(2, '22:30', $profilid);

			$tidsid = $dbh->nyTidsperiode(3, '09:00', $profilid);
			$tidsid = $dbh->nyTidsperiode(3, '23:30', $profilid);
		break;
	}
	$dbh->aktivProfil(session_get('uid'), $profilid );
	
	if ( post_exist('address-1') ) {
		$dbh->nyAdresse(post_get('address-1'), 1, session_get('uid') );
		print "<p>Email address (" . post_get('address-1') . ') is added to your account.</p>';
	}
	if ( post_exist('address-2') ) {
		$dbh->nyAdresse(post_get('address-2'), 2, session_get('uid') );
		print "<p>Telephone number (" . post_get('address-2') . ') is added to your account.</p>';
	}
	
	print "<p><font size=\"+1\">" . gettext("Congratulations</font>, your first profile is successfully created.");

}


/*
 * the function eqgroupview() prints out a nice html table showing the requested 
 * filter group in i hiearchy, with all filters in detail.
 *
 */
 
function eqgroupviewsmall($dbh, $eqid) {

	$t = '<h3>Filter group composition</h3>';

	$filtre = $dbh->listFiltreGruppe($eqid, 0);
	$t .= '<table width="100%" border="0">';
	for ($i = 0; $i < sizeof($filtre); $i++) {

		/*
		$filtre[$row][0] = $data["id"]; 
		$filtre[$row][1] = $data["navn"];
		$filtre[$row][2] = $data["prioritet"];
		$filtre[$row][3] = $data["inkluder"];
		$filtre[$row][4] = $data["positiv"];		
		*/

		if ($filtre[$i][3] == 't') {
			if ($filtre[$i][4] == 't') {
				$inkicon = '<img src="icons/pluss.gif" border="0" alt="operator" style="margin-bottom: -5px">';
			} else {
				$inkicon = '<img src="icons/plussinverse.gif" border="0" alt="operator" style="margin-bottom: -5px">';		
			}  	
		} else {
			if ($filtre[$i][4] == 't') {
				$inkicon = '<img src="icons/minus.gif" border="0" alt="operator" style="margin-bottom: -5px">';
			} else {
				$inkicon = '<img src="icons/and.gif" border="0" alt="operator" style="margin-bottom: -5px">';		
			}
		}
	
		$t .= '<tr><td class="eqoel">' . $inkicon . '&nbsp;' . $filtre[$i][1] . '</td></tr>';

	}
	$t .= '</table>';
	return $t;
}


function showTimeTable($dbh, $brukerinfo, $listofhelg) {

	$t_per = $dbh->listPerioder($brukerinfo[4], 0);
	
	if (sizeof($t_per) < 1)  {
		echo '<p>No time periods. Please setup your profile.</p>';
		return 0;
	}

	echo '<table class="timetable" border="0" cellpadding="0" cellspacing="0">';
	echo '<tr class="header"><td class="clock">' . gettext('Time') . '</td><td class="helg">' . gettext('Weekday') . '</td>' .
		'<td class="eqg">' . gettext('Supervised filter groups') . '</td></tr>';

	$rc = 0;
	$alt[0] = 'even'; $alt[1] = 'odd';
	
	// Fetch all time periods for the weekend type requested, and stuff into new array
	foreach ($t_per AS $t_p) 
		if ( in_array($t_p[1], $listofhelg ) ) $actual_tp[] = $t_p;
	
	// Traverse all fetched time periods.
	for ($i = 0; $i < sizeof($actual_tp); $i++) {
		$t_p = $actual_tp[$i];
		$t_p['next'] = $actual_tp[ ($i + 1) % sizeof($actual_tp) ];

		if (! in_array($t_p[1], $listofhelg ) ) continue;

		if ($t_p[0] == 1068) { // active
			echo '<tr class="period active ' . $alt[++$rc % 2] . '">';
		} else {
			echo '<tr class="period ' . $alt[++$rc % 2] . '">';
		}

		echo '<td class="clock">';
		echo '<a class="tt" href="?action=periode-setup&amp;subaction=endre&amp;tid=' . $t_p[0] . '&amp;pid=' . $brukerinfo[4] . '#endre">';
		echo leading_zero($t_p[2],2) . ":" . leading_zero($t_p[3],2) . '</a><br>';
		echo '<img src="icons/clock.png"><br>' ;		
		echo '<span style="font-size:x-small">-' . leading_zero($t_p['next'][2],2) . ":" . leading_zero($t_p['next'][3], 2) . '</span>';

		echo "</td>";
			
		echo '<td class="helg">' . helgdescr($t_p[1]) . '</td>'; // <br><small>(' . $t_p[0] . ')</small>
		echo '<td class="eqg">';
		
		$t_utg = $dbh->listUtstyrPeriode(session_get('uid'), $t_p[0], 0);

		echo '<table class="eqgroup" border="0" cellpadding="0" cellspacing="0">';
		$rrc = 0; $ecount = 0;
		foreach ($t_utg AS $t_u) {
			$estring = '<td class="eqname"><div class="hoverelement eqid' . $t_u[0]  . '">';
			$estring .= '<div class="window">' . eqgroupviewsmall($dbh, $t_u[0] ) . '</div>';
			
			$estring .= '<img src="icons/equipment.png">&nbsp;';
			if ($t_u[4]) $estring .= '<a class="tt" href="?action=utstyrgrp&amp;gid=' . $t_u[0] . '">';
				else $estring .= '<a class="tt" href="?action=equipment-group-view&amp;gid=' . $t_u[0] . '">';
			$estring .= $t_u[1];
			$estring .= "</a>";
			
			$estring .= "</div></td>"; 
			$estring .= '<td class="eqaddress">';
			
			$p_adr = $dbh->listVarsleAdresser(session_get('uid'), $t_p[0], $t_u[0], 0);
			$estring .= '<ul>';
			$vcount = 0;
			if (is_array($p_adr)) {
				foreach ($p_adr AS $p_a) {
					if (!is_null($p_a[3]) ) {
						$vcount++;
						$vstr = '<a class="tt" href="?action=adress">' . $p_a[1] . '</a>';
						if ($p_a[3] == 0) {
							$estring .= '<li class="direct">' . $vstr . "</li>";
						} else if ($p_a[3] == 1) {
							$estring .= '<li class="queue">' . $vstr . " (" . gettext('Daily queue') . ")</li>";
						} else if ($p_a[3] == 2) {
							$estring .= '<li class="queue">' . $vstr . " (" . gettext('Weekly queue') . ")</li>";
						} else if ($p_a[3] == 3) {
							$estring .= '<li class="queue">' . $vstr . " (" . gettext('Queued until profile changes') . ")</li>";
						} else if ($p_a[3] == 4) {
							$estring .= '<li class="direct">' . $vstr . " (" . gettext('No alert') . ")</li>";
						} else {
							$estring .= '<li class="queue">' . $vstr . " (" . gettext('Uknown queue type') . ")</li>";
						}
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
			echo '<img src="icons/cancel.gif">&nbsp;' . gettext('No alert');
			echo '</td></tr>'; 
		}
		echo '</table>';

		echo "</td></tr>";
	}
	echo "</table>";
	
}

if (isset($subaction) && $subaction == 'settaktiv') {
	$dbh->aktivProfil(session_get('uid'), $pid);
}



$brukerinfo = $dbh->brukerInfo( session_get('uid') );
$profiler = $dbh->listProfiler( session_get('uid'), 1);
$grupperettighet = $dbh->listUtstyrRettighet(session_get('uid'), 1);

    
$acprofilename = "No active profile";


if (sizeof($grupperettighet) < 1) {
		echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>' . gettext("You do not have permission to <b>any</b> alerts. Please ask your administrator to setup your alert permissions.") . '</td></tr></table>'; 	
} elseif (sizeof($profiler) < 1) {
	easysetup($dbh);
} elseif ($brukerinfo[4] < 1) { 
		echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>' . gettext("No alert profile is active for the moment. That means no alerts will be sent.") . '</td></tr></table>'; 
} else {
	foreach ($profiler AS $p) {
		if ($brukerinfo[4] == $p[0]) {
			$acprofilename = $p[1];
			$acprofileid = $p[0];
		}
	}
}
    


if ($brukerinfo[4] > 0) {
	echo '<h1 style="margin-bottom: 0px;"><span style="border-bottom: thin solid #999 ">' . $acprofilename . '</span></h1>' .
	'<p style="margin-top: 1px; font-size: 0.7em; color: #999">Active profile</p>';
	if (session_get('tview') == 2) {
		echo '<p>' . gettext('Show timetable for') . ' [ <a href="?tview=1">' . gettext('weekdays and weekend separate') . '</a> | ' . gettext('the whole week together in one view') . ' ]';
		echo '<h3 style="margin-top: .6em; margin-bottom: 0px">' . gettext('Timetable whole week') . "</h3>";
		echo '<p style="margin-top: 0px; margin-bottom: 1em">[ <a href="index.php?action=periode&pid=' . $acprofileid . '">Edit timetable</a> ]</p>';		
		showTimeTable($dbh, $brukerinfo, array(1,2,3) );
	} else {
		echo '<p style="font-size: small">' . gettext('Show timetable for') . ' [ ' . gettext('weekdays and weekend separate') . ' | <a href="?tview=2">' . gettext('the whole week together in one view') . '</a> ]';
		echo '<h3 style="margin-top: .6em; margin-bottom: 0px">' . gettext('Timetable Monday to Friday') . "</h3>";
		echo '<p style="margin-top: 0px; margin-bottom: 1em">[ <a href="index.php?action=periode&pid=' . $acprofileid . '">Edit timetable</a> ]</p>';
		showTimeTable($dbh, $brukerinfo, array(1,2) );
		
		echo '<h3 style="margin-top: .6em; margin-bottom: 0px">' . gettext('Timetable Saturday and Sunday') . "</h3>";
		echo '<p style="margin-top: 0px; margin-bottom: 1em">[ <a href="index.php?action=periode&pid=' . $acprofileid . '">Edit timetable</a> ]</p>';		
		showTimeTable($dbh, $brukerinfo, array(1,3) );
	}
}




// Lag en dropdown meny for å velge aktiv profil
print '<div align="right"><form name="form1" method="post" action="index.php?action=oversikt&subaction=settaktiv"><p>';
print gettext('Change active profile') . ': <select name="pid" id="selectprof" onChange="this.form.submit()">';
if ($brukerinfo[4] < 1) { 
	echo '<option value="0">' . gettext("Choose alert profile") . '</option>'; 
}
for ($i = 0; $i < sizeof($profiler); $i++) {
	print '<option value="' . $profiler[$i][0] . '" '; 
	if ($brukerinfo[4] == $profiler[$i][0]) print 'selected'; 
	print '>' . $profiler[$i][1] . '&nbsp;&nbsp;</option>';
}

if (sizeof($profiler) < 1) {
	print '<option value="0">' . gettext("No profiles exists...") . '</option>';
}
print '</select>';

if ($brukerinfo[4] < 1) { 
	echo "<p>" . gettext("No alert profile is active. Activate a profile from the menu above."); 
}
if (isset($subaction) && $subaction == 'settaktiv') {
	print "<p>" . gettext("Active profile changed.");
}
print '</form></div>';



?>
</td></tr>
</table>
