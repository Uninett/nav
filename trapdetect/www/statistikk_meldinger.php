<!-- Tar inn fire variable, $name, $antdager, $oid og $date -->

<?php require('include.inc'); ?>

<?php tittel("Meldinger angående $name med trap'en $oid") ?>

Her er oversikt over de meldingene som har kommet inn fra <?php echo $name; ?> av type <?php echo $oid;?>. 

<?php topptabell(statistikk) ?>

<?php

$dagteller = 0;

$dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");
$dbh_m = pg_Connect ("dbname=manage user=navall password=uka97urgf");

$ar = substr($date,-2);
$temp = substr($date,0,4);
$dag = substr($temp,0,2);
$mnd = substr($temp,-2);
$date = "20".$ar."-".$mnd."-".$dag;
$sporring = "SELECT * FROM status WHERE trap='$oid' AND trapsource='$name' AND (fra like '%$date%'";
while ($dagteller <= $antdager) {
  $date = date("Y-m-d", mktime(0,0,0,$mnd,$dag-$dagteller,$ar));
  if ($dagteller == 0) {
    $sporring = "SELECT * FROM status WHERE trap='$oid' AND trapsource='$name' AND (fra like '%$date%'";
  } else { 
    $sporring = $sporring." OR fra LIKE '%$date%'";
  }
  $dagteller++;
}

$sporring = $sporring.") ORDER BY fra DESC";

# Skriver ut resultat av sporring
$result = pg_exec($dbh_m,$sporring) or die ("Fikk ingenting fra databasen.");
$antall = pg_numrows($result);

print "<p><h3>Meldinger mottatt fra $name angående $oid-traps</h3></p>";
print "<p><b>Antall elementer: $antall</b></p>\n";
	
$linjeteller = 0;
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
    echo "<br>";
    if ($row["til"]) {
      echo "FRISKMELDT: ".$row["til"]."<br>";
    }
    echo "-<br>\n";
  } else {
    echo "-<br>\n";
  }
}

?>

<?php bunntabell() ?>