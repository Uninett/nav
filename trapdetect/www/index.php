<?php require('include.inc'); ?>

<?php tittel("TrapDetect") ?>

Her er en oversikt over de enheter som har sendt inn sykmeldinger til TrapDetect, og som ennå ikke er friskmeldte.

<?php topptabell(status) ?>

<p><center><u><h3>Status nå</h3></u></center></p>

<?php

	$dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");
	mysql_select_db("manage", $dbh);

	$sporring = "SELECT * FROM status WHERE tilstandsfull='Y' AND til is null ORDER BY fra desc";

	$result = mysql_query("$sporring", $dbh) or die ("Fikk ingenting fra databasen.");
	$antall = mysql_num_rows($result);

	print "<b>Antall innlegg: $antall</b><br><br>\n";

	# Skriver ut alle innlegg i spørringen.
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
			echo "<br>-<br>";
		} else {
			echo "-<br>\n";
		}
	}
?>

<?php bunntabell() ?>
