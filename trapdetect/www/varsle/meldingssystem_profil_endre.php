<?php 

require('meldingssystem.inc');
html_topp("Endringen er lagret");

$vars = $HTTP_POST_VARS;
if ($vars[sms] == 'on') {
  $vars[sms] = 'Y';
} else {
  $vars[sms] = 'N';
}
#skrivpost($vars);

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);

# Oppretter kontakt med databasen.
$dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");

########################################
# Legger data inn i databasen
# Gjøres ved å oppdatere det som er der 
# fra før.
########################################
if ($admin && $ny) {
  $sporring = "insert into bruker (bruker,mail,tlf,status,sms,dsms_fra,dsms_til) values ";
  $sporring .= "('$bruker','$vars[mail]','$vars[tlf]','$vars[status]','$vars[sms]','$vars[dsmsfra]','$vars[dsmstil]')";
  $done = pg_exec($sporring);

  $hent_id = pg_exec("select id from bruker where bruker='$bruker'");
  $res = pg_fetch_array($hent_id,0);
  
  foreach ($vars[org] as $element) {
    pg_exec("insert into brukeriorg (brukerid,orgid) values ($res[id],$element)");
  }
} else {
  $hent_id = pg_exec("select id from bruker where bruker='$bruker'");
  $res = pg_fetch_array($hent_id,0);
  if ($admin) {
    $sporring = "update bruker set mail='$vars[mail]',tlf='$vars[tlf]',status='$vars[status]'";
    $sporring .= ",sms='$vars[sms]', dsms_fra='$vars[dsmsfra]',dsms_til='$vars[dsmstil]' where bruker='$bruker'";

    if ($vars[org]) {
# Sletter alle innlegg med denne brukerid
      $slett = pg_exec("delete from brukeriorg where brukerid=$res[id]");
# Legger inn alle valgte orgid
      foreach ($vars[org] as $element) {
	pg_exec("insert into brukeriorg (brukerid,orgid) values ($res[id],$element)");
      }
    }
  } else {
    $sporring = "update bruker set mail='$vars[mail]',tlf='$vars[tlf]',status='$vars[status]'";
    $sporring .= ",dsms_fra='$vars[dsmsfra]',dsms_til='$vars[dsmstil]' where bruker='$bruker'";
  }
  $done = pg_exec($sporring);
}
#print "$sporring<br>\n";

# Skriver status-melding
if ($done) {
  print "Databasen oppdatert. Gå tilbake til hovedsiden<br>\n";
} else {
  print "En feil skjedde under innlegging i databasen. Gå tilbake til hovedsiden<br>\n";
}

# Skriver tilbake-til-hovedsidenknapp
knapp_hovedside($bruker);

?>

</body></html>