<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('Endre felles utstyrsgrupper'); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>" . gettext("Her velger du filtre som tilsammen danner denne utstyrsgruppen. ");

echo '<p><a href="#nyttfilter">' . gettext("Legg til nytt filter") . "</a>";




$brukernavn = session_get('bruker'); $uid = session_get('uid');

if (get_exist('gid')) session_set('grp_gid', get_get('gid'));

if ($subaction == 'slett') {

	if (get_get('fid') > 0) { 
	
		$dbh->slettGrpFilter(session_get('grp_gid'), get_get('fid') );
		$adresse='';
		print "<p><font size=\"+3\">" . gettext("OK</font>, filteret er fjernet fra gruppen.");

	} else {
		print "<p><font size=\"+3\">" . gettext("Feil</font>, filteret er <b>ikke</b> fjernet.");
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
    print "<p><font size=\"+3\">" . gettext("Feil</font>, nytt filter er <b>ikke</b> lagt til i databasen.");
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
		array(gettext('Inkl'), gettext('Neg'), gettext('Utstyrfilter'), gettext('Flytt'), gettext('Valg..') ),
		array(10, 10, 50, 15, 15),
		array('center', 'center', 'left', 'center', 'right'),
		array(false, false, false, false, false),
		0
);


print "<h3>" . gettext("Utstyrsfiltre") . "</h3>";

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
		'<img alt="Flytt opp" src="icons/arrowup.gif" border="0"></a>';
	
	if ($down) $flytt .= '<a href="index.php?subaction=swap&a=' . $filtre[$i][0] . '&b='. $filtre[$i+1][0] . '&ap=' . 
		$filtre[$i][2] . '&bp=' . $filtre[$i+1][2] . '">' . 
		'<img alt="Flytt ned" src="icons/arrowdown.gif" border="0"></a>';
		
  	$valg = '<a href="index.php?subaction=slett&fid=' . 
  		$filtre[$i][0] . '">' . 
  		'<img alt="Delete" src="icons/delete.gif" border=0></a>';	
  	
  	if ($filtre[$i][3] == 't') {
		$inkicon = '<img src="icons/pluss.gif" border="0" alt="Inkluder">';
	} else {
		$inkicon = '<img src="icons/minus.gif" border="0" alt="Ekskluder">';
	}
	
	if ($filtre[$i][4] == 't') {
		$negicon = '<img src="icons/pos.gif" border="0" alt="Normal">';
	} else {
		$negicon = '<img src="icons/neg.gif" border="0" alt="Omvendt">';
	}

  $l->addElement( array($inkicon, // inkluder
  			$negicon,
  			$filtre[$i][1],  // navn
  			$flytt,
			$valg ) 
		  );
}


print $l->getHTML();

print "<p>[ <a href=\"index.php\">Refresh <img src=\"icons/refresh.gif\" alt=\"Refresh\" border=0> ]</a> ";
print gettext("Antall filtre: ") . sizeof($filtre);

?>

<a name="nyttfilter"></a><p><h3><?php echo gettext("Legg til nytt filter"); ?></h3>
<form name="form1" method="post" action="index.php?subaction=nyttfilter">
  <table width="100%" border="0" cellspacing="0" cellpadding="3">
    
    <tr>

    	<td width="50%">
<?php
print '<select name="filterid">';
$filtervalg = $dbh->listFiltreFastAdm(session_get('grp_gid'), $sort);
for ($i = 0; $i < sizeof($filtervalg); $i++)
	print "<option value=\"" . $filtervalg[$i][0]. "\">" . $filtervalg[$i][1]. "</option>\n";
	if ($i == 0) {
		print "<option value\"empty\">" . gettext("Ingen filtre tilgjengelig...") . "</option>";
	}
print '</select>';
?>    	
</td>



<td align="left" valign="center" width="20%">
<p>
<img src="icons/pluss.gif" border="0" alt="Inkluder">
<input name="inkluder" type="radio" value="1" checked><?php echo gettext("Inkluder"); ?><br>
<img src="icons/minus.gif" border="0" alt="Ekskluder">
<input name="inkluder" type="radio" value="0"><?php echo gettext("Eksluder"); ?>
</td>
 

<td align="left" valign="center" width="20%">
<p>
<img src="icons/pos.gif" border="0" alt="Vanlig" vspace="0">
<input type="radio" name="invers" value="1" checked><?php echo gettext("Vanlig"); ?><br>

<img src="icons/neg.gif" border="0" alt="Invers">
<input type="radio" name="invers" value="0"><?php echo gettext("Motsatt"); ?>
</td>


   	</tr>
   	<tr>
   	<td>&nbsp;</td>
   	<td>&nbsp;</td>
   	<td><?php
if ($i > 0 ) { 
      print '<input type="submit" name="Submit" value="' . gettext("Legg til") . '"></td>';
 } else {
 	print "<p>" . gettext("Legg til");
 }
?></td>   	   	   	
   	</tr>
   	
   	
  </table>
</form>


</td></tr>
</table>
