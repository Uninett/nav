<?php

require("meldingssystem.inc");
html_topp("Sletter innlegg");

$keys = array_keys($HTTP_POST_VARS);

#foreach ($keys as $key) {
#  print "$key -> $HTTP_POST_VARS[$key]<br>\n";
#}

$dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");
mysql_select_db("trapdetect", $dbh);

# Finner trapname
$res = mysql_query("select syknavn from trap where id=$trapid");
$trapname = mysql_fetch_row($res);
print "Sletter abonnementet for <b>$trapname[0]</b>, bruker <b>$bruker</b><br>\n";

$sporring = "delete from varsel where userid=$brukerid and trapid=$trapid";
#print "$sporring<br>\n";
mysql_query($sporring);
$antall += mysql_affected_rows();

$sporring = "delete from unntak where userid=$brukerid and trapid=$trapid";
#print "$sporring<br>\n";
mysql_query($sporring);
$antall += mysql_affected_rows();

#print "Antall rader slettet: $antall<br>\n";

echo "<form action=meldingssystem_start.php?bruker=$bruker method=\"POST\">";
echo "<input type=submit value=\"Til hovedsiden\">\n";
echo "</form>\n";


?>

</body></html>