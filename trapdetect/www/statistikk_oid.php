<?php require('include.inc'); ?>
<?php require('statistikk.inc'); ?>

<?php tittel("Oversikt over OID'er innkommet") ?>

Viser oversikt over alle ulike traps som er kommet inn. Du kan bruke de to variablene dato og antall dager for å bestemme henholdsvis hvilken dato du skal starte på (default i dag) og hvor langt bakover i tid du skal se (default ingen).

<?php topptabell(statistikk) ?>

<?php

echo "<form action=statistikk_oid.php method=GET>\n";
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


# Tingen som gjør noe begynner her. Sjekk også statistikk.inc.

list ($data,$max) = lagDatatmp();
list ($imagemap, $bilde) = tegnBilde($data,$max);
$antall = sizeof($imagemap);

echo "<center><img src=\"pics/$bilde.png\" usemap=\"#map\" border=0></center>\n";
# Tegner opp imagemap
echo "<map name=\"map\">";
for ($i = 0; $i < $antall; $i++) {
  $oid = key ($imagemap);
  list($x,$y,$xx,$yy) = $imagemap[$oid];
  echo "<area shape=rect href=\"statistikk_oid_det.php?oid=$oid&dato=$dato&dager=$dager\" coords=\"$x,$y,$xx,$yy\">\n";
  next($imagemap);
}
echo "</map>";


# Funksjon som lager et dataarray + finner maxverdi og returnerer dette.
function lagDatatmp() {

  global $dato, $dager;

  $dbh = pg_Connect ("dbname=manage user=manage password=eganam");

  $ar = substr($dato,-2);
  $temp = substr($dato,0,4);
  $dag = substr($temp,0,2);
  $mnd = substr($temp,-2);

  $teller = 0;
  $data = array();
  while ($teller <= $dager) {
    $dbdato = date ("Y-m-d",mktime(0,0,0,$mnd,$dag-$teller,$ar));

    $sporring = "SELECT trap FROM status WHERE fra LIKE '%$dbdato%' ";
    $result = pg_exec($dbh,$sporring) or die ("Fikk ingenting fra databasen.");
    $antall = pg_numrows($result);
    for ($i=0;$i<$antall;$i++) {
      $row = pg_fetch_array ($result,$i);
      $data[$row[trap]] ++;
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

  if ($sort) {
# Sorterer etter navn
  } else {
# Sorterer etter antall som default
    arsort ($data);
  }

  return array ($data,$max);
}

?>

<?php bunntabell() ?>
