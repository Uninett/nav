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
<p><?php echo gettext("Filter and filter group access"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>";
echo gettext("Here you can setup permissions to user groups, and assign filters and filter groups to user groups."); 





if (get_exist('subaction'))
	session_set('gruppesubaction', get_get('subaction'));
if (get_exist('gid'))
	session_set('endregruppeid', get_get('gid') );
if (get_exist('hl'))
	session_set('endregruppehighlight', get_get('hl') );



if (session_get('gruppesubaction') == "endregruppe") {
	print "<h3>" . gettext("Changing user group access to filter group...") . "</h3>";
	
	reset ($HTTP_POST_VARS);
	
	while ( list($n, $val) = each ($HTTP_POST_VARS)) {
		
		if ( preg_match("/rvalg([0-9]+)/i", $n, $m) ) {
			$var = "rvelg" . $m[1];				
			$dbh->endreRettighet(session_get('endregruppeid'), $m[1], isset(${$var}));
		}
		if ( preg_match("/dvalg([0-9]+)/i", $n, $m) ) {
			$var = "dvelg" . $m[1];		
			$dbh->endreDefault(session_get('endregruppeid'), $m[1], isset(${$var}) );	
		}
		if ( preg_match("/fdvalg([0-9]+)/i", $n, $m) ) {
			$var = "fdvelg" . $m[1];		
			$dbh->endreDefaultFilter(session_get('endregruppeid'), $m[1], isset(${$var}) );	
		}
	}

	$navn = ""; $descr = ""; //gettext("Description : ");
	print "<p><font size=\"+1\">" . gettext("OK</font>, changes applied for user group.");
	
	session_set('gruppesubaction', 'clean');
}

$l = new Lister( 103,
	array(gettext('User group'), gettext('#users'), gettext('#perms'), 
		gettext('#std.groups'), gettext('#std.filters'), gettext('Options..') ),
	array(25, 15, 15, 15, 15, 10),
	array('left', 'left', 'left', 'left', 'left', 'left' ),
	array(true, true, true, true, true, false),
	0
);

print "<h3>" . gettext("User groups") . "</h3>";

if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );
	
$grupper = $dbh->listBrukerGrupper($l->getSort() );

if (session_get('gruppesubaction') == 'endre')
	$l->highlight(session_get('endregruppehighlight'));

for ($i = 0; $i < sizeof($grupper); $i++) {
  
	$valg = '<a href="index.php?action=filter-group-access&subaction=endre&gid=' . $grupper[$i][0] . '&hl=' . $i . '">' .
		'<img alt="Edit" src="icons/edit.gif" border=0></a>';

	if ($grupper[$i][3] > 0 ) { 
		$ab = $grupper[$i][3]; 
	} else { 
		$ab = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; 
	}

	if ($grupper[$i][4] > 0 ) { 
		$ar = $grupper[$i][4]; 
	} else { 
		$ar = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; 
	}

	if ($grupper[$i][5] > 0 ) { 
		$ag = $grupper[$i][5]; 
	} else { 
		$ag = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; 
	}
	if ($grupper[$i][6] > 0 ) { 
		$adf = $grupper[$i][6]; 
	} else { 
		$adf = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; 
	}	
	$l->addElement( array(
		$grupper[$i][1],	// gruppenavn
		$ab,			// #bruekre
		$ar,			// #rettigheter
		$ag,			// #std grupper
		$adf,			// #std. filter..
		$valg
		) 
	);
	
	$inh = new HTMLCell("<p class=\"descr\">" . $grupper[$i][2] . "</p>");	  
	$l->addElement (&$inh);	
	
	
}

print $l->getHTML();

print "<p>[ <a href=\"index.php?action=filter-group-access\">" . gettext("update") . " <img class=\"refresh\" src=\"icons/refresh.gif\" alt=\"oppdater\" border=0> ]</a> ";
print gettext("Number of groups: ") . sizeof($grupper);




