<?php
/*
 * function for checking syntax on user input.
 *
 */

function check_syntax_address_sms(&$string) {
	// Removing non-relevant characters
	$string = preg_replace('/[^\+0-9]/', '', $string);
	
	// Removing trailing +47
	$string = preg_replace('/^(\+47)(.*?)$/', '$2', $string);
	
	// Check if the result contains 8 numbers...
	return preg_match('/^[0-9]{8}$/', $string);
}





?>