<?php require('meldingssystem.inc');

html_topp("Varslingssiden for ITEA");

print "<p><h2>Velkommen til varslingssiden</h2></p>\n";
print "<p><u>Hva vil du gjøre?</u></p>\n";

if (!$bruker) {
  $bruker = $REMOTE_USER;
}
list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);

#$dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");
$dbh = pg_connect("dbname=trapdetect");

########################################
# Skriver ut meny for administratorer
########################################
if ($admin) {
  print "<p><b>ADMINISTRERE BRUKERE</b></p>\n";
  print "Du har adminrettigheter som bruker <b>$REMOTE_USER</b><br>\n";
  print "Du administrerer nå ";
  if ($bruker == $REMOTE_USER) {
    print "din egen konto<br>\n";
  } else {
    print "<b>$bruker</b> sin konto<br>\n";
  }
  print "Use the force... velg bruker som du skal administrere.<br>\n";
  print "<form action=meldingssystem_start.php method=POST>\n";
  print "<select name=bruker>\n";
  $sporring = pg_exec("select user from user");
  while ($res = pg_fetch_array($sporring)) {
    if ($bruker == $res[user]) {
      print "<option value=$res[user] selected>$res[user]</option>\n";
    } else {
      print "<option value=$res[user]>$res[user]</option>\n";
    }
  }
  print "</select>\n";
  print "<input type=submit value=\"Skift bruker\">";
  print "</form>\n";
 
  # Form for ny bruker
  print "<form action=meldingssystem_profil.php method=POST>\n";
  print "<input type=text name=bruker value=\"<brukernavn>\" size=15>\n";
  print "<input type=submit value=\"Opprett ny brukerprofil\">\n";
  print "</form>\n";

  # Form for sletting av bruker
  # Legger inn to bokser som begge må krysses av for å verifisere sletting
  # Dette fordi det er en alvorlig sak å slette en bruker.
  print "<form action=meldingssystem_slett_bruker.php method=POST>";
  print "<input type=checkbox name=slett1>";
  print "<input type=submit name=submit value=\"Slett $bruker\">";
  print "<input type=checkbox name=slett2>";
  print "(velg begge boksene for verifisering av sletting)";
  print "<input type=hidden name=bruker value=$bruker>";
  print "</form>";
} else {
  print "Du er registrert som bruker <b>$bruker</b><br>\n";
}

print "<hr width=450 align=left>\n";
########################################
# Skriver ut meny for ny varsling
########################################
print "<b>LEGG TIL NY VARSLING</b>";
echo "<form action=meldingssystem.php method=\"POST\">\n";
echo "<input type=hidden name=bruker value=$bruker>";
echo "<input type=submit value=\"Ny varsling\">&nbsp;Legg til nytt abonnement.\n";
echo "</form>\n";

print "<hr width=450 align=left>\n";

#############################################
# Skriver ut meny for endring av brukerprofil
#############################################
print "<b>ENDRING AV BRUKERPROFIL</b>";
print "<form action=meldingssystem_profil.php method=POST>\n";
print "<input type=submit value=\"Endre profil\">&nbsp;Trykk på knappen for å gå til siden for profilendring.<br>\n";
print "Her kan blant annet telefonnr. og mailadresse endres, samt tidspunkt for forsinket sms.<br>\n";
print "<input type=hidden name=bruker value=$bruker>\n";
print "</form>\n";

print "<hr width=450 align=left>\n";

print "<B>REDIGERING AV ABONNEMENT</B>\n";
echo "<form action=meldingssystem2.php method=\"POST\">\n";

##################################################
# Henter alle varslingstyper fra databasen, 
# legger de i et array for senere bruk.
##################################################
$result = pg_exec("select * from varseltype");
while ($svar = pg_fetch_row($result)) {
  $varseltype[$svar[1]] = $svar[0];
}
$type = array_keys($varseltype);

##############################
# Finner brukerid
##############################
$res=pg_exec("select id,sms from user where user='$bruker'");
$brukerid = pg_fetch_row($res);
$sms = $brukerid[1];

############################################################
# Finner alle traps som brukeren abonnerer på varsling på
############################################################
$sporring="select trapid,syknavn from varsel,trap where userid=$brukerid[0] and trapid=trap.id group by trapid order by syknavn";
$res=pg_exec($sporring);

$res2=pg_exec("select trapid,syknavn from unntak,trap where userid=$brukerid[0] and trapid=trap.id group by trapid order by syknavn");

