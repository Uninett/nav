<?php
/*
 * $Id$
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
error_reporting(0);

	header("Content-type: text/vnd.wap.wml");  

	echo '<?xml version="1.0" encoding="UTF-8"?>'; 
	echo '<!DOCTYPE wml PUBLIC "-//WAPFORUM//DTD WML 1.1//EN" "http://www.wapforum.org/DTD/wml_1.1.xml">';
?>

<wml>
<card id="main" title="NAVprofiles">

<?php

$filename = "/usr/local/nav/local/etc/conf/db.conf";

// Get fileconfiglines            
$conffile = file($filename);

// Init variables, in case they dont exist in config file...
$dhost = "localhost";
$dport = "5432";
$ddb = "navprofiles";
$duser = "navprofile";
$dpass = "";

foreach ($conffile as $confline) {
    $tvar = split('=', trim($confline));
    $prop = trim($tvar[0]); $value = trim($tvar[1]);

    switch ($prop) {
        case 'dbhost'		: $dhost = $value; break;
        case 'dbport'		: $dport = $value; break;
        case 'db_navprofile'	: $ddb   = $value; break;
        case 'script_navprofile' 	: $duser = $value; break;
        case 'userpw_navprofile' 	: $dpass = $value; break;
    }
}

$cstr = "user=$duser password=$dpass dbname=$ddb";         
//echo "<p>" . $cstr;

if (! $dbcon = pg_connect($cstr) ) {
    echo gettext("<p>Database error! Sorry.</p></card></wml>");
    exit();
} 
            
require("db.php");
require("varlib.php");

$dbh = new WDBH($dbcon);


/*
 *	OVERSIKT OVER VARIABLER
 *		k wapkey
 *		p profilid på brukerprofil det byttes til..
 *		
 *
 *
 */


if (get_exist('k') ) {
	$user = $dbh->sjekkwapkey(get_get('k'));
	
	if ($user[0] == 0) {
		echo "<p>WAP key is invalid.</p></card></wml>";
		exit();	
	}

} else {
	echo "<p>WAP key not submitted.</p></card></wml>";
	exit();
}

echo "<p>You are successfully logged in as <br/>" . $user[1]. "</p>";



if ( get_exist('p') ) {
	$nyprofil = get_get('p') == 0 ? 'null' : get_get('p');
	$dbh->aktivProfil($user[0], $nyprofil );
	$dbh->nyLogghendelse($user[0], 9, "Active profile is changed to (id=" . get_get('p') . ")");
	echo '<p>Active profile is changed. (new id: ' . $nyprofil . ')</p>';
}

echo '<p><b>Active profile:</b></p>';

$profiler = $dbh->listprofiler($user[0]);
$selval = is_null($user[3]) ? 0 : $user[3];

echo '<p><select name="p" value="' . $selval . '" ivalue="' . $selval . '">' . "\n";
echo '<option value="0">No active profile</option>' . "\n";

for ($i = 0; $i < sizeof($profiler); $i++) {
	echo '<option value="' . $profiler[$i][0] . '">' . 
		$profiler[$i][1] . '</option>' . "\n";
}

if (sizeof($profiler) < 1) {
	echo '<option value="0">No profiles..</option>';
}

echo '</select></p>';


echo '<do type="accept" label="Change profile" >';
#echo '<postfield name="p" value="$(p)" />';
echo '<go href="?k=' . get_get('k') . '&amp;p=$(p:escape)"/></do>';


echo '</card></wml>';

pg_close($dbcon);
?>
