<html><head><title>Varslingsregistrering - Steg 2</title>
<!-- Får inn disse variable:
eier: kan være flere variable
trap: sier seg selv
bruker: brukernavn på han som er på
-->
<?php
require ('meldingssystem.inc');
list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);
if ($admin && $REMOTE_USER != $bruker) {
  print "Du er innlogget som <b>$bruker</b> med administratorrettighetene til <b>$REMOTE_USER</b><br>\n";
}

?>

<script Language="JavaScript">
<!--
function popup(url, name, width, height)
{
  settings=
  "toolbar=no,location=no,directories=no,"+
  "status=no,menubar=no,scrollbars=yes,"+
  "resizable=yes,width="+width+",height="+height;
  MyNewWindow=window.open(url,name,settings);
}
//-->
</script>
</head>

<body bgcolor=white>

<?php

$border=0;
$temp = $HTTP_POST_VARS;

$postvars = array();
if (preg_match("/\d+/",$temp[trap])) {
  $postvars = finn_enheter($bruker,$temp[trap]);
} else {
  $postvars = $temp;
}

$eier = $postvars[eier];
$trap = $postvars[trap];

$keys = array_keys($postvars);
foreach ($keys as $key) {
# Skifter _ til . i navnet til enhetene.
  $tempkey = preg_replace("/_/",".",$key);
  $postvars[$tempkey] = $postvars[$key];
}

print "<p><h3>STEG 2</h3>Her er oversikt over alle kategorier og underkategorier som tilhører $trap-trapen. Velg kategori (og evt. underkategori) du vil abonnere på og trykk <b>Gå videre</b> nederst på siden.</p>";

##################################################
# En liten ting som viser hjelp om nødvendig
##################################################

echo "<p><a href=\"#\" onClick=\"popup('meldingssystem2_hjelp.php', 'Win1', 500, 300); return false\">Hjelp</a></p>\n";

echo "<form action=meldingssystem.php method=\"POST\">";
echo "<input type=hidden name=bruker value=$bruker>";
echo "<input type=submit value=\"Tilbake til steg 1\">\n";
echo "</form>\n";

knapp_hovedside($bruker);

echo "<hr width=90%>\n";

##############################
# Kobler til database
##############################
$dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");
mysql_select_db("trapdetect", $dbh);

# Henter ut om bruker kan velge sms
$handle = mysql_query("select sms from user where user='$bruker'");
$svar = mysql_fetch_array($handle);
$sms = $svar[sms];

##################################################
# Henter alle varslingstyper fra databasen, 
# legger de i et array for senere bruk.
##################################################
$result = mysql_query("select * from varseltype");
while ($svar = mysql_fetch_row($result)) {
  $varseltype[$svar[1]] = $svar[0];
}
$type = array_keys($varseltype);

##################################################
# Henter tilgjenglige kategorier for trapen
##################################################
$sporring = "select trapkat.kat from trapkat,trap where trap.syknavn='".$trap."' and trap.id=trapkat.trapid";
$res = mysql_query($sporring,$dbh);

