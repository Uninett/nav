<?php
require ('meldingssystem.inc');
require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);
#if ($admin && $REMOTE_USER != $bruker) {
#  print "Du er innlogget som <b>$bruker</b> med administratorrettighetene til <b>$REMOTE_USER</b><br>\n";
#}

navstart('Service oppdatert',$bruker);

$postvars = $HTTP_POST_VARS;
#skrivpost($HTTP_POST_VARS);

# Connect to db
$dbh = pg_Connect ("dbname=manage user=navall password=uka97urgf");

$dato = date("d-m-Y H:i");
$log = "\n$dato endret $postvars[bruker] følgende:\n";

if (sizeof($postvars[enheterpa]) > 0) {
  foreach ($postvars[enheterpa] as $enhet) {
    $sporring = "update boks set active='t' where sysname='$enhet'";
#    print "$sporring<br>\n";
    $ok = pg_exec($sporring);
#    if ($ok) { print "Update OK<br>\n"; }
    $log .= "tok $enhet AV service\n";
  }
}

if (sizeof($postvars[enheterav]) > 0) {
  foreach ($postvars[enheterav] as $enhet) {
    $sporring = "update boks set active='f' where sysname='$enhet'";
#    print "$sporring<br>\n";
    $ok = pg_exec($sporring);
#    if ($ok) { print "Update OK<br>\n"; }
    $log .= "satte $enhet PÅ service\n";
  }
}

print "<p>Databasen er oppdatert.</p>";

$filnavn = 'servicelogg';

$fil = fopen ($filnavn, "r");
$innhold = fread ($fil, filesize($filnavn));
fclose ($fil);

$file = fopen ($filnavn, "w");
fwrite ($file, $log.$innhold);
fclose ($file);

knapp_serviceside($bruker);

navslutt();

?>


