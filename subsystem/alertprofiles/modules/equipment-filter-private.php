<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('Filters'); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>" . gettext("A filter is a set of filtermatches, which constitutes a group of conditions for an quipment to be included. Equipment groups is created by several filters in an ordered list.
<p>When creating an alert profile, you choose filter groups to choose which equipment you want to supervise."); 
echo '<p><a href="?subaction=ny">' . gettext("Add a new filter") . '</A>';


session_set('lastaction', 'filter');
$brukernavn = session_get('bruker'); $uid = session_get('uid');



if (in_array(get_get('subaction'), array('ny', 'endre') )) {


	print '<a name="ny"></a><div class="newelement">';
	
	if ($subaction == 'endre') {
		print '<h2>' .gettext("Rename filter") . '</h2>';
	} else {
		print '<h2>' .gettext("Add a new filter") . '</h2>';
	}
	

	
	echo '<form name="form1" method="post" action="index.php?action=filter&subaction=';

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
            if (!$dbh->permissionEquipmentFilter( session_get('uid'), $fid ) ) {
                echo "<h2>Security violation</h2>";
                exit(0);
            }
            
		$dbh->endreFilter($fid, $navn);

		
		print "<p><font size=\"+3\">" . gettext("OK</font>, filter is renamed.");
		$navn='';

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the filter is <b>not</b> changed.");
	}

  
}

if (isset($subaction) && $subaction == 'slett') {

	if ($fid > 0) { 
            if (!$dbh->permissionEquipmentFilter( session_get('uid'), $fid ) ) {
                echo "<h2>Security violation</h2>";
                exit(0);
            }	
		$foo = $dbh->slettFilter($fid);
		$navn = '';
		
		print "<p><font size=\"+3\">" . gettext("OK</font>, the filter is removed from the database.");

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the filter will <b>not</b> be removed.");
	}

  
}

if (isset($subaction) && $subaction == "nyttfilter") {
  print "<h3>" . gettext("Registering a new profile...") . "</h3>";
  

  if ($navn == "") $navn = gettext("No name");

  if ($uid > 0) { 
    
    $filterid = $dbh->nyttFilter($navn, $uid);
    
    print "<p><font size=\"+3\">" . gettext("OK</font>, a new filter is created. Open the filter to add filtermatches.");
    
  } else {
    print "<p><font size=\"+3\">" . gettext("An error occured</font>, a new profile is <b>not</b> created.");
  }


}


$l = new Lister( 110,
		array(gettext('Name'), gettext('#match'), gettext('#groups'), gettext('Options..') ),
		array(50, 15, 15, 20),
		array('left', 'right', 'right', 'right'),
		array(true, true, true, false),
		0
);

print "<h3>" .gettext("Your equipment filters") . "</h3>";

if (! isset($sort) ) { $sort = 1; }
$filtre = $dbh->listFiltre($uid, $sort);

for ($i = 0; $i < sizeof($filtre); $i++) {

  $valg = '<a href="index.php?action=match&fid=' . $filtre[$i][0] . '">' . 
  	'<img alt="Open" src="icons/open2.gif" border=0></a>&nbsp;' .
  	'<a href="index.php?action=filter&subaction=endre&navn=' . $filtre[$i][1] . '&fid=' . $filtre[$i][0] . '#nyttfilter">' .
    '<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;' .
    '<a href="index.php?action=filter&subaction=slett&fid=' . $filtre[$i][0] . '">' .
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

print "<p>[ <a href=\"index.php?action=" . best_get('action'). "\">" .gettext("update") . " <img src=\"icons/refresh.gif\" class=\"refresh\" alt=\"oppdater\" border=0> ]</a> ";
print gettext("Number of filters: ") . sizeof($filtre);

?>

</td></tr>
</table>
