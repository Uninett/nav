<?php require('include.inc'); ?>
<?php require('statistikk.inc'); ?>

<?php tittel("Oversikt over OID'er innkommet") ?>

Viser oversikt over alle ulike traps som er kommet inn. Du kan bruke de to variablene dato og antall dager for å bestemme henholdsvis hvilken dato du skal starte på (default i dag) og hvor langt bakover i tid du skal se (default ingen).

<?php topptabell(statistikk) ?>

<?php

echo "<form action=statistikk_ant.php method=GET>\n";
if (!$dato) {
  $dato = date(dmy);
}
if (!$dager) {
  $dager = 0;
}
echo "<table><tr><td>Startdato</td>\n";
echo "<td>Dager bakover i tid</td></tr>";
echo "<tr><td><input type=text name=dato size=6 maxlength=6 value=$dato></td>\n";
echo "<td><input type=text name=dager size=2 maxlength=2 value=$dager></td><br>";
echo "<td><input type=submit value=Submit></td></tr></table>\n";
echo "</form>\n";


# Fikser overskrift
if ($dager == 0) {
  echo "<p><center><h3>Antall traps inn ".$dato." </h3></center></p>";
} else {
  $ar = substr($dato,-2);
  $temp = substr($dato,0,4);
  $dag = substr($temp,0,2);
  $mnd = substr($temp,-2);
  $tmpdato = date ("dmy",mktime(0,0,0,$mnd,$dag-$dager,$ar));
  echo "<p><center><h3>Antall traps inn i tidsrommet ".$tmpdato." - ".$dato." </h3></center></p>";
}

function lagDatatmp() {

  global $dato, $dager;

#  $dbh = pg_Connect ("dbname=trapdetect user=trapdetect password=tcetedpart");
  $dbh = pg_Connect ("dbname=manage user=manage password=eganam");

  $ar = substr($dato,-2);
  $temp = substr($dato,0,4);
  $dag = substr($temp,0,2);
  $mnd = substr($temp,-2);

  $teller = 0;
  $data = array();
  while ($teller <= $dager) {
    $dbdato = date ("Y-m-d",mktime(0,0,0,$mnd,$dag-$teller,$ar));

    $sporring = "SELECT count(trapsource),trapsource FROM status WHERE fra LIKE '%$dbdato%' group by trapsource";
    $result = pg_exec($dbh,$sporring) or die ("Fikk ingenting fra databasen.");

    $antall = pg_numrows($result);
    for ($i=0;$i<$antall;$i++) {
      $row = pg_fetch_row ($result,$i);
      $data[$row[1]] += $row[0];
    }
    $teller++;
  }

  $keys = array_keys($data);
  $key = current($keys);
  $max = 0;
  while ($key) {
    if ($data[$key] > $max) { 
      $max = $data[$key];
    }
    $key = next ($keys);
  }

# Sortering:
  if ($sort) {

  } else {
# Sorterer default etter størrelse
    arsort ($data);
  }
  return array ($data,$max);
}

# Tingen som gjør noe begynner her. Sjekk også statistikk.inc.

list ($data,$max) = lagDatatmp();
list ($imagemap, $bilde) = tegnBilde($data,$max);
$antall = sizeof($imagemap);

echo "<center><img src=\"pics/$bilde.png\" usemap=\"#map\" border=0></center>\n";
# Tegner opp imagemap
echo "<map name=\"map\">";
for ($i = 0; $i < $antall; $i++) {
  $name = key ($imagemap);
  list($x,$y,$xx,$yy) = $imagemap[$name];
  echo "<area shape=rect href=\"statistikk_ant_det.php?navn=$name&dato=$dato&dager=$dager\" coords=\"$x,$y,$xx,$yy\">\n";
  next($imagemap);
}
echo "</map>";

?>

<?php bunntabell() ?>
