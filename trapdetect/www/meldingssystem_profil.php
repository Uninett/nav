<?php 
require('meldingssystem.inc');

html_topp("Endring av profil");

$smsfra_array = array("15:00:00","17:00:00","22:00:00","23:30:00");
$smstil_array = array("06:00:00","07:00:00","08:00:00","10:00:00");

#skrivpost($HTTP_POST_VARS);

$border=0;

$alert = "Valgene dine vil ikke bli oppdatert i databasen selv om du forandrer på dem her. Dette fordi du ikke har admin-rettigheter.";

list ($bruker,$admin) = verify_user($bruker,"bredal");

$dbh = pg_Connect ("dbname=trapdetect user=trapdetect password=tcetedpart");

# Henter all info om bruker
$sporring = "select * from bruker where bruker='$bruker'";
$res = pg_exec($dbh,$sporring);
$ny = 0;
if (pg_numrows($res) == 0) {
#  print "Ny bruker<br>\n";
  $ny = 1;
} else {
  $brukerinfo = pg_fetch_array($res,0);
}

# Henter alle org i org-tabellen
$hent_org = pg_exec("select * from org");
$antall = pg_numrows($hent_org);
$org = array();
for ($i=0;$i<$antall;$i++) {
  $res = pg_fetch_array($hent_org,$i);
  $org[$res[id]] = $res[navn];
}

if (!$ny) {
# Henter alle org som bruker er med i
  $hent_useriorg = pg_exec("select * from brukeriorg where brukerid=$brukerinfo[id]");
  $antall = pg_numrows($hent_useriorg);
  $useriorg = array();
  for ($i=0;$i<$antall;$i++) {
    $res = pg_fetch_array($hent_useriorg,$i);
    $useriorg[$res[orgid]]++;
  }
}

# Skriver ut info om bruker som kan forandres
print "<form name=minform action=meldingssystem_profil_endre.php METHOD=POST>\n";
print "<table border=$border>\n";
print "<tr><td>Mailadresse:</td><td><input type=text size=30 name=mail value=$brukerinfo[mail]></td><td>Organisasjoner*</td></tr>\n";
print "<tr><td>Telefonnr:</td><td><input type=text size=15 name=tlf value=$brukerinfo[tlf]></td><td rowspan=4 valign=top>\n";

# Organisasjonstilhørighet
if ($admin) {
  print "<select name=org[] size=6 multiple>\n";
  while (list($key,$val) = each($org)) {
    if ($useriorg[$key]) {
      print "<option value=$key selected>$val</option>";
    } else {
      print "<option value=$key>$val</option>";
    }
  }
  print "</select>\n";
} else {
  print "<table border=$border>";
  while (list($key,$val) = each($org)) {
    if ($useriorg[$key]) {
      print "<tr><td><b>$val</b></td></tr>";
    } else {
      print "<tr><td><font color=silver>$val</font></td></tr>";
    }
  }
  print "</table>";
}

# Status-informasjon
print "</td></tr><br>\n";
print "<tr><td>Status:</td><td>\n";
print "<select name=status>\n";
if ($brukerinfo[status] == "fri") {
  print "<option value=fri selected>fri</option>\n";
  print "<option value=aktiv>aktiv</option>\n";
} else {
  print "<option value=fri>fri</option>\n";
  print "<option value=aktiv selected>aktiv</option>\n";
}
print "</select>\n";
print "</td></tr>\n";

# Forandringer av delayed-sms
print "<tr><td>Delayed sms fra:</td><td>\n";
delayedsms($brukerinfo[dsms_fra],$smsfra_array,"dsmsfra");
print "</td></tr>";
print "<tr><td>Delayed sms til:</td><td>";
delayedsms($brukerinfo[dsms_til],$smstil_array,"dsmstil");
print "</td></tr>";
print "</table>\n";

# sms-varslingsknapp
print "Mulighet for sms-varsling*&nbsp;";

if ($admin) {
  if ($brukerinfo[sms] == "Y") {
    print "<input type=checkbox name=sms checked>";
  } else {
    print "<input type=checkbox name=sms>";
  }
} else {
  if ($brukerinfo[sms] == "Y") {
    print "JA";
  } else {
    print "NEI";
  }
}
print "<br>\n";


# Skriver knappen for lagre endringer
if ($ny) {
  print "<input type=hidden name=ny value=1>\n";
}
echo "<input type=hidden name=bruker value=$bruker>\n";
print "<p><input type=submit value=\"Lagre endringer\"></p>";
print "</form>\n";

# Skriver tilbake-til-hovedsidenknapp
knapp_hovedside($bruker);

print "* - kan bare forandres av administrator<br<\n";

function delayedsms($tid,$array,$type) {
  print "<select name=$type>\n";
  foreach ($array as $element) {
    if (!strcmp($element,$tid)) {
      print "<option value=$element selected>$element</option>\n";
    } else {
      print "<option value=$element>$element</option>\n";
    }
  }
  print "</select>\n";
}

?>

</body></html>