if (session_get('gruppesubaction') == 'endre' OR session_get('gruppesubaction') == 'nygruppe') {

	$gr = $dbh->brukergruppeInfo(session_get('endregruppeid') );
	$navn = $gr[0];
	$descr = $gr[1];
	
	echo '<div style="
		padding: 2px 5px 5px 50px; 
		background: #fafafa; 
		margin: 10px 5px 10px 5px;
		border: 1px solid #ccc"><h1>' . $navn . '</h1>';
	echo '<p>' . $descr. '</p></div>';
	
	echo '<form action="index.php?action=filter-group-access&subaction=endregruppe" method="post">';

	$l = new Lister( 105,
		array(gettext('Define<br>permissions'), gettext('Available<br>to users'), gettext('Group name') ),
		array(15, 15, 70),
		array('left', 'left', 'left'),
		array(false, false, true),
		2
	);

	if ( get_exist('sortid') )
		$l->setSort(get_get('sort'), get_get('sortid') );	

	$sort = isset($sort) ? $sort : 0;
	$utstyr = $dbh->listGrUtstyr(session_get('uid'), session_get('endregruppeid'), $sort);
	
	for ($i = 0; $i < sizeof($utstyr); $i++) {
	
		if ($utstyr[$i][3] == 't') $r = " checked"; else $r = "";
		$rvelg = '<input name="rvelg' . $utstyr[$i][0] . '" type="checkbox" value="1"' . $r . '>';
		$rvelg .= '<input name="rvalg' . $utstyr[$i][0] . '" value="1" type="hidden">';

		if ($utstyr[$i][4] == 't') $d = " checked"; else $d = "";
		$dvelg = '<input name="dvelg' . $utstyr[$i][0] . '" type="checkbox" value="1"' . $d . '>';
		$dvelg .= '<input name="dvalg' . $utstyr[$i][0] . '" value="1" type="hidden">';

		$l->addElement( array(
			$rvelg,
			$dvelg,			
			$utstyr[$i][1]
		) );
	}

	print "<h3>" . gettext("User groups can access which filter groups") . "</h3>";
	print $l->getHTML();
	



	
	$l = new Lister( 105,
		array(gettext('Available<br>to users'), gettext('Filter name') ),
		array(30, 70),
		array('left', 'left'),
		array(false, true),
		2
	);


	$sort = isset($sort) ? $sort : 0;
	$filter = $dbh->listGrFilter(session_get('uid'), session_get('endregruppeid'), $sort);
	
	for ($i = 0; $i < sizeof($filter); $i++) {
	
		if ($filter[$i][2] == 't') $d = " checked"; else $d = "";
		$fdvelg = '<input name="fdvelg' . $filter[$i][0] . '" type="checkbox" value="1"' . $d . '>';
		$fdvelg .= '<input name="fdvalg' . $filter[$i][0] . '" value="1" type="hidden">';

		$l->addElement( array(
			$fdvelg,			
			$filter[$i][1]
		) );
	}
	
	print "<h3>" . gettext("User groups can access which filters") . "</h3>";
	print $l->getHTML();	
	
	
	
	print '<p><input type="submit" name="Submit" value="' . gettext("Change filter group access for ")  . $navn .  '">';









	print "<h3>" . gettext("Users subscribed to the group") . "</h3><ul>";


	if ( get_exist('sortid') )
		$l->setSort(get_get('sort'), get_get('sortid') );	
	
	// Henter ut alle brukerene og om de tilhører gruppen eller ikke
	$brukere = $dbh->listGrBrukere(session_get('endregruppeid'), $l->getSort() );
	for ($i = 0; $i < sizeof($brukere); $i++) {
	
		if ($brukere[$i][3] == 't') {
			print '<li>' . $brukere[$i][2]  . ' (' . $brukere[$i][1] . ')</li>';
		}
	}
	if (sizeof($brukere) < 1)  {
		print '<li>No users</li>';
	}

	echo '</ul>';

	echo '</form>';

}

?>


</td></tr>
</table>
