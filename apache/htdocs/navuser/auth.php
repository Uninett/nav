<?php

/* 
 * auth.inc
 * - Denne inneholder authentiseringsrutinene for portalen til NAV.
 *
 *

 * Dette er et generelt bibliotek for å lagre sesjonsvariable,
 *	grunnen til at det er lagt i eget bibliotek er at php har endret litt
 *  på funksjonsnavnene for å lage sesjonsvariable og da er det enklere å endre
 *  ett sted enn 100. 
 
 */



/* 
 * Dette er en generell feilmeldingsklasse. 
 */
class Error {
  var $type;
  var $message;
  var $type_name;
  
  function Error ($errtype) {
    $this->type_name = array('Ukjent Feil', 'Feil under innlogging', 'Databasefeil');
    $this->type = $errtype;
  }

  function getHeader () {
    return $this->type_name[$this->type];
  }

  function setMessage ($msg) {
    $this->message = $msg;
  }

  function getHTML () {
    $html =  "<table width=\"100%\" class=\"feilWindow\"><tr><td class=\"mainWindowHead\"><h2>";
    $html .= $this->GetHeader();
    $html .= "</h2></td></tr>";
    $html .= "<tr><td><p>" . $this->message . "</td></tr></table>";
    return $html;
  }

}

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
	unset( $_SESSION[$var] );
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
global $login;
$login = false;

if (! $dbcon = @pg_connect("user=manage password=eganam dbname=navuser") ) {
	$error = new Error(2);
	$error->message = "Kunne ikke koble til database.";
} else {

  /*
   * Denne seksjonen omhandler brukere som allerede er innlogget
   */


	if ( session_get('login') ) {
		$login = true;	
	}
    
  /*
   * Denne seksjonen omhandler innlogging for første gang
   */
  if (isset($username)) {
    
	$username = addslashes($username);
	$passwd = addslashes($passwd);
    
	if (! $query = @pg_exec($dbcon, "SELECT id, admin FROM bruker WHERE brukernavn = '$username' AND passord = '$passwd'")  ) {
		$error = new Error(2);
		$error->message = "Feil med datbasespørring.";
    } else {
		if (pg_numrows($query) == 1) {
			if ( $data = pg_fetch_array($query, $row) ) {
				// INNLOGGING OK!!
				session_set('uid', $data["id"]);
				session_set('admin', $data["admin"]);
				session_set('bruker', $username);
				session_set('login', true);
				$login = true;
			} else {
				$error = new Error(2);
				$error->message = "Noe feil skjedde når jeg prøvde å hente ut brukerid fra databasen.";
			}
    	} else {
			$error = new Error(1);
			$error->message = "Du skrev inn feil brukernavn eller passord, forsøk igjen...";
    	}
    
  	}

  }

}  


if ($action == "logout") {
	$login = false;
	session_set('login', false);
}

?>
