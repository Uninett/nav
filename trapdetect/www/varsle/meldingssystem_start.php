<?php 

require('meldingssystem.inc');
require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');

if (!$bruker) {
  $bruker = $REMOTE_USER;
}
list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);

navstart("Varslingsiden for ITEA",$bruker);

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

-->
</script>

<?php
#$dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");
$dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");
$dbh_m = pg_Connect ("dbname=manage user=navall password=uka97urgf");

##################################################
# Henter alle varslingstyper fra databasen, 
# legger de i et array for senere bruk.
##################################################
$result = pg_exec($dbh,"select * from varseltype");
$rows = pg_numrows($result);
$varseltype = array();
for ($i=0;$i < $rows; $i++) {
  $svar = pg_fetch_row($result,$i);
  $varseltype[$svar[1]] = $svar[0];
}
$type = array_keys($varseltype);

##############################
# Finner brukerid
##############################
$res=pg_exec($dbh,"select id,sms,navn from bruker where bruker='$bruker'");
if (pg_numrows($res) == 0 && !$admin) {
  print "Du er foreløpig ikke registrert som bruker av TrapDetect. Ta kontakt med en av administratorene for å bli registrert som bruker.<br>\n";

  # Henter alle administratorer fra tekstfilen.
  $filename = "/usr/local/trapdetect/www/msyst.conf";
  $contents = file($filename);
  
  print "<br>ADMINISTRATORER:<br>\n";
  print "<table>\n";
  print "<tr><td>EMAIL</td><td>TLF</td></tr>";
  foreach ($contents as $name) {
    $name = chop($name);
    $res = pg_exec($dbh, "select navn,mail,tlf from bruker where bruker='$name'");
    $svar = pg_fetch_row($res,0);
    print "<tr><td>$svar[0]</td><td>$svar[1]</td><td>$svar[2]</td></tr>\n";
  }
  print "</table>\n";
} else {
  
   ############################################
   # Skriver åpningshilsen.
   ############################################
  if (pg_numrows($res) == 0) {
    print "<p>Du er admin, men er ikke bruker av systemet. Gå til brukerprofilen din og legg inn informasjon om deg selv.</p>";
    #############################################
    # Skriver ut meny for endring av brukerprofil
    #############################################
    print "<form action=meldingssystem_profil.php method=POST>\n";
    print "<input type=submit value=\"Brukerprofil\">\n";
    print "<input type=hidden name=bruker value=$bruker>\n";
    print "</form>\n";
  } else {

    $brukerid = pg_fetch_row($res,0);
    $sms = $brukerid[1];
    $navn = $brukerid[2];

    print "<p><center><h1>Velkommen til din varslingsprofil</h1></center></p>\n";
    print "<p>Hei $navn! Her kan du styre din varslingsprofil. For mer informasjon trykk <a href=\"#\" onClick=\"popup('meldingssystem_start_hjelp.html', 'Win1', 500, 500); return false\">her</a>.</p>";
    #############################################
    # Skriver ut meny for endring av brukerprofil
    #############################################
    print "<form action=meldingssystem_profil.php method=POST>\n";
    print "<input type=submit value=\"Brukerprofil\">\n";
    print "<input type=hidden name=bruker value=$bruker>\n";
    print "</form>\n";
        
    ############################################################
    # Finner alle traps som brukeren abonnerer på varsling på
    ############################################################

    $sporring="select trapid,syknavn from varsel,trap where brukerid=$brukerid[0] and trapid=trap.id group by trapid,syknavn order by syknavn";
    
    $res=pg_exec($dbh,$sporring);
    
    $res2=pg_exec($dbh,"select trapid,syknavn from unntak,trap where brukerid=$brukerid[0] and trapid=trap.id group by trapid,syknavn order by syknavn");

    if (pg_numrows($res) == 0 and pg_numrows($res2) == 0) {
      echo "<p>Du abonnerer foreløpig ikke på noe. For å starte et abonnement, trykk på 'Nytt abonnement'.</p>\n";
    varselmeny();
    } else {
      for ($i=0; $i < pg_numrows($res); $i++) {
	$row=pg_fetch_row($res,$i);
	$traps[$row[0]] = $row[1];
      }
      for ($i=0; $i < pg_numrows($res2); $i++) {
	$row=pg_fetch_row($res2,$i);
	$traps[$row[0]] = $row[1];
      }

      print "<hr width=450 align=left>\n";      
############################################################
# Skriver ut oversikt over alle abonnement som brukeren har
############################################################

      print "<b>REDIGERING AV VARSELTYPE<br></b>\n";
      print "Her er en oversikt over de varslene du abonnerer på. De er listet opp en etter en, med alle de enheter og varslingstyper de er registrert med. Du kan skifte varslingstype på de kategorier/underkategorier/enheter du vil og deretter trykke <b>Lagre endringer.</b>\n";
      $unntak = array();
      $keys = array_keys($traps);

      print "<form action=meldingssystem4.php method=\"POST\">\n";
      print "<table cellspacing=2 border=0>\n";
      foreach($keys as $key) {
	print "<tr><td>\n";
	print "<b>$traps[$key]:</b></td><td>\n";
	print "</td></tr>\n";
	$sporring="select * from varsel where brukerid=$brukerid[0] and trapid=$key order by kat,ukat";
	$res = pg_exec($dbh,$sporring);
	$rows = pg_numrows($res);
	for ($i=0; $i < $rows; $i++){
        # Henter alle innlegg som ligger under denne trap og brukerid
	  $row=pg_fetch_array($res,$i);
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

	$sporring="select boksid,vtypeid,status from unntak where brukerid=$brukerid[0] and trapid=$key";
	$res=pg_exec($dbh,$sporring);
	$rows = pg_numrows($res);
      # Henter alle innlegg som ligger i unntak-tabellen
	for ($i=0; $i < $rows; $i++){
	  $row=pg_fetch_array($res,$i);
	  $sporring = "select sysname from boks where boksid=$row[boksid]";
	  $hent_sysname = pg_exec($dbh_m,$sporring);
	  $hent_sysname_ant = pg_numrows($hent_sysname);
	  # Hvis sysname finnes i databasen, kan være slettet i løpet av natten.
	  if ($hent_sysname_ant > 0) {
	    $row_manage = pg_fetch_array($hent_sysname,0);
	    $row[sysname] = $row_manage[sysname];
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

      print "<hr width=450 align=left>\n";

##############################
# Skriver dropdown-menyen
# for redigering
##############################
      print "<B>ENDRE VARSLINGSPROFIL FOR EN HENDELSE DU ABONNERER PÅ</B>\n";
      print "<br>Her kan man forandre hvilke bokser/enheter man vil ha alarm på. Du kan selvfølgelig forandre varslingstypen her også. Velg først abonnementet det gjelder og trykk på knappen.";
      echo "<form action=meldingssystem2.php method=\"POST\">\n";
      echo "<select name=trap>";
      
      $keys = array_keys($traps);

      foreach($keys as $key) {
	echo "<option value=$key>$traps[$key]";
      }  
      echo "</select>";

      echo "<input type=hidden name=bruker value=$bruker>";
      echo "<input type=submit value=\"Endre varslingsprofil\">\n";
      echo "</form>";

      print "<hr width=450 align=left>";
      varselmeny();
      ##############################
      # Skriver dropdown-menyen
      # for sletting
      ##############################
      print "<B>FJERN EN HENDELSE FRA DIN PROFIL</B>\n";
      print "<br>Hvis du ikke vil abonnere på et varsel lenger, kan du bare slette det. Velg det abonnementet som skal slettes og trykk på <b>Slett abonnement</b>.";
      print "<form action=meldingssystem_slett.php method=POST>";
      print "<select name=trapid>";
      foreach($keys as $key) {
	echo "<option value=$key>$traps[$key]";
      }
  
      echo "</select>";
      echo "<input type=hidden name=brukerid value=$brukerid[0]>";
      echo "<input type=hidden name=bruker value=$bruker>";
      echo "<input type=submit value=\"Slett abonnement\">\n";
      echo "</form>";
    }
  }
}


########################################
# Skriver ut meny for ny varsling
########################################
function varselmeny() {
  global $bruker,$traps;

  print "<b>ABONNER PÅ NY HENDELSE</b>";
  print "<br>Her går man hvis man skal abonnere på et nytt varsel. Man velger hvilken hendelse man skal ha varsel på, hvilke bokser dette gjelder, og hvilken varseltype som skal brukes.";
  echo "<form action=meldingssystem.php method=\"POST\">\n";
  echo "<input type=hidden name=bruker value=$bruker>";
  echo "<input type=submit value=\"Nytt abonnement\">\n";
  echo "</form>\n";
  print "<hr width=450 align=left>\n";
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

navslutt();

?>

