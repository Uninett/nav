<?php require('include.inc'); ?>

<?php tittel("Hovedlogg") ?>

Hovedloggen som logger all aktivitet. Output og kommentarer fra hovedprogram.<br><br>

<?php topptabell(logg) ?>

<?php

######################################## Sjekk på datoformat og om fil finnes

$path = "/home/trapdet";
if (preg_match("/\d{6}/", $dato)) {
	print "<p><center><h3><u>Logg for $dato</u></h3></center></p>\n";

	# Sjekker om fila finnes, skriver feilmelding hvis ikke.
	if (is_file ("$path/log/traplog$dato")) {
		$file = "$path/log/traplog$dato";

######################################## Program


	echo "<form action=traplogbak.php method=\"POST\">\n";
	if ($sokeord) {
	 	echo "Søk på ord: <input type=text name=sokeord value=$sokeord>\n";
	} else {
	 	echo "Søk på ord: <input type=text name=sokeord>\n";
	}
	echo "<input type=hidden name=dato value=$dato>\n";
	echo "<input type=submit>\n";
	echo "</form>\n";

	$filename = "$file";
	$innhold = file($filename);

	function tell_linjer($innhold) {
		$innlegg = 0;
		$teller = 0;
		while($innhold[$teller]) {
			if (preg_match("/^-/i", $innhold[$teller])) {
				$innlegg++;
			}
			$teller++;
		}
		return $innlegg;
	}

	function skrivalt($innhold) {
		$teller = 0;
		while($innhold[$teller]) {
			print "$innhold[$teller]<br>\n";
			$teller++;
		}
	}

	function hentsokeord($array, $sokeord) {
		$teller = 0;
		$innlegg = 0;
		$ord = 0;
		$mulig = 0;

		$sokeord = preg_replace("/\//", "\/", $sokeord);

		while($array[$teller]) {
			if (((preg_match("/\d+\/\d+\/\d+/i", $array[$teller])) && !($mulig))) {
       				$start = $teller;
				$mulig = 1;
				if (preg_match("/$sokeord/i", $array[$teller])) {
					$ord = 1;
				} else {
					$ord = 0;
				}
			} elseif (($mulig) && (preg_match("/$sokeord/i", $array[$teller]))) {
				$ord = 1;
			} elseif ((preg_match("/^-/i", $array[$teller])) && ($mulig) && ($ord)) {
				$innlegg++;
				for ($i = $start; $i <= $teller; $i++) {
					$streng .= "$array[$i]<br>\n";
				}
				$mulig = 0;
				$start = 0;
				$ord = 0;
			} elseif ((preg_match("/^-/i", $array[$teller])) && ($mulig)) {
				$mulig = 0;
			}
			$teller++;
       		}
		return array ($innlegg, $streng);
	}

	if ($sokeord) {
		list ($antall, $streng) = hentsokeord($innhold, $sokeord);
		print "<b>Antall innlegg: $antall</b><br><br>\n";
		print "$streng<br>\n";
	} else {
		$antall = tell_linjer($innhold);
		print "<b>Antall innlegg: $antall</b><br><br>\n";
		skrivalt($innhold);
	}

######################################## Sjekk ferdig

	} else {
		print "Denne filen finnes ikke. Vi har bare lagret data siden ";
		if (date("dmy") > date("dmy", mktime(0,0,0,8,30,2000))) {
			$tomndsiden = date ("d M Y", mktime(0, 0, 0, date("m")-2, 1, date("Y")));
			print "$tomndsiden.<br>\n";
		} else {
			print "14 July 2000.<br>\n";
		}
	}
} else {
	print "Dato må være på format ddmmyy";
}


?>

<?php bunntabell() ?>
