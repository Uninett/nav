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
<p><?php echo gettext('Filters'); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


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
		array(gettext('Name'), gettext('Owner'), gettext('#match'), gettext('#groups'), gettext('Options..') ),
		array(40, 10, 15, 15, 10),
		array('left', 'left', 'left', 'left', 'left'),
		array(true, true, true, true, false),
		1
);
if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );


if (! isset($sort) ) { $sort = 1; }
$filtre = $dbh->listFiltre($uid, $l->getSort());



for ($i = 0; $i < sizeof($filtre); $i++) {


	if ($filtre[$i][4] == 't' ) { 
		$eier = "<img alt=\"Min\" src=\"icons/person1.gif\">"; 
		$valg = '<a href="index.php?action=match&fid=' . $filtre[$i][0] . '">' . 
			'<img alt="Open" src="icons/open2.gif" border=0></a>&nbsp;' .
			'<a href="index.php?action=filter&subaction=endre&navn=' . $filtre[$i][1] . '&fid=' . $filtre[$i][0] . '#nyttfilter">' .
			'<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;';
			
		if ($filtre[$i][3] < 1 or get_get('allowdelete') == 1 ) {
			$valg .= '<a href="index.php?action=filter&subaction=slett&fid=' . $filtre[$i][0] . '">' .
		'<img alt="Delete" src="icons/delete.gif" border=0></a>';
		} else {
			$valg .= '<img alt="Delete" title="This filter is in use in at least one filter group." src="icons/delete-grey.gif" border=0>';
		}
			
			
	} else {
		$eier = "<img alt=\"Gruppe\" src=\"icons/person100.gif\">";
		$valg = '<a href="index.php?action=equipment-filter-view&fid=' . $filtre[$i][0] . 
			'">' . '<img alt="Open" src="icons/open2.gif" border=0></a>';
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
  		$eier,
			$am, 
			$ag,
			$valg ) 
		  );
}

print "<p>";
print $l->getHTML();

print "<p>[ <a href=\"index.php?action=" . best_get('action'). "\">" .gettext("update") . " <img src=\"icons/refresh.gif\" class=\"refresh\" alt=\"oppdater\" border=0> ]</a> ";
print gettext("Number of filters: ") . sizeof($filtre);

if (get_get('allowdelete') != 1 ) {
	print '<p align="right">[ <a href="index.php?action=' . best_get('action'). '&allowdelete=1">Allow removal of filters in use</a> ]';
}

?>

</td></tr>
</table>
