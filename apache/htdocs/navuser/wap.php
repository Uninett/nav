<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p>Konfigurerering av WAP</p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();
?>

<p>Her kan du sett opp og skru av muligheten for å 
administrere din konto via en WAP-portal. Husk at du alltid må holde wapkey'en hemmelig, 
og hvis du har misstanke om at noen kan ha fått tak i den kan du generere ny wapkey her. 
Men da må du huske å oppdatere bokmerke på mobilen din.

<?php

include("databaseHandler.php");

$dbh = new DBH($dbcon);
$uid = session_get('uid');

if ($subaction == 'nykey') {
	$nk = chr (rand(0, 25) + ord('A')) .
		chr (rand(0, 25) + ord('A')) .
		rand(0, 9) . rand(0,9) .
		chr (rand(0, 25) + ord('A'));

	$dbh->settwapkey(session_get('uid'), $nk);
}
if ($subaction == 'slettkey') {
	$dbh->slettwapkey($uid);
}

;


$k = $dbh->hentwapkey($uid);
print "<h2>Wapkey</h2>";

if ($k[0] == null) {
	print "<p>Du har ingen wapkey. Du må generere en for å bruke WAP.";
	print "<p>[ <a href=\"index.php?subaction=nykey\">Generer wapkey</a> ]";	
} else {
	print "<p>Din wapkey er: <b>" . $k[0] . "</b>.";
	print "<p>Det betyr at du kan nå din brukerprofil fra denne wapsiden:<br>";
	print "<pre>http://pot.uninett.no/~andrs/nav-frontend/www/wap.php?" . $k[0] . "</pre>";

	print "<p>[ <a href=\"index.php?subaction=nykey\">Generer ny key</a> | 
<a href=\"index.php?action=wap&subaction=slettkey\">Fjern wapkey</a> ]";

}
?>

</td></tr>
</table>
