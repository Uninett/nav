<?php require('include.inc'); ?>

<?php tittelspesial("Slett") ?>

<?php topptabell(diverse) ?>

<?php

# Connecter til database
$dbh = mysql_connect("localhost", "nett", "stotte") or die ("Kunne ikke åpne connection til databasen.");
mysql_select_db("manage", $dbh);

# Finner id'ene som skal friskmeldes
$linje = array_shift ($argv);
preg_match_all("/\d+/",$linje,$array);
$temp = $array[0]; # merkelig opplegg...

foreach ($temp as $id) {
	print "Friskmelder $id<br>\n ";
	friskmeld($id);
}


function friskmeld($id) {

	global $dbh;

	$sporring = "UPDATE status SET til=now() WHERE id=".$id;
	$result = mysql_query("$sporring", $dbh);
}

?>

<?php bunntabell() ?>
