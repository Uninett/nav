<?php

require ('meldingssystem.inc');
html_topp("Varslingsregistrering - Steg 3");

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);
if ($admin && $REMOTE_USER != $bruker) {
  print "Du er innlogget som <b>$bruker</b> med administratorrettighetene til <b>$REMOTE_USER</b><br>\n";
}

#skrivpost($HTTP_POST_VARS);

$dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");
$dbh_m = pg_Connect ("dbname=manage user=navall password=uka97urgf");

echo "<p><h3>STEG 3 av 3</h3>Velg varslingstype for de valgte enheter for <b>$trap</b> bruker <b>$bruker</b></p>\n";

$borders=0;
$unntak = array(); # Holder styr på alt som ikke skal være med 

$postvars = $HTTP_POST_VARS;
$keys = array_keys($postvars);

########################################
# Finner ut om bruker kan velge sms.
########################################
$sporring = "select sms from bruker where bruker='$bruker'";
#print "$sporring<br>\n";
$res = pg_exec($dbh,$sporring);
$temp = pg_fetch_row($res,0);
$sms = $temp[0];

#################
# Finner trapid
#################
$sporring="select id from trap where syknavn='$trap'";
$res = pg_exec($dbh,$sporring);
$temp = pg_fetch_row($res,0);
$trapid = $temp[0];

##################################################
# Henter alle enhetene som evt. eksisterer fra før
##################################################
$eksisterer_ukat = array();
$eksisterer_kat = array();
$eksisterer_enhet = array();
$sporring = "select varsel.kat,varsel.ukat,varsel.vtypeid from varsel,bruker where brukerid=bruker.id and bruker.bruker='$bruker' and trapid=$trapid";
#print "$sporring<br>\n";
$res = pg_exec($dbh,$sporring);
$antall = pg_numrows($res);
for ($i=0;$i<$antall;$i++) {
  $temp = pg_fetch_row($res,$i);
  if ($temp[0] && $temp[1]) {
    $eksisterer_ukat[$temp[0]][$temp[1]] = $temp[2];
  } elseif ($temp[0]) {
    $eksisterer_kat[$temp[0]] = $temp[2];
  }
}

# Henter id
$temp_boksid = array();
$sporring = "select boksid,vtypeid from unntak,bruker where brukerid=bruker.id and bruker.bruker='$bruker' and trapid=$trapid and unntak.status='pluss'";
#print "$sporring<br>\n";
$res = pg_exec($dbh,$sporring);
$antall = pg_numrows($res);
for ($i=0;$i<$antall;$i++) {
  $row = pg_fetch_row($res,$i);
  $temp_boksid[$row[0]] = $row[1];
}

# Henter sysname
$eksisterer_enhet = array();
foreach (array_keys($temp_boksid) as $key) {
  $sporring = "select sysname from boks where boksid=$key";
#  print "$sporring<br>\n";
  $res = pg_exec($dbh_m,$sporring);
  $row = pg_fetch_row($res,0);
  $eksisterer_enhet[$row[0]] = $temp_boksid[$key];
}

##################################################
# Legger alle variablene i forskjellige array
# alt etter tilhørighet.
# kategorier: hvis en kat er valgt havner den her, key=kat
# underkat: hvis en underkat er valgt, havner den her, key=kat
# list: alle enhetene som er valgt, key=kat
##################################################

$uarr = array();
$arr = array();
$eier = array();
foreach ($keys as $var) {
  if (preg_match("/kat_(.+)/",$var,$matches)) { 
# Kategorivalg (ikke underkategorier)
    $kategorier[$matches[1]]++;
  } elseif (preg_match("/list_(.+)/",$var,$matches)) { 
# Valg fra listene
    $arr = array();
    foreach ($postvars[$matches[0]] as $temp) {
      array_push ($arr, $temp);
    }
    $list[$matches[1]] = $arr;
  } elseif (preg_match("/eier/",$var)) {
    array_push($eier,$postvars[$var]);
  } elseif (preg_match("/(.+)_(.+)/",$var,$matches) or preg_match("/ukat_(.+)/",$var,$matches)) { 
# Bare underkat igjen
    $arr = array();
    if ($underkat[$matches[1]]) { 
# Tidligere underkat eksisterer
      $arr = $underkat[$matches[1]];
      array_push($arr,$matches[2]);
      $underkat[$matches[1]] = $arr;
    } else {
      array_push($arr,$matches[2]);
      $underkat[$matches[1]] = $arr;
    }
  }
}


##################################################
# Henter alle varslingstyper fra databasen, 
# legger de i et array for senere bruk.
##################################################
$result = pg_exec($dbh,"select * from varseltype");
$antall = pg_numrows($result);
$varseltype=array();
for ($i=0;$i<$antall;$i++) {
  $svar = pg_fetch_row($result,$i);
  $varseltype[$svar[1]] = $svar[0];
}
$type = array_keys($varseltype);

echo "<form action=meldingssystem4.php method=\"POST\">\n";

##################################################
# Her begynner utskriving av data
##################################################

