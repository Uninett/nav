<?php require('meldingssystem.inc');

html_topp("Varslingssiden for ITEA");

print "<table width=600><tr><td>\n";

if (!$bruker) {
  $bruker = $REMOTE_USER;
}
list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);

if ($admin) {
  $dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");
  $dbh_m = pg_Connect ("dbname=manage user=navall password=uka97urgf");

  print "<h1>Velkommen til admin-siden</h1>";
  print "<p>Her kan du legge til nye brukere, eller forandre på de eksisterende brukerne. I tilegg kan du forandre på alle abonnement som brukerne har. </p>";

  print "<p><b>ADMINISTRERE BRUKERE</b></p>\n";
  print "Du har adminrettigheter som bruker <b>$REMOTE_USER</b><br>\n";
  print "Du administrerer nå ";
  if ($bruker == $REMOTE_USER) {
    print "din egen konto<br>\n";
  } else {
    print "<b>$bruker</b> sin konto<br>\n";
  }
  print "Use the force... velg bruker som du skal administrere.<br>\n";
  print "<form action=meldingssystem_admin.php method=POST>\n";
  print "<select name=bruker>\n";
  $sporring = pg_exec($dbh,"select bruker from bruker");
  $antall = pg_numrows($sporring);
  for ($i=0;$i<$antall;$i++) {
    $res = pg_fetch_array($sporring,$i);
    if ($bruker == $res[bruker]) {
      print "<option value=$res[bruker] selected>$res[bruker]</option>\n";
    } else {
      print "<option value=$res[bruker]>$res[bruker]</option>\n";
    }
  }
  print "</select>\n";
  print "<input type=submit value=\"Skift bruker\">";
  print "</form>\n";

# Form for ny bruker
  print "<form action=meldingssystem_profil.php method=POST>\n";
  print "<input type=text name=bruker value=\"<brukernavn>\" size=15>\n";
  print "<input type=submit value=\"Opprett ny brukerprofil\">\n";
  print "</form>\n";

# Form for sletting av bruker
# Legger inn to bokser som begge må krysses av for å verifisere sletting
# Dette fordi det er en alvorlig sak å slette en bruker.
  print "<form action=meldingssystem_slett_bruker.php method=POST>";
  print "<form>";
  print "<input type=checkbox name=slett1>";
  print "<input type=submit name=submit value=\"Slett $bruker\">";
  print "<input type=checkbox name=slett2>";
  print "(velg begge boksene for verifisering av sletting)";
  print "<input type=hidden name=bruker value=$bruker>";
  print "</form>";

  print "<p><b>REDIGERE ABONNEMENT</b></p>\n";
  print "For å redigere abonnementene til $bruker, sender jeg deg direkte til hovedsiden med $bruker sitt navn. Dermed kan du gjøre alt som han/hun kan gjøre.<br>\n";
  knapp_hovedside($bruker,'Til varslingssiden');
} else {
  print "Du har ikke admin-rettigheter. Kom deg vekk!<br>\n";
}

print "</table>";

?>