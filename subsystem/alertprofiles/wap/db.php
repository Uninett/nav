<?php
/*
 * $Id$
 *
 * A library for managing the accounts and account profiles stored in
 * the navprofiles database.
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

class WDBH {

	// Må ha inn en ferdig oppkoblet databasekobling til postgres
	var $connection;

	// Konstruktor
	function WDBH($connection) {
		$this->connection = $connection;
	}

	// Henter ut informasjon om en periode..
	function sjekkwapkey($wapkey) {

		$uid = 0;
		$querystring = "
			SELECT
				Account.login as al, Account.id as aid, Accountproperty.value,
				account.name as aname, preference.activeprofile as ap
			FROM AccountProperty, Account, Preference
			WHERE
				(property = 'wapkey') AND
				(value = $1) AND
				(account.id = accountproperty.accountid) AND
				(account.id = preference.accountid)";
		$queryparams = array($wapkey);

		if (
			$query = pg_query_params($this->connection, $querystring) AND
			pg_num_rows($query) == 1
		) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$uid = $data["aid"];
			$brukernavn = $data["al"];
			$navn = $data["aname"];
			$aktivprofil = $data["ap"];
		} else {
			checkDBError($this->connection, $querystring, $queryparams, __FILE__, __LINE__);
		}

		return array($uid, $brukernavn, $navn, $aktivprofil);
	}



	// Liste alle profilene til en bruker
	function listProfiler($uid) {

		$profiler = NULL;

		$sorts = array (
				'aktiv DESC, Brukerprofil.navn',
				'Brukerprofil.navn',
				'Q.antall, aktiv DESC, Brukerprofil.navn');

		$querystring = "SELECT
				(Preference.activeProfile = Brukerprofil.id) AS aktiv,
				Brukerprofil.id, Brukerprofil.navn, Q.antall
			FROM Account, Preference, Brukerprofil
			LEFT OUTER JOIN (
					SELECT pid, count(tid) AS antall
					FROM (
						SELECT Tidsperiode.id AS tid, Brukerprofil.id AS pid
						FROM Tidsperiode, Brukerprofil
						WHERE
							(Brukerprofil.accountid = $1) AND
							(Brukerprofil.id = Tidsperiode.brukerprofilid)
					) AS Perioder
					GROUP BY Perioder.pid
				) AS Q ON (Brukerprofil.id = Q.pid)
			WHERE
				(Brukerprofil.accountid = $1) AND
				(Account.id = Brukerprofil.accountid) AND
				(Account.id = Preference.accountid)
			ORDER BY aktiv DESC, Brukerprofil.navn";

		$queryparams = array($uid);

		if ($query = pg_query_params($this->connection, $querystring, $queryparams)) {
			$tot = pg_num_rows($query); 

			for ($row = 0; $row < $tot; $row++) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$profiler[$row][0] = $data["id"];
				$profiler[$row][1] = $data["navn"];
				$profiler[$row][2] = $data["antall"];
				$profiler[$row][3] = $data["aktiv"];
			}
		} else {
			checkDBError($this->connection, $querystring, $queryparams, __FILE__, __LINE__);
		}

		return $profiler;
	}

	// opprette ny hendelse i loggen
	function nyLogghendelse($brukerid, $type, $descr) {

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Logg (accountid, type, descr, tid)
			VALUES ($1, $2, $3, current_timestamp)";
		$queryparams = array($brukerid, $type, $descr);

		if ($query = pg_query_params($this->connection, $querystring, $queryparams)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystring, $queryparams, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}


	function aktivProfil($uid, $profilid) {

		// Spxrring som legger inn i databasen
		$querystring = "UPDATE Preference
			SET activeProfile = $1
			WHERE accountid = $2";
		$queryparams = array($profilid, $uid);

		if ($query = pg_query_params($this->connection, $querystring, $queryparams)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystring, $queryparams, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}





}

?>
