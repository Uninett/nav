<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p>Mine adresser</p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();
?>

<p>Her kan du administrere dine varlingsadresser. 
<a href="#nyadresse">Legg til ny adresse</a>

<?php

if (get_get('subaction') == 'endret') {

	if (post_get('aid') > 0) { 
	
		$aid = $dbh->endreAdresse(post_get('aid'), post_get('adressetype'), post_get('adresse') );
		$adresse=0;
		print "<p><font size=\"+3\">OK</font>, adressen er endret.";

	} else {
		print "<p><font size=\"+3\">Feil</font> oppstod, adressen er <b>ikke</b> endret.";
	}


  
}

if (get_get('subaction') == 'slett') {

	
	if (get_get('aid') > 0) { 
	
		$dbh->slettAdresse(get_get('aid') );
		$adresse='';
		print "<p><font size=\"+3\">OK</font>, adressen er slettet fra databasen.";

	} else {
		print "<p><font size=\"+3\">Feil</font>, adressen er <b>ikke</b> slettet.";
	}

  
}

if (get_get('subaction') == 'nyadresse') {
	$aid = $dbh->nyAdresse(post_get('adresse'), post_get('adressetype'), session_get('uid') );
	
  if ($aid > 0) { 
    $adresse=0;
    
    print "<p><font size=\"+3\">OK</font>, ny adresse er lagt til i databasen.";

  } else {
    print "<p><font size=\"+3\">Feil</font>, ny bruker er <b>ikke</b> lagt til i databasen.";
  }


  
}

print "<h3>Mine adresser</h3>";

//	function Lister($id, $labels, $c, $align, $isorts, $defaultsort) {
$l = new Lister( 101,
		array('Type', 'Adresse', 'Valg..'),
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
		case 1 : $type = '<img alt="mail" src="icons/mail.gif" border=0>&nbsp;E-post'; break;
		case 2 : $type = '<img alt="sms" src="icons/mobil.gif" border=0>&nbsp;SMS'; break;
		case 3 : $type = '<img alt="irc" src="icons/irc.gif" border=0>&nbsp;IRC'; break;
		case 4 : $type = '<img alt="icq" src="icons/icq.gif" border=0>&nbsp;ICQ'; break;				
		default : $type = '<img alt="ukjent" src="" border=0>&nbsp;Ukjent'; break;				
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

print "<p>[ <a href=\"index.php?action=" . $action. "\">Refresh <img src=\"icons/refresh.gif\" alt=\"Refresh\" border=\"0\"> ]</a> ";
print "Antall adresser: " . sizeof($adr);

print '<a name="nyadresse"></a><p>';

if (get_get('subaction') == 'endre') {
	print '<h2>Endre adresse</h2>';
} else {
	print '<h2>Legg til ny adresse</h2>';
}

?>



<form name="form1" method="post" action="index.php?subaction=<?php
if ($subaction == 'endre') echo "endret"; else echo "nyadresse";
?>">

<?php
if (get_get('subaction') == 'endre') {
	print '<input type="hidden" name="aid" value="' . $aid . '">';
}
?>
  <table width="100%" border="0" cellspacing="0" cellpadding="3">
    <tr>
      <td width="30%">Adressetype</td>
      <td width="70%">
      	<select name="adressetype" id="selectadr">
<?php
$tsel = 1;
if (get_get('subaction') == 'endre') {
	$tsel = $oldtype;
} else {
	$adresse = '';
}

print '<option value="1" '; if ($tsel == 1) print 'selected'; print '>E-post</option>';
print '<option value="2" '; if ($tsel == 2) print 'selected'; print '>SMS</option>';
print '<option value="3" '; if ($tsel == 3) print 'selected'; print '>IRC</option>';
print '<option value="4" '; if ($tsel == 4) print 'selected'; print '>ICQ</option>';

?>
		</select>
      </td>
    </tr>
    
    
    <tr>
      <td valign="top">Adresse</td>
      <td>
      <input name="adresse" type="text" size="50" value="<?php echo $adresse; ?>">
      <p>Kan være f.eks:<br>
      epost: <i>bruker@uninett.no</i><br>
      sms: <i>99372612</i><br>
      irc: <i>nick@irc.homelien.no</i><br>
      icq: <i>123456789</i>
      </td>
    </tr>


    <tr>
      <td align="right" colspan="2"><input type="submit" name="Submit" value="<?php
if ($subaction == 'endre') echo "Lagre endringer"; else echo "Legg til ny adresse";
?>"></td>
    </tr>
    
    
  </table>

</form>


</td></tr>
</table>
