<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('My addresses'); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();

$brukernavn = session_get('bruker'); $uid = session_get('uid');

echo "<p>";
echo gettext("Here you can setup your alert addresses.");

if (in_array(get_get('subaction'), array('ny', 'endre') )) {


	print '<a name="nyadresse"></a><div class="newelement">';
	
	if (get_get('subaction') == 'endre') {
		print '<h2>' . gettext("Change address") . '</h2>';
	} else {
		print '<h2>' . gettext("Add new address") . '</h2>';
	}
	
	echo '<form name="form1" method="post" action="index.php?action=adress&subaction=';
	if ($subaction == 'endre') echo "endret"; else echo "nyadresse";
	echo '">';
	
	if (get_get('subaction') == 'endre') {
		print '<input type="hidden" name="aid" value="' . $aid . '">';
	}
	
	echo '
	  <table width="100%" border="0" cellspacing="0" cellpadding="3">
	    <tr>
	      <td width="30%">' .  gettext("Address type") . '</td>
	      <td width="70%">
	      	<select name="adressetype" id="selectadr">';
	      	
	$tsel = 1;
	if (get_get('subaction') == 'endre') {
		$tsel = $oldtype;
	} else {
		$adresse = '';
	}
	
	echo '<option value="1" '; if ($tsel == 1) echo 'selected'; echo '>' . gettext("E-mail") . '</option>';
	
	if (access_sms($brukernavn)) {
		echo '<option value="2" '; if ($tsel == 2) echo 'selected'; echo '>' . gettext("SMS") . '</option>';
	}
//	echo '<option value="3" '; if ($tsel == 3) echo 'selected'; echo '>' . gettext("IRC") . '</option>';
//	echo '<option value="4" '; if ($tsel == 4) echo 'selected'; echo '>' . gettext("ICQ") . '</option>';
	
	echo '
			</select>
	      </td>
	    </tr>';
	    
	echo '
	    <tr>
	      <td valign="top">' .  gettext("Address") . '</td>
	      <td>
	      <input name="adresse" type="text" size="50" value="' .  $adresse . '">
	      <p>' . gettext("Examples :") . '<br>
	      mail: <i>bruker@uninett.no</i><br>
	      sms: <i>99372612</i>
	      </td>
	    </tr>';
	
	
	echo '<tr>
	      <td align="right" colspan="2"><input type="submit" name="Submit" value="';
	if ($subaction == 'endre') echo gettext("Save changes"); 
		else echo gettext("Add new address");
	echo '"></td>
	    </tr></table></form></div>';


} else {
	echo '<p><a href="?subaction=ny">';
	echo " " . gettext("Add new address"); 
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
		echo "<p><font size=\"+3\">" . gettext("OK</font>, address is changed.");

	} else {
		echo "<p><font size=\"+3\">" . gettext("An error</font> occured, the address is  <b>not</b> changed.");
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
		echo "<p><font size=\"+3\">" . gettext("OK</font>, the address is removed from the database.");

	} else {
		echo "<p><font size=\"+3\">" . gettext("An error occured</font>, the address is <b>not</b> removed.");
	}

  
}

if (get_get('subaction') == 'nyadresse') {
	$nyadr = post_get('adresse');

	if ( post_get('adressetype') != 2 OR check_syntax_address_sms($nyadr)  ) {
		$aid = $dbh->nyAdresse($nyadr, post_get('adressetype'), session_get('uid') );
	} else {	
		$aid = 0;
	    echo "<p><font size=\"+3\">" . gettext("Invalid input syntax</font>. The mobile telephone number should be exactly eight numbers.");
	} 
if ($aid > 0) { 
	$adresse=0;
	
	echo "<p><font size=\"+3\">" . gettext("OK</font>, a new address is added to the database.");

} else {
	echo "<p><font size=\"+3\">" . gettext("An error occured</font>, a new user is <b>not</b> added to the database.");
}


  
}

echo "<h3>" . gettext("My addresses") . "</h3>";

//	function Lister($id, $labels, $c, $align, $isorts, $defaultsort) {
$l = new Lister( 101,
		array(gettext('Type'), gettext('Address'), gettext('Options..') ),
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
		case 1 : $type = '<img alt="mail" src="icons/mail.gif" border=0>&nbsp;' . gettext("E-mail"); break;
		case 2 : $type = '<img alt="sms" src="icons/mobil.gif" border=0>&nbsp;' . gettext("SMS"); break;
		case 3 : $type = '<img alt="irc" src="icons/irc.gif" border=0>&nbsp;' . gettext("IRC"); break;
		case 4 : $type = '<img alt="icq" src="icons/icq.gif" border=0>&nbsp;' . gettext("ICQ"); break;				
		default : $type = '<img alt="ukjent" src="" border=0>&nbsp;' . gettext("Unknown"); break;				
	}

  $valg = '<a href="index.php?action=' . best_get('action') . '&subaction=endre&aid=' . $adr[$i][0] . 
  		'&oldtype=' . $adr[$i][2] . '&adresse=' . $adr[$i][1] . '#nyadresse">' . 
  		'<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;' .
  		'<a href="index.php?action=' . best_get('action') . '&subaction=slett&aid=' . $adr[$i][0] .'">' . 
  		'<img alt="Delete" src="icons/delete.gif" border=0></a>';

  $l->addElement( array($type,  // type
  						$adr[$i][1],  // adresse
						$valg) 
				);
}

echo $l->getHTML();

echo "<p>[ <a href=\"index.php?action=" . best_get('action') . "\">" . gettext("update") . " <img src=\"icons/refresh.gif\" class=\"refresh\" alt=\"oppdater\" border=\"0\"> ]</a> ";
echo gettext("Number of addresses: ") . sizeof($adr);

?>

</td></tr>
</table>
