<?php require('include.inc'); ?>

<?php tittel("Dagens hendelsesregister") ?>

Viser oversikt over alle enheter som er rapportert syke, og friskmeldinger.

<?php topptabell(hendelsesregister) ?>

<?php 
if (preg_match("/\d{6}/", $dato)) {
  if ($dato == date("dmy")) {
    echo "<p><center><u><h3>Dagens hendelsesregister</h3></u></center></p>";
    $idag = date("Y-m-d");
  } else {
    echo "<p><center><u><h3>Hendelsesregister for $dato</h3></u></center></p>\n";
    $ar = substr($dato,-2);
    $temp = substr($dato,0,4);
    $dag = substr($temp,0,2);
    $mnd = substr($temp,-2);
    $idag = "20".$ar."-".$mnd."-".$dag;
  }
}
?>
<form action=history.php method="GET">
Velg visning:
<?php

$dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");
$dbh_m = pg_Connect ("dbname=manage user=navall password=uka97urgf");

if ($valg == "frisk") {
  echo "<input type=radio name=valg value=frisk checked>Friskmeldte\n";
  echo "<input type=radio name=valg value=syk>Sykmeldte\n";
	echo "<input type=radio name=valg value=begge>Begge\n";
} elseif ($valg == "syk") {
  echo "<input type=radio name=valg value=frisk>Friskmeldte\n";
  echo "<input type=radio name=valg value=syk checked>Sykmeldte\n";
  echo "<input type=radio name=valg value=begge>Begge\n";
} else {
  echo "<input type=radio name=valg value=frisk>Friskmeldte\n";
  echo "<input type=radio name=valg value=syk>Sykmeldte\n";
  echo "<input type=radio name=valg value=begge checked>Begge\n";
}

echo "<br>\n";
echo "Velg OID: <select name=oid>\n";

$liste = array();
# Henter suboider fra TrapDetect.conf og hiver de inn i et array til senere bruk.
$hovedoid = array();
$sporring = "select syknavn from trap";
$res = pg_exec($dbh,$sporring);
$antall = pg_numrows($res);
for ($i=0;$i<$antall;$i++) {
  $trapnavn = pg_fetch_array($res,$i);
  array_push($hovedoid,$trapnavn[syknavn]);
}

foreach ($hovedoid as $trapnavn) {
  $suboid = array();
  $sporring = "select s.navn from trap t, subtrap s where (t.syknavn='$trapnavn' or t.frisknavn='$trapnavn') and t.id=s.trapid";
  $res = pg_exec($dbh,$sporring);
  $antall_sub = pg_numrows($res);
  for ($j=0;$j<$antall_sub;$j++) {
    $subs = pg_fetch_row($res,$j);
    array_push($suboid,$subs[0]);
  }
  $liste[$trapnavn] = $suboid;
}


if ($oid == "Alle") {
  echo "<option value=Alle selected>Alle\n";
  $oid = "";
} else {
  echo "<option value=Alle>Alle\n";
}

# Skriver ut listen over alle oider som man kan velge å søke etter.
$keys = array_keys($liste);
sort($keys);
foreach ($keys as $temp) {
  if ($temp && $oid == $temp) {
    echo "<option value=$temp selected>".$temp."\n";
  } elseif ($temp) {
    echo "<option value=$temp>".$temp."\n";
  }
}

echo "</select>\n";
echo "&nbsp<input type=text name=sokestreng size=20 maxsize=20 value=$sokestreng><br>\n";
echo "<input type=hidden name=dato value=$dato>\n";
echo "<input type=submit>\n";
echo "</form>\n";

#################### Her begynner uthenting av data
if ($valg == "frisk") {
  if ($oid) {
    $sporring = "select * from status where fra like '%$idag%' and trap=\"$oid\" and til is not null order by fra desc";
  } else {
    $sporring = "select * from status where fra like '%$idag%' and til is not null order by fra desc";
  }
} else if ($valg == "syk") {
  if ($oid) {
    $sporring = "select * from status where fra like '%$idag%' and trap=\"$oid\" and til is null order by fra desc";
  } else {
    $sporring = "select * from status where fra like '%$idag%' and til is null order by fra desc";
  }
} else {
  if ($oid) {
    $sporring = "select * from status where fra like '%$idag%' and trap=\"$oid\" order by fra desc";
  } else {
    $sporring = "select * from status where fra like '%$idag%' order by fra desc";
  }
}
$result = pg_exec($dbh_m,$sporring) or die ("Fikk ingenting fra databasen.");
$antall = pg_numrows($result);	

# Må sjekke søkestrengen for tilfeller av / siden preg_match ikke liker 
# slike tegn
$sokestreng = str_replace ("/","\/",$sokestreng);

# Skriver alt til en variabel innlegg som så sjekkes for søkestrengen
# og deretter legges det i utskriftsarrayet hvis den finnes.
$linjeteller = 0;
$innleggteller = 0;
$innlegg_array = array();
for ($i=0;$i<$antall;$i++) {
  $row = pg_fetch_array ($result,$i);
  $innlegg = "";
  $innlegg = $row["fra"]."<br>\n";
  $innlegg .= $row["trap"]." mottatt fra ".$row["trapsource"]."<br>\n";
		
# Suboider hentet, ligger i $suboid, skriver ut trapdescription
  if ($row["trapdescr"]) {
    $descr = split(" ",$row["trapdescr"]);
    $teller = 0;
    while ($delinnlegg = array_shift($descr)) {
# Hvis delinnlegget er en suboid skal vi skrive ut dette.
      if (in_array($delinnlegg,$liste[$row["trap"]])) {
	if ($teller == 0) {
	  $innlegg .= $delinnlegg." = ".array_shift($descr);
	  $teller = 1;
	} else {
	  $innlegg .= "<br>\n".$delinnlegg." = ".array_shift($descr);
	}
# Hvis ikke skriver vi ut alle delinnleggene til neste suboid
      } else {
	$innlegg .= $delinnlegg."  ";
      }
    }
    $innlegg .= "<br>";
    if ($row["til"]) {
      $innlegg .= "FRISKMELDT: ".$row["til"]."<br>";
    }
    $innlegg .= "-<br>\n";
  } else {
    $innlegg .= "-<br>\n";
  }

# Søker etter søkestrengen i hele innlegget. Teller opp
# hvor mange som skrives ut.
  if (preg_match("/$sokestreng/", $innlegg)) {
    array_push ($innlegg_array, $innlegg);
    $innleggteller++;
  }
}

# Skriver ut alt i innleggsarrayet
echo "<p><B>Antall innlegg:</B> ".$innleggteller." av ".$antall."</p>\n";
while ($temp = array_shift($innlegg_array)) {
  echo $temp;
}

?>

<?php bunntabell() ?>