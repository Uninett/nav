<?php 
/*
 *	index.php
 *
 *	Main file for NAVuser. All submodules will be called from this file.
 *
 */


// Report all errors except E_NOTICE
error_reporting (E_ALL ^ E_NOTICE);

require("session.php");
require("databaseHandler.php");
require("dbinit.php");

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
<title><?php echo gettext('NAVuser'); ?></title>
<link rel="stylesheet" type="text/css" media="all" charset="utf-8" href="css/stil.css">
<style type="text/css" media="all">@import "css/stil.css";</style>
<meta http-equiv="content-type" content="text/html; charset=utf-8">
</head>

<body bgcolor="#ffffff" text="#000000">


    <div style="position:absolute; right:0px; top: 0px; width: 100%; height: 71; background-image:url('/images/main/navlogo+background.gif'); background-repeat: no-repeat; "></div>
    <div style="position:absolute; left: 30px; top: 71px; width: 95%; margin: 0px; padding: 0px">
      <table cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
          <td width="0%" valign="top" style="padding: 1px 15px 0px 5px;"><a class="navbar" href="#">Preferences</a></td>
          <td width="0%" valign="top"><img src="/images/main/navbar-separator.gif" alt="" /></td>
          <td width="0%" valign="top" style="padding: 1px 15px 0px 5px;"><a class="navbar" href="/index.py/toolbox">Toolbox</a></td>
          <td width="0%" valign="top"><img src="/images/main/navbar-separator.gif" alt="" /></td>
	  <td width="0%" valign="top" style="padding: 1px 15px 0px 5px;"><a class="navbar" href="#">Useradmin</a></td>
          <td width="0%" valign="top"><img src="/images/main/quicklink-start.gif" alt="" /></td>
          <td width="0%" valign="top" style="background-image:url('/images/main/quicklink-fill.gif'); background-repeat: none">
          <select>
            <option> Choose a tool </option>
            <option> Network Explorer </option>
	    <option> VlanPlot </option>
	    <option> RaGen </option>
	    <option> Cricket </option>
	    <option> Device Browser </option>
	  </select>
          </td>
          <td width="0%" valign="top"><img src="/images/main/quicklink-end.gif" alt="" /></td>
          <td width="100%" valign="top" align="right"><img src="/images/main/navbar-separator.gif" alt="" /></td>
          <td width="0%" valign="top" style="padding: 1px 5px 0px 5px;"><a class="navbar" href="/index.py/logout">Logout</a></td>
      </tr>
    </table>
  </div>

  <img src="/images/blank.gif" height="100" alt="blank"><br>







<table width="100%">
<tr><td valign="top" width="20%">

<?php

/*
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
					$error->message = gettext("Du forsøkte å hente inn en submodul som din bruker ikke har tilgang til. Forsøk å logge ut og inn igjen, og hvis det fortsatt ikke fungerer varsle systemadministrator.");
					print $error->getHTML();
				}
			} else { // Vises som default...
				return array('oversikt.php', 'velkommen.php');
			}
		} 
		// Vises til de som ikke er innlogget.
		return array('velkommen.php');

	}
	

}

?>

<table class="meny">
<tr><td class="menyHead">
<p><?php echo gettext('NAV Meny'); ?>
</td></tr>

<tr><td>
<?php

if ( get_get('action')  ) {
	session_set('action', get_get('action') );
}

$meny = NEW Meny($login);

print "<P>";
$meny->newOption(gettext("Oversikt"), "oversikt", 0, array('oversikt.php', 'velkommen.php') );
$meny->newOption(gettext("Adresser"), "adress", 1,array('adress.php') );
$meny->newOption(gettext("Profiler"), "profil", 1, array('profil.php') );
$meny->newOption(gettext("Utstyrsgrupper"), "utstyr", 1, array('utstyr.php') );
$meny->newOption(gettext("Utstyrsfiltre"), "filter", 1, array('filter.php') );
$meny->newOption(gettext("Hjelp"), "hjelp", 1, array('hjelp.php') );

print "<p>";
$meny->newOption(gettext("WAP-oppsett"), "wap", 1, array('wap.php') );
$meny->newOption(gettext("Endre passord"), "passord", 1, array('endrepassord.php') );

print "<p>";
$meny->newOption(gettext("Brukere"), "admin", 105, array('admin.php') );
$meny->newOption(gettext("Brukergrupper"), "gruppe", 105, array('gruppe.php') );
$meny->newOption(gettext("Felles Utst.grp."), "futstyr", 100, array('fellesutstyr.php') );
$meny->newOption(gettext("Felles Utst.filter"), "ffilter", 100, array('fellesfilter.php') );
$meny->newOption(gettext("Adm. match-felt"), "filtermatchadm", 100, array('filtermatchadm.php') );
$meny->newOption(gettext("Logg"), "logg", 20, array('logg.php') );


$meny->newModule('periode', 1, array('periode.php') );
$meny->newModule('utstyrgrp', 1, array('utstyrgrp.php') );
$meny->newModule('futstyrgrp', 100, array('fellesutstyrgrp.php') );
$meny->newModule('match', 1, array('match.php') );
$meny->newModule('brukertilgruppe', 50, array('velgbrukergrupper.php') );

?>

</td></tr>
</table>


<table class="meny">
<tr><td class="menyHead">
<p><?php echo gettext('Innlogging'); ?>
</td></tr>

<tr><td>
<?php

/*
 * Innloggingsvindu. Viser innloggingsfelt om man ikke er logget inn.
 * Ellers viser den brukernavn som er innlogget.
 */

if ( $login) {
  print "<p>" . gettext("Du er logget inn som ") . session_get('bruker');
//  print "<p><a href=\"index.php?action=logout\">" . gettext("Logg ut") . "</a>";
} else {
	echo "<p>" . gettext("Du er dessverre ikke innlogget korrekt.");
}

?>

</td></tr>
</table>




<table class="meny">
<tr><td class="menyHead">
<p><?php
	echo gettext("Velg språk");
?>
</td></tr>


<!-- ************* LANGUAGE HANDLING ************* -->
<tr><td>
<?php

print '<table width="100%" border="0"><tr><td width="50%"><p align="center">';
if ($language == 'en') {
	print '<img src="icons/gbr.png" alt"' . gettext("Engelsk") . '">';
} else {
	if ($login) { 
		print '<a href="index.php?langset=en">';
	}
	print '<img src="icons/gbrg.png" alt"' . gettext("Engelsk") . '">';
	if ($login) { 
		print '</a>';
	}

}
print '</td><td width="50%"><p align="center">';
if ($language == 'no') {
	print '<img src="icons/nor.png" alt"' . gettext("Norsk") . '">';
} else {
	if ($login) { 
		print '<a href="index.php?langset=no">';
	}
	print '<img src="icons/norg.png" alt"' . gettext("Norsk") . '">';
	if ($login) { 
		print '</a>';
	}
}
print '</td></tr></table>';

if ($langset) {
	echo gettext("Velkommen!"); 
}

?>
</td></tr>
<!-- **************** ***************** -->


</table>







<div class="noCSS">
<table class="meny">
<tr><td class="menyHead">
<?php
echo '<p><b>' . gettext('StyleSheets') . '</b>';
echo '</td></tr>';
echo '<tr><td>';
echo '<p>';
echo gettext("Du har en nettleser som ikke støtter stylesheets. Vi anbefaler bruk av en nettleser som støtter stylesheets.");
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
		$error->message = gettext("Kan ikke lese filen") . " &lt;" . $incfile . "&gt;";
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
?>

</body>
</html>
