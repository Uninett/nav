<?php 
/*
 *	index.php
 *
 *	Main file for Alert profiles. All submodules will be called from this file.
 *
 */


// Report all errors except E_NOTICE
error_reporting (E_ALL ^ E_NOTICE);

require("config.php");
require("databaseHandler.php");
require("session.php");

require("dbinit.php");

require("leading_zero.function.php");
require("hasPrivilege.function.php");
require("check_syntax.function.php");

require("auth.php");

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



require("listing.php");
?>

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>

<head>
<title><?php echo gettext('NAV Alert Profiles'); ?></title>
<link rel="stylesheet" type="text/css" media="all" charset="utf-8" href="css/stil.css">
<style type="text/css" media="all">@import "css/stil.css";</style>
<meta http-equiv="content-type" content="text/html; charset=utf-8">
</head>

<body bgcolor="#ffffff" text="#000000">


<!-- INCLUDE HEADER -->
<?php
exec('/usr/local/nav/bin/navTemplate.py user=' . session_get('bruker') . ' content=%%% path=AlertProfiles:/alertprofiles ', $out );

$pyhtml = implode(" ",$out);

preg_match('/<body.*?>(.*?)%%%/', $pyhtml, $header);
preg_match('/%%%(.*?)<\/body>/', $pyhtml, $footer);


echo $header[1];

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

	function newOption($name, $action, $level, $files) {

		if ($this->adm >= $level) {
			print "<A href=\"index.php?action=" . $action . "\">";
			print $name;
			print "</A><BR>\n";
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
					$error = new Error(3);
					$error->message = gettext("You have <b>no access</b> to this module.");
					print $error->getHTML();
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
<tr><td class="menyHead">
<p><?php echo gettext('NAV Menu'); ?>
</td></tr>

<tr><td>
<?php

if ( get_get('action')  ) {
	session_set('action', get_get('action') );
}

$meny = NEW Meny($login);

echo "<p>";
$meny->newOption(gettext("Overview"), "oversikt", 0, array('modules/overview.php') );
$meny->newOption(gettext("Account info"), "account-info", 1, array('modules/account-info.php') );
$meny->newOption(gettext("Addresses"), "adress", 1,array('modules/address.php') );
$meny->newOption(gettext("Profiles"), "profil", 1, array('modules/alert-profile.php') );
$meny->newOption(gettext("Equip. groups"), "utstyr", 1, array('modules/equipment-group-private.php') );
$meny->newOption(gettext("Equip. filters"), "filter", 1, array('modules/equipment-filter-private.php') );
$meny->newOption(gettext("Alert language"), "language", 1, array('modules/language-settings.php') );
$meny->newOption(gettext("WAP setup"), "wap", 1, array('modules/wap-setup.php') );
$meny->newOption(gettext("Help"), "hjelp", 1, array('modules/help.php') );

echo "<p>";
/*
$meny->newOption(gettext("Users"), "admin", 1000, array('modules/user-admin.php') );
$meny->newOption(gettext("User groups"), "gruppe", 1000, array('modules/user-group-admin.php') );
*/
$meny->newOption(gettext("Pub eq.groups"), "futstyr", 100, array('modules/equipment-group-public.php') );
$meny->newOption(gettext("Pub eq.filters"), "ffilter", 100, array('modules/equipment-filter-public.php') );
$meny->newOption(gettext("Match fields"), "filtermatchadm", 100, array('modules/filtermatch-admin.php') );
$meny->newOption(gettext("Log"), "logg", 20, array('modules/log.php') );


$meny->newModule('periode', 1, array('modules/timeperiod.php') );
$meny->newModule('periode-setup', 1, array('modules/timeperiod-setup.php') );
$meny->newModule('utstyrgrp', 1, array('modules/equipment-group-setup.php') );
$meny->newModule('equipment-group-view', 1, array('modules/equipment-group-view.php') );
$meny->newModule('match', 1, array('modules/equipment-filter-setup.php') );
$meny->newModule('brukertilgruppe', 50, array('modules/user-to-group-admin.php') );

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

// Viser feilmelding om det har oppstått en feil.
if ( $error != null ) {
  print "<table width=\"100%\" class=\"feilWindow\"><tr><td class=\"mainWindowHead\"><h2>";
  print $error->GetHeader();
  print "</h2></td></tr>";
  print "<tr><td><p>" . $error->message . "</td></tr></table>";
  $error = null;
}

/*
 * Hovedmeny. Her velger man alle undersidene..
 * variablen action settes i URL'en.
 */

$filer = $meny->fileInclude(session_get('action') );
foreach($filer as $incfile) {

	if( file_exists($incfile)) {
		require($incfile);
	} else {
		$error = new Error(4);
		$error->message = gettext("Could not read file") . " &lt;" . $incfile . "&gt;";
		print $error->getHTML();
		$error = null;
	}
}

// Viser feilmelding om det har oppstått en feil.
if ( $error != null ) {
	print "<table width=\"100%\" class=\"feilWindow\"><tr><td class=\"mainWindowHead\"><h2>";
	print $error->GetHeader();
	print "</h2></td></tr>";
	print "<tr><td><p>" . $error->message . "</td></tr></table>";
}

?>

</td></tr></table>
<?php
include("dbclose.php");
echo $footer[1];
?>

</body>
</html>
