<?php

require("meldingssystem.inc");
html_topp("$HTTP_POST_VARS[bruker] slettet");
#skrivpost($HTTP_POST_VARS);

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);

if ($admin && $slett1 && $slett2) {
$dbh = pg_Connect ("dbname=trapdetect user=trapdetect password=tcetedpart");

  $sporring = "select id from bruker where bruker='$bruker'";
  $res = pg_exec($sporring);
  $svar = pg_fetch_array($res,0);

  # Sletter alt i alle tabeller.
  $sporring = "delete from bruker where bruker='$bruker'";
  pg_exec($sporring);
  $sporring = "delete from brukeriorg where brukerid=$svar[id]";
  pg_exec($sporring);
  $sporring = "delete from varsel where brukerid=$svar[id]";
  pg_exec($sporring);
  $sporring = "delete from unntak where brukerid=$svar[id]";
  pg_exec($sporring);

  print "$bruker slettet, gå tilbake til hovedsiden<br>\n";
  knapp_hovedside($REMOTE_USER);
} elseif ($admin) {
  print "Du må trykke på begge knappene for å verifisere slettingen<br>\n";
  knapp_hovedside($bruker);
} else {
  print "Du har ikke rettigheter til denne operasjonen, gå tilbake til hovedsiden<br>\n";
  knapp_hovedside($bruker);
}

print "</body></html>\n";
?>