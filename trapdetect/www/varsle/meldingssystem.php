<?php
require ('meldingssystem.inc');

html_topp("Varslingsregistrering - Steg 1");

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);
if ($admin && $REMOTE_USER != $bruker) {
  print "Du er innlogget som <b>$bruker</b> med administratorrettighetene til <b>$REMOTE_USER</b><br>\n";
}
echo "<p>Velkommen til varslingsregistrering. Dette er en 3-stegsprosess der
du må gjennom følgende punkter:";

echo "<ul><li>Steg 1: Valg av Trap for varsling";
echo "<li>Steg 2: Valg av eventuelle enheter.";
echo "<li>Steg 3: Valg av varslingstype";
echo "</ul></p>";

echo "<hr width=90%>";

print "<p><h3>STEG 1</h3>Her er alle traps du har tilgang til med <b>$bruker</b> sin ";
print "organisasjonstilhørighet. Velg trap du vil abonnere på og trykk <b>gå videre</b>.</p>\n";


# Connecter til db
$dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");

# Henter alle orger bruker er medlem i

$sporring = "select org.navn from brukeriorg,org,bruker where bruker.id=brukeriorg.brukerid and brukeriorg.orgid=org.id and bruker.bruker='$bruker'";

$result = pg_exec($dbh,$sporring);
$rows = pg_numrows($result);
$eier = array();
for ($i=0;$i < $rows; $i++) {
  $row = pg_fetch_row($result,$i);
  array_push($eier,$row[0]);
}

# Henter suboider fra databasen og hiver de inn i et array til senere bruk.
# Spør etter organisasjonsforhold, som kan være flere for en bruker
$antall_org = sizeof($eier);
$sporring = "select syknavn,beskrivelse from trap,trapeier,org where (";

foreach ($eier as $navn) {
  $teller++;
  if ($teller < $antall_org) {
    $sporring .= "org.navn='".$navn."' or ";
  } else {
    $sporring .= "org.navn='".$navn."')";
  }
}

$sporring .= " and trapeier.orgid=org.id and trap.id=trapid group by syknavn,beskrivelse order by syknavn";
$result = pg_exec($dbh,$sporring);
$rows = pg_numrows($result);

echo "<form action=meldingssystem2.php method=\"POST\">";
echo "Velg trap: <select name=trap>\n";

$besk = array();

for ($i=0;$i < $rows;$i++) {
  $row = pg_fetch_array($result,$i);
# Skriver ut listen over alle oider som man kan velge å søke etter.
  echo "<option value=".$row["syknavn"].">".$row["syknavn"]."\n";
# Tar vare på bekrivelsene
  $besk[$row["syknavn"]] = $row["beskrivelse"];
}

echo "</select>\n";

# Skriver ut alle orgforholdene og navnet på bruker
echo "<input type=hidden name=bruker value=$bruker>";
foreach ($eier as $navn) {
  echo "<input type=hidden name=eier[] value=$navn>";
}
echo "<input type=submit value=\"Gå videre\">\n";
echo "</form>\n";

# Skriver ut beskrivelse av alle traps
$keys = array_keys($besk);
foreach ($keys as $key) {
  echo "<B>".$key."</B>: ".$besk[$key]."<br>\n";
}

knapp_hovedside($bruker);

echo "</body></html>";

?>