<?php
/*
 * session.php
 * (c) Andreas Åkre Solberg (andrs@uninett.no) - Mai, 2002
 *
 * Dette er et generelt bibliotek for å lagre sesjonsvariable,
 *	grunnen til at det er lagt i eget bibliotek er at php har endret litt
 *  på funksjonsnavnene for å lage sesjonsvariable og da er det enklere å endre
 *  ett sted enn 100.
 *
 */



/*
 *	FUNKSJONER for sesjonshåndtering.
 */

function session_set($var, $par) {
	$varname = "SeSsIoN_" . $var;
	$_SESSION[$varname] = $par;
}

function session_get($var) {
	$varname = 'SeSsIoN_' . $var;
	return $_SESSION[$varname];
}

function session_delete($var) {
	$varname = 'SeSsIoN_' . $var;
//	session_unregister( $_SESSION[$varname] );
	unset($_SESSION[$varname]);
}

function session_exist($var) {
	return array_key_exists($var, $_SESSION); 
}

function get_get($var) {
	if (get_exist($var) )
		return $_GET[$var] ;
	else
		return false;
}

function get_exist($var) {
	return array_key_exists($var, $_GET); 
}

function post_get($var) {
	if (post_exist($var))
		return $_POST[$var] ;
	else
		return undef;
}

function post_exist($var) {
	if ( array_key_exists($var, $_POST) )
		return (strlen($_POST{$var}) > 0);
	else return false;
}


// Starter sesjonshåndtering...
session_start();

?>
