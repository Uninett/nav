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
    $this->type_name = array(gettext('Ukjent Feil'), gettext('Feil under innlogging'), 
    	gettext('Databasefeil'), gettext('Sikkerhetsfeil'), gettext('Lese/Skrive feil') );
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


global $login;
$login = false;



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
    
	if (! $query = @pg_exec($dbcon, "SELECT id, admin, lang FROM bruker WHERE brukernavn = '$username' AND passord = '$passwd'")  ) {
		$error = new Error(2);
		$error->message = gettext("Feil med datbasespørring.");
    } else {
		if (pg_numrows($query) == 1) {
			if ( $data = pg_fetch_array($query, $row) ) {
				// INNLOGGING OK!!
				$foo =  gethostbyaddr (getenv ("REMOTE_ADDR") );
				$dbh->nyLogghendelse($data["id"], 1, gettext("Logget inn fra ") . $foo);
				session_set('uid', $data["id"]);
				session_set('admin', $data["admin"]);
				session_set('lang', $data["lang"]);
				session_set('bruker', $username);
				session_set('login', true);
				$login = true;
			} else {
				$error = new Error(2);
				$error->message = gettext("Noe feil skjedde når jeg prøvde å hente ut brukerid fra databasen.");
			}
    	} else {
			$error = new Error(1);
			$error->message = gettext("Du skrev inn feil brukernavn eller passord, forsøk igjen...");
    	}
    
  	}

  }


if ($action == "logout") {
	$dbh->nyLogghendelse(session_get('uid'), 2, gettext("Logget ut") );
	$login = false;
	session_set('login', false);
}

?>
