<?php
/*
 * function wrapper for hasPrivilege.
 *
 * PATH_BIN contains the path to the hasPrivilege.py script.
 */

function access_address_type($username, $addresstype) {
	$atypes = array(
		1 => 'e-mail',
		2 => 'sms',
	);
	$returncode = 'NA';
	$interpreter = $_ENV['PYTHONHOME'] ? $_ENV['PYTHONHOME'] . '/bin/python' : "";
	
	$cmd = $interpreter . ' ' . PATH_BIN . '/hasPrivilege.py ' . escapeshellcmd($username) . ' alert_by ' . $atypes[$addresstype];
	system($cmd, $returncode);
	return ($returncode === 0);
}
function access_sms($username) {
	return access_address_type($username, 2);
}

?>