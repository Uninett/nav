<?php require('include.inc'); ?>

<?php tittel("TrapDetect") ?>

Her er en oversikt over de enheter som har sendt inn sykmeldinger til TrapDetect, og som ennå ikke er friskmeldte.

<?php topptabell(status) ?>

<p><center><u><h3>Status nå</h3></u></center></p>

<?php

$dbh = pg_Connect ("dbname=trapdetect user=trapdetect password=tcetedpart");
$dbh_m = pg_Connect ("dbname=manage user=manage password=eganam");

$sporring = "SELECT * FROM status WHERE tilstandsfull='Y' AND til is null ORDER BY fra desc";

$result = pg_exec($dbh_m,$sporring) or die ("Fikk ingenting fra databasen.");
$antall = pg_numrows($result);

print "<b>Antall innlegg: $antall</b><br><br>\n";

# Skriver ut alle innlegg i spørringen.
for ($i=0;$i<$antall;$i++) {
  $row = pg_fetch_array ($result,$i);
  echo $row["fra"]."<br>\n";
  echo $row["trap"]." mottatt fra ".$row["trapsource"]."<br>\n";
		
# Henter suboider
  $suboid = array();
  $sporring = "select s.navn from trap t, subtrap s where (t.syknavn='$row[trap]' or t.frisknavn='$row[trap]') and t.id=s.trapid";
  $res = pg_exec($dbh,$sporring);
  $antall_sub = pg_numrows($res);
  for ($j=0;$j<$antall_sub;$j++) {
    $subs = pg_fetch_row($res,$j);
    array_push($suboid,$subs[0]);
  }

# Suboider hentet, ligger i $suboid, skriver ut trapdescription
  if ($row["trapdescr"]) {
    $descr = split(" ",$row["trapdescr"]);
    $teller = 0;
    while ($delinnlegg = array_shift($descr)) {
# Hvis delinnlegget er en suboid skal vi skrive ut dette.
      if (in_array($delinnlegg,$suboid)) {
	if ($teller == 0) {
	  echo $delinnlegg." = ".array_shift($descr);
	  $teller = 1;
	} else {
	  echo "<br>\n".$delinnlegg." = ".array_shift($descr);
	}
# Hvis ikke skriver vi ut alle delinnleggene til neste suboid
      } else {
	echo $delinnlegg." ";
      }
    }
    echo "<br>-<br>";
  } else {
    echo "-<br>\n";
  }
}
?>

<?php bunntabell() ?>
