<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p>Hendelseslogg</p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();
?>

<p>Her er en liste over siste hendelser i NAVuser.

<?php


$brukernavn = session_get('bruker'); $uid = session_get('uid');

print "<h3>Loggdata</h3>";


if (get_get('subaction') == 1) {
	$dbh->nyLogghendelse($uid, 1, "Logg inn fra 129.241.103.4");
	print "<p>Hendelse registert....";
}

if (get_get('subaction') == 2) {
	$dbh->nyLogghendelse($uid, 2, "Logg ut fra 129.231.13.24");
	print "<p>Hendelse registert....";	
}


$l = new Lister( 223,
	array('Hendelse', 'Navn', 'Tid', 'Beskrivelse'),
	array(10, 20, 20, 50),
	array('left', 'left', 'left', 'left'),
	array(true, true, true, true ),
	1
);


if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );


$logg = $dbh->listLogg($l->getSort() );

/* Set locale to norwegian */
setlocale (LC_ALL, 'no_NO');


for ($i = 0; $i < sizeof($logg); $i++) {


	$type = $logg[$i][0];
	$descr = $logg[$i][1];		
	$tid = strftime ("%H:%M, %a %e %b %y", $logg[$i][2] );
	$navn = $logg[$i][3];


  if ($brukere[$i][4] == 't') { 
    $sms = '<img alt="Ja" src="icons/ok.gif">';
  } else {
    $sms = '<img alt="Nei" src="icons/cancel.gif">';
  }
  

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

  $l->addElement( array($type, $navn,  $tid, $descr
			) 
		  );
}

print $l->getHTML(1);

print "<p>[ <a href=\"index.php\">Refresh <img src=\"icons/refresh.gif\" alt=\"Refresh\" border=0> ]</a> ";
print "Antall viste hendelser: " . sizeof($logg);


?>


</td></tr>
</table>
