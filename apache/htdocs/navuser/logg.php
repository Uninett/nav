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
	$tid =   htmlentities (strftime ("%H:%M, %a %e %b %y", $logg[$i][2] ) );
	$navn = $logg[$i][3];

	$hikon[1] = 'in.gif';
	$hikon[2] = 'out.gif';
	$hikon[3] = 'logg_new.gif';
	$hikon[4] = 'logg_del.gif';
	$hikon[5] = 'logg_edit.gif';
	$hikon[6] = 'logg_new.gif';
	$hikon[7] = 'logg_del.gif';
	$hikon[8] = 'logg_edit.gif';

	$hi = '<img alt="Hendelse" src="icons/' . $hikon[$type] . '">';


  $l->addElement( array($hi, $navn, $tid,  $descr
			) 
		  );
}

print $l->getHTML(1);

print "<p>[ <a href=\"index.php\">Refresh <img src=\"icons/refresh.gif\" alt=\"Refresh\" border=0> ]</a> ";
print "Antall viste hendelser: " . sizeof($logg);


?>


</td></tr>
</table>
