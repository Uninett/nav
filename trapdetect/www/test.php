<?php require('include.inc'); ?>

<?php tittel("TESTSIDE") ?>

TESTSIDE

<?php topptabell(status) ?>

<p><center><u><h3>TEST</h3></u></center></p>

<?php

$teller = 0;
while ($teller < 30) {
	$date = date("d m Y", mktime(0,0,0,date("m"),date("d")-$teller,date("Y")));
	print "$date<br>\n";
	$teller++;
}

?>

<?php bunntabell() ?>

