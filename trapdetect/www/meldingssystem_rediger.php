<?php
require("meldingssystem.inc");
html_topp("Henter data...");
echo "Henter data fra databasen...";
echo "ferdig, trykk på knappen for å redigere.<br>\n";

finn_enheter($bruker,$trap);

function finn_enheter($bruker,$trapid) {

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

  echo "<form action=meldingssystem2.php method=\"POST\">";

######################################################################
# Henter alle kategorier og underkategorier fra varsel-tabellen
######################################################################
  while($row=mysql_fetch_array($res)){
    if ($row[kat] && $row[ukat]) {
      echo "<input type=hidden name=$row[ukat] value=$row[kat]>\n";
    } elseif ($row[kat]) {
      echo "<input type=hidden name=$row[kat] value=1>\n";
    } 
  }

######################################################################
# Henter sysname til alle enhetene som ligger i unntak-tabellen
######################################################################
  $sporring = "select manage.nettel.sysname from trapdetect.unntak,manage.nettel where userid=$brukerid and trapid=$trapid and manage.nettel.id=trapdetect.unntak.nettelid";
  $res = mysql_query($sporring);
  while ($row=mysql_fetch_row($res)) {
    echo "<input type=hidden name=$row[0] value=1>\n";
  }

  echo "<input type=hidden name=trap value=$trapnavn[0]>\n";
  foreach ($eier as $name) {
    echo "<input type=hidden name=eier[] value=".$name.">\n";
  }
  echo "<input type=hidden name=bruker value=$bruker>\n";
# Ferdig med formen.
  echo "<input type=submit value=\"Rediger\">";
  echo "</form>";
}

?>

</body></html>