<?php

if (! $dbcon = @pg_connect("user=manage password=eganam dbname=navuser") ) {
	print "<h1>Databasefeil</h1>";
	print "<p>Hele portalen blir sperret når ikke databasen er tiljgenglig.";
	print "<p>Dette av sikkerhetsmessige årsaker";
	exit(0);
} 


$dbh = new DBH($dbcon);


?>
