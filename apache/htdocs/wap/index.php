<?php
	header("Content-type: text/vnd.wap.wml");  

	print '<?xml version="1.0" encoding="UTF-8"?>'; 
	print '<!DOCTYPE wml PUBLIC "-//WAPFORUM//DTD WML 1.1//EN" "http://www.wapforum.org/DTD/wml_1.1.xml">';
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
    print gettext("Hele portalen blir sperret når ikke databasen er tilgjenglig.");
    exit(0);
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
		print "<p>Wapnøkkel er ugyldig.</p></card></wml>";
		exit(0);	
	}

} else {
	print "<p>Du må oppgi wapnøkkel i urlen.</p></card></wml>";
	exit(0);
}

print "<p>Du er logget inn som <br/>" . $user[1]. "</p>";


if ( get_exist('p') ) {
	$dbh->aktivProfil($user[0], get_get('p') );
	$dbh->nyLogghendelse($user[0], 9, "Endret profil med WAP til (id=" . get_get('p') . ")");
	print '<p>Aktiv profil er endret</p>';
}

print '<p><b>Aktiv profil</b></p>';


$profiler = $dbh->listprofiler($user[0]);

print '<p><select name="p">';

for ($i = 0; $i < sizeof($profiler); $i++) {
	print '<option value="' . $profiler[$i][0] . '" '; 
	if ($brukerinfo[4] == $profiler[$i][0]) print 'selected'; 
	print '>' . $profiler[$i][1] . '</option>';
}

if (sizeof($profiler) < 1) {
	print '<option value="0">Ingen profiler..</option>';
}

print '</select></p>';


print '<do type="accept" label="Bytt profil" >';
#print '<postfield name="p" value="$(p)" />';
print '<go href="?k=' . get_get('k') . '&amp;p=$(p:escape)"/></do>';


print '</card></wml>';

pg_close($dbcon);
?>
