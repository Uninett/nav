<?php
/* $Id$
 *
 * Copyright 2002-2004 UNINETT AS
 * 
 * This file is part of Network Administration Visualized (NAV)
 *
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *
 * Authors: Andreas Aakre Solberg <andreas.solberg@uninett.no>
 *
 */
?><table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<?php
echo '<p>' . gettext("Setup filter group") . '</p>';

if (get_exist('gid')) session_set('grp_gid', get_get('gid'));

$utstginfo = $dbh->utstyrgruppeInfo(session_get('grp_gid') );

echo '<div class="subheader">' . $utstginfo[0] . '</div>';

?>
</td></tr>

<tr><td>
<?php

include("loginordie.php");
loginOrDie();

echo '<p>' . gettext('Setup the filter group using the formula:') . '<p>' .
	gettext('Filter group = ((&lt;filter 1&gt; &lt;operator&gt; &lt;filter 2&gt;)... &lt;operator&gt; &lt;filter n&gt;)'); 


echo '<p><a href="#nyttfilter">';
echo gettext("Add new filter"); 
echo "</a>";




$brukernavn = session_get('bruker'); $uid = session_get('uid');



if ( session_get('admin') < 100 && !$dbh->permissionEquipmentGroup( session_get('uid'), session_get('grp_gid') ) ) {
    echo "<h2>Security violation</h2>";
    exit(0);
}


if (isset($subaction) && $subaction == 'slett') {

	if (get_get('fid') > 0) { 
	
		$dbh->slettGrpFilter(session_get('grp_gid'), get_get('fid') );
		$adresse='';
		print "<p><font size=\"+3\">" . gettext("OK</font>, the filter is removed from the group.");

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the filter is <b>not</b> removed.");
	}

  
}

if (isset($subaction) && $subaction == "nyttfilter") {  
  if (($uid > 0) AND (isset($filterid))){ 
  	
  	$ink = ((post_get('inkluder') == 1) || (post_get('inkluder') == 2)) ? 1 : 0;
  	$positiv = ((post_get('inkluder') == 1) || (post_get('inkluder') == 3)) ? 1 : 0;
  	
  	//print "<p>Value: " . post_get('inkluder') . " Ink:$ink Positiv:$positiv .";
  	
    $matchid = $dbh->nyttGrpFilter(session_get('grp_gid'), post_get('filterid'), 
		$ink, $positiv );
  } else {
    print "<p><font size=\"+3\">" . gettext("An error</font> occured, a new filter is <b>not</b> added.");
  }

}

if (isset($subaction) && $subaction == "swap") {  
	$matchid = $dbh->swapFilter(session_get('grp_gid'), 
		get_get('a'), get_get('b'), get_get('ap'), get_get('bp') );
}

$l = new Lister( 114,
		array(gettext('Operator') . '&nbsp;', gettext('Filter'), gettext('Move'), gettext('Options..') ),
		array(25,  45, 15, 15),
		array('right', 'left', 'center', 'right'),
		array(false, false, false, false),
		0
);


