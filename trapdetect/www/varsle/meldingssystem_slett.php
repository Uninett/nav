<?php

require("meldingssystem.inc");
html_topp("Sletter innlegg");

$keys = array_keys($HTTP_POST_VARS);

#foreach ($keys as $key) {
#  print "$key -> $HTTP_POST_VARS[$key]<br>\n";
#}

$dbh = pg_Connect ("dbname=trapdetect user=varsle password=lgagikk5p");

# Finner trapname
$res = pg_exec("select syknavn from trap where id=$trapid");
$trapname = pg_fetch_row($res,0);
print "Sletter abonnementet for <b>$trapname[0]</b>, bruker <b>$bruker</b><br>\n";

$sporring = "delete from varsel where brukerid=$brukerid and trapid=$trapid";
#print "$sporring<br>\n";
pg_exec($sporring);

$sporring = "delete from unntak where brukerid=$brukerid and trapid=$trapid";
#print "$sporring<br>\n";
pg_exec($sporring);

echo "<form action=meldingssystem_start.php?bruker=$bruker method=\"POST\">";
echo "<input type=submit value=\"Til hovedsiden\">\n";
echo "</form>\n";


?>

</body></html>