<?php 
require("session.php");
require("databaseHandler.php");
require("dbinit.php");

require("auth.php");

header("Content-Type: text/html; charset=utf-8");


// I18N support information here
$language = 'no';

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
<title><?php echo gettext('Uninett NAV'); ?></title>
<style type="text/css" media="all">@import "css/stil.css";</style>
<style type="text/css" media="all">@import "css/listing.css";</style>
<link rel="stylesheet" type="text/css" media="all" charset="utf-8" href="css/stil.css">
<link rel="css/stylesheet" type="text/css" media="all" charset="utf-8" href="css/listing.css">

<meta http-equiv="content-type" content="text/html; charset=utf-8">
</head>

<body bgcolor="#ffffff" text="#000000">
<table width="100%">
<tr><td align="left">
<a href="index.php">
<img border="0" src="images/nav4.jpg" alt="Topplogo">
</a>
</td></tr>
</table>

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
 * Dette er en generell feilmeldingsklasse. 
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
<tr class="menyHead"><td>
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
$meny->newOption(gettext("Brukere"), "admin", 50, array('admin.php') );
$meny->newOption(gettext("Brukergrupper"), "gruppe", 100, array('gruppe.php') );
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
<tr class="menyHead"><td>
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
  print "<p><a href=\"index.php?action=logout\">" . gettext("Logg ut") . "</a>";
} else {
  print "<p>" . gettext("Du er <b>ikke</b> logget inn.");
  print "<p class=\"field\">";
  print "<form method=\"post\" action=\"index.php\">";
  print "<INPUT type=\"text\" class=\"fieldOne\" name=\"username\" value=\"";
  if (isset($username)) print $username; else print "bruker";
  print "\"><br>";
  print "<INPUT type=\"password\" class=\"fieldOne\" name=\"passwd\"><br>";
  print "<INPUT type=\"submit\" class=\"subm\" name=\"submit\" value=\"" . gettext("Logg inn") . "\">";
  print "</FORM>";
}
  
?>

</td></tr>
</table>




<table class="meny">
<tr class="menyHead"><td>
<p><?php
	echo gettext("Velg språk");
?>
</td></tr>


<!-- ************* SPRÅK HÅNDTERING ************* -->
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





<table class="meny">
<tr class="menyHead"><td>
<p><?php echo gettext('Kontakt'); ?>
</td></tr>

<tr><td>

<p>
<b>Uninett AS</b><br>
Teknobyen<br>
Abelsgate 5<br>
7030 Trondheim
<p>
<?php 
echo gettext("Tlf: 73 55 79 00"); 
echo "<br>";
echo gettext("Fax: 73 55 79 01");
echo "<p>"; 
echo gettext("Epost:");
echo "<br>";
?>
<small><a href=mailto:info@uninett.no>info@uninett.no</a></small>

</td></tr>
</table>

<table class="meny">
<tr class="menyHead"><td>
<p><?php
	echo gettext("HTML og CSS");
?>
</td></tr>

<tr><td>
<P align="center"><a href="http://validator.w3.org/check/referer"><img border="0" src="http://www.w3.org/Icons/valid-html401" alt="Valid HTML 4.01!" height="31" width="88"></a><br>

<a href="http://jigsaw.w3.org/css-validator/"><img style="border:0;width:88px;height:31px" src="http://jigsaw.w3.org/css-validator/images/vcss" alt="Valid CSS!"></a></p>

</td></tr>
</table>



<div class="noCSS">
<table class="meny">
<tr class="menyHead"><td>
<?php
echo '<p><b>' . gettext('StyleSheets') . '</b>';
echo '</td></tr>';
echo '<tr><td>';
echo '<p>';
echo gettext("Du har en nettleser som ikke støtter stylesheets. 
Vi anbefaler bruk av en nettleser som støtter stylesheets.");
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
