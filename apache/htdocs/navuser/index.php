<?php 
include("dbinit.php"); 
include("auth.php");

header("Content-Type: text/html; charset=utf-8");

include("listing.php");
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

function menyOption($name, $action, $level, $login) {
	$adm = 0;
	if ($login) { 
		$adm = session_get('admin'); 
	} 
	if ($adm >= $level) {
		print "<A href=\"index.php?action=" . $action . "\">";
		print $name;
		print "</A><BR>\n";
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

print "<P>";
menyOption("Oversikt", "oversikt", 0, $login);
menyOption("Adresser", "adress", 1, $login);
menyOption("Profiler", "profil", 1, $login);
menyOption("Utstyrsgrupper", "utstyr", 1, $login);
menyOption("Utstyrsfiltre", "filter", 1, $login);
menyOption("Hjelp", "hjelp", 1, $login);

print "<p>";
menyOption("WAP-oppsett", "wap", 1, $login);
menyOption("Endre passord", "passord", 1, $login);

print "<p>";
menyOption("Brukere", "admin", 50, $login);
menyOption("Brukergrupper", "gruppe", 100, $login);
menyOption("Felles Utstgrp.", "futstyr", 100, $login);
menyOption("Logg", "logg", 20, $login);

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
switch( session_get('action') ) {
  case 'admin' : include('admin.php'); break;
  case 'profil' : include('profil.php'); break;
  case 'adress' : include('adress.php'); break;
  case 'utstyr' : include('utstyr.php'); break;
  case 'futstyr' : include('fellesutstyr.php'); break;  
  case 'utstyrgrp' : include('utstyrgrp.php'); break;
  case 'periode' : include('periode.php'); break;
  case 'filter' : include('filter.php'); break; 
  case 'match' : include('match.php'); break;
  case 'brukertilgruppe' : include('velgbrukergrupper.php'); break;
  case 'gruppe' : include('gruppe.php'); break;
  case 'wap' : include('wap.php'); break;  
  case 'hjelp' : include('hjelp.php'); break;    
  default :
  if ($login) include('oversikt.php');
  	include('velkommen.php');
}

// Viser feilmelding om det har oppstÂtt en feil.
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