if (pg_numrows($res) == 0 and pg_numrows($res2) == 0) {
  echo "Du abonnerer foreløpig ikke på noe\n";
} else {
  echo "<select name=trap>";
  while ($row=pg_fetch_row($res)) {
    $traps[$row[0]] = $row[1];
  }
  while ($row=pg_fetch_row($res2)) {
    $traps[$row[0]] = $row[1];
  }
##############################
# Skriver dropdown-menyen
# for redigering
##############################
  $keys = array_keys($traps);
  foreach($keys as $key) {
    echo "<option value=$key>$traps[$key]";
  }
  
  echo "</select>";

  echo "<input type=hidden name=bruker value=$bruker>";
  echo "<input type=submit value=\"Rediger eksisterende abonnement\"><br>Velg en av de abonnementene du allerede abonnerer på, og trykk på knappen for å redigere.\n";
  echo "</form>";

  print "<hr width=450 align=left>";
##############################
# Skriver dropdown-menyen
# for sletting
##############################
  print "<B>SLETTING AV ABONNEMENT</B>\n";
  print "<form action=meldingssystem_slett.php method=POST>";
  print "<select name=trapid>";
  foreach($keys as $key) {
    echo "<option value=$key>$traps[$key]";
  }
  
  echo "</select>";
  echo "<input type=hidden name=brukerid value=$brukerid[0]>";
  echo "<input type=hidden name=bruker value=$bruker>";
  echo "<input type=submit value=\"Slett abonnement\"><br>Velg det abonnementet som skal slettes og trykk på <b>Slett abonnement</b>.\n";
  echo "</form>";

  print "<hr width=450 align=left>\n";
############################################################
# Skriver ut oversikt over alle abonnement som brukeren har
############################################################
  print "<p><b>REDIGERING AV VARSELTYPE</b></p>\n";
  print "Skift varslingstype på de kategorier/underkategorier/enheter du vil og trykk <b>Lagre endringer</b>\n";
  $unntak = array();
  $keys = array_keys($traps);

  print "<form action=meldingssystem4.php method=\"POST\">\n";
  print "<table cellspacing=2 border=0>\n";
  foreach($keys as $key) {
    print "<tr><td>\n";
    print "<b>$traps[$key]:</b></td><td>\n";
#    lagSlettBoks($key,$traps[$key]);
    print "</td></tr>\n";
    $sporring="select * from varsel where userid=$brukerid[0] and trapid=$key order by kat,ukat";
    $res = pg_exec($sporring);
  
# Henter alle innlegg som ligger under denne trap og brukerid
    while ($row=pg_fetch_array($res)) {
# Vi vil ikke liste underkategoriene som er unntak
      if ($row[vtypeid] != 0) {
	print "<tr><td>&nbsp;</td><td>$row[kat]</td><td>$row[ukat]</td><td>\n";
# Hvis begge er definert er det en underkategori
	if ($row[kat] && $row[ukat]) {
	  lagDropDown($type,"$key:ukat:$row[kat],$row[ukat]",$row[vtypeid]);
	} elseif ($row[kat]) { 
# Hvis ikke er det en kategori
	  lagDropDown($type,"$key:kat:$row[kat]",$row[vtypeid]);
	} else { 
# Det er en trap uavhengig av enheter
	  lagDropDown($type,"$key:spesial",$row[vtypeid]);
	}
	print "</td></tr>\n";
      } else {
	array_push($unntak,"$row[kat],$row[ukat]");
      }
    }

    $sporring="select manage.nettel.sysname,nettelid,vtypeid,status from manage.nettel,unntak where userid=$brukerid[0] and trapid=$key and manage.nettel.id=nettelid order by manage.nettel.sysname";
    $res=pg_exec($sporring);
# Henter alle innlegg som ligger i unntak-tabellen
    while ($row=pg_fetch_array($res)) {
# Hvis det er en pluss så skal det kunne velges varseltype
      if ($row[status] == "pluss") {
	print "<tr><td>&nbsp;</td><td>$row[sysname]</td><td>&nbsp;</td><td>\n";
	lagDropDown($type,"$key:enhet:$row[sysname]",$row[vtypeid]);
	print "</tr>\n";
      } else {
# Lagrer alle unntakene.
	array_push($unntak,$row[sysname]);
      }
    }
    $unntak_alle[$key] = $unntak;
    print "<tr><td>&nbsp;</td></tr>\n";
  }
  print "</table>\n";

  foreach (array_keys($unntak_alle) as $temp) {
    foreach ($unntak_alle[$temp] as $enhet) {
      print "<input type=hidden name=$temp:unntak[] value=$enhet>\n";
    }
  }
  print "<input type=hidden name=bruker value=$bruker>\n";
  print "<input type=submit name=submit_form value=\"Lagre endringer\">\n";
  print "</form>\n";
}
##################################################
# En funksjon som skriver ut en drop-down
# liste som inneholder alle varseltypene som 
# er i databasen.
##################################################
function lagDropDown($array,$name,$vtype) {
  global $varseltype,$sms,$unntak;

  echo "<select name=$name>\n";
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

########################################
# En funksjon som lager en slettboks
# Spesifikk for denne siden
########################################
function lagSlettBoks($trapid,$trapname) {
  global $bruker,$brukerid;
  print "\n\t<form action=meldingssystem_slett.php method=\"POST\">\n";
  print "\t<input type=submit name=$trapid value=Slett>\n";
  print "\t<input type=hidden name=trapid value=$trapid>\n";
  print "\t<input type=hidden name=trapname value=$trapname>\n";
  print "\t<input type=hidden name=bruker value=$bruker>\n";
  print "\t<input type=hidden name=brukerid value=$brukerid[0]>\n";
  print "\t</form>\n";
}
?>
</body></html>
