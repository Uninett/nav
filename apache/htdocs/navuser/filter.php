<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('Utstyrsfiltre'); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>" . gettext("Et utstyrsfilter er et sett av filtermatch'er som utgjør en gruppe med betingelser for at et utstyr skal 
inkluderes i det aktuelle filteret. Man kan sette sammen mange utstyrsfiltre til en utstyrsgruppe. 
<p>Når du skal lage en varslingsprofil velger du blandt utstyrsgruppene dine for å definere hvilket utstyr 
du ønsker å overvåke."); 
echo '<p><a href="#nyttfilter">' . gettext("Legg til nytt filter") . '</A>';


session_set('lastaction', 'filter');
$brukernavn = session_get('bruker'); $uid = session_get('uid');

if ($subaction == 'endret') {

	if ($fid > 0) { 
	
		$dbh->endreFilter($fid, $navn);

		
		print "<p><font size=\"+3\">" . gettext("OK</font>, filternavnet er endret.");
		$navn='';

	} else {
		print "<p><font size=\"+3\">" . gettext("Feil</font> oppstod, filteret er <b>ikke</b> endret.");
	}

  
}

if ($subaction == 'slett') {

	if ($fid > 0) { 
	
		$foo = $dbh->slettFilter($fid);
		$navn = '';
		
		print "<p><font size=\"+3\">" . gettext("OK</font>, filteret er slettet fra databasen.");

	} else {
		print "<p><font size=\"+3\">" . gettext("Feil</font>, filteret er <b>ikke</b> slettet.");
	}

	// Viser feilmelding om det har oppstått en feil.
	if ( $error != NULL ) {
		print $error->getHTML();
		$error = NULL;
	}
  
}

if ($subaction == "nyttfilter") {
  print "<h3>" . gettext("Registrerer ny profil...") . "</h3>";
  
  $error = NULL;

  if ($navn == "") $navn = gettext("Uten navn");

  if ($uid > 0) { 
    
    $filterid = $dbh->nyttFilter($navn, $uid);
    
    print "<p><font size=\"+3\">" . gettext("OK</font>, et nytt filter er opprettet. Åpne filteret for å legge til betingelser og begrensninger.");
    
  } else {
    print "<p><font size=\"+3\">" . gettext("Feil</font>, ny profil er <b>ikke</b> lagt til i databasen.");
  }

  // Viser feilmelding om det har oppstÂtt en feil.
  if ( $error != NULL ) {
    print $error->getHTML();
    $error = NULL;
  }

}


$l = new Lister( 110,
		array(gettext('Navn'), gettext('#match'), gettext('#grupper'), gettext('Valg..') ),
		array(50, 15, 15, 20),
		array('left', 'right', 'right', 'right'),
		array(true, true, true, false),
		0
);

print "<h3>" .gettext("Dine utstyrsfiltre") . "</h3>";

if (! isset($sort) ) { $sort = 1; }
$filtre = $dbh->listFiltre($uid, $sort);

for ($i = 0; $i < sizeof($filtre); $i++) {

  $valg = '<a href="index.php?action=match&fid=' . $filtre[$i][0] . '">' . 
  	'<img alt="Open" src="icons/open2.gif" border=0></a>&nbsp;' .
  	'<a href="index.php?action=filter&subaction=endre&navn=' . $filtre[$i][1] . '&fid=' . $filtre[$i][0] . '#nyttfilter">' .
    '<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;' .
    '<a href="index.php?action=filter&subaction=slett&fid=' . $filtre[$i][0] . '">' .
    '<img alt="Delete" src="icons/delete.gif" border=0></a>';

  if ($filtre[$i][2] > 0 ) 
    { $am = $filtre[$i][2]; }
  else 
    {
      $am = "<img alt=\"Ingen\" src=\"icons/stop.gif\">";

    }

  if ($filtre[$i][3] > 0 ) 
    { $ag = $filtre[$i][3]; }
  else 
    { $ag = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; }


  $l->addElement( array($filtre[$i][1],  // navn
			$am, 
			$ag,
			$valg ) 
		  );
}

print $l->getHTML();

print "<p>[ <a href=\"index.php?action=" . $action. "\">" .gettext("oppdater") . " <img src=\"icons/refresh.gif\" alt=\"oppdater\" border=0> ]</a> ";
print gettext("Antall filtre: ") . sizeof($filtre);

print '<a name="nyttfilter"></a><p>';

if ($subaction == 'endre') {
	print '<h2>' .gettext("Endre navn på filter") . '</h2>';
} else {
	print '<h2>' .gettext("Legg til nytt filter") . '</h2>';
}

?>

<form name="form1" method="post" action="index.php?action=filter&subaction=<?php
if ($subaction == 'endre') echo "endret"; else echo "nyttfilter";
?>">
<?php
if ($subaction == 'endre') {
	print '<input type="hidden" name="fid" value="' . $fid . '">';
}
?>

  <table width="100%" border="0" cellspacing="0" cellpadding="3">
    <tr>
      <td width="30%"><p><?php echo gettext("Navn"); ?></p></td>
      <td width="70%"><input name="navn" type="text" size="40" 
value="<?php echo $navn; ?>"></td>
    </tr>

    <tr>
      <td>&nbsp;</td>
      <td align="right"><input type="submit" name="Submit" value="<?php
if ($subaction == 'endre') echo gettext("Lagre endringer"); else echo gettext("Legg til nytt filter");
?>"></td>
    </tr>
  </table>

</form>


</td></tr>
</table>