if (mysql_num_rows($res) == 0) {
  echo "Denne type trap er uavhengig av enheter.<br>\n";
  echo "Velg varslingstype for ".$trap.":\n";
  echo "<form action=meldingssystem4.php method=\"POST\">";

  $sporring = "select id from trap where syknavn='$trap'";
  $res = mysql_query($sporring,$dbh);
  $tjoho = mysql_fetch_row($res);

  lagDropDown($type,"$tjoho[0]:spesial");
} else {

  $antall_enheter = 0;
  $kategorier = array();

######################################################################
# Sjekker eierforholdet mellom enhetene i de tilgjengelige kat og brukerens org.
# $row[kat] er alle kategoriene som er funnet med kat som key
# $rows[] inneholder alle underkategoriene
# $antall_i_kat er antallet enheter i hver kat for medlemmen i denne org-en
######################################################################
  mysql_select_db("manage", $dbh);
  $antall_i_kat = array();
  
  while ($row = mysql_fetch_array($res)) {
    
# Må hente inn alle eierforhold
    $sporring = "select count(kat),underkat from nettel where kat='".$row["kat"]."' and (";
    
    for ($i=0;$i<sizeof($eier);$i++) {
      
      if ($i<(sizeof($eier)-1)) {
	$sporring .= "eier='".$eier[$i]."' or ";
      } else {
	$sporring .= "eier='".$eier[$i]."'";
      }
    }
    $sporring .= ") group by underkat";
    
    $result = mysql_query($sporring,$dbh);
    $antall = mysql_num_rows($result);

    if ($antall > 0) {
# Hvis det finnes underkategorier
      $temparray = array();
      while ($rows = mysql_fetch_row($result)) {
	$antall_enheter += $rows[0]; 
# Teller opp totalt antall enheter
	$antall_i_kat[$row["kat"]] += $rows[0];
	if ($rows[1]) { 
# Hvis det er en verdi der, fortsetter vi
	  array_push ($temparray, $rows[1]); 
# Legger alle underkat i en array
	}
      }
      $kategorier[$row["kat"]] = $temparray; 
# Ferdig med alle underkategoriene, hiver dem i en hash
    }
  }
  
  $keys = array_keys($kategorier);
  echo "Det er totalt ".$antall_enheter." enheter tilgjengelig for <b>$trap</b> for bruker <b>$bruker</b><br>\n";

##################################################
# Skriver ut alle kategorier og underkategorier 
# og lister over enheter med i dem.
##################################################
  echo "<form action=meldingssystem3.php method=\"POST\">";
  echo "\n<table width=90%  cellpadding=3 border=$border>";

  foreach ($keys as $key) { 
# Går gjennom alle kategorier
    echo "\n\t<tr><td valign=top>\n";

  $underkat = $kategorier[$key];
  $tempkey = strtoupper($key); 
# Kun for syns skyld -> uppercase

# KATEGORIER - sjekker om variabelnavn lik kategori finnes

  if ($postvars[$key]) {
    echo "\t<input type=checkbox name=kat_".$key." checked>".$tempkey."<br>(".$antall_i_kat[$key]." enheter)";
  } else {
    echo "\t<input type=checkbox name=kat_".$key.">".$tempkey."<br>(".$antall_i_kat[$key]." enheter)";
  }

  echo "\t</td>\n";

  if (sizeof($underkat) > 0) { 
# Hvis det ikke er underkat-er så skipper vi dette.
    $harunderkat = 1;
    echo "\t<td valign=top>\n\t\t<table cellpadding=8 border=$border><tr><td valgin=top>\n";
    echo "\t\tVelg underkategorier for ".$key."\n</td>";
    echo "\t\t<td>Enheter med i $key\n";
    echo "\t\t</td></tr>\n";
    foreach($underkat as $element) {
      $sporring = "select sysname from nettel where kat='".$key."' and underkat='".$element."' and (";
      for ($i=0;$i<sizeof($eier);$i++) {
	if ($i<(sizeof($eier)-1)) {
	  $sporring .= "eier='".$eier[$i]."' or ";
	} else {
	  $sporring .= "eier='".$eier[$i]."' ";
	}
      }
      $sporring .= ") order by sysname";

      $res = mysql_query($sporring,$dbh);
      $antall = mysql_num_rows($res);

# Skriver ut underkategorien og lager en checkbox.
      echo "\n\t\t<tr><td>";

# UNDERKATEGORIER - spør om variabel med kat finnes og om variabel med ukat finnes
      if ($postvars[$element] == $key) {
	echo "\n\t\t<input type=checkbox checked name=".$key."_".$element.">".$element."(".$antall.")";
      } else {
	echo "\n\t\t<input type=checkbox name=".$key."_".$element.">".$element."(".$antall.")";
      }
      echo "</td><td>\n";

# Lager en liste over alle enheter med denne kategori og underkategori
      echo "\t\t<select name=list_".$key."_".$element."[] multiple size=3>";
      while ($rad = mysql_fetch_row($res)) {

# ENHETER MED UNDERKATEGORI - variabelnavn med enhet brukes
	if ($postvars[$rad[0]]) {
	  echo "\n\t\t\t<option selected>$rad[0]</option>";
	} else {
	  echo "\n\t\t\t<option>$rad[0]</option>";
	}
      }
      echo "</select>\n";
      echo "\t\t</td></tr>";
    }
    echo "</table>\n";
    echo "</td>";
    echo "</tr>";
  }
  
# Listen over alle enheter med denne kategori som ikke er med i noen underkategori.
  $sporring = "select sysname from nettel where kat='".$key."' and (underkat is null or underkat='') and (";
  for ($i=0;$i<sizeof($eier);$i++) {
    if ($i<(sizeof($eier)-1)) {
      $sporring .= "eier='".$eier[$i]."' or ";
    } else {
      $sporring .= "eier='".$eier[$i]."' ";
    }
  }
  $sporring .= ") order by sysname";
 
  $res = mysql_query($sporring,$dbh);
  $antall = mysql_num_rows($res);
  if ($antall > 0) {
    if ($harunderkat) {
      echo "<td>&nbsp</td>";
    }
    echo "\n\t\t<td valign=bottom>";
    echo "Enheter i $key uten underkategori";
    echo "</td></tr><tr><td>&nbsp</td><td>";
    echo "<select name=list_".$key."[] multiple size=10>";
    while ($rad = mysql_fetch_row($res)) {
# ENHETER UTEN UNDERKATEGORI - sjekker om variabel lik navn på enhet finnes
      if ($postvars[$rad[0]]) {
	echo "<option selected>$rad[0]</option>\n";
      } else {
	echo "<option>$rad[0]</option>\n";
      }
    }
    echo "</select>";
    echo "\n\t</td></tr>\n";
  }
  }
  echo "</table>\n";

}