//print "<h3>" . gettext("Filters") . "</h3>";
print "<p>";

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
	if ($up) $flytt .= '<a href="index.php?action=utstyrgrp&subaction=swap&a=' . $filtre[$i][0] . '&b='. $filtre[$i-1][0] .'&ap=' .
		$filtre[$i][2] . '&bp=' . $filtre[$i-1][2] . '">' . 
		'<img alt="' . gettext("Move up") . '" src="icons/arrowup.gif" border="0"></a>';
	
	if ($down) $flytt .= '<a href="index.php?action=utstyrgrp&subaction=swap&a=' . $filtre[$i][0] . '&b='. $filtre[$i+1][0] . '&ap=' . 
		$filtre[$i][2] . '&bp=' . $filtre[$i+1][2] . '">' . 
		'<img alt="' . gettext("Move down") . '" src="icons/arrowdown.gif" border="0"></a>';
	
  	$flytt = strlen($flytt) > 0 ? $flytt : '&nbsp;';
  	
  	$valg = '<a href="index.php?action=utstyrgrp&subaction=slett&fid=' . 
  		$filtre[$i][0] . '">' . 
  		'<img alt="Delete" src="icons/delete.gif" border=0></a>';	
  	
		if ($filtre[$i][3] == 't') {
			if ($filtre[$i][4] == 't') {
				$inkicon = gettext('Add') .
					'&nbsp;<img src="icons/pluss.gif" border="0" alt="operator" style="margin-bottom: -5px">';
			} else {
				$inkicon = gettext('Add inverse') .
					'&nbsp;<img src="icons/plussinverse.gif" border="0" alt="operator" style="margin-bottom: -5px">';		
			}  	
		} else {
			if ($filtre[$i][4] == 't') {
				$inkicon = gettext('Subtract') . 
					'&nbsp;<img src="icons/minus.gif" border="0" alt="operator" style="margin-bottom: -5px">';
			} else {
				$inkicon = gettext('And') . 
					'&nbsp;<img src="icons/and.gif" border="0" alt="operator" style="margin-bottom: -5px">';		
			}
		}
		$inkicon .= '&nbsp;&nbsp;';


	
	$fm = '<ul style="margin-top: 0px">';
	$match = $dbh->listMatch($filtre[$i][0], 0 );
	for ($j = 0; $j < sizeof($match); $j++) {
		/*
		$match[$row][0] = $data["id"]; 
		$match[$row][1] = $data["name"];
		$match[$row][2] = $data["matchtype"];
		$match[$row][3] = $data["verdi"];		
		*/
		$fm .= '<li style="margin-top: 0px">' . $match[$j][1] . ' ' . $type[$match[$j][2]] . ' ' . $match[$j][3] . '</li>' ."\n";
	}
	$fm .= "</ul>";

	$fnavn = '<p style="margin-top: .8em; padding: 0px"><a style="margin-bottom: 0px" href="index.php?action=match&amp;fid=' . $filtre[$i][0] . '"><b>' .
		$filtre[$i][1] . '</b></a>' .
		$fm;
	
	$l->addElement( array($inkicon, // inkluder
		$fnavn,  // navn
		$flytt,
		$valg ) 
	);
}


print $l->getHTML();

print "<p>[ <a href=\"index.php?action=utstyrgrp\">" . gettext("update") . " <img src=\"icons/refresh.gif\" class=\"refresh\" alt=\"oppdater\" border=0> ]</a> ";
print gettext("Number of filters: ") . sizeof($filtre);

?>

<a name="nyttfilter"></a>
<div class="newelement"><h3><?php echo gettext("Add filter to group"); ?></h3>
<form name="form1" method="post" action="index.php?action=utstyrgrp&subaction=nyttfilter" style="margin: 0px">
  <table width="100%" border="0" cellspacing="0" cellpadding="3">
    
    <tr>
    	<td align="left" valign="top" width="50%">


<p>Operator<br>

<?php 
$optionactive = "";
if (sizeof($filtre) < 1) {
	$optionactive = "disabled";
}
?>

<input name="inkluder" type="radio" value="1" checked>
<img src="icons/pluss.gif" border="0" alt="Inkluder" style="margin-bottom: -5px">
<?php
	echo gettext("Add"); 
?>
<br>

<input name="inkluder" type="radio" value="3" <?php echo $optionactive; ?> >
<img src="icons/minus.gif" border="0" alt="Ekskluder" style="margin-bottom: -5px">
<?php 
	echo gettext("Subtract"); 
?> 
<br>

<input name="inkluder" type="radio" value="4" <?php echo $optionactive; ?> >
<img src="icons/and.gif" border="0" alt="Ekskluder" style="margin-bottom: -5px">
<?php 
	echo gettext("And"); 
?>
<br>

<input name="inkluder" type="radio" value="2" <?php echo $optionactive; ?> >
<img src="icons/plussinverse.gif" border="0" alt="Inkluder NOT" style="margin-bottom: -5px">
<?php 
	echo gettext("Add inverse"); 
?>



</td>


<td align="left" valign="top" width="50%">
<p>Choose a filter<br>
<?php
print '<select name="filterid">';
$sort = isset($sort) ? $sort : 0;
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
print '</select><p>';



if ($i > 0 ) { 
      print '<input type="submit" name="Submit" value="' . gettext("Add filter") . '"></td>';
 } else {
 	print gettext("No more filters to add");
 }
?>

</td></tr>
        
   	
  </table>
</form>
</div>

<?php
    if (!post_exist('matchfelt') ) {
        echo '<div align="right"><form name="finnished" method="post" action="index.php?action=' . session_get('lastaction') . '">';
        echo '<input type="submit" name="Submit" value="' . gettext('Finished setting up filter group') . '">';
        echo '</form></div>';
    }
?>

</td></tr>
</table>
