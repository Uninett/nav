<?php
/*
 * function wrapper for hasPrivilege.
 *
 * PATH_BIN contains the path to the hasPrivilege.py script.
 */

function access_address_type($username, $addresstype) {
	return true;
}
function access_sms($username) {
	return access_address_type($username, 2);
}

?>