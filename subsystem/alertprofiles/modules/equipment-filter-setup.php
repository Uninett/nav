<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<?php
echo '<p>Filter setup</p>';
if ( get_exist('fid') ) {
	session_set('match_fid', get_get('fid') );
}
$utstginfo = $dbh->utstyrfilterInfo( session_get('match_fid') );
echo '<div class="subheader">' . $utstginfo[0] . '</div>';

?>

</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();

echo "<p>";
echo gettext("Here you can setup conditions to be fulfilled for a specific event to be match by the filter. If one or more conditions returns false the event will not be included in the filter.");
echo '<p><a href="#nymatch">';
echo gettext("Add new condition");
echo '</a>';


$dbhk = $dbinit->get_dbhk();

$brukernavn = session_get('bruker'); $uid = session_get('uid');



if ( session_get('admin') < 100 && !$dbh->permissionEquipmentFilter( session_get('uid'), session_get('match_fid') ) ) {
	echo "<h2>Security violation</h2>";
	exit(0);
}


if (isset($subaction) && $subaction == 'slett') {

	if (session_get('match_fid') > 0) { 
	
		$dbh->slettFiltermatch(session_get('match_fid'), get_get('mid') );

		print "<p><font size=\"+3\">" . gettext("OK</font>, the condition is removed from the filter.");

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the match is <b>not</b> removed.");
	}

  
}

if (isset($subaction) && $subaction == "nymatch") {
	print "<h3>" . gettext("Registering new condition...") . "</h3>";
	
	//if ($navn == "") $navn = gettext("No name");
	if ($uid > 0) { 
	
		$matchid = $dbh->nyMatch(post_get('matchfelt'), post_get('matchtype'), 
		post_get('verdi'), session_get('match_fid') );
		print "<p><font size=\"+3\">" . gettext("OK</font>, a new condition (match) is added to this filter.");
	
	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, a new match is  <b>not</b> added.");
	}
	
	$subaction = "";
	unset($matchfelt);
  
}


$l = new Lister(111,
    array(gettext('Field'), gettext('Condition'), gettext('Value'), gettext('Option..') ),
    array(40, 15, 25, 20),
    array('left', 'left', 'left', 'right'),
    array(true, true, true, false),
    0
);


print "<h3>" . gettext("Filter matches") . "</h3>";

if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );
	
$match = $dbh->listMatch(session_get('match_fid'), $l->getSort() );

for ($i = 0; $i < sizeof($match); $i++) {

	$valg = '<a href="index.php?action=match&subaction=slett&mid=' . 
		$match[$i][0] . '">' .
		'<img alt="Delete" src="icons/delete.gif" border=0>' .
		'</a>';
	
	
	$l->addElement( array(
		$match[$i][1],  // felt
		$type[$match[$i][2]], // type
		$match[$i][3], // verdi
		$valg ) 
	);
}

print $l->getHTML();

print "<p>[ <a href=\"index.php?action=match\">" . gettext("update") . " <img src=\"icons/refresh.gif\" class=\"refresh\" alt=\"oppdater\" border=0> ]</a> ";
print "Antall filtermatcher: " . sizeof($match);


echo '<a name="nymatch"></a><p><h3>';
echo gettext("Add new condition");
echo '</h3>';



print '<form name="form1" method="post" action="index.php?action=match&subaction=velgmatchfelt">';

?>
  <table width="100%" border="0" cellspacing="0" cellpadding="3">


    <tr>
    	<td width="30%"><p><?php echo gettext('Choose field'); ?></p></td>
    	<td width="70%">
    	<select name="matchfelt" id="select" onChange="this.form.submit()">
<?php

// Viser oversikt over hvilke filtermatchfelter man kan velge...
$matchfields = $dbh->listMatchField(1);

foreach ($matchfields AS $matchfield) {
	$sel = "";
	if ($matchfield[0] == best_get('matchfelt')) { $sel = " selected"; }
	print '<option value="' . $matchfield[0] . '"' . $sel . '>' . $matchfield[1] . '</option>';
}

echo '</select></td></tr>';


echo '</form><form name="nymatch" method="post" action="index.php?action=match&subaction=nymatch">';

if ( post_exist('matchfelt') ) {
	$valgt_matchfelt = post_get('matchfelt');
} else {
	$valgt_matchfelt = $matchfields[0][0];
}
//echo '<p>Valg matchfelt er: ' . $valgt_matchfelt . ' postverdi er:' .  post_get('matchfelt');
/*
	$mf[0] = $data["name"];
	$mf[1] = $data["descr"];
	$mf[2] = $data["valuehelp"];
	$mf[3] = $data["valueid"];
	$mf[4] = $data["valuename"];
	$mf[5] = $data["valuecategory"];
	$mf[6] = $data["valuesort"];
	$mf[7] = $data["listlimit"];
	$mf[8] = $data["showlist"];
*/

$matchfieldinfo = $dbh->matchFieldInfo($valgt_matchfelt);

echo '<tr><td colspan="2"><small><p>';
echo $matchfieldinfo[1];
echo '</small></td></tr>';

echo '<tr>';


// Valg av operator ----------------------------------------

echo '<td width="30%"><p>';
echo gettext("Choose condition");
echo '</p></td><td width="70%">';

echo '<input type="hidden" name="matchfelt" value="' . $valgt_matchfelt . '">';

print '<select name="matchtype" id="select">';

if ( sizeof($matchfieldinfo[9]) > 0) {
	foreach ($matchfieldinfo[9] as $matchtype) {
		print '<option value="' . $matchtype . '">' . $type[$matchtype] . '</option>';
	}
} else {
	print '<option value="0" selected>' . gettext("equals") . '</option>';	
}
echo '</select>';
echo '</td></tr>';
echo '<tr><td colspan="2"><small><p>';
echo $matchfieldinfo[2];
echo '</small></td></tr>';


?>
   	
    <tr>     
    	<td width="30%"><p><?php echo gettext('Set value'); ?></p></td>
    	<td width="70%">
<?php    





if ($matchfieldinfo[8] == 't' ) {
  
	// Valg av verdi ----------------------------------------	
	
		
	$verdier = $dbhk->listVerdier(
		$matchfieldinfo[3],
		$matchfieldinfo[4],
		$matchfieldinfo[5],
		$matchfieldinfo[6],
		$matchfieldinfo[7]
	);  
  
  
	echo '<select name="verdi" id="select">';    

	ksort($verdier);

	// Traverser kategorier
	foreach ($verdier AS $cat => $catlist) {
		if ($cat != "") echo '<optgroup label="' . $cat . '">';
		foreach ($catlist AS $catelem) {
			echo ' <option value="' . $catelem[0] . '">' . $catelem[1] . '</option>' . "\n";
		}
		if ($cat != "") echo '</optgroup>';
	}
				
	echo '</select>';
	
} else {
	echo '<input name="verdi" size="40">';
}    

?>

        </td></tr>



    <tr>
      <td>&nbsp;</td>
      
<?php

$tekst = gettext("Add condition");

print '<td align="right"><input type="submit" name="Submit" value="' . $tekst . '"></td>';



?>
    </tr>
  </table>

</form>

<?php
	echo '<p><form name="finnished" method="post" action="index.php?action=' . session_get('lastaction') . '">';
	echo '<input type="submit" name="Submit" value="' . gettext('Finished setting up filter') . '">';
	echo '</form>';
?>

</td></tr>
</table>
