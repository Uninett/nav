<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("Choose user groups"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>";
echo gettext("Here you can specify which user groups the specific user is member of. When a user is member of an user group, he gets permissions to all equipment the groups allow.");

echo "<p>";




if (get_exist('subaction')) 
	session_set('subaction', get_get('subaction'));

if (get_exist('vbuid')) 
	session_set('vbuid', get_get('vbuid'));

if (session_get('subaction') == "valgt") {


	reset ($HTTP_POST_VARS);
	while ( list($n, $val) = each ($HTTP_POST_VARS)) {
		if ( preg_match("/gvalg([0-9]+)/i", $n, $m) ) {
			$var = "gvelg" . $m[1];
			$dbh->endreBrukerTilGruppe(session_get('vbuid'), $m[1], isset(${$var}) );
		} 

	}

	print '<p>' . gettext("The user is not member of the chosen user groups.") . "<p>" . 
	gettext("Go to ") .  '<a href="index.php?action=admin">' . gettext("user administration") . '</a>.';	
}

if (session_get('subaction') == 'velge') {


	if ( session_get('vbuid') >0) {


		print "<h3>" . gettext("Choose user groups") . "</h3>";
	
		$l = new Lister( 299,
			array(gettext('User group'), gettext('#users'), gettext('#permissions'), 
				gettext('#std. eq.groups'), gettext('Options..')),
			array(45, 15, 15, 15, 10),
			array('left', 'center', 'center', 'center', 'right' ),
			array(true, true, true, true, false),
			0
		);

		if ( get_exist('sortid') )
			$l->setSort(get_get('sort'), get_get('sortid') );

		$grupper = $dbh->listBrukersGrupperAdv($l->getSort(),  session_get('vbuid') );

		for ($i = 0; $i < sizeof($grupper); $i++) {
    
			if ($grupper[$i][3] > 0 ) { 
				$ab = $grupper[$i][3]; 
			} else { 
				$ab = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; 
			}

			if ($grupper[$i][4] > 0 ) { 
				$ar = $grupper[$i][4]; 
			} else { 
				$ar = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; 
			}

			if ($grupper[$i][5] > 0 ) { 
				$ag = $grupper[$i][5]; 
			} else { 
				$ag = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; 
			}
		
			$r = "";
			if ($grupper[$i][6] == 't') 
				$r = " checked";
		
			$valg = '<input name="gvelg' . $grupper[$i][0] . '" type="checkbox" value="1"' . $r . '>' .
				'<input name="gvalg' . $grupper[$i][0] . '" value="1" type="hidden">';
		
			$l->addElement( array($grupper[$i][1],  // gruppenavn
				$ab,  // #brukere
				$ar, // #rettigheter
				$ag,  // #std grupper
				$valg
				) 
			);
		
			$inh = new HTMLCell("<p class=\"descr\">" . $grupper[$i][2] . "</p>");	  
			$l->addElement (&$inh);	
	
		}
	
	
?>

<form name="brukertilgruppe" method="post" action="index.php?subaction=valgt">	
<?php
	
		print $l->getHTML();
		print '<p align="right"><input type="submit" name="Submit" value="' . gettext("Add to the selected user groups") . '"></form>';

		print "<p>[ <a href=\"index.php\">" . gettext("update") . " <img src=\"icons/refresh.gif\" alt=\"oppdater\" border=0> ]</a> ";
		print gettext("Number of user groups: ") . sizeof($grupper);

	} else {
		print "<p>" . gettext("No user is chosen.");
	}

}
?>



</td></tr>
</table>
