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
<p><?php echo gettext('Event log'); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();
?>



<?php

echo '<p>';
echo gettext("Here is a list of the recent events on NAV Alert Profiles. ");

$brukernavn = session_get('bruker'); $uid = session_get('uid');

print "<h3>" . gettext("Log") . "</h3>";



$l = new Lister( 223,
	array(gettext('Event'), gettext('Name'), gettext('Time'), gettext('Description') ),
	array(10, 20, 20, 50),
	array('left', 'left', 'left', 'left'),
	array(true, true, true, true ),
	2
);


if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );


$logg = $dbh->listLogg($l->getSort() );

/* Set locale to norwegian */
setlocale (LC_ALL, 'no_NO');


for ($i = 0; $i < sizeof($logg); $i++) {


	$type = $logg[$i][0];
	$descr = $logg[$i][1];		
	$tid =   htmlentities (strftime ("%H:%M, %a %e %b %y", $logg[$i][2] ) );
	$navn = $logg[$i][3];

	$hikon[1] = 'in.gif';
	$hikon[2] = 'out.gif';
	$hikon[3] = 'logg_new.gif';
	$hikon[4] = 'logg_del.gif';
	$hikon[5] = 'logg_edit.gif';
	$hikon[6] = 'logg_new.gif';
	$hikon[7] = 'logg_del.gif';
	$hikon[8] = 'logg_edit.gif';
	$hikon[9] = 'logg_wap.gif';

	$hi = '<img alt="Hendelse" src="icons/' . $hikon[$type] . '">';


  $l->addElement( array($hi, $navn, $tid,  $descr
			) 
		  );
}

print $l->getHTML(1);

print "<p>[ <a href=\"index.php?action=logg\">" . gettext("update") . " <img class=\"refresh\" src=\"icons/refresh.gif\" alt=\"oppdater\" border=0> ]</a> ";
print gettext("Number of shown events: ") . sizeof($logg);


?>


</td></tr>
</table>