echo "<table border=$borders cellspacing=5>\n";

##################################################
# Først skrives alle valgte kategorier ut
##################################################

if ($kategorier) {
  print "<br>\n";
  $keys = array_keys($kategorier);
  foreach ($keys as $key) {
    echo "<tr valign=top><td>";
    echo $key;
    echo "</td><td>\n";
    if ($eksisterer_kat[$key]) {
      lagDropDown2($type,"kat:".$key,$eksisterer_kat[$key]);
    } else {
      lagDropDown($type,"kat:".$key);
    }
    if ($underkat[$key]) {
      echo "</td><td>\n";
      skrivUnderkategorier($key);
      $underkat[$key] = "";
    }
    if ($list[$key]) {
      echo "</td></tr><tr><td>&nbsp;</td><td>&nbsp;</td><td>\n";
      skrivEnkeltenheter($key,"N",1);
    }
    if ($list) {
      foreach (array_keys($list) as $temp) {
	if (preg_match("/$key.+/",$temp)) {
	  echo "</td><td>";
	  skrivEnkeltenheter($key,"N",1);
	}
      }
    }
    echo "</td></tr>";
  }
} else {
  echo "Ingen kategorier valgt<br>\n";
}

##################################################
# Deretter skrives alle valgte underkategorier
# utenom de som allerede er skrevet ut ovenfor.
# Dette vil skje dersom en kategori ikke er
# valgt, mens noen underkategorier er valgt.
##################################################

if ($underkat) {
  $ukats = array_keys($underkat);
  foreach ($ukats as $underkategorier) {
    if ($underkat[$underkategorier]) {
      echo "<tr><td valign=top>\n";
      if (!$kategorier[$underkategorier]) { 
# formatering
	echo "$underkategorier</td><td>&nbsp;</td><td>";
      }
      skrivUnderkategorier($underkategorier);
      echo "</td></tr>";
    }
  }
}

##################################################
# Så skrives alle enkeltenheter ut som ikke er
# skrevet ut ennå.
#
# Dette vil skje hvis det er enheter som er valgt
# uten at hverken kategorien eller underkategorien
# er valgt. Altså det laveste nivået man kan
# velge enkeltenheter på.
##################################################

if ($list) {
  $keys = array_keys($list);
  foreach ($keys as $key) {
    if ($list[$key]) {
      echo "<tr><td valign=top>\n";
      echo $key."</td><td>&nbsp;</td><td>\n";
      skrivEnkeltenheter($key,"Y",1);
      echo "</td></tr>";
    }
  }
}
echo "</table>\n";

##################################################
# Utskriving er ferdig, sender data til neste
# side med submit.
##################################################
print "<table border=$borders><tr><td>";
foreach($unntak as $element) {
  echo "<input type=hidden name=$trapid:unntak[] value=$element>\n";
}
echo "<input type=hidden name=bruker value=".$bruker.">\n";
echo "<input type=submit value=\"Gå videre\">";
echo "</form>\n";
print "</td><td>";
knapp_hovedside($bruker,'Angre');
print "</td></tr></table>\n";

############################################################
####################     FUNKSJONER     ####################
############################################################

##################################################
# En funksjon som skriver ut underkategorier som
# tilhører kategorien $key.
#
# Metoden lager en egen tabell. Ta hensyn til dette, 
# og gjør klar med <td> og </td> før og etter 
# metoden kalles.
##################################################
function skrivUnderkategorier($key) {
  global $underkat,$list,$type,$kategorier, $borders, $unntak,$eksisterer_ukat;

  echo "\n\t<table cellspacing=5 border=$borders>\n";
  foreach ($underkat[$key] as $ukat) {
# Hvis kat er satt er dette unntak
    if ($kategorier[$key]) {
      echo "\t<tr><td>";
      echo $ukat."</td><td>Ikke med</td>\n";
      array_push($unntak,$key.",".$ukat);

      $listvar = $key."_".$ukat;
      if ($list[$listvar]) { 
# finner valgte enheter
	echo "\t<td>\n";
# Siden dette er unntak fra unntak så skal de være med.
	skrivEnkeltenheter($listvar,"Y",0);
#				echo "\t</td>\n";
      }
    } else { 
# Dette skal legges til
      echo "\t<tr><td>";
      echo $ukat."</td><td>";
      if ($eksisterer_ukat[$key][$ukat]) {
	lagDropDown2($type, "ukat:".$key.",".$ukat,$eksisterer_ukat[$key][$ukat]);
      } else {
	lagDropDown($type, "ukat:".$key.",".$ukat);
      }
      echo "\t</td>\n";

      $listvar = $key."_".$ukat;
      if ($list[$listvar]) { 
# finner valgte enheter altså unntak
	echo "\t<td>\n";
	skrivEnkeltenheter($listvar,"N",0);
#				echo "\t</td>\n";
      }
    }
  }
  echo "\t</tr></table>";
}

