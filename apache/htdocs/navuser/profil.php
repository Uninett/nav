<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("Mine profiler"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>";
echo gettext("Her kan du endre og opprette nye profiler.");
echo '<p><a href="#nyprofil">';
echo gettext("Legg til ny profil"); 
echo "</a>";

if (get_get('subaction') == 'settaktiv') {
	$dbh->aktivProfil(session_get('uid'), get_get('pid') );
        if (get_get('pid') > 0) {
            echo "<p><font size=\"+3\">" . gettext('Aktivisert</font>. Du har nå byttet aktiv profil.');
        } else {
            echo "<p><font size=\"+3\">" . gettext('Deaktivert</font>. Du har nå ingen aktive profiler.');
        }
}

if (get_get('subaction') == 'endret') {

	if ($pid > 0) { 
	
		$dbh->endreProfil($pid, post_get('navn'), post_get('ukedag'), 
			post_get('uketidh'), post_get('uketidm'), post_get('tidh'), post_get('tidm') );
		$navn='';

		print "<p><font size=\"+3\">" . gettext("OK</font>, profilnavnet er endret.");

	} else {
		print "<p><font size=\"+3\">" . gettext("Feil</font> oppstod, profilen er <b>ikke</b> endret.");
	}
}

if (get_get('subaction') == 'slett') {
	if ($pid > 0) { 
		$foo = $dbh->slettProfil($pid);
		$navn = '';
		
		print "<p><font size=\"+3\">" . gettext("OK</font>, profilen er slettet fra databasen.");
	} else {
		print "<p><font size=\"+3\">" . gettext("Feil</font>, profilen er <b>ikke</b> slettet.");
	}
}


if (get_get('subaction') == "nyprofil") {
  print "<h3>" . gettext("Registrerer ny profil...") . "</h3>";
  
  $error = NULL;
	
	$navn = "";
  if (post_get('navn') == "") $navn = gettext("Uten navn"); else $navn = post_get('navn');

  if (session_get('uid') > 0) { 
    
    $profilid = $dbh->nyProfil(post_get('navn'), session_get('uid'), post_get('ukedag'),
    	post_get('uketidh'), post_get('uketidm'), post_get('tidh'), post_get('tidm') );
    $tidsid = $dbh->nyTidsperiode(1, '08:00', $profilid);
    
    print "<p><font size=\"+3\">" . gettext("OK</font>, En ny profil er opprettet for brukeren " . session_get('bruker') . ", denne har id $profilid. Profilen har bare en tidsperiode, fra 08:00 til 08:00 alle dager.");
    
  } else {
    print "<p><font size=\"+3\">" . gettext("Feil</font>, ny profil er <b>ikke</b> lagt til i databasen.");
  }


}

$l = new Lister( 106,
	array(gettext('Aktiv'), gettext('Navn'), gettext('#perioder'), gettext('Valg..')),
	array(10, 50, 15, 25),
	array('left', 'left', 'right', 'right'),
	array(true, true, true, false),
	1);

print "<h3>" . gettext("Dine profiler") . "</h3>";

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
  if ($profiler[$i][4] == 't') { 
    $sms = '<img alt="' . gettext("Ja") . '" src="icons/ok.gif">';
  } else {
    $sms = '<img alt="' . gettext("Nei") . '" src="icons/cancel.png">';
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

print '<p>[ <a href="index.php?subaction=settaktiv&pid=0">' . gettext("Deaktiver aktiv profil") . '</a> | ' .  
    "<a href=\"index.php\">oppdater <img src=\"icons/refresh.gif\" alt=\"oppdater\" border=0></a> ] ";
print gettext("Antall profiler: ") . sizeof($profiler);

print '<a name="nyprofil"></a><p>';

if ($subaction == 'endre') {
	print '<h2>' . gettext("Endre navn på profil") . '</h2>';
} else {
	print '<h2>' . gettext("Legg til ny profil") . '</h2>';
}

?>

<form name="form1" method="post" action="index.php?action=profil&subaction=<?php
if ($subaction == 'endre') echo "endret"; else echo "nyprofil";
?>">
<?php
if ($subaction == 'endre') {
	print '<input type="hidden" name="pid" value="' . $pid . '">';

}
?>
  <table width="100%" border="0" cellspacing="0" cellpadding="3">


    <tr>
 
<?php   

if (get_get('subaction') == "endre")  {
	$p = $dbh->brukerprofilInfo($pid);
	
	$navn = $p[0];
	$ukedag = $p[1];
	$uketidh = $p[2];
	$uketidm = $p[3];
	$tidh = $p[4];
	$tidm = $p[5];
} else {
	$navn = "";
	$ukedag = 0;
	$uketidh = "09";
	$uketidm = "00";
	$tidh = "07";
	$tidm = "30";
}

$dagnavn[0] = gettext("Mandag");
$dagnavn[1] = gettext("Tirsdag");
$dagnavn[2] = gettext("Onsdag");
$dagnavn[3] = gettext("Torsdag");
$dagnavn[4] = gettext("Fredag");
$dagnavn[5] = gettext("Lørdag");
$dagnavn[6] = gettext("Søndag");

?>
    
      <td><p><?php echo gettext("Navn"); ?></p></td>
      <td><input name="navn" type="text" size="40" 
value="<?php echo $navn; ?>"></td>
      <td align="right"><input type="submit" name="Submit" value="<?php
if ($subaction == 'endre') echo gettext("Lagre endringer"); else 
	echo gettext("Legg til ny profil");
?>"></td>
    </tr>
	<tr>
<?php
echo "<td>";
echo gettext("Ukevarsling");
echo "</td>";

echo '<td><select name="ukedag">';

	for ($i = 0; $i < 7; $i++) {
		print '<option value="' . $i . '"';
		if ($i == $ukedag) print " selected";
		print '>' . $dagnavn[$i];
	}
										
?>
		</select>
		<input name="uketidh" type="text" value="<?php echo $uketidh; ?>" size="2">&nbsp;:&nbsp;
		<input name="uketidm" type="text" value="<?php echo $uketidm; ?>" size="2">
		</td>
	</tr>
	
	<tr>
<?php echo "<td>"; echo gettext("Dagvarsling") . "</td>"; ?>
		<td><input name="tidh" type="text" value="<?php echo $tidh; ?>" size="2">&nbsp;:&nbsp;
			<input name="tidm" type="text" value="<?php echo $tidm; ?>" size="2">
		</td>
	</tr>	
	
  </table>

</form>


</td></tr>
</table>
