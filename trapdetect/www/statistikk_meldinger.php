<!-- Tar inn fire variable, $name, $antdager, $oid og $date -->

<?php require('include.inc'); ?>

<?php tittel("Meldinger angående $name med trap'en $oid") ?>

Her er oversikt over de meldingene som har kommet inn fra <?php echo $name; ?> av type <?php echo $oid;?>. 

<?php topptabell(statistikk) ?>

<?php

$dagteller = 0;

$dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");
mysql_select_db("manage", $dbh);

$sporring;

$ar = substr($date,-2);
$temp = substr($date,0,4);
$dag = substr($temp,0,2);
$mnd = substr($temp,-2);
$date = "20".$ar."-".$mnd."-".$dag;
$sporring = "SELECT * FROM status WHERE trap=\"$oid\" AND trapsource=\"$name\" AND (fra like \"%$date%\"";
while ($dagteller <= $antdager) {
	$date = date("Y-m-d", mktime(0,0,0,$mnd,$dag-$dagteller,$ar));
	if ($dagteller == 0) {
		$sporring = "SELECT * FROM status WHERE trap=\"$oid\" AND trapsource=\"$name\" AND (fra like \"%$date%\"";
	} else { 
		$sporring = $sporring." OR fra LIKE \"%$date%\"";
	}
	$dagteller++;
}

$sporring = $sporring.") ORDER BY fra DESC";

# Skriver ut resultat av sporring
$result = mysql_query("$sporring", $dbh) or die ("Fikk ingenting fra databasen.");
$antall = mysql_num_rows($result);

print "<p><h3>Meldinger mottatt fra $name angående $oid-traps</h3></p>";
print "<p><b>Antall elementer: $antall</b></p>\n";
	
	$linjeteller = 0;
	while ($row = mysql_fetch_array ($result)) {
		echo $row["fra"]."<br>\n";
		echo $row["trap"]." mottatt fra ".$row["trapsource"]."<br>\n";
		
		# Henter suboid - maa optimaliseres etterhvert
		$filename = "/home/trapdet/etc/TrapDetect.conf";
		$innhold = file($filename);

		$teller = 0;
		$bool = 0;
		$suboid = array();
		while($innhold[$teller]) {
			if (!(preg_match("/^#/i", $innhold[$teller]))) {
				# Vet at neste er en suboid
				$temp = $row["trap"];
				if (preg_match("/$temp/i", $innhold[$teller])) {
					$bool = 1;
				} elseif (preg_match("/^-/", $innhold[$teller])) {
					$bool = 0;
				} elseif ($bool) {
					$split = split (" ", $innhold[$teller]);
					if ($split[1]) {
						array_push($suboid,chop($split[1]));
					}
				}
			}
			$teller++;
		}

		# Suboid'er hentet, ligger i $suboid, skriver ut trapdescription
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