##################################################
# En funksjon som skriver ut enheter som
# tilhører kategorien $key, og som tar inn en
# boolsk variabel $med. Hvis denne er satt til
# "Y", vil enheten få valg om varseltype.
#
# Metoden lager en egen tabell. Ta hensyn til dette, 
# og gjør klar med <td> og </td> før og etter 
# metoden kalles.
##################################################
function skrivEnkeltenheter($key,$med,$tabell) {
  global $list,$type, $borders,$unntak,$eksisterer_enhet;

  if ($tabell == 1) {
    echo "\n\t\t<table border=$borders>";
    if ($med == "Y") {
      foreach ($list[$key] as $enhet) {
	echo "\n\t\t<tr><td>";
	echo $enhet;
	echo "</td><td>";
	if ($eksisterer_enhet[$enhet]) {
	  lagDropDown2($type, "enhet:".$enhet,$eksisterer_enhet[$enhet]);
	} else {
	  lagDropDown($type, "enhet:".$enhet);
	}
	echo "</td></tr>";
      }
      $list[$key] = "";
    } else {
# Siden dette er unntak fra tillegg så skal de ikke være med.
      if ($list[$key]) {
	foreach ($list[$key] as $enhet) { 
# Alle som eksplisitt har denne key.
	  echo "\n\t\t<tr><td>";
	  echo $enhet;
	  echo "</td><td>ikke med</td></tr>\n";
	  array_push($unntak,$enhet);
	}
	$list[$key] = "";
      }
# Sjekker alle andre for å se om det er noen underkategorienheter som skal være med
      foreach (array_keys($list) as $temp) {
	if (preg_match("/$key.+/",$temp)) {
	  if ($list[$temp]) {
	    foreach ($list[$temp] as $enhet) {
# Alle som implisitt har denne key.
	      echo "\t\t<tr><td>";
	      echo $enhet;
	      echo "</td><td>ikke med</td></tr>\n";
	      array_push($unntak,$enhet);
	    }
	    $list[$temp] = "";
	  }
	}
      }
    }
    echo "\t\t</table>\n";
  } elseif ($list[$key]) {
# Hvis den ikke er tom
    if ($med == "Y") {
      $teller = 0;
      foreach ($list[$key] as $enhet) {
	if ($teller != 0) {
	  echo "\n\t\t<tr><td>&nbsp;</td><td>&nbsp;</td><td>";
	}
	$teller++;
	echo $enhet;
	echo "</td><td>";
	if ($eksisterer_enhet[$enhet]) {
	  lagDropDown2($type, "enhet:".$enhet,$eksisterer_enhet[$enhet]);
	} else {
	  lagDropDown($type, "enhet:".$enhet);
	}
	echo "</td></tr>";
      }
      $list[$key] = "";
    } else {
# Siden dette er unntak fra tillegg så skal de ikke være med.
      $teller = 0;
      foreach ($list[$key] as $enhet) { 
# Alle som eksplisitt har denne key.
	if ($teller != 0) {
	  echo "\n\t\t<tr><td>&nbsp;</td><td>&nbsp;</td><td>";
	}
	$teller++;
	echo $enhet;
	echo "</td><td>ikke med</td></tr>\n";
	array_push($unntak,$enhet);
      }
      $list[$key] = "";
# Sjekker alle andre for å se om det er noen underkategorienheter som skal være med
      foreach (array_keys($list) as $temp) {
	if (preg_match("/$key.+/",$temp)) {
	  if ($list[$temp]) {
	    foreach ($list[$temp] as $enhet) { 
# Alle som implisitt har denne key.
	      echo "\t\t<tr><td>";
	      echo $enhet;
	      echo "</td><td>ikke med</td></tr>\n";
	      array_push($unntak,$enhet);
	    }
	    $list[$temp] = "";
	  }
	}
      }
    }
  }
}

##################################################
# En funksjon som skriver ut en drop-down
# liste som inneholder alle varseltypene som 
# er i databasen.
##################################################
function lagDropDown($array,$name) {
  global $varseltype,$sms,$trapid;
  echo "<select name=$trapid:$name>\n";
  foreach ($array as $element) {
    if ($element == "mail") {
      echo "<option value=".$varseltype[$element]." selected>".$element."</option>\n";
    } elseif (preg_match("/sms/",$element)) {
      if ($sms == 'Y') {
	echo "<option value=".$varseltype[$element].">".$element."</option>\n";
      }
    } else {
      echo "<option value=".$varseltype[$element].">".$element."</option>\n";
    }
  }
  echo "</select>\n";
}

function lagDropDown2($array,$name,$vtype) {
  global $varseltype,$sms,$trapid;
  echo "<select name=$trapid:$name>\n";
  foreach ($array as $element) {
    if ($varseltype[$element] == $vtype) {
      echo "<option value=".$varseltype[$element]." selected>".$element."</option>\n";
    } elseif (preg_match("/sms/",$element)) {
      if ($sms == 'Y') {
	echo "<option value=".$varseltype[$element].">".$element."</option>\n";
      }
    } else {
      echo "<option value=".$varseltype[$element].">".$element."</option>\n";
    }
  }
  echo "</select>\n";
}

?>

</body></html>