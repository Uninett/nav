<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("Public filters"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>" . gettext("Public filters is shared among administrators, and can be assigned to user groups, and used by regular users.");


echo '<p>' . gettext('Filters are used to build filter groups, which in turn are the building 
blocks in your alert profiles. Like filter groups, filters may be
predefined by the NAV administrator or you may define your own.') . '<p>' .
	gettext('Open an existing filter or create a new.'); 

if (get_get('allowdelete') == 1 ) {
	print '
<div style="
		padding: 2px 50px 5px 50px; 
		background: #772020; 
		color: #fcfcfc ! important;
		margin: 10px 5px 10px 5px;
		border: 1px solid #000"><h2>Warning</h2><p>You are about to delete a filter that is contained in at least one filter group. Deleting such a filter will change the behaviour of those filter groups. Be absolutely sure that you know what you do.</p></div>';
}


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
	value="' .  best_get('navn') . '"></td>
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



if (isset($subaction) && $subaction == 'endret') {

	if ($fid > 0) { 
	
		$dbh->endreFilter($fid, $navn);
		$dbh->nyLogghendelse($uid, 8, gettext("Name changed on public filter") . " (" . $navn . ")");
		
		print "<p><font size=\"+3\">" . gettext(" OK</font>, filter name is changed.");
		$navn='';

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the filter is <b>not</b> changed.");
	}

  
}

if (isset($subaction) && $subaction == 'slett') {

	if ($fid > 0) { 
	
		$foo = $dbh->slettFilter($fid);
		$dbh->nyLogghendelse($uid, 7, gettext("Public filter is removed") . " (id=" . $fid . ")");		
		$navn = '';
		
		print "<p><font size=\"+3\">" . gettext("OK</font>, the filter is removed from the database.");

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the filter is <b>not</b> removed.");
	}

  
}

if (isset($subaction) && $subaction == "nyttfilter") {
  print "<h3>" . gettext("Registering new filter...") . "</h3>";
  

  if ($navn == "") $navn = gettext("No name");

  if ($uid > 0) { 
    
    $filterid = $dbh->nyttFilterAdm($navn);
	$dbh->nyLogghendelse($uid, 6, gettext("New public filter") . " (" . $navn . ")");    
    
    print "<p><font size=\"+3\">" . gettext("OK</font>, a new filter is created. Open the filter to add matchfields.");
    
  } else {
    print "<p><font size=\"+3\">" . gettext("An error</font> occured, a new filter is <b>not</b> added to the database.");
  }


}


$l = new Lister( 110,
		array(gettext('Name'), gettext('#match'), gettext('#groups'), gettext('Options..') ),
		array(50, 15, 15, 20),
		array('left', 'right', 'right', 'right'),
		array(true, true, true, false),
		0
);

//print "<h3>" . gettext("Public filters") . "</h3>";
print "<p>";
if (! isset($sort) ) { $sort = 1; }
$filtre = $dbh->listFiltreAdm($sort);

for ($i = 0; $i < sizeof($filtre); $i++) {

	$valg = '<a href="index.php?action=match&fid=' . $filtre[$i][0] . '">' . 
		'<img alt="Open" src="icons/open2.gif" border=0></a>&nbsp;' .
		'<a href="index.php?action=ffilter&subaction=endre&navn=' . $filtre[$i][1] . '&fid=' . $filtre[$i][0] . '#nyttfilter">' .
		'<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;';

	if ($filtre[$i][3] < 1 or get_get('allowdelete') == 1 ) {
		$valg .= '<a href="index.php?action=ffilter&subaction=slett&fid=' . $filtre[$i][0] . '">' .
	'<img alt="Delete" src="icons/delete.gif" border=0></a>';
	} else {
		$valg .= '<img alt="Delete" title="This filter is in use in at least one filter group." src="icons/delete-grey.gif" border=0>';
	}

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

print "<p>[ <a href=\"index.php?action=ffilter\">" . gettext('update') . " <img src=\"icons/refresh.gif\" alt=\"oppdater\" class=\"refresh\" border=0> ]</a> ";
print gettext("Number of filters: ") . sizeof($filtre);

if (get_get('allowdelete') != 1 ) {
	print '<p align="right">[ <a href="index.php?action=' . best_get('action'). '&allowdelete=1">Allow removal of filters in use</a> ]';
}

?>


</td></tr>
</table>
