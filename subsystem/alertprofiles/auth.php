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




global $login;
$login = false;

  /*
   * Already logged in
   */
if ( session_get('login') ) {
	$login = true;	
}
if (!isset($_ENV['REMOTE_USER'])) {
    $dbh->nyLogghendelse(session_get('uid'), 2, gettext("Logged out") );
    $login = false;
    session_set('login', false);
}

/*
* First time login to NAVuser..
*
*	If remote_user is set, and Alert profiles has not yet registered that the user 
*	has logged in, or Alert Profiles has registered a login with another username,
*	THEN Alert Profiles will recheck and create session information, permissions etc.
*
*/


if (session_exist('login')) { echo "Sesison exist..."; }

if (isset($_ENV['REMOTE_USER'] ) AND
	( session_get('login') === false  OR 
		(session_get('bruker') != $_ENV['REMOTE_USER']) 
	) ) {




    $username = $_ENV['REMOTE_USER'];

    $querystring = "
SELECT Account.id AS aid, ap.value 
FROM Preference, Account 
	LEFT OUTER JOIN (
		SELECT accountid, property, value FROM AccountProperty WHERE property = 'language' 
	) AS ap ON 
    (Account.id = ap.accountid) 
WHERE (Account.login = '$username') AND 
    (Account.id = Preference.accountid) ";



    if (! $query = pg_exec($dbh->connection, $querystring)  ) {
        $nerror = new Error(2);
        $nerror->message = gettext("Error occured with database query.");
        $error[] = $nerror;
    } else {
        if (pg_numrows($query) == 1) {
            if ( $data = pg_fetch_array($query, 0) ) {
                // INNLOGGING OK!!
                $foo =  gethostbyaddr (getenv ("REMOTE_ADDR") );
                $dbh->nyLogghendelse($data["aid"], 1, gettext("Logged in from ") . $foo);
                
                $bgr = $dbh->listBrukersGrupper($data["aid"], 0);
                $uadmin = 1;
                foreach ($bgr AS $bg) {
                	if ($bg[0] == 1) $uadmin = 100;
                	if ($bg[0] == 2) $uadmin = 0;
                }
                
                // MUST BE REMOVED!
				if ($data["aid"] == 1000) {
					$uadmin = 10000;
				} 
				
				session_delete('uid');
				session_delete('admin');
				session_delete('lang');
				session_delete('bruker');
				session_delete('login');
				session_delete('action');
				session_delete('subaction');

//				session_destroy();

                session_set('uid', $data["aid"]);
                session_set('admin', $uadmin);
                session_set('lang', $data["value"]);
                session_set('bruker', $username);
                session_set('login', true);
                $login = true;
            } else {
                $nerror = new Error(2, 1);
                $nerror->message = gettext("Something bad happened when trying to fetch the user ID from the database.");
				$error[] = $nerror;
/* 				session_delete('uid'); */
/* 				session_delete('admin'); */
/* 				session_delete('lang'); */
/* 				session_delete('bruker'); */
/* 				session_delete('login'); */
/* 				session_delete('action'); */
/* 				session_delete('subaction');				 */
/*                 session_set('login', false); */				
            }
        } else {
            $nerror = new Error(1, 1);
            $nerror->message = gettext("Database inconsistency. You are correctly logged in, but your user is not correctly configured to work with NAV Alert Profiles. Contact your system administrator.");
			$error[] = $nerror;

/* 			session_delete('uid'); */
/* 			session_delete('admin'); */
/* 			session_delete('lang'); */
/* 			session_delete('bruker'); */
/* 			session_delete('login'); */
/* 			session_delete('action'); */
/* 			session_delete('subaction'); */
/* 			session_set('login', false); */
        }
    }
}




?>
