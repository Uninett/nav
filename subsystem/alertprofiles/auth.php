<?php
/*
 * $Id$
 *
 * Contains authentication functionality for the alertProfiles
 * interface.
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

	$querystring = 'SELECT Account.id AS aid, ap.value
		FROM Preference, Account
		LEFT OUTER JOIN (
				SELECT accountid, property, value
				FROM AccountProperty
				WHERE property = \'language\'
			) AS ap ON (Account.id = ap.accountid)
		WHERE
			(Account.login = $1) AND
			(Account.id = Preference.accountid)';
	$queryparams = array($username);

	if (! $query = pg_query_params($dbh->connection, $querystring, $queryparams)  ) {
		checkDBError($dbh->connection, $querystring, $queryparams, __FILE__, __LINE__);
		$error = new Error(2);
		$error->message = gettext("Error occured with database query.");
		global $RUNTIME_ERRORS;
		$RUNTIME_ERRORS[][] = $error;
	} else {
		if (pg_num_rows($query) == 1) {
			if ( $data = pg_fetch_array($query, 0, PGSQL_ASSOC) ) {
				// INNLOGGING OK!!
				$foo =  gethostbyaddr (getenv ("REMOTE_ADDR") );
				$dbh->nyLogghendelse($data["aid"], 1, gettext("Logged in from ") . $foo);

				$bgr = $dbh->listBrukersGrupper($data["aid"], 0);
				$uadmin = 1;
				foreach ($bgr AS $bg) {
					if ($bg[0] == 1) $uadmin = 100;
					//if ($bg[0] == 2) $uadmin = 0;
				}

				// MUST BE REMOVED!
				/* 				if ($data["aid"] == 1000) { */
				/* 					$uadmin = 10000; */
				/* 				}  */

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
				$error = new Error(2, 1);
				$error->message = gettext("Something bad happened when trying to fetch the user ID from the database.");
				global $RUNTIME_ERRORS;
				$RUNTIME_ERRORS[][] = $error;
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
			$error = new Error(1, 1);
			$error->message = gettext("Database inconsistency. You are correctly logged in, but your user is not correctly configured to work with NAV Alert Profiles. Contact your system administrator.");
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;

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
