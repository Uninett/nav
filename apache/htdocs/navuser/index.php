<?php 
require("session.php");
require("databaseHandler.php");
require("dbinit.php");


require("auth.php");

header("Content-Type: text/html; charset=utf-8");

require("listing.php");
?>

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>Uninett NAV</title>
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
		
		//return array('jalla.php', 'jalla2.php');
		
		if ($this->login) { // Er man innlogget?

			// Har man tilgang til modulen man skal laste?
			if (isset($this->level{$action}) ) {
				if ($this->adm >= $this->level{$action} ) {
					return $this->files{$action};


				} else {
					$error = new Error(3);
					$error->message = "Du forsøkte å hente inn en submodul som din bruker ikke har tilgang til. Forsøk å logge ut og inn igjen, og hvis det fortsatt ikke fungerer varsle systemadministrator.";
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
<p>NAV Meny
</td></tr>

<tr><td>
<?php

if ( get_get('action')  ) {
	session_set('action', get_get('action') );
}

$meny = NEW Meny($login);

print "<P>";
$meny->newOption("Oversikt", "oversikt", 0, array('oversikt.php', 'velkommen.php') );
$meny->newOption("Adresser", "adress", 1,array('adress.php') );
$meny->newOption("Profiler", "profil", 1, array('profil.php') );
$meny->newOption("Utstyrsgrupper", "utstyr", 1, array('utstyr.php') );
$meny->newOption("Utstyrsfiltre", "filter", 1, array('filter.php') );
$meny->newOption("Hjelp", "hjelp", 1, array('hjelp.php') );

print "<p>";
$meny->newOption("WAP-oppsett", "wap", 1, array('wap.php') );
$meny->newOption("Endre passord", "passord", 1, array('endrepassord.php') );

print "<p>";
$meny->newOption("Brukere", "admin", 50, array('admin.php') );
$meny->newOption("Brukergrupper", "gruppe", 100, array('gruppe.php') );
$meny->newOption("Felles Utst.grp.", "futstyr", 100, array('fellesutstyr.php') );
$meny->newOption("Felles Utst.filter", "ffilter", 100, array('fellesfilter.php') );
$meny->newOption("Logg", "logg", 20, array('logg.php') );


$meny->newModule('periode', 1, array('periode.php') );
$meny->newModule('utstyrgrp', 1, array('utstyrgrp.php') );
$meny->newModule('match', 1, array('match.php') );
$meny->newModule('brukertilgruppe', 50, array('velgbrukergrupper.php') );
?>

</td></tr>
</table>


<!--
<table class="meny">
<tr class="menyHead"><td>
<p>Applett-ting
</td></tr>

<tr><td>
<p><a href="/">Start Applet</a>
</td></tr>
</table>
-->


<table class="meny">
<tr class="menyHead"><td>
<p>Innlogging
</td></tr>

<tr><td>
<?php

/*
 * Innloggingsvindu. Viser innloggingsfelt om man ikke er logget inn.
 * Ellers viser den brukernavn som er innlogget.
 */

if ( $login) {
  print "<p>Du er logget inn som " . session_get('bruker');
  print "<p><a href=\"index.php?action=logout\">Logg ut</a>";
} else {
  print "<p>Du er <b>ikke</b> logget inn.";
  print "<p class=\"field\">";
  print "<form method=\"post\" action=\"index.php\">";
  print "<INPUT type=\"text\" class=\"fieldOne\" name=\"username\" value=\"";
  if (isset($username)) print $username; else print "bruker";
  print "\"><br>";
  print "<INPUT type=\"password\" class=\"fieldOne\" name=\"passwd\"><br>";
  print "<INPUT type=\"submit\" class=\"subm\" name=\"submit\" value=\"Logg inn\">";
  print "</FORM>";
}
  
?>

</td></tr>
</table>


<table class="meny">
<tr class="menyHead"><td>
<p>Kontakt
</td></tr>

<tr><td>

<p>
<b>Uninett AS</b><br>
Teknobyen<br>
Abelsgate 5<br>
7030 Trondheim
<p>
Tlf: 73 55 79 00<br>
Fax: 73 55 79 01
<p>Epost: <br>
<small><a href=mailto:info@uninett.no>info@uninett.no</a></small>

</td></tr>
</table>

<table class="meny">
<tr class="menyHead"><td>
<p>HTML og CSS
</td></tr>

<tr><td>
<P align="center"><a href="http://validator.w3.org/check/referer"><img border="0" src="http://www.w3.org/Icons/valid-html401" alt="Valid HTML 4.01!" height="31" width="88"></a><br>

<a href="http://jigsaw.w3.org/css-validator/"><img style="border:0;width:88px;height:31px" src="http://jigsaw.w3.org/css-validator/images/vcss" alt="Valid CSS!"></a></p>

</td></tr>
</table>

<div class="noCSS">
<table class="meny">
<tr class="menyHead"><td><p><b>StyleSheets</b>
</td></tr>
<tr><td>
<p>Du har en nettleser som ikke støtter stylesheets. 
Vi anbefaler bruk av en nettleser som støtter stylesheets.
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
		$error->message = "Kan ikke lese filen &lt;" . $incfile . "&gt;";
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
