<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p>Brukeradministrasjon</p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();
?>

<p>Her kan du endre og opprette nye brukere, og deres rettigheter.

<p><a href="#nybruker">Legg til ny bruker</a>

<p>
<?php

include("databaseHandler.php");
$dbh = new DBH($dbcon);



if (get_get('subaction') == 'endre') {
	session_set('endrebrukerid', get_get('cuid'));
}


if (get_get('subaction') == 'endret' ) {

	if (session_get('endrebrukerid') > 0) { 
		$dbh->endreBruker(session_get('endrebrukerid'), post_get('brukernavn'), post_get('navn'), 
			post_get('passord'), post_get('admin'), post_get('sms'), post_get('kolengde') );

		print "<p><font size=\"+3\">OK</font>, brukeren er endret.";

    	if (post_exist('epost')) {
    		$dbh->nyAdresse(post_get('epost'), 1, session_get('endrebrukerid') );
    		print " Og ny epostadresse er lagt til brukeren.";
   		}
    

	} else {
		print "<p><font size=\"+3\">Feil</font> oppstod, brukeren er <b>ikke</b> endret.";
	}
	
}

if (get_get('subaction') == "slett") {
	
	if (get_get('cuid') > 0) { 
	
		$dbh->slettBruker(get_get('cuid') );

		print "<p><font size=\"+3\">OK</font>, brukeren er slettet fra databasen.";

	} else {
		print "<p><font size=\"+3\">Feil</font>, brukeren er <b>ikke</b> slettet.";
	}


}

if (get_get('subaction') == "nybruker") {
  print "<h3>Registrerer ny bruker...</h3>";
  
  $error = NULL;
  
 
  
  $uid = $dbh->nyBruker(post_get('navn'), post_get('brukernavn'), post_get('passord'), 
  	post_get('admin'), post_get('sms'), post_get('kolengde'), &$error);

  if ($uid > 0) { 
    $navn = ""; $brukernavn = ""; $passord = ""; $admin = 1; $sms = 0;
    
    
 
    
    $profilid = $dbh->nyProfil('Standard', $uid, 0, 8, 0, 7,30 );
    $tidsid = $dbh->nyTidsperiode(1, '08:00', $profilid);
    
    $dbh->aktivProfil($nybruker, $profilid);
    if (isset($epost)) {
    	$dbh->nyAdresse(post_get('epost'), 1, $uid);
    }
    
    print "<p><font size=\"+3\">OK</font>, ny bruker med brukernavn $brukernavn er lagt til i databasen med brukerid $uid. En ny standard profil er opprettet for brukeren, denne har id $profilid. Profilen har bare en tidsperiode, fra 08:00 til 08:00 alle dager.";
	print '<p>Du vil ofte <a href="index.php?action=brukertilgruppe&subaction=velge&vbuid=' . $uid . '">melde brukeren opp i noen brukergrupper</a>.';

  } else {
    print "<p><font size=\"+3\">Feil</font>, ny bruker er <b>ikke</b> lagt til i databasen.";
  }


}

$l = new Lister( 102,
	array('Brukernavn', 'Navn', 'Admin', 'SMS', 'Kø','#prof', '#adr', 'Valg..'),
	array(15, 25, 10, 10, 5, 10, 10, 15),
	array('left', 'left', 'right', 'center', 'center', 'right', 'right', 'right'),
	array(true, true, true, true, true, true, true, false),
	1
);


print "<h3>Lokale brukere</h3>";


if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );


$brukere = $dbh->listbrukere($l->getSort() );

for ($i = 0; $i < sizeof($brukere); $i++) {

	if (get_get('subaction') == 'endre' AND session_get('endrebrukerid') == $brukere[$i][0]  ) {
		$brukernavn = $brukere[$i][1];
		$navn = $brukere[$i][2];
		$admin = $brukere[$i][3];		
		$csms = $brukere[$i][4];
		$kolengde = $brukere[$i][7];
	}

  if ($brukere[$i][4] == 't') { 
    $sms = '<img alt="Ja" src="icons/ok.gif">';
  } else {
    $sms = '<img alt="Nei" src="icons/cancel.gif">';
  }
  
  $valg = '<a href="index.php?action=brukertilgruppe&subaction=velge&vbuid=' . $brukere[$i][0] . '">' .
  	'<img alt="Velge grupper" src="icons/gruppe.gif" border=0></a>&nbsp;' .  	
  	'<a href="index.php?action=admin&subaction=endre&cuid=' . $brukere[$i][0] . '#nybruker">' . 
  	'<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;' .
    '<a href="index.php?action=admin&subaction=slett&cuid=' . $brukere[$i][0]. '">' .
    '<img alt="Delete" src="icons/delete.gif" border=0></a>';

  if ($brukere[$i][5] > 0 ) 
    { $pa = $brukere[$i][5]; }
  else 
    {
      $pa = "<img alt=\"Ingen\" src=\"icons/stop.gif\">";

    }

  if ($brukere[$i][6] > 0 ) 
    { $aa = $brukere[$i][6]; }
  else 
    { $aa = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; }

  switch ($brukere[$i][3]) {
  	case 0: $adm = "<img alt=\"Deaktivert\" src=\"icons/person0.gif\">";
  	break;
  	case 1: $adm = "<img alt=\"Standard\" src=\"icons/person1.gif\">";
  	break;
  	case 100: $adm = "<img alt=\"Admin\" src=\"icons/person100.gif\">";
  	break;
  	default: $adm = "<p>Ukjent";  	
  }

  $l->addElement( array($brukere[$i][1],  // brukernavn
			$brukere[$i][2],  // navn
			$adm, // admin
			$sms,  // sms
			$brukere[$i][7], // kølengde
			$pa, 
			$aa,
			$valg
			) 
		  );
}

