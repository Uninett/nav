<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("Public equipment filters"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>" . gettext("Public equipment filters is shared among administrators, and is used to create public equipment groups connected to user groups.");

echo '<p><a href="?subaction=ny">'; 
echo gettext("Add a new filter") . "</A>";


session_set('lastaction', 'ffilter');
$brukernavn = session_get('bruker'); $uid = session_get('uid');




if (in_array(get_get('subaction'), array('ny', 'endre') )) {


	print '<a name="ny"></a><div class="newelement">';
	
	if ($subaction == 'endre') {
		print '<h2>' .gettext("Rename filter") . '</h2>';
	} else {
		print '<h2>' .gettext("Add a new filter") . '</h2>';
	}
	

	
	echo '<form name="form1" method="post" action="index.php?action=ffilter&subaction=';

	if ($subaction == 'endre') echo "endret"; else echo "nyttfilter";
	echo '">';

	if ($subaction == 'endre') {
		print '<input type="hidden" name="fid" value="' . $fid . '">';
	}

	
	echo '<table width="100%" border="0" cellspacing="0" cellpadding="3">
	    <tr>
	      <td width="30%"><p>' . gettext("Name") . '</p></td>
	      <td width="70%"><input name="navn" type="text" size="40" 
	value="' .  $navn . '"></td>
	    </tr>';
	
	echo '<tr>
	      <td>&nbsp;</td>
	      <td align="right"><input type="submit" name="Submit" value="';

	if ($subaction == 'endre') echo gettext("Save changes"); else echo gettext("Add a new filter");
	echo '"></td>
	    </tr>
	  </table>
	</form></div>';


}



if ($subaction == 'endret') {

	if ($fid > 0) { 
	
		$dbh->endreFilter($fid, $navn);
		$dbh->nyLogghendelse($uid, 8, gettext("Name changed on public equipment filter") . " (" . $navn . ")");
		
		print "<p><font size=\"+3\">" . gettext(" OK</font>, filter name is changed.");
		$navn='';

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the filter is <b>not</b> changed.");
	}

  
}

if ($subaction == 'slett') {

	if ($fid > 0) { 
	
		$foo = $dbh->slettFilter($fid);
		$dbh->nyLogghendelse($uid, 7, gettext("Public equipment filter is removed") . " (id=" . $fid . ")");		
		$navn = '';
		
		print "<p><font size=\"+3\">" . gettext("OK</font>, the filter is removed from the database.");

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the filter is <b>not</b> removed.");
	}

	// Viser feilmelding om det har oppstått en feil.
	if ( $error != NULL ) {
		print $error->getHTML();
		$error = NULL;
	}
  
}

if ($subaction == "nyttfilter") {
  print "<h3>" . gettext("Registering new filter...") . "</h3>";
  
  $error = NULL;

  if ($navn == "") $navn = gettext("No name");

  if ($uid > 0) { 
    
    $filterid = $dbh->nyttFilterAdm($navn);
	$dbh->nyLogghendelse($uid, 6, gettext("New public equipment filter") . " (" . $navn . ")");    
    
    print "<p><font size=\"+3\">" . gettext("OK</font>, a new filter is created. Open the filter to add matchfields.");
    
  } else {
    print "<p><font size=\"+3\">" . gettext("An error</font> occured, a new filter is <b>not</b> added to the database.");
  }

  // Viser feilmelding om det har oppstÂtt en feil.
  if ( $error != NULL ) {
    print $error->getHTML();
    $error = NULL;
  }

}


$l = new Lister( 110,
		array(gettext('Name'), gettext('#match'), gettext('#groups'), gettext('Options..') ),
		array(50, 15, 15, 20),
		array('left', 'right', 'right', 'right'),
		array(true, true, true, false),
		0
);

print "<h3>" . gettext("Your equipment filters") . "</h3>";

if (! isset($sort) ) { $sort = 1; }
$filtre = $dbh->listFiltreAdm($sort);

for ($i = 0; $i < sizeof($filtre); $i++) {

  $valg = '<a href="index.php?action=match&fid=' . $filtre[$i][0] . '">' . 
  	'<img alt="Open" src="icons/open2.gif" border=0></a>&nbsp;' .
  	'<a href="index.php?action=ffilter&subaction=endre&navn=' . $filtre[$i][1] . '&fid=' . $filtre[$i][0] . '#nyttfilter">' .
    '<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;' .
    '<a href="index.php?action=ffilter&subaction=slett&fid=' . $filtre[$i][0] . '">' .
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

print "<p>[ <a href=\"index.php\">" . gettext('update') . " <img src=\"icons/refresh.gif\" alt=\"oppdater\" class=\"refresh\" border=0> ]</a> ";
print gettext("Number of filters: ") . sizeof($filtre);

?>


</td></tr>
</table>
