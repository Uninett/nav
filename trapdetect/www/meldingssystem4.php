<?php
require ('meldingssystem.inc');
html_topp("Varslingsregistrering - legg inn i databasen");
list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);
if ($admin && $REMOTE_USER != $bruker) {
  print "Du er innlogget som <b>$bruker</b> med administratorrettighetene til <b>$REMOTE_USER</b><br>\n";
}

# Kobler til database.
#echo "<p>Oppretter kontakt med databasen...";
$dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");
#echo "ok</p>\n";

##################################################
# Henter nødvendige data; brukerid
##################################################
mysql_select_db("trapdetect", $dbh);
$resultat = mysql_query("select id from user where user='".$bruker."'");
$userid = mysql_fetch_row($resultat);
##################################################

$postvars = $HTTP_POST_VARS;
$keys = array_keys($postvars);
$trapvars = array();

foreach ($keys as $key) {
  preg_match("/^(\d+):(.+)/",$key,$matches);
  # Legger inn det arrayet som skal inneholde postvars til denne trapen
  if (!$trapvars[$matches[1]]) {
    $tempvars = array();
  } else {
    $tempvars = $trapvars[$matches[1]];
  }

  if (preg_match("/(list|unntak)/",$key)) {
    $tempvars[$matches[2]] = $postvars[$key];
    foreach ($postvars[$key] as $temp) {
#      echo "$key -> $temp<br>\n";
    }
  } elseif(!preg_match("/bruker/",$key)) {
    $tempvars[$matches[2]] = $postvars[$key];
#    echo "$key -> $postvars[$key]<br>\n";
  } else {
#    echo "$key -> $postvars[$key]<br>\n";
  }

  $trapvars[$matches[1]] = $tempvars;
}

$keys = array_keys($trapvars);
foreach ($keys as $key) {
  if ($key) {
#    print "KEY: $key<br>\n";
    $temp = $trapvars[$key];
    legginn($key,$temp);
    $tempkeys = array_keys($temp);
    foreach ($tempkeys as $tempkey) {
#      print "$tempkey -> $temp[$tempkey]<br>\n";
    }
  }
}


##################################################
# Funksjon som legger inn alle data om et varsel
# Tar inn navn på trap, trapid og arrayet som
# inneholder alle variable.
##################################################
function legginn($trapid,$variable) {
  global $userid,$dbh;

#  print "Funksjon legginn får inn $trapid, $variable<br>\n";

  $resultat = mysql_query("select syknavn from trap where id=$trapid");
  $trapname = mysql_fetch_row($resultat);

##################################################
# Parser variable og lager spørringer.
##################################################

# Leter først etter unntak som vi må ha for å lage spørringer.
  $enhetunntak = array();
  $ukatunntak = array();

  if ($variable["unntak"]) {
    foreach ($variable["unntak"] as $element) {
      if (preg_match("/(.+),(.+)/",$element,$matches)) {
# Dette er et underkategoriunntak
	$sporring = "insert into varsel (userid,trapid,kat,ukat,vtypeid) values (".$userid[0].",".$trapid.",'".$matches[1]."','".$matches[2]."',0) ";
	array_push($ukatunntak,$sporring);
      } else { 
# Dette er en enhet
	array_push($enhetunntak,$element);
      }
    }
  }

################################################################################
# Under spørringene behandler jeg unntak slik:
# Hvis det bare er en kategori uten unntak på underkategoriene, lager jeg 
# spørringen direkte, med bare kat satt i varsel.
# Hvis det er en kategori MED unntak på underkategoriene, er dette allerede
# i unntak-arrayet, så det bryr jeg meg ikke om.
# Hvis det er en underkategori uten kategori, legger jeg den direkte inn
# i varsel UTEN kat.
#
# Dette er viktig å forstå for uthenting av varsel.
################################################################################
  $keys = array_keys($variable);

  $sporringer = array();
  foreach ($keys as $element) {
    if (preg_match("/^kat:(.+)/",$element,$matches)) { 
# Vi har funnet en hovedkategori
      $sporring = "insert into varsel (userid,trapid,kat,vtypeid) values (".$userid[0].",".$trapid.",'".$matches[1]."',".$variable[$matches[0]].")";
      array_push($sporringer,$sporring);
    } elseif (preg_match("/^ukat:(.+),(.+)/",$element,$matches)) { 
# Vi har funnet en underkategori
      $sporring = "insert into varsel (userid,trapid,kat,ukat,vtypeid) values (".$userid[0].",".$trapid.",'".$matches[1]."','".$matches[2]."',".$variable[$matches[0]].")";
      array_push($sporringer,$sporring);
    } elseif (preg_match("/enhet:(.+)/",$element,$matches)) { 
# Vi har funnet en enhet som skal legges til.
      mysql_select_db("manage", $dbh);
      $res = mysql_query("select id from nettel where sysname='".$matches[1]."'");
      if (mysql_num_rows($res) == 0) { 
# Noe gikk galt, kanskje med sysname
	$matches[1] = preg_replace("/_/",".",$matches[1]); 
# Skifter underscore med punktum
	$res = mysql_query("select id from nettel where sysname='".$matches[1]."'"); 
# Ny spørring kjøres
      }
      $enhet = mysql_fetch_row($res);
      $sporring = "insert into unntak (userid,trapid,nettelid,vtypeid,status) values (".$userid[0].",".$trapid.",".$enhet[0].",".$variable[$matches[0]].",'pluss')";
      array_push($sporringer,$sporring);
    } elseif (preg_match("/spesial/",$element)) { 
# Denne kommer av traps uavhengige av enheter
      $sporring = "insert into varsel (userid,trapid,vtypeid) values (".$userid[0].",".$trapid.",".$variable["spesial"].")";
      array_push($sporringer,$sporring);
    }
  }

##################################################
# Ferdig med alle elementene i inputstrengen,
# trenger nå å skrive alle unntak for enheter som
# er i $enhetunntak til unntak-tabellen.
##################################################
  foreach ($enhetunntak as $innlegg) {
    mysql_select_db("manage", $dbh);
    $res = mysql_query("Select id from nettel where sysname='".$innlegg."'");
    $enhet = mysql_fetch_row($res);
    $sporring = "insert into unntak (userid,trapid,nettelid,status) values (".$userid[0].",".$trapid.",".$enhet[0].",'minus')";
    array_push($sporringer,$sporring);
  }

  foreach ($ukatunntak as $innlegg) {
    array_push($sporringer,$innlegg);
  }

######################################################################
# Legger alle spørringene inn i databasen.
#
# Sletter først alle innlegg med samme bruker og trap som eksisterer
# fra før. Så legges alle innleggene inn.
######################################################################
  mysql_select_db("trapdetect", $dbh);
  mysql_query("delete from varsel where userid=".$userid[0]." and trapid=".$trapid);
  mysql_query("delete from unntak where userid=".$userid[0]." and trapid=".$trapid);
  foreach ($sporringer as $sporring) {
#    echo "$sporring<br>\n";
    mysql_query($sporring);
  }

  echo "<p>Innleggene for <b>$trapname[0]</b> er nå lagt i databasen.</p>";

}

echo "<p>Trykk på <b>Registrer ny trap</b>-knappen for å legge til et nytt abonnement eller gå tilbake til hovedsiden med å trykke <b>Til hovedsiden</b></p>";

echo "<form action=meldingssystem.php method=\"POST\">";
echo "<input type=hidden name=bruker value=$bruker>";
echo "<input type=submit value=\"Registrer ny trap\">\n";
echo "</form>\n";

knapp_hovedside($bruker);

?>
</body></html>
