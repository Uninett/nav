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



$l = new Lister( 223,
	array('Hendelse', 'Navn', 'Tid', 'Beskrivelse'),
	array(10, 20, 20, 50),
	array('left', 'left', 'left', 'left'),
	array(true, true, true, true ),
	2
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


  if ($type == 1) { 
    $hi = '<img alt="Inn" src="icons/in.gif">';
  } else if ($type == 2) {
    $hi = '<img alt="Out" src="icons/out.gif">';
  } else {
  	$hi = 'NA';
  }


  $l->addElement( array($hi, $navn,  $tid, $descr
			) 
		  );
}

print $l->getHTML(1);

print "<p>[ <a href=\"index.php\">Refresh <img src=\"icons/refresh.gif\" alt=\"Refresh\" border=0> ]</a> ";
print "Antall viste hendelser: " . sizeof($logg);


?>


</td></tr>
</table>
