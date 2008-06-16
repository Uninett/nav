<?php 
/*
 *	index.php
 *
 *	Main file for Alert profiles. All submodules will be called from this file.
 *
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



// Report all errors except E_NOTICE
error_reporting (E_ALL ^ E_NOTICE);

require_once 'config.php';
require_once 'error.php';
require_once 'php4support.php';
require_once 'databaseHandler.php';
require_once 'session.php';

require_once 'dbinit.php';

require_once 'leading_zero.function.php';
require_once 'hasPrivilege.function.php';
require_once 'check_syntax.function.php';

require_once 'auth.php';

require_once 'listing.php';

// set to the user defined error handler
$old_error_handler = set_error_handler("myErrorHandler");

header("Content-Type: text/html; charset=utf-8");


// I18N support information here
$language = 'en';

if ($login) {
	$language = session_get('lang');
}

if (get_exist('langset') && $login) {
	$dbh->setlang(session_get('uid'), get_get('langset'));
	session_set('lang', get_get('langset'));
	$language = session_get('lang');
}

putenv("LANG=$language");
putenv("LANGUAGE=$language");
setlocale(LC_ALL, $language);

// Set the text domain as 'messages'
$domain = 'messages';
bindtextdomain($domain, "./locale/");
textdomain($domain);

?>

<!-- DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>

<head>
<title><?php echo gettext('NAV Alert Profiles'); ?></title>
<meta name="keywords" content="nav, alert, sms, network, failure, message, itea, uninett">
<meta name="author" content="Andreas &Aring;kre Solberg">
<meta name="description" content="Alert Profiles is a subsystem of NAV (Network Administration Visualized) which handles alert subscription administration.">
<meta http-equiv="content-type" content="text/html; charset=utf-8">
<link rel="Home" href="../">
<link rel="Author" href="mailto:andrs@uninett.no">
<link rel="Stylesheet" type="text/css" media="all" charset="utf-8" href="css/stil.css">
<style type="text/css" media="all">@import "css/stil.css";</style>

</head>

<body bgcolor="#ffffff" text="#000000" -->


<!-- INCLUDE HEADER -->
<?php
$interpreter = $_ENV['PYTHONHOME'] ? $_ENV['PYTHONHOME'] . '/bin/python' : "";
$cmd = $interpreter . ' ' . PATH_BIN . '/navTemplate.py user=' . session_get('bruker') . 
	' content=%%% path=AlertProfiles:/alertprofiles 2>&1';

exec($cmd, $out, $retval );

/* exec('export', $aaa); echo '<pre>' . implode("\n", $aaa) . '</pre>'; */

$pyhtml = implode("\n",$out);

if ($retval == 0) {
	//echo '<h1>' . `which python`. ":::::" .$cmd . 'RetVAL:' . $retval . '</h1><pre>' . $pyhtml . '</pre>';
	
	
	if (preg_match('/^(.*)%%%/s', $pyhtml, $header) and
		preg_match('/%%%(.*?)<\/(body|BODY)>/s', $pyhtml, $footer) ) {
			
			$newheader = $header[1];
			$newheader = preg_replace('/<head>/', '<head><link rel="Stylesheet" type="text/css" media="all" charset="utf-8" href="css/stil.css">', $newheader);
			
			echo $newheader;
		
	} else {
		print '<div style="background: #ffffff; border: thin solid black; width: 100%"><h3>Error creating header. navTemplate.py returns bad content:</h3><textarea style="width: 100%; height: 20%">' . 
		$pyhtml . 
		'</textarea></div>';	
	}
	
	

} else {
	print '<div style="background: #ffffff; border: thin solid black; width: 100%"><h3>Error creating header. navTemplate.py throws errors:</h3><pre>' . 
		$pyhtml . 
		'</pre></div>';
}

?>
<!-- /INCLUDE HEADER -->






<table width="100%">
<tr><td valign="top" width="20%">

<?php

/*
	******************
	DEGBUGGING Session

print "<p>bruker:" . session_get('bruker');
print "<br>admin:" . session_get('admin');
print "<br>uid:" . session_get('uid');
print "<br>login:" . session_get('login');
print "<br>visoversikt:" . session_get('visoversikt');
print "<br>Nlogin:" . $login;
 */	



/* 
 * Menu class
 */
class Meny {
	var $level;
	var $files;
	var $login;
	var $adm;


	// Constructor
	function Meny($login) {
		$this->login = false;
		$this->adm = 0;
		if ($login) { 
			$this->login = $login;
			$this->adm = session_get('admin'); 
		} 	
	}

	function newOption($name, $action, $actionnow, $level, $files) {

		if ($this->adm >= $level) {
			if ($action != $actionnow) {
				print "<A href=\"index.php?action=" . $action . "\">";
			}
			print $name;
			if ($action != $actionnow) {			
				print "</A>";
			}
			print "<br>\n";
		}
		
		$this->level{$action} = $level;
		$this->files{$action} = $files;
	}
	
