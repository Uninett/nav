<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('Mine adresser'); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>";
echo gettext("Her kan du administrere dine varlingsadresser.");

if (in_array(get_get('subaction'), array('ny', 'endre') )) {


	print '<a name="nyadresse"></a><div class="newelement">';
	
	if (get_get('subaction') == 'endre') {
		print '<h2>' . gettext("Endre adresse") . '</h2>';
	} else {
		print '<h2>' . gettext("Legg til ny adresse") . '</h2>';
	}
	
	echo '<form name="form1" method="post" action="index.php?subaction=';
	if ($subaction == 'endre') echo "endret"; else echo "nyadresse";
	echo '">';
	
	if (get_get('subaction') == 'endre') {
		print '<input type="hidden" name="aid" value="' . $aid . '">';
	}
	
	echo '
	  <table width="100%" border="0" cellspacing="0" cellpadding="3">
	    <tr>
	      <td width="30%">' .  gettext("Adressetype") . '</td>
	      <td width="70%">
	      	<select name="adressetype" id="selectadr">';
	      	
	$tsel = 1;
	if (get_get('subaction') == 'endre') {
		$tsel = $oldtype;
	} else {
		$adresse = '';
	}
	
	print '<option value="1" '; if ($tsel == 1) print 'selected'; print '>' . gettext("E-post") . '</option>';
	print '<option value="2" '; if ($tsel == 2) print 'selected'; print '>' . gettext("SMS") . '</option>';
//	print '<option value="3" '; if ($tsel == 3) print 'selected'; print '>' . gettext("IRC") . '</option>';
//	print '<option value="4" '; if ($tsel == 4) print 'selected'; print '>' . gettext("ICQ") . '</option>';
	
	echo '
			</select>
	      </td>
	    </tr>';
	    
	echo '
	    <tr>
	      <td valign="top">' .  gettext("Adresse") . '</td>
	      <td>
	      <input name="adresse" type="text" size="50" value="' .  $adresse . '">
	      <p>' . gettext("Kan være f.eks:") . '<br>
	      mail: <i>bruker@uninett.no</i><br>
	      sms: <i>99372612</i>
	      </td>
	    </tr>';
	
	
	echo '<tr>
	      <td align="right" colspan="2"><input type="submit" name="Submit" value="';
	if ($subaction == 'endre') echo gettext("Lagre endringer"); 
		else echo gettext("Legg til ny adresse");
	echo '"></td>
	    </tr></table></form></div>';


} else {
	echo '<p><a href="?subaction=ny">';
	echo " " . gettext("Legg til ny adresse"); 
	echo "</a>";

}

if (get_get('subaction') == 'endret') {


	if (post_get('aid') > 0) { 
            if (!$dbh->permissionAddress( session_get('uid'), post_get('aid') ) ) {
                echo "<h2>Security violation</h2>";
                exit(0);
            }
	
		$aid = $dbh->endreAdresse(post_get('aid'), post_get('adressetype'), post_get('adresse') );
		$adresse=0;
		print "<p><font size=\"+3\">" . gettext("OK</font>, adressen er endret.");

	} else {
		print "<p><font size=\"+3\">" . gettext("Feil</font> oppstod, adressen er <b>ikke</b> endret.");
	}


  
}

if (get_get('subaction') == 'slett') {

	
	if (get_get('aid') > 0) { 
            if (!$dbh->permissionAddress( session_get('uid'), get_get('aid') ) ) {
                echo "<h2>Security violation</h2>";
                exit(0);
            }
            	
		$dbh->slettAdresse(get_get('aid') );
		$adresse='';
		print "<p><font size=\"+3\">" . gettext("OK</font>, adressen er slettet fra databasen.");

	} else {
		print "<p><font size=\"+3\">" . gettext("Feil</font>, adressen er <b>ikke</b> slettet.");
	}

  
}

if (get_get('subaction') == 'nyadresse') {
	$aid = $dbh->nyAdresse(post_get('adresse'), post_get('adressetype'), session_get('uid') );
	
  if ($aid > 0) { 
    $adresse=0;
    
    print "<p><font size=\"+3\">" . gettext("OK</font>, ny adresse er lagt til i databasen.");

  } else {
    print "<p><font size=\"+3\">" . gettext("Feil</font>, ny bruker er <b>ikke</b> lagt til i databasen.");
  }


  
}

print "<h3>" . gettext("Mine adresser") . "</h3>";

//	function Lister($id, $labels, $c, $align, $isorts, $defaultsort) {
$l = new Lister( 101,
		array(gettext('Type'), gettext('Adresse'), gettext('Valg..') ),
		array(20, 60, 20),
		array('left', 'left', 'right'),
		array(true, true, false),
		0 
);

if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );

$adr = $dbh->listAdresser(session_get('uid'), $l->getSort() );

for ($i = 0; $i < sizeof($adr); $i++) {


	switch($adr[$i][2]) {
		case 1 : $type = '<img alt="mail" src="icons/mail.gif" border=0>&nbsp;' . gettext("E-post"); break;
		case 2 : $type = '<img alt="sms" src="icons/mobil.gif" border=0>&nbsp;' . gettext("SMS"); break;
		case 3 : $type = '<img alt="irc" src="icons/irc.gif" border=0>&nbsp;' . gettext("IRC"); break;
		case 4 : $type = '<img alt="icq" src="icons/icq.gif" border=0>&nbsp;' . gettext("ICQ"); break;				
		default : $type = '<img alt="ukjent" src="" border=0>&nbsp;' . gettext("Ukjent"); break;				
	}

  $valg = '<a href="index.php?action=' . $action . '&subaction=endre&aid=' . $adr[$i][0] . 
  		'&oldtype=' . $adr[$i][2] . '&adresse=' . $adr[$i][1] . '#nyadresse">' . 
  		'<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;' .
  		'<a href="index.php?action=' . $action . '&subaction=slett&aid=' . $adr[$i][0] .'">' . 
  		'<img alt="Delete" src="icons/delete.gif" border=0></a>';

  $l->addElement( array($type,  // type
  						$adr[$i][1],  // adresse
						$valg) 
				);
}

print $l->getHTML();

print "<p>[ <a href=\"index.php?action=" . $action. "\">" . gettext("oppdater") . " <img src=\"icons/refresh.gif\" alt=\"oppdater\" border=\"0\"> ]</a> ";
print gettext("Antall adresser: ") . sizeof($adr);

?>

</td></tr>
</table>
