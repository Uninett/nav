<!-- Får inn disse variable:
eier: kan være flere variable
trap: sier seg selv
bruker: brukernavn på han som er på
-->

<?php
require ('meldingssystem.inc');
html_topp('Sett på service');

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);
if ($admin && $REMOTE_USER != $bruker) {
  print "Du er innlogget som <b>$bruker</b> med administratorrettighetene til <b>$REMOTE_USER</b><br>\n";
}

$border=0;
$temp = $HTTP_POST_VARS;

$enheterav = finn_enheter('t', $bruker);
$enheterpa = finn_enheter('f', $bruker);

print "<p><h3>Sett på service</h3>Her er oversikt over alle enheter du har mulighet til å sette på service. I tabellen til venstre kan du merke de enhetene du vil sette PÅ service. I tabellen til høyre kan du merke de enhetene du vil TA AV service. Trykk så <b>OK</b></p>";

# Knapp til loggen
print "<form action=meldingssystem_service_logg.php method=POST>";
print "<input type=hidden name=bruker value=$bruker>";
print "<input type=submit value=\"Logg\">\n";
print "</form>\n";

knapp_hovedside($bruker);

##############################
# Kobler til database
##############################
$dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");
$dbh_m = pg_Connect ("dbname=manage user=navall password=uka97urgf");

$antall_enheter = sizeof($enheterpa) + sizeof($enheterav);
echo "Det er totalt $antall_enheter enheter tilgjengelig for bruker <b>$bruker</b><br>\n";

##################################################
# Skriver ut alle enhetene og merker dem som
# allerede er på service.
##################################################
echo "<form action=meldingssystem_service_sett.php method=\"POST\">";
echo "\n<table width=90%  cellpadding=3 border=$border>";
echo "<tr><td>Enheter ikke på service</td><td>Enheter på service</td></tr><tr><td>\n";

# Enheter som ikke er på service

echo "<select name=enheterav[] multiple size=20>\n";

$temp = array_keys($enheterav);
sort ($temp);
foreach ($temp as $enhet) {
  echo "<option>$enhet</option>\n";
}
echo "</select>\n";

# Enheter som er på service

echo "</td><td>\n";
echo "<select name=enheterpa[] multiple size=20>\n";

$temp = array_keys($enheterpa);
sort ($temp);
$antallpa = sizeof($temp);
if ($antallpa == 0) {
  echo "<option>Ingen</option>";
} else {
  foreach ($temp as $enhet) {
    echo "<option>$enhet</option>\n";
  }
}
echo "</select>\n";

echo "</td></tr>\n";
echo "</table>\n";

# Tabell ferdig

echo "<input type=hidden name=bruker value=$bruker>\n";
echo "<input type=submit value=\"OK\">";
echo "</form>\n";

# Stygg måte å resette på...
echo "<form action=meldingssystem_service.php method=\"POST\">";
echo "<input type=hidden name=bruker value=$bruker>\n";
echo "<input type=submit value=Reset>";
echo "</form>";

########################################
# Henter alle bokser som er på/av service
########################################
function finn_enheter($bol, $bruker) {
  $array = array();
  $dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");
  $dbh_m = pg_Connect ("dbname=manage user=navall password=uka97urgf");

  # Henter eierforhold
  $sporring = "select o.navn from bruker b, brukeriorg bio, org o where b.bruker='$bruker' and b.id=bio.brukerid and bio.orgid=o.id";
  $res = pg_exec($dbh,$sporring);
  $antall = pg_numrows($res);

  # Lager del-spørring ut fra hvor mange org bruker er medlem i.
  # Delspørring blir lagret i $temp.
  $temp = "";
  for ($i=0;$i<$antall;$i++) {
    $row = pg_fetch_array($res,$i);
    if ($i<$antall-1) {
      $temp .= "orgid='".strtolower($row[0])."' or ";
    } else {
      $temp .= "orgid='".strtolower($row[0])."'";
    }
  }

  # Lager selve spørringen.
  $sporring;
  if ($bol == 'f') {
    $sporring = "select sysname,kat from boks where active='f' and ($temp)";
  } elseif ($bol == 't') {
    $sporring = "select sysname,kat from boks where active='t' and ($temp)";
  } else {
    print "Ingen kjente boolske verdier<br>";
  }

  $result = pg_exec($dbh_m,$sporring);
  $rows = pg_numrows($result);

  for ($i=0;$i<$rows;$i++) {
    $rad = pg_fetch_row($result,$i);
    $array[$rad[0]] = $rad[1];
  }
  return $array;
}


?>

</body></html>
