<?php

if (! $dbcon = @pg_connect("user=manage password=eganam dbname=navprofiles") ) {
	print "<h1>" . gettext("Databasefeil") . "</h1>";
	print "<p>" . gettext("Hele portalen blir sperret når ikke databasen er tilgjenglig.");
	exit(0);
} 


$dbh = new DBH($dbcon);


?>
