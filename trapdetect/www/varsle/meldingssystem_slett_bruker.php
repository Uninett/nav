<?php

require("meldingssystem.inc");
html_topp("$HTTP_POST_VARS[bruker] slettet");
#skrivpost($HTTP_POST_VARS);

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);

if ($admin && $slett1 && $slett2) {
$dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");

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

  print "$bruker slettet, gå tilbake til varslingssiden<br>\n";
  knapp_hovedside($REMOTE_USER,'Varslingsside');
} elseif ($admin) {
  print "Du må trykke på begge knappene for å verifisere slettingen<br>\n";
  knapp_hovedside($bruker,'Varslingsside');
} else {
  print "Du har ikke rettigheter til denne operasjonen, gå tilbake til varslingssiden<br>\n";
  knapp_hovedside($bruker,'Varlsingsside');
}

print "</body></html>\n";
?>