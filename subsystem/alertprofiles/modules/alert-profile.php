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
<p><?php echo gettext("My alert profiles"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo '<p>' . gettext("Here you can create and setup alert profiles.");
echo '<p>' . gettext('Typically each profile is for an intended work mode. Examples are: "at 
work", "on vacation", "at 24hour duty", etc. You may define as many 
profiles as you like and you can easily swap to reselect your active 
profile.');
echo '<p>' . gettext('A profile consist of a set of time periods. Open a profile to edit the 
time periods and its definitions.');

$dagnavn[0] = gettext("Monday");
$dagnavn[1] = gettext("Tuesday");
$dagnavn[2] = gettext("Wedenesday");
$dagnavn[3] = gettext("Thursday");
$dagnavn[4] = gettext("Friday");
$dagnavn[5] = gettext("Saturday");
$dagnavn[6] = gettext("Sunday");

if (in_array(get_get('subaction'), array('ny', 'endre') )) {
	
	
	print '<a name="nyadresse"></a><div class="newelement">';
	
	if ($subaction == 'endre') {
		print '<h2>' . gettext("Rename profile") . '</h2>';
	} else {
		print '<h2>' . gettext("Add new profile") . '</h2>';
	}
	
	
	echo '<form name="form1" method="post" action="index.php?action=profil&subaction=';
	if ($subaction == 'endre') echo "endret"; else echo "nyprofil";
	echo '">';
	if ($subaction == 'endre') {
		print '<input type="hidden" name="pid" value="' . $pid . '">';
	}

	echo '
	  <table width="100%" border="0" cellspacing="0" cellpadding="3">
	    <tr>';
	
	if (get_get('subaction') == "endre")  {
		$p = $dbh->brukerprofilInfo($pid);
		
		$navn = $p[0];
		$ukedag = $p[1];
		$uketidh = $p[2];
		$uketidm = $p[3];
		$tidh = leading_zero($p[4], 2);
		$tidm = leading_zero($p[5], 2);
	} else {
		$navn = "";
		$ukedag = 0;
		$uketidh = "09";
		$uketidm = "00";
		$tidh = "07";
		$tidm = "30";
	}
	

	
    echo '<td><p>' . gettext("Name") . '</p></td>
	      <td><input name="navn" type="text" size="40" value="';
	echo $navn;
	echo '"></td>';
	echo '<td align="right"><input type="submit" name="Submit" value="';

	if ($subaction == 'endre') 
		echo gettext("Save changes"); else 
		echo gettext("Add new profile");
	echo '"></td>
	    </tr>
		<tr>';

	echo "<td>";
	echo gettext("Weekly alerts");
	echo "</td>";
	
	echo '<td><select name="ukedag">';
	
	for ($i = 0; $i < 7; $i++) {
		print '<option value="' . $i . '"';
		if ($i == $ukedag) print " selected";
		print '>' . $dagnavn[$i];
	}
											
	echo '</select>
			<input name="uketidh" type="text" value="' .  $uketidh . '" size="2">&nbsp;:&nbsp;
			<input name="uketidm" type="text" value="' .  $uketidm . '" size="2">
			</td>
		</tr>';
		
	echo '<tr><td>' .  gettext("Daily alerts") . '</td>
			<td><input name="tidh" type="text" value="' .  $tidh . '" size="2">&nbsp;:&nbsp;
				<input name="tidm" type="text" value="' .  $tidm . '" size="2">
			</td>
		</tr></table></form></div>';


} else {
	echo '<p><a href="?subaction=ny">';
	echo gettext("Add new profile"); 
	echo "</a>";
}



if (get_get('subaction') == 'settaktiv') {
	$dbh->aktivProfil(session_get('uid'), get_get('pid') );
        if (get_get('pid') > 0) {
            echo "<p><font size=\"+3\">" . gettext('Activated</font>. You have now selected active profile.');
        } else {
            echo "<p><font size=\"+3\">" . gettext('Deactivated</font>. You have now <b>no</b> active profiles.');
        }
}

if (get_get('subaction') == 'endret') {

	if ($pid > 0) { 
	
            if (!$dbh->permissionProfile( session_get('uid'), $pid ) ) {
                echo "<h2>Security violation</h2>";
                exit(0);
            }        
        
        
		$dbh->endreProfil($pid, post_get('navn'), post_get('ukedag'), 
			post_get('uketidh'), post_get('uketidm'), post_get('tidh'), post_get('tidm') );
		$navn='';

		print "<p><font size=\"+3\">" . gettext("OK</font>, profile is renamed.");

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the profile is <b>not</b> changed.");
	}
}

if (get_get('subaction') == 'slett') {
	if ($pid > 0) {
        
            if (!$dbh->permissionProfile( session_get('uid'), $pid ) ) {
                echo "<h2>Security violation</h2>";
                exit(0);
            }         
        
		$foo = $dbh->slettProfil($pid);
		$navn = '';
		
		print "<p><font size=\"+3\">" . gettext("OK</font>, the profile is removed.");
	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the profile is <b>not</b> removed.");
	}
}


if (get_get('subaction') == "nyprofil") {
  print "<h3>" . gettext("Registering new profile...") . "</h3>";
  
	
	$navn = "";
  if (post_get('navn') == "") $navn = gettext("No name"); else $navn = post_get('navn');

  if (session_get('uid') > 0) { 
    
    $profilid = $dbh->nyProfil(post_get('navn'), session_get('uid'), post_get('ukedag'),
    	post_get('uketidh'), post_get('uketidm'), post_get('tidh'), post_get('tidm') );
    $tidsid = $dbh->nyTidsperiode(1, '08:00', $profilid);
    
    print "<p><font size=\"+3\">" . gettext("OK</font>, a new profile is created for user " . session_get('bruker') . ". The profile ID is $profilid. The profile has only one time period, from 08:00 to 08:00 all days.");    
  } else {
    print "<p><font size=\"+3\">" . gettext("An errror</font> occured, a new profile is <b>not</b> created.");
  }


}

$l = new Lister( 106,
	array(gettext('Active'), gettext('Name'), gettext('#periods'), gettext('Options..')),
	array(10, 50, 25, 10),
	array('left', 'left', 'left', 'left'),
	array(true, true, true, false),
	1);

//print "<h3>" . gettext("My profiles") . "</h3>";
print "<p>";

if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );

$profiler = $dbh->listProfiler(session_get('uid'), $l->getSort() );

for ($i = 0; $i < sizeof($profiler); $i++) {

  if ($profiler[$i][3] == 't') {
    $aktiv = "<img alt=\"Aktiv\" src=\"icons/selecton.png\">";
  } else {
    $aktiv = "<a href=\"index.php?action=profil&subaction=settaktiv&pid=". $profiler[$i][0] .
      "\"><img alt=\"Aktiv\" src=\"icons/selectoff.png\" border=0></a>";
  }
  $valg = '<a href="index.php?action=periode&pid=' . $profiler[$i][0] . 
    '"><img alt="Open" src="icons/open2.gif" border=0></A>&nbsp;' .
    '<a href="index.php?action=profil&subaction=endre&pid=' . 
    $profiler[$i][0] . '&navn=' . $profiler[$i][1] . '#nyprofil">' . 
    '<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;' .
    '<a href="index.php?action=profil&subaction=slett&pid=' . 
    $profiler[$i][0] . '">' . 
    '<img alt="Delete" src="icons/delete.gif" border=0></a>';

        $l->addElement( array($aktiv,
                        $profiler[$i][1],  // brukernavn
                        $profiler[$i][2],  // navn
                        $valg
                )
        );

}

print $l->getHTML();

print '<p>[ <a href="index.php?action=profil&subaction=settaktiv&pid=0">' . gettext("Deactivate active profile") . '</a> | ' .  
    "<a href=\"index.php?action=profil\">" . gettext('update') . " <img src=\"icons/refresh.gif\" class=\"refresh\" alt=\"oppdater\" border=0></a> ] ";
print gettext("Number of profiles: ") . sizeof($profiler);


?>

</td></tr>
</table>
