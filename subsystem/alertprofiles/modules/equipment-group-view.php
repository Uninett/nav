<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<?php
echo '<p>' . gettext("Equipment group overview") . '</p>';

if (get_exist('gid')) session_set('grp_gid', get_get('gid'));

$utstginfo = $dbh->utstyrgruppeInfo(session_get('grp_gid') );
echo '<div class="subheader"><img src="icons/equipment.png"> ' . $utstginfo[0] . 
	'<p style="font-size: x-small; font-weight: normal; margin: 2px; text-align: left"><img src="icons/gruppe.gif"> This is a public equipment group, owned by the administrators. You are free to use this equipment group to set up alert profiles, but you cannot change the equipment group composition.</div>';

?>

</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();

echo "<p>";
echo gettext("Here is a read only overview of the requested equipment group. The composition of the equipment group, consisting of the include/exclude list of equipment filters is shown below.");

$brukernavn = session_get('bruker'); $uid = session_get('uid');


/*
 * the function eqgroupview() prints out a nice html table showing the requested 
 * equipment group in i hiearchy, with all equipment filters in detail.
 *
 */
 
function eqgroupview($dbh, $eqid) {

	echo '<h3>Equipment group overview</h3>';

	$filtre = $dbh->listFiltreGruppe($eqid, 0);
	
	$l = new Lister( 114,
		array(gettext('Include'), gettext('Invert'), gettext('Equipment filter') ),
		array(10, 15, 75 ),
		array('left', 'center', 'left'),
		array(false, false, false),
		0
	);	
	
	for ($i = 0; $i < sizeof($filtre); $i++) {

		/*
		$filtre[$row][0] = $data["id"]; 
		$filtre[$row][1] = $data["navn"];
		$filtre[$row][2] = $data["prioritet"];
		$filtre[$row][3] = $data["inkluder"];
		$filtre[$row][4] = $data["positiv"];		
		*/

		if ($filtre[$i][3] == 't') {
			$inkicon = '<img src="icons/pluss.gif" border="0" alt="' . gettext("Include") . 
			'"> <span style="vertical-align: top">Include</span>';
		} else {
			$inkicon = '<img style="imglow" src="icons/minus.gif" border="0" alt="' . gettext("Exclude") . 
			'"> <span style="vertical-align: top">Exclude</span>';
		}
	
		if ($filtre[$i][4] == 't') {
			$negicon = '&nbsp;';
		} else {
			$negicon = gettext('NOT');
		}


		$fm = "<ul>";
		$match = $dbh->listMatch($filtre[$i][0], 0 );
		for ($j = 0; $j < sizeof($match); $j++) {
			/*
			$match[$row][0] = $data["id"]; 
			$match[$row][1] = $data["name"];
			$match[$row][2] = $data["matchtype"];
			$match[$row][3] = $data["verdi"];		
			*/
			$fm .= '<li>' . $match[$j][1] . ' ' . $type[$match[$j][2]] . ' ' . $match[$j][3] . '</li>' ."\n";
		}
		$fm .= "</ul>";
		$l->addElement( array(
			$inkicon, // inkluder
			$negicon,
			$filtre[$i][1] . $fm ) 
		);
	
	}

	print $l->getHTML();

}

/* Print overview for equipment group if requested */

eqgroupview($dbh, session_get('grp_gid'));

echo '<a href="?action=' . session_get('lastaction') . '">' . gettext('Return to ');
switch (session_get('lastaction')) {
	case 'utstyr' 	: echo gettext('equipment group list'); break;
	case 'oversikt' : echo gettext('overview'); break;
	default : echo gettext('previous page'); break;
}
echo '</a>';

?>
</td></tr>
</table>
