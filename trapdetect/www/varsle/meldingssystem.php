<?php
require ('meldingssystem.inc');

html_topp("Varslingsregistrering - Steg 1");

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);
if ($admin && $REMOTE_USER != $bruker) {
  print "Du er innlogget som <b>$bruker</b> med administratorrettighetene til <b>$REMOTE_USER</b><br>\n";
}
echo "<p>Velkommen til varslingsregistrering. Dette er en 3-stegsprosess der
du må gjennom følgende punkter:";

echo "<ul><li>Steg 1: Valg av hendelse for varsling";
echo "<li>Steg 2: Valg av eventuelle enheter.";
echo "<li>Steg 3: Valg av varslingstype";
echo "</ul></p>";

echo "<hr width=90%>";

print "<p><h3>STEG 1 AV 3</h3>Her er alle hendelser du har tilgang til med <b>$bruker</b> sin ";
print "organisasjonstilhørighet. Velg hendelse du vil abonnere på og trykk <b>gå videre</b>.</p>\n";

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

# Henter brukerid
$sporring = "select id from bruker where bruker='$bruker'";
$svar = pg_exec($dbh,$sporring);
$brukerid = pg_fetch_row($svar,0);

############################################
# Henter alle traps som bruker abonnerer på
############################################
$sporring="select trapid,syknavn from varsel,trap where brukerid=$brukerid[0] and trapid=trap.id group by trapid,syknavn order by syknavn";
$res=pg_exec($dbh,$sporring);
$res2=pg_exec($dbh,"select trapid,syknavn from unntak,trap where brukerid=$brukerid[0] and trapid=trap.id group by trapid,syknavn order by syknavn");

if (pg_numrows($res) != 0 or pg_numrows($res2) != 0) {
  for ($i=0; $i < pg_numrows($res); $i++) {
    $row=pg_fetch_row($res,$i);
    $traps[$row[0]] = $row[1];
  }
  for ($i=0; $i < pg_numrows($res2); $i++) {
    $row=pg_fetch_row($res2,$i);
    $traps[$row[0]] = $row[1];
  }
  $traps = array_values($traps);
}


##############################################
# Henter suboider fra databasen og hiver de 
# inn i et array til senere bruk.
# Spør etter organisasjonsforhold, 
# som kan være flere for en bruker
##############################################
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
  if (sizeof($traps) != 0) {
    if (!in_array($row['syknavn'],$traps)) {
      echo "<option value=".$row["syknavn"].">".$row["syknavn"]."\n";
      $besk[$row["syknavn"]] = $row["beskrivelse"];
    }
  } else {
    echo "<option value=".$row["syknavn"].">".$row["syknavn"]."\n";
    $besk[$row["syknavn"]] = $row["beskrivelse"];    
  }
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

knapp_hovedside($bruker,"Angre");

echo "</body></html>";

?>