print $l->getHTML(1);

print "<p>[ <a href=\"index.php?action=" . $action. "\">Refresh <img src=\"icons/refresh.gif\" alt=\"Refresh\" border=0> ]</a> ";
print "Antall brukere: " . sizeof($brukere);
?>
<a name="nybruker"></a><p><h3>
<?php
if (get_get('subaction') == 'endre') {
	echo "Endre brukerinfo";
} else {
	echo "Legg til ny bruker";
}
?></h3>
<form name="form1" method="post" action="index.php?action=admin&subaction=<?php
if (get_get('subaction') == 'endre') echo "endret"; else echo "nybruker";
?>">



  <table width="100%" border="0" cellspacing="0" cellpadding="3">
    <tr>
      <td width="30%"><p>Navn</p></td>
      <td width="70%"><input name="navn" type="text" size="40" 
value="<?php echo $navn; ?>"></td>
    </tr>
    <tr>
      <td>E-post</td>
      <td><input size="50" name="epost" type="text" 
value="<?php 
if ($subaction == 'endre') {
	echo $epost;
} else {
	echo "bruker@uninett.no";
} ?>"><?php
if (get_get('subaction') == 'endre') {
	echo '&nbsp;<b>Legg til ny epost?</b>';
}
?>
</td>
    </tr>    
    <tr>
      <td>Brukernavn</td>
      <td><input name="brukernavn" type="text" 
value="<?php echo $brukernavn; ?>"></td>
    </tr>

    <tr>
      <td>Passord </td>
      <td><input type="password" name="passord">
</td>
    </tr>
    <tr>
<?php
		
$ta[0] = ""; $ta[1] = ""; $ta[2] = ""; 
switch($admin) {
	case 0: $ta[0] = " selected"; break;
	case 100: $ta[2] = " selected"; break;
	default: $ta[1] = " selected";	
}
		
?>    
    
      <td>Administrator niv&aring;</td>
      <td align="center"><select name="admin" id="select">
          <option value="0"<?php echo $ta[0]; ?> >0 Konto avsl&aring;tt</option>
          <option value="1"<?php echo $ta[1]; ?> >1 Vanlig bruker</option>
          <option value="100"<?php echo $ta[2]; ?> >100 Administrator</option>
        </select></td>
    </tr>
    <tr>
    
<?php
		
$ta[0] = ""; $ta[1] = ""; $ta[2] = ""; $ta[3] = ""; $ta[4] = ""; 
switch($kolengde) {
	case 0: $ta[0] = " selected"; break;
	case 7: $ta[1] = " selected"; break;
	case 30: $ta[3] = " selected"; break;
	case 60: $ta[4] = " selected"; break;				
	default: $ta[2] = " selected";	
}
		
?>       

      <td>Maks alarmkølengde</td>
      <td align="center"><select name="kolengde" id="select">
          <option value="0"<?php echo $ta[0]; ?> >Ingen kø</option>
          <option value="7"<?php echo $ta[1]; ?> >En uke</option>
          <option value="14"<?php echo $ta[2]; ?> >To uker</option>          
          <option value="30"<?php echo $ta[3]; ?> >En måned</option>
          <option value="60"<?php echo $ta[4]; ?> >To måneder</option>          
        </select></td>
    </tr>    
    <tr>
      <td><input name="sms" type="checkbox" 
<?php 
	  if ($csms == 't') echo "checked";
?> value="1">Tilgang til SMS alarm</td>
      <td align="right"><input type="submit" name="Submit" 
<?php
if ($subaction == 'endre') {
	echo 'value="Lagre endringer"';
} else {
	echo 'value="Legg til bruker"';
}
?>
></td>
    </tr>
  </table>

</form>


</td></tr>
</table>
