<?php require('include.inc'); ?>
<?php require('statistikk.inc'); ?>

<?php tittel("TrapDetect") ?>

Denne siden viser oversikt over hvilke enheter som har sendt ut denne trapen. Oversikten er begrenset til å vise
antall traps, mer detaljert informasjon må finnes på status, eller i hendelsesregistret.

<?php topptabell(statistikk) ?>

<?php

if ($dager > 0) {
  $ar = substr($dato,-2);
  $temp = substr($dato,0,4);
  $dag = substr($temp,0,2);
  $mnd = substr($temp,-2);
  $tmpdato = date ("dmy",mktime(0,0,0,$mnd,$dag-$dager,$ar));
  echo "<center><p><h3>Antall $oid-traps mottatt i tidsrommet $tmpdato-$dato</h3></p></center>\n";
} else {
  echo "<center><p><h3>Antall $oid-traps mottatt den $dato</h3></p></center>\n";
}

function lagDataDettmp () {

  global $dato, $dager, $oid;

  $dbh = pg_Connect ("dbname=manage user=manage password=eganam");

  $ar = substr($dato,-2);
  $temp = substr($dato,0,4);
  $dag = substr($temp,0,2);
  $mnd = substr($temp,-2);

  $teller = 0;
  while ($teller <= $dager) {
    $dbdato = date ("Y-m-d",mktime(0,0,0,$mnd,$dag-$teller,$ar));

    $sporring = "SELECT * FROM status WHERE fra LIKE '%$dbdato%' AND trap='$oid'";
    $result = pg_exec($dbh,$sporring) or die ("Fikk ingenting fra databasen.");
    $antall = pg_numrows($result);
    array ($data);

    for ($i=0;$i<$antall;$i++) {
      $row = pg_fetch_array ($result,$i);
      $data[$row["trapsource"]] ++;
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

  return array ($data,$max);

}

list ($data,$max) = lagDataDettmp();
list ($imagemap, $bilde) = tegnBilde($data, $max);

echo "<center><img src=\"pics/$bilde.png\" usemap=\"#map\" border=0></center>";

$antall = sizeof($imagemap);
echo "<map name=\"map\">";
for ($i = 0; $i < $antall; $i++) {
  $navn = key ($imagemap);
  list($x,$y,$xx,$yy) = $imagemap[$navn];
  echo "<area shape=rect href=\"statistikk_meldinger.php?name=$navn&date=$dato&antdager=$dager&oid=$oid\" coords=\"$x,$y,$xx,$yy\">\n";
  next($imagemap);
}
echo "</map>";
?>


<?php bunntabell() ?>
