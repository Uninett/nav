<?php require('include.inc'); ?>
<?php require('statistikk.inc'); ?>

<?php tittel("Totaloversikt traps") ?>

Oversikt over det totale antall traps som ligger i databasen.

<?php topptabell(statistikk) ?>

<?php

$dbh = pg_Connect ("dbname=trapdetect user=trapdetect password=tcetedpart");
$dbh_m = pg_Connect ("dbname=manage user=manage password=eganam");

# Totalt antall innlegg
$sporring = "select count(*) from status";
$result = pg_exec($dbh_m,$sporring) or die ("<br>Fikk ingenting fra databasen!<br>");
$antall_innlegg = pg_fetch_row($result,0);

echo "<p><b>Totalt antall innlegg</b>: ".$antall_innlegg[0]."</p>\n";

####################

# Antall dager innsamlet data
# Finner den første datoen og bruker den som utgangspunkt.
$sporring = "select fra from status order by fra limit 1";
$result = pg_exec($dbh_m,$sporring) or die ("<br>Fikk ingenting fra databasen!<br>");
$dato = pg_fetch_row($result,0);

$temp = explode (" ", $dato[0]); #dato
$temp2 = explode ("-", $temp[0]); # yyyy-mm-dd

$temp = date ("z", mktime(0,0,0,$temp2[1],$temp2[2],$temp2[0])); # Dager i året da vi startet
$temp2 = date("z", mktime(0,0,0,date("m"),date("d"),date("Y"))); # Dager i året nå

# En liten sjekk på om vi er i ulike år...
if ($temp2 > $temp) {
  $antall_dager = $temp2 - $temp;
} else {
  $antall_dager = 365 - $temp + $temp2;
}

echo "<p><b>Antall dager innsamlet data</b>: ".$antall_dager."</p>\n";

####################

# Finner de ulike traps og hvor mange ganger de har forekommet
$sporring = "select count(trap),trap from status group by trap";
$result = pg_exec($dbh_m,$sporring);

echo "<p><b>Fordeling på de ulike traps\n";
echo "<a href=statistikk_oid.php?dager=".$antall_dager.">[grafisk fremvisning]</a></b>:<br>";
echo "<table border=1>\n";

$antall = pg_numrows($result);
for ($i=0;$i<$antall;$i++) {
  $row = pg_fetch_row($result,$i);
  echo "\t<tr><td>".$row[1]."</td><td>".$row[0]."</td></tr>\n";
}
echo "</table></p>\n\n";

####################

# Finner de ulike enhetene som har gitt traps
$sporring = "select count(trapsource),trapsource from status group by trapsource";
$result = pg_exec($dbh_m,$sporring);
$antall_enheter = pg_numrows($result);

$teller = 0;
$column = 4; # antall kolonner i tabellen

echo "<b>Fordeling på enheter (".$antall_enheter.")\n";
echo "<a href=statistikk_ant.php?dager=".$antall_dager.">[grafisk fremvisning]</a></b>:<br>";
echo "<table border=1>\n\t<tr>\n\t";
for ($i=0;$i<$antall_enheter;$i++) {
  $row = pg_fetch_row($result,$i);
  if ($teller<$column) {
    echo "<td>".$row[1]."</td><td>".$row[0]."</td>\n\t";
    $teller++;
  } else {
    echo "</tr>\n\t<tr>\n\t";
    echo "<td>".$row[1]."</td><td>".$row[0]."</td>\n\t";
		$teller = 1;
  }
}

# Rydder opp og spacer de siste kolonnene hvis det er noen.
if ($teller < 4) {
  while ($teller<$column) {
    echo "<td>&nbsp;</td><td>&nbsp;</td>\n\t";
    $teller++;
  }
}
echo "</tr></table>";

?>


<?php bunntabell() ?>