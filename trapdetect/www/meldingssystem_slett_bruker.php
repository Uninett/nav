<?php

require("meldingssystem.inc");
html_topp("$HTTP_POST_VARS[bruker] slettet");
#skrivpost($HTTP_POST_VARS);

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);

if ($admin && $slett1 && $slett2) {
  $dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");
  mysql_select_db("trapdetect", $dbh);

  $sporring = "select id from user where user='$bruker'";
  $res = mysql_query($sporring);
  $svar = mysql_fetch_array($res);

  # Sletter alt i alle tabeller.
  $sporring = "delete from user where user='$bruker'";
  mysql_query($sporring);
  $sporring = "delete from useriorg where userid=$svar[id]";
  mysql_query($sporring);
  $sporring = "delete from varsel where userid=$svar[id]";
  mysql_query($sporring);
  $sporring = "delete from unntak where userid=$svar[id]";
  mysql_query($sporring);

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