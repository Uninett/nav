<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<?php
echo '<p>' . gettext("Setup equipment group") . '</p>';
if (get_exist('gid')) session_set('grp_gid', get_get('gid'));
$utstginfo = $dbh->utstyrgruppeInfo(session_get('grp_gid') );
echo '<div class="subheader">' . $utstginfo[0] . '</div>';

?>
</td></tr>

<tr><td>
<?php

include("loginordie.php");
loginOrDie();

echo "<p>";
echo gettext("Here you select equipment filters which make up the equipment group."); 
echo '<p><a href="#nyttfilter">';
echo gettext("Add new filter"); 
echo "</a>";




$brukernavn = session_get('bruker'); $uid = session_get('uid');



if ( session_get('admin') < 100 && !$dbh->permissionEquipmentGroup( session_get('uid'), session_get('grp_gid') ) ) {
    echo "<h2>Security violation</h2>";
    exit(0);
}


if ($subaction == 'slett') {

	if (get_get('fid') > 0) { 
	
		$dbh->slettGrpFilter(session_get('grp_gid'), get_get('fid') );
		$adresse='';
		print "<p><font size=\"+3\">" . gettext("OK</font>, the filter is removed from the group.");

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
  $error = NULL;
  if (($uid > 0) AND (isset($filterid))){ 
    $matchid = $dbh->nyttGrpFilter(session_get('grp_gid'), post_get('filterid'), 
    	post_get('inkluder'), post_get('invers') );
  } else {
    print "<p><font size=\"+3\">" . gettext("An error</font> occured, a new filter is <b>not</b> added.");
  }

  // Viser feilmelding om det har oppstått en feil.
  if ( $error != NULL ) {
    print $error->getHTML();
    $error = NULL;
  }
}

if ($subaction == "swap") {  
	$matchid = $dbh->swapFilter(session_get('grp_gid'), 
		get_get('a'), get_get('b'), get_get('ap'), get_get('bp') );
}

$l = new Lister( 114,
		array(gettext('Incl'), gettext('Neg'), gettext('Equipment filter'), gettext('Move'), gettext('Options..') ),
		array(10, 10, 50, 15, 15),
		array('center', 'center', 'left', 'center', 'right'),
		array(false, false, false, false, false),
		0
);


print "<h3>" . gettext("Equipment filters") . "</h3>";

$filtre = $dbh->listFiltreGruppe(session_get('grp_gid'), 1);

for ($i = 0; $i < sizeof($filtre); $i++) {

	$up = false; $down = false;
	if (sizeof($filtre) > 1) {
		// Nedover pil først.
		if ( ($i == 0) AND ($filtre[1][3] == 't') ) $down = true;
		if ( ($i > 0) AND ($i < sizeof($filtre) -1)) $down = true;
		
		// oppover pil
		if ( ($i == 1) AND ($filtre[1][3] == 't')) $up = true;
		if ($i > 1) $up = true;
	}

	$flytt = "";
	if ($up) $flytt .= '<a href="index.php?subaction=swap&a=' . $filtre[$i][0] . '&b='. $filtre[$i-1][0] .'&ap=' .
		$filtre[$i][2] . '&bp=' . $filtre[$i-1][2] . '">' . 
		'<img alt="' . gettext("Move up") . '" src="icons/arrowup.gif" border="0"></a>';
	
	if ($down) $flytt .= '<a href="index.php?subaction=swap&a=' . $filtre[$i][0] . '&b='. $filtre[$i+1][0] . '&ap=' . 
		$filtre[$i][2] . '&bp=' . $filtre[$i+1][2] . '">' . 
		'<img alt="' . gettext("Move down") . '" src="icons/arrowdown.gif" border="0"></a>';
		
  	$valg = '<a href="index.php?action=utstyrgrp&subaction=slett&fid=' . 
  		$filtre[$i][0] . '">' . 
  		'<img alt="Delete" src="icons/delete.gif" border=0></a>';	
  	
  	if ($filtre[$i][3] == 't') {
		$inkicon = '<img src="icons/pluss.gif" border="0" alt="' . gettext("Include") . '">';
	} else {
		$inkicon = '<img src="icons/minus.gif" border="0" alt="' . gettext("Exclude") . '">';
	}
	
	if ($filtre[$i][4] == 't') {
		$negicon = '<img src="icons/pos.gif" border="0" alt="' . gettext("Normal") . '">';
	} else {
		$negicon = '<img src="icons/neg.gif" border="0" alt="' . gettext("Inverted") . '">';
	}

  $l->addElement( array($inkicon, // inkluder
  			$negicon,
  			$filtre[$i][1],  // navn
  			$flytt,
			$valg ) 
		  );
}


print $l->getHTML();

print "<p>[ <a href=\"index.php\">" . gettext("update") . " <img src=\"icons/refresh.gif\" alt=\"oppdater\" border=0> ]</a> ";
print gettext("Number of filters: ") . sizeof($filtre);

?>

<a name="nyttfilter"></a><p><h3><?php echo gettext("Add new filter"); ?></h3>
<form name="form1" method="post" action="index.php?subaction=nyttfilter">
  <table width="100%" border="0" cellspacing="0" cellpadding="3">
    
    <tr>

    	<td width="50%">
<?php
print '<select name="filterid">';
if (session_get('lastaction') == 'futstyr') {
    $filtervalg = $dbh->listFiltreFastAdm(session_get('grp_gid'), $sort);
} else {
    $filtervalg = $dbh->listFiltreFast($uid, session_get('grp_gid'), $sort);
}
for ($i = 0; $i < sizeof($filtervalg); $i++)
	print "<option value=\"" . $filtervalg[$i][0]. "\">" . $filtervalg[$i][1]. "</option>\n";
	if ($i == 0) {
		print "<option value\"empty\">" . gettext("No filters avaiable...") . "</option>";
	}
print '</select>';
?>    	
</td>



<td align="left" valign="center" width="20%">
<p>
<img src="icons/pluss.gif" border="0" alt="Inkluder">
<input name="inkluder" type="radio" value="1" checked><?php echo gettext("Include"); ?><br>
<img src="icons/minus.gif" border="0" alt="Ekskluder">
<input name="inkluder" type="radio" value="0"><?php echo gettext("Exclude"); ?>
</td>
 

<td align="left" valign="center" width="20%">
<p>
<img src="icons/pos.gif" border="0" alt="Vanlig" vspace="0">
<input type="radio" name="invers" value="1" checked><?php echo gettext("Normal"); ?><br>

<img src="icons/neg.gif" border="0" alt="Invers">
<input type="radio" name="invers" value="0"><?php echo gettext("Inverted"); ?>
</td>
</tr>
        
        
   	<tr>
   	<td>&nbsp;</td>
   	<td>&nbsp;</td>
<td><?php
if ($i > 0 ) { 
      print '<input type="submit" name="Submit" value="' . gettext("Add") . '"></td>';
 } else {
 	print "<p>" . gettext("Add");
 }
?></td>   	   	   	
   	</tr>
   	
   	
  </table>
</form>

<?php
    if (!post_exist('matchfelt') ) {
        echo '<p><form name="finnished" method="post" action="index.php?action=' . session_get('lastaction') . '">';
        echo '<input type="submit" name="Submit" value="' . gettext('Finished setting up equipment group') . '">';
        echo '</form>';
    }
?>

</td></tr>
</table>
