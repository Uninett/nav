<?php
/*
 * function wrapper for hasPrivilege.
 */

function access_address_type($username, $addresstype) {
	return true;
}
function access_sms($username) {
	return access_address_type($username, 2);
}

?>