foreach ($eier as $name) {
  echo "<input type=hidden name=eier value=".$name.">\n";
}
echo "<input type=hidden name=bruker value=".$bruker.">\n";
echo "<input type=hidden name=trap value=".$trap.">\n";
echo "<input type=submit value=\"Gå videre\">";
echo "</form>\n";

# Stygg måte å resette på...
echo "<form action=meldingssystem2.php method=\"POST\">";
foreach ($eier as $name) {
  echo "<input type=hidden name=eier[] value=$name>\n";
}
echo "<input type=hidden name=bruker value=".$bruker.">\n";
echo "<input type=hidden name=trap value=$trap>";
echo "<input type=submit value=Reset>";
echo "</form>";

##################################################
# En funksjon som skriver ut en drop-down
# liste som inneholder alle varseltypene som 
# er i databasen.
##################################################

function lagDropDown($array,$name) {
  global $varseltype,$sms;
  echo "<select name=$name>\n";
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

function finn_enheter($bruker,$trapid) {
  $array = array();

  $dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");  
  mysql_select_db("trapdetect",$dbh);
  
########################################
# Henter alle eierforhold og brukernavn
########################################
  $sporring = "select org.navn,user.id from useriorg,org,user where user.id=useriorg.userid and useriorg.orgid=org.id and user.user='".$bruker."'";
  $result = mysql_query($sporring, $dbh);

  $eier = array();
  while ($row = mysql_fetch_row($result)) {
    array_push($eier,$row[0]);
    $brukerid=$row[1];
  }

##############################
# Finner navn på trap
##############################
  $sporring = "select syknavn from trap where id=$trapid";
  $res = mysql_query($sporring);
  $trapnavn = mysql_fetch_row($res);

######################################################################
# Finner alle ting fra varsel-tabellen som brukeren abonnerer på
######################################################################
  $sporring = "select * from varsel where userid=$brukerid and trapid=$trapid";
  $res = mysql_query($sporring);

######################################################################
# Henter alle kategorier og underkategorier fra varsel-tabellen
######################################################################
  while($row=mysql_fetch_array($res)){
    if ($row[kat] && $row[ukat]) {
      $array[$row[ukat]] = $row[kat];
    } elseif ($row[kat]) {
      $array[$row[kat]] = 1;
    } 
  }

######################################################################
# Henter sysname til alle enhetene som ligger i unntak-tabellen
######################################################################
  $sporring = "select manage.nettel.sysname from trapdetect.unntak,manage.nettel where userid=$brukerid and trapid=$trapid and manage.nettel.id=trapdetect.unntak.nettelid";
  $res = mysql_query($sporring);
  while ($row=mysql_fetch_row($res)) {
    $array[$row[0]] = 1;
  }

  $array[trap] = $trapnavn[0];
  $temp = array();
  foreach ($eier as $name) {
    array_push($temp,$name);
  }
  $array[eier] = $temp;
  $array[bruker] = $bruker;
# Ferdig med formen.

  mysql_close($dbh);

  foreach (array_keys($array) as $element) {
#    print "$element -> $array[$element]<br>\n";
  }

  return $array;
}

?>


</body></html>
