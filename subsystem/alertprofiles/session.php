<?php
/*
 * $Id$
 *
 * A general library for session variables.  This library exists
 * because PHP has changed the names of some of the session related
 * functions, and it's easier to fix this in one place rather then in
 * 100.
 *
 *
 * Copyright 2002-2004 UNINETT AS
 * 
 * This file is part of Network Administration Visualized (NAV)
 *
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *
 * Authors: Andreas Aakre Solberg <andreas.solberg@uninett.no>
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
/* 	if (!session_exist($var)){ */
/* 		return null; */
/* 	} */
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
/* 	if (!get_exist($var)){ */
/* 		return null; */
/* 	} */
	if (get_exist($var) )
		return $_GET[$var] ;
	else
		return false;
}

function get_exist($var) {
	return array_key_exists($var, $_GET); 
}

function post_get($var) {
/* 	if (!post_exist($var)){ */
/* 		return null; */
/* 	} */
	if (post_exist($var))
		return $_POST[$var] ;
	else
		return null;
}

function post_exist($var) {
	if ( array_key_exists($var, $_POST) )
		return (strlen($_POST{$var}) > 0);
	else return false;
}

function best_get($var) {
	if ( post_exist($var)) { return post_get($var); }
	if ( get_exist($var)) { return get_get($var); }
	if ( session_exist($var)) { return session_get($var); }
	return null;
}

// Starter sesjonshåndtering...
session_start();

?>
