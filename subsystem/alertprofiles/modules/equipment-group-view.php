<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<?php
echo '<p>' . gettext("Filter group overview") . '</p>';

if (get_exist('gid')) session_set('grp_gid', get_get('gid'));

$utstginfo = $dbh->utstyrgruppeInfo(session_get('grp_gid') );
echo '<div class="subheader"><img src="icons/equipment.png"> ' . $utstginfo[0] . 
	'<p style="font-size: x-small; font-weight: normal; margin: 2px; text-align: left"><img src="icons/person100.gif"> This is a public filter group, owned by the administrators. You are free to use this filter group to set up alert profiles, but you cannot change the filter group composition.</div>';

?>

</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();

echo "<p>";
echo gettext("Here is a read only overview of the requested filter group. The composition of the filter group, consisting of the include/exclude list of filters is shown below.");
echo "<p>";
$brukernavn = session_get('bruker'); $uid = session_get('uid');


/*
 * the function eqgroupview() prints out a nice html table showing the requested 
 * filter group in i hiearchy, with all filters in detail.
 *
 */
 
function eqgroupview($dbh, $eqid) {
	global $type;
	echo '<h3>Filter group overview</h3>';

	$filtre = $dbh->listFiltreGruppe($eqid, 0);
	
	$l = new Lister( 114,
		array(gettext('Operator') . '&nbsp;', gettext('Filter') ),
		array(25, 75 ),
		array('right', 'left'),
		array(false, false),
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


		$fm = '<ul style="margin-top: 0px;">';
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
			$filtre[$i][1] . $fm ) 
		);
	
	}

	print $l->getHTML();

}

/* Print overview for filter group if requested */

eqgroupview($dbh, session_get('grp_gid'));

echo '<a href="?action=' . session_get('lastaction') . '">' . gettext('Return to ');
switch (session_get('lastaction')) {
	case 'utstyr' 	: echo gettext('filter group list'); break;
	case 'oversikt' : echo gettext('overview'); break;
	default : echo gettext('previous page'); break;
}
echo '</a>';

?>
</td></tr>
</table>