	function newModule($action, $level, $files) {
		$this->level{$action} = $level;
		$this->files{$action} = $files;
	}	
	
	
	function fileInclude($action) {

		if ($this->login) { // Er man innlogget?

			// Har man tilgang til modulen man skal laste?
			if (isset($this->level{$action}) ) {
				if ($this->adm >= $this->level{$action} ) {
					return $this->files{$action};


				} else {
					$ne = new Error(3, 1);
					$ne->message = gettext("You have <b>no access</b> to this module.");
					$error[] = $ne;
				}
			} else { // Vises som default...
				return array('modules/overview.php');
			}
		} 
		// Vises til de som ikke er innlogget.
		return array('modules/welcome.php');

	}
	

}

?>

<table class="meny">
	<caption>
		<?php echo gettext('Alert Profiles'); ?>
	</caption>
<tr><td>
<?php

if ( get_get('action')  ) {
	session_set('action', get_get('action') );
}

$meny = NEW Meny($login);

echo '<p><img src="icons/person1.gif" style="float: right">';
$meny->newOption(gettext("My active profile"), "oversikt", session_get('action'), 0, array('modules/overview.php') );
$meny->newOption(gettext("Profiles"), "profil", session_get('action'), 1, array('modules/alert-profile.php') );
$meny->newOption(gettext("Filter groups"), "utstyr", session_get('action'), 1, array('modules/equipment-group-private.php') );
$meny->newOption(gettext("Filters"), "filter", session_get('action'), 1, array('modules/equipment-filter-private.php') );

if (access_sms(session_get('bruker'))) {
	// Just creating a simple link, as the menu class isn't usable for
	// linking to other subsystems.
	print '<a href="/mysms/">' . gettext("My SMS") . "</a><br>\n";
}

echo "<hr><p>";
$meny->newOption(gettext("My permissions"), "account-info", session_get('action'), 1, array('modules/account-info.php') );
$meny->newOption(gettext("Addresses"), "adress", session_get('action'), 1,array('modules/address.php') );
$meny->newOption(gettext("Alert language"), "language", session_get('action'), 1, array('modules/language-settings.php') );
$meny->newOption(gettext("WAP setup"), "wap", session_get('action'), 1, array('modules/wap-setup.php') );
$meny->newOption(gettext("Help"), "hjelp", session_get('action'), 1, array('modules/help.php') );

if (session_get('admin') >= 100) {
	echo '<hr><p><span style="font-weight: bold">Admin menu</span><img src="icons/person100.gif" style="float: right"><br>';
}
/*
$meny->newOption(gettext("Users"), "admin", 1000, array('modules/user-admin.php') );
*/
$meny->newOption(gettext("Public access"), "filter-group-access", session_get('action'), 100, array('modules/filter-group-access.php') );
$meny->newOption(gettext("Public filter groups"), "futstyr", session_get('action'), 100, array('modules/equipment-group-public.php') );
$meny->newOption(gettext("Public filters"), "ffilter", session_get('action'), 100, array('modules/equipment-filter-public.php') );
$meny->newOption(gettext("Filter variables"), "filtermatchadm", session_get('action'), 100, array('modules/filtermatch-admin.php') );
$meny->newOption(gettext("Log"), "logg", session_get('action'), 20, array('modules/log.php') );







$meny->newModule('periode', 1, array('modules/timeperiod.php') );
$meny->newModule('periode-setup', 1, array('modules/timeperiod-setup.php') );
$meny->newModule('utstyrgrp', 1, array('modules/equipment-group-setup.php') );
$meny->newModule('equipment-group-view', 1, array('modules/equipment-group-view.php') );
$meny->newModule('equipment-filter-view', 1, array('modules/equipment-filter-view.php') );
$meny->newModule('match', 1, array('modules/equipment-filter-setup.php') );
//$meny->newModule('brukertilgruppe', 50, array('modules/user-to-group-admin.php') );

?>

</td></tr>
</table>







<div class="noCSS">
<table class="meny">
<tr><td class="menyHead">
<?php
echo '<p><b>' . gettext('StyleSheets') . '</b>';
echo '</td></tr>';
echo '<tr><td>';
echo '<p>';
echo gettext("Your Internet browser do not support style sheets. We reccomend using a browser which support style sheets with Alert Profiles.");
?>
</td></tr>
</table>
</div>

</td>

<td valign="top" align="left" class="main" width="80%">

<?php

// Shows errors if occured
flusherrors();

/*
 * Hovedmeny. Her velger man alle undersidene..
 * variablen action settes i URL'en.
 */

$filer = $meny->fileInclude(session_get('action') );
foreach($filer as $incfile) {

	if( file_exists($incfile)) {
		require($incfile);
	} else {
		$nerror = new Error(4);
		$nerror->message = gettext("Could not read file") . " &lt;" . $incfile . "&gt;";
/* 		print '<pre>DEBUG ERRORS'; */
/* 		print_r($error); */
/* 		print '</pre>'; */
		$error[] = $nerror;

	}
}
flusherrors();


?>

</td></tr></table>
<?php
include("dbclose.php");
echo $footer[1];
?>

</body>
</html>
