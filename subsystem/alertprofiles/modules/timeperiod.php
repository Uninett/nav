<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<?php
echo '<p>Setup profile</p>';


if (get_get('subaction')) {
	session_set('subaction', get_get('subaction') );
}

if (get_get('pid')) {
	session_set('periode_pid', get_get('pid'));
}
//print "<p>Pid now: " . session_get('periode_pid');

if (get_get('tid')) {
	session_set('periode_tid', get_get('tid'));
}
//print "<p>Tid now: " . session_get('periode_tid');


$utstginfo = $dbh->brukerprofilInfo(session_get('periode_pid') );
echo '<div class="subheader">' . $utstginfo[0] . '</div>';

?>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo '<p>';
echo gettext("To add a new time period, you have to click on the time you want the time period to start (on the time table below).");


if (!$dbh->permissionProfile( session_get('uid'), session_get('periode_pid') ) ) {
    echo "<h2>Security violation</h2>";
    exit(0);
} 

function helgdescr($helg) {
	switch($helg) {
		case 1 : return gettext('All week');
		case 2 : return gettext('Weekdays');
		case 3 : return gettext('Weekend');
		default: return gettext('Uknown');
	}
}


if (session_get('subaction') == 'slett' ) {

	if (session_get('periode_pid') > 0) { 
	
		$dbh->slettPeriode(session_get('periode_tid') );
		$adresse='';
		print "<p><font size=\"+3\">" . gettext("OK</font>, time period (") . session_get('periode_pid'). gettext(") is removed.");

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the time period is <b>not</b> removed.");
	}

	session_set('subaction', 'idle');
  
}


$konflikter = $dbh->listPeriodekonflikter(session_get('periode_pid'));
if (sizeof($konflikter) > 0) {
    $kl = new Lister (423,
                array('Dagtype', 'Tid', 'Antall kolliderende tidsperioder'),
                array(30, 20, 50),
                array('left', 'left', 'left'),
                array(false, false, false),
                0
    );
    for ($i = 0; $i < sizeof($konflikter); $i++) {
        $kl->addElement( array($konflikter[$i][1],$konflikter[$i][2],$konflikter[$i][0])  );
    }
    echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>';
    echo '<h2>' . gettext("Conflicts") . '</h2>';
    echo '<p>' . gettext("You have setup two or more time periods in which starts at the same time. Remove or change some of the time periods causing the conflict and this warning will go away.");
    echo '<p>' . gettext("Here is a list of occuring conflicts:");

    echo $kl->getHTML();

    echo  '</td></tr></table>'; 

}




// dette er for hverdager mandag til fredag
$l[0] = new Lister( 108,
		array(gettext('Time'), gettext('Weekday'), gettext('#addresses'), 
			gettext('#equip grp.'), gettext('Options..') ),
		array(20, 20, 20, 20, 20),
		array('right', 'center', 'right', 'right', 'right'),
		array(true, false, false, false, false),
		0
	);


// dette er tabellen for helga, lørdag og søndag
$l[1] = new Lister( 109,
		array(gettext('Time'), gettext('Weekday'), gettext('#addresses'), 
			gettext('#equip. grp.'), gettext('Options..') ),
		array(20, 20, 20, 20, 20),
		array('right', 'center', 'right', 'right', 'right'),
		array(true, false, false, false, false),
		0
	);

if ( get_exist('sortid') ) {
	$l[0]->setSort(get_get('sort'), get_get('sortid') );
	$l[1]->setSort(get_get('sort'), get_get('sortid') );	
}

$perioder = $dbh->listPerioder(session_get('periode_pid'), $l[0]->getSort() );

for ($i = 0; $i < sizeof($perioder); $i++) {
	
	if ($perioder[$i][2] > 9) $t = $perioder[$i][2]; else $t = "0" . $perioder[$i][2];
	if ($perioder[$i][3] > 9) $m = $perioder[$i][3]; else $m = "0" . $perioder[$i][3];
	$klokke = "$t:$m";
	$valg = '<a href="index.php?action=periode-setup&subaction=endre&tid=' . $perioder[$i][0] . 
		'"><img alt="Open" src="icons/open2.gif" border=0></a>&nbsp;' .
		'<a href="index.php?subaction=slett&tid=' . $perioder[$i][0] . '">' .
		'<img alt="Delete" src="icons/delete.gif" border=0></a>';
	
	if ($perioder[$i][4] > 0 ) 
		{ $aa = $perioder[$i][4]; }
	else 
		{ $aa = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; }
	
	if ($perioder[$i][5] > 0 ) 
		{ $au = $perioder[$i][5]; }
	else 
		{ $au = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; }
	
	// mangdag til fredag
	if (($perioder[$i][1] == 1) OR ($perioder[$i][1] == 2)) {
		$l[0]->addElement( array($klokke,
			helgdescr($perioder[$i][1] ),
			$aa,  // # adresser
			$au,  // # utstyrsgrupper
			$valg
			) 
		);
		$kt[0][] = array($perioder[$i][2], $perioder[$i][3]);
	}
	
	// lørdag og søndag
	if (($perioder[$i][1] == 1) OR ($perioder[$i][1] == 3)) {
		$l[1]->addElement( array($klokke,
				helgdescr($perioder[$i][1] ),    
				 $aa,  // # adresser
				 $au,  // # utstyrsgrupper
				 $valg
				) 
	   );
		$kt[1][] = array($perioder[$i][2], $perioder[$i][3]);
	}
}

print "<h3>" . gettext("Monday - Friday") . "</h3>";
print "<table width=\"100%\"><tr><td>\n";
print "<A HREF=\"index.php?action=periode-setup&subsaction=new&pid=$pid&coor1=\">\n";
print "<img border=\"0\" class=\"ilink\" title=\"Create new time period here\" alt=\"Timeplan Man-Fre\" src=\"timeplan.php?";
$c = 0;
foreach ($kt[0] as $el) {
     print "t[" . $c . "]=" . $kt[0][$c][0] . "&m[" . $c . "]=" . $kt[0][$c++][1] . "&";
}
print "\" ISMAP></A></td><td valign=\"top\">";
$tabell = $l[0]->getHTML();
echo $tabell;
print "</td></tr></table>";



print "<h3>" . gettext("Saturday and Sunday") . "</h3>";
print '<table width="100%"><tr><td>';
print "<A HREF=\"index.php?action=periode-setup&subaction=new&pid=$pid&coor2=\"><img border=\"0\" class=\"ilink\" alt=\"Timeplan Lør-Søn\" title=\"Create new time period here\" src=\"timeplan.php?";
$c = 0;
foreach ($kt[1] as $el) {
     print "t[" . $c . "]=" . $kt[1][$c][0] . "&m[" . $c . "]=" . $kt[1][$c++][1] . "&";
}
print '" ISMAP></A></td><td valign="top">';
print $l[1]->getHTML();
print '</td></tr></table>';

print "<p>[ <a href=\"index.php\">" . gettext("update") . "<img src=\"icons/refresh.gif\" class=\"refresh\" alt=\"oppdater\" border=\"0\"> ]</a> ";
print gettext("Number of periods: ") . sizeof($perioder);


echo '<p><form name="finnished" method="post" action="index.php?action=profil">';
echo '<input align="right" type="submit" name="Submit" value="' . gettext('Finished setting up profile') . '">';
echo '</form>';

?>

</td></tr>
</table>
