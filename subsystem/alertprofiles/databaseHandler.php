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

function checkDBError($connection, $query, $parameters, $file, $line) {
	// Send query.
	pg_send_query_params($connection, $query, $parameters);
	$result = pg_get_result($connection);
	$error = pg_result_error($result);

	if ($error) {
		$e = "<p>Error in query in <strong>$file</strong>
				near line <strong>$line</strong>:</p>
				<p>$error</p>";
		trigger_error($e, E_USER_ERROR);
	}
}

class DBH {

	// Må ha inn en ferdig oppkoblet databasekobling til postgres
	var $connection;


	// Konstruktor
	function DBH($connection) {
		$this->connection = $connection;
	}


	function permissionAddress($uid, $aid) {
		$querystr = 'SELECT COUNT(*) AS count FROM alarmadresse WHERE
			accountid = $1 AND
			id = $2';
		$querypar = array($uid, $aid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$num_rows = pg_fetch_result($query, 'count');
			if ($num_rows > 0)
				return true;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}
		return false;
	}

	function permissionProfile($uid, $pid) {
		$querystr = 'SELECT COUNT(*) AS count FROM brukerprofil WHERE
			accountid = $1 AND
			id = $2';
		$querypar = array($uid, $pid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$num_rows = pg_fetch_result($query, 'count');
			if ($num_rows > 0)
				return true;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}

		return false;
	}

	function permissionEquipmentGroup($uid, $id) {
		$querystr = 'SELECT COUNT(*) AS count FROM utstyrgruppe WHERE
			accountid = $1 AND
			id = $2';
		$querypar = array($uid, $id);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$num_rows = pg_fetch_result($query, 'count');
			if ($num_rows > 0)
				return true;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}

		return false;
	}


	function permissionEquipmentFilter($uid, $id) {
		$querystr = 'SELECT COUNT(*) AS count FROM utstyrfilter WHERE
			accountid = $1 AND
			id = $2';
		$querypar = array($uid, $id);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$num_rows = pg_fetch_result($query, 'count');
			if ($num_rows > 0)
				return true;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}

		return false;
	}


	function listBrukere($sort) {

		$brukere = NULL;

		$sorts = array ('login',
				'name',
				'name',
				'name',
				'queuelength, name',
				'pa, name',
				'aa, name');

		$querystr = 'SELECT account.id, account.login, account.name,
					null as admin, null as sms, preference.queuelength,
					profiler.pa, adresser.aa
			FROM Preference, Account
			LEFT OUTER JOIN (
				SELECT
					count(brukerprofil.id) AS pa,
					brukerprofil.accountid AS uid
				FROM brukerprofil
				GROUP BY (Brukerprofil.accountid)
			) AS profiler ON (Account.id = profiler.uid)
			LEFT OUTER JOIN (
				SELECT
					count(alarmadresse.id) AS aa,
					alarmadresse.accountid AS uid
				FROM alarmadresse
				GROUP BY (alarmadresse.accountid)
			) AS adresser ON (account.id = adresser.uid)
			WHERE (preference.accountid = account.id)
			ORDER BY '.pg_escape_string($sorts[$sort]);

		if ($query = pg_query($this->connection, $querystr)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$brukere[] = array(
						$data["id"],
						$data["login"],
						$data["name"],
						$data["admin"],
						$data["sms"],
						$data["pa"],
						$data["aa"],
						$data["queuelength"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, array(), __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $brukere;
	}


	// lister alle brukerne og om de tilhører en bestemt gruppe
	function listGrBrukere($gid, $sort) {

		$brukere = NULL;

		$sorts = array ('login',
				'name',
				'name, login');

		$querystr = 'SELECT id, login, name, (medlem.groupid > 0) AS medlem
			FROM Account
			LEFT OUTER JOIN (
					SELECT groupid, accountid
					FROM AccountInGroup
					WHERE groupid = $1
				) AS Medlem ON (account.id = medlem.accountid)
			ORDER BY '.pg_escape_string($sorts[$sort]);
		$querypar = array($gid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {

		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$brukere[] = array(
						$data["id"],
						$data["login"],
						$data["name"],
						$data["medlem"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $brukere;
	}


	function listLogg($sort) {

		$logg = NULL;

		$sorts = array ('Logg.type, tid DESC',
				'Account.name, tid DESC',
				'tid DESC',
				'Logg.descr, tid DESC');

		$querystr = 'SELECT logg.type, logg.descr,
				date_part(\'epoch\', logg.tid) AS tid, account.name
			FROM account, logg
			WHERE account.id = logg.accountid
			ORDER BY '.pg_escape_string($sorts[$sort]).'
			LIMIT 100';

		if ($query = pg_query($this->connection, $querystr)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$logg[] = array(
						$data["type"],
						$data["descr"],
						$data["tid"],
						$data["name"]
					);
			}
		} else {
			checkDBError($this->connection, $querystr, array(), __FILE__, __LINE__);
		}

		return $logg;
	}


	// Liste over filtermatch som er tilgjengelige for valg
	function listFilterMatchAdm($sort) {
		$fm = NULL;

		$sorts = array (
				'matchfieldid',
				'name',
				'valueid');

		$querystr = "SELECT matchfieldid, name, valueid
			FROM MatchField
			ORDER BY ".pg_escape_string($sorts[$sort]);

		if ($query = pg_query($this->connection, $querystr)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$fm[] = array(
						$data["matchfieldid"],
						$data["name"],
						$data["valueid"]
					);
			}
		} else {
			checkDBError($this->connection, $querystr, array(), __FILE__, __LINE__);
		}

		return $fm;
	}


	function listBrukerGrupper($sort) {
		$brukere = NULL;

		$sorts = array ('name',
				'ab, name',
				'ar, name',
				'ad, name',
				'adf, name');

		$querystr = 'SELECT id, name, descr, BCount.ab, Rcount.ar,
					Dcount.ad, DFCount.adf
			FROM Accountgroup
			LEFT OUTER JOIN (
					SELECT count(accountid) AS ab, groupid
					FROM AccountInGroup
					GROUP BY groupid
				) AS BCount ON (id = BCount.groupid)
			LEFT OUTER JOIN (
					SELECT count(utstyrgruppeid) AS ar, accountgroupid
					FROM Rettighet
					GROUP BY accountgroupid
				) AS RCount ON (id = RCount.accountgroupid)
			LEFT OUTER JOIN (
					SELECT count(utstyrgruppeid) AS ad, accountgroupid
					FROM DefaultUtstyr
					GROUP BY accountgroupid
				) AS DCount ON (id = DCount.accountgroupid)
			LEFT OUTER JOIN (
					SELECT count(utstyrfilterid) AS adf, accountgroupid
					FROM DefaultFilter
					GROUP BY accountgroupid
				) AS DFCount ON (id = DFCount.accountgroupid)
			ORDER BY '.pg_escape_string($sorts[$sort]);

		if ($query = pg_query($this->connection, $querystr)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$brukere[] = array(
						$data["id"],
						$data["name"],
						$data["descr"],
						$data["ab"],
						$data["ar"],
						$data["ad"],
						$data["adf"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, array(), __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $brukere;
	}


	// list alle gruppene en Account er medlem av.
	function listBrukersGrupper($uid, $sort) {
		$bruker = NULL;

		$sorts = array ('name',
				'name',
				'name',
				'name',
				'pa, name',
				'aa, name');

		$querystr = 'SELECT id, name, descr
			FROM AccountGroup, AccountInGroup
			WHERE
				AccountInGroup.groupid = Accountgroup.id AND
				AccountInGroup.accountid = $1
			ORDER BY name';
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$grupper[] = array(
						$data["id"],
						$data["name"],
						$data["descr"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $grupper;
	}


	// Lister alle gruppene en Account er medlem av med avansert visning (tellere)
	function listBrukersGrupperAdv($sort, $uid) {

		$brukere = NULL;

		$sorts = array ('name',
				'ab, name',
				'ar, name',
				'ad, name');

		$querystr = 'SELECT id, name, descr, BCount.ab, Rcount.ar,
				Dcount.ad, (Medlem.groupid > 0) AS medl
			FROM AccountGroup
			LEFT OUTER JOIN (
					SELECT count(accountid) AS ab, groupid
					FROM AccountInGroup
					GROUP BY groupid
				) AS BCount ON (id = BCount.groupid)
			LEFT OUTER JOIN (
					SELECT count(utstyrgruppeid) AS ar, accountgroupid
					FROM Rettighet
					GROUP BY accountgroupid
				) AS RCount ON (id = RCount.accountgroupid)
			LEFT OUTER JOIN (
					SELECT count(utstyrgruppeid) AS ad, accountgroupid
					FROM DefaultUtstyr
					GROUP BY accountgroupid
				) AS DCount ON (id = DCount.accountgroupid)
			LEFT OUTER JOIN (
					SELECT accountid, groupid FROM AccountInGroup
					WHERE accountid = $1
				) AS Medlem ON (id = Medlem.groupid)
			ORDER BY '.pg_escape_string($sorts[$sort]);
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$brukere[] = array(
						$data["id"],
						$data["name"],
						$data["descr"],
						$data["ab"],
						$data["ar"],
						$data["ad"],
						$data["medl"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $brukere;
	}


	function listAdresser($uid, $sort) {
		$adr = NULL;

		$sorts = array ('type, adresse', 'adresse');

		$querystr = 'SELECT id, adresse, type
			FROM Alarmadresse
			WHERE accountid = $1
			ORDER BY '.pg_escape_string($sorts[$sort]);
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$adr[] = array(
						$data["id"],
						$data["adresse"],
						$data["type"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $adr;
	}


	// Lister opp alle adresser knyttet til tidsprofiler, og henter ut køvariabel
	function listAlleVarsleAdresser($uid, $tid, $sort) {
		$adr = NULL;

		$sorts = array (
				'min, gnavn',
				'type',
				'adresse, gnavn',
				'vent, adresse'
			       );

		$querystr = 'SELECT alarmadresse.id AS adrid, adresse, type,
					vent, utstyrgruppe.id AS gid,
					utstyrgruppe.navn AS gnavn,
					(Utstyrgruppe.accountid = $1) AS min
			FROM Utstyrgruppe, Varsle, Alarmadresse
			WHERE
				utstyrgruppe.id = varsle.utstyrgruppeid AND
				alarmadresse.id = varsle.alarmadresseid AND
				varsle.tidsperiodeid = $2
			ORDER BY '.pg_escape_string($sorts[$sort]);
		$querypar = array($uid, $tid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$adr[] = array(
						$data["adrid"],
						$data["adresse"],
						$data["type"],
						$data["vent"],
						$data["gid"],
						$data["gnavn"],
						$data["min"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $adr;
	}


	// Lister opp alle adresser knyttet til tidsprofiler for en gitt utstyrsgruppe, 
	// og henter ut køvariabel
	function listVarsleAdresser($uid, $tid, $gid, $sort) {

		$adr = NULL;

		$sorts = array ('type, adresse', 'adresse');

		$querystr = 'SELECT id, adresse, type, vent
			FROM (
					SELECT adresse, id, type
					FROM Alarmadresse
					WHERE accountid = $1
				) AS adr
			LEFT OUTER JOIN (
					SELECT vent, alarmadresseid
					FROM Varsle
					WHERE tidsperiodeid = $2
					AND utstyrgruppeid = $3
				) AS periode ON (adr.id = periode.alarmadresseid)
			ORDER BY '.pg_escape_string($sorts[$sort]);
		$querypar = array($uid, $tid, $gid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$adr[] = array(
						$data["id"],
						$data["adresse"],
						$data["type"],
						$data["vent"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $adr;
	}


	// Lister ut alle mulige filtermatch felter.
	function listMatchField($sort) {

		$matcher = NULL;

		$sorts = array (
				'name',
				'matchfieldid'
			       );

		$querystr = 'SELECT matchfieldid, name, descr, valuehelp 
			FROM MatchField
			ORDER BY '.pg_escape_string($sorts[$sort]);

		if ($query = pg_query($this->connection, $querystr)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$matcher[] = array(
						$data["matchfieldid"],
						$data["name"],
						$data["descr"],
						$data["valuehelp"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, array(), __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $matcher;
	}


	// Hent ut info om et matchfield felt.
	function matchFieldInfo($mid) {
		$mf = NULL;

		$querystr = 'SELECT name, descr, valuehelp, valueid, valuename,
					valuecategory, valuesort, listlimit, showlist
			FROM MatchField
			WHERE matchfieldid = $1';
		$querypar = array($mid);

		$query = pg_query_params($this->connection, $querystr, $querypar);

		if ($query and pg_num_rows($query) == 1) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$mf[0] = $data["name"];
			$mf[1] = $data["descr"];
			$mf[2] = $data["valuehelp"];
			$mf[3] = $data["valueid"];
			$mf[4] = $data["valuename"];
			$mf[5] = $data["valuecategory"];
			$mf[6] = $data["valuesort"];
			$mf[7] = $data["listlimit"];
			$mf[8] = $data["showlist"];
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		$querystr = 'SELECT operatorid
			FROM Operator
			WHERE matchfieldid = $1
			ORDER BY operatorid';
		$querypar = array($mid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$operators[] = $data["operatorid"];
			}

		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";

		}

		$mf[9] = $operators;

		return $mf;
	}


	// Liste alle profilene til en bruker
	function listProfiler($uid, $sort) {

		$profiler = NULL;

		$sorts = array (
				'aktiv DESC, Brukerprofil.navn',
				'Brukerprofil.navn',
				'Q.antall, aktiv DESC, Brukerprofil.navn');

		$querystr = 'SELECT (Preference.activeprofile = Brukerprofil.id) AS aktiv,
					Brukerprofil.id, Brukerprofil.navn, Q.antall
			FROM Preference, Account, Brukerprofil
			LEFT OUTER JOIN (
				SELECT pid, count(tid) AS antall
				FROM (
					SELECT Tidsperiode.id AS tid, Brukerprofil.id AS pid
					FROM Tidsperiode, Brukerprofil
					WHERE
						Brukerprofil.accountid = $1 AND
						Brukerprofil.id = Tidsperiode.brukerprofilid
				) AS Perioder
				GROUP BY Perioder.pid
			) AS Q ON (Brukerprofil.id = Q.pid)
			WHERE
				Brukerprofil.accountid = $1 AND
				Account.id = Brukerprofil.accountid AND
				Account.id = Preference.accountid
			ORDER BY '.pg_escape_string($sorts[$sort]);
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$profiler[] = array(
						$data["id"],
						$data["navn"],
						$data["antall"],
						$data["aktiv"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $profiler;
	}


	// Liste alle tidsperiodene til en profil
	function listPerioder($pid, $sort) {
		$perioder = NULL;

//		$sorts = array (
//				'time, minutt',
//				'aa, time, minutt',
//				'au, time, minutt',
//				'time, minutt'
//			);

		$querystr = 'SELECT Tidsper.id, Tidsper.helg,
				date_part(\'hour\', Tidsper.starttid) AS time,
				date_part(\'minute\', Tidsper.starttid) AS minutt,
				adresser.aa, grupper.au
			FROM (
					SELECT id, helg, starttid
					FROM Tidsperiode
					WHERE Tidsperiode.brukerprofilid = $1
				) AS Tidsper
			LEFT OUTER JOIN (
					SELECT count(aid) AS aa, tid
					FROM (
							SELECT DISTINCT Varsle.alarmadresseid AS aid,
									Varsle.tidsperiodeid AS tid
							FROM Varsle, Tidsperiode
							WHERE
								Tidsperiode.brukerprofilid = $1 AND
								Tidsperiode.id = Varsle.tidsperiodeid
						) AS Acount
					GROUP BY tid
				) AS adresser ON (Tidsper.id = adresser.tid)
			LEFT OUTER JOIN (
					SELECT count(gid) AS au, tid
				 	FROM (
							SELECT DISTINCT Varsle.utstyrgruppeid AS gid,
									Varsle.tidsperiodeid AS tid
							FROM Varsle, Tidsperiode
							WHERE
								Tidsperiode.brukerprofilid = $1 AND
								Tidsperiode.id = Varsle.tidsperiodeid
						) AS Gcount
					GROUP BY tid
				) AS grupper ON (Tidsper.id = grupper.tid)
			ORDER BY time, minutt';
		$querypar = array($pid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$perioder[] = array(
						$data["id"],
						$data["helg"],
						$data["time"],
						$data["minutt"],
						$data["aa"],
						$data["au"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $perioder;
	}

	// Denne funksjonen returnerer en liste over alle tidsperioder som
	// kræsjer, altså har samme tid.
	function listPeriodekonflikter($pid) {
		$konf = NULL;

		$querystr =  'SELECT antall, dag, starttid
			FROM (
					SELECT count(id) AS antall, dag, starttid
					FROM (
							SELECT id, \'hverdag\' AS dag, starttid
							FROM Tidsperiode
							WHERE
								brukerprofilid = $1 AND
								((helg = 2) OR (helg = 1))
							UNION
							SELECT id, \'helg\' AS dag, starttid
							FROM Tidsperiode
							WHERE
								brukerprofilid = $1 AND
								((helg = 3) OR (helg = 1))
						) AS subs
					GROUP BY dag, starttid
				) AS subss
			WHERE antall > 1';
		$querypar = array($pid);


		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$konf[] = array(
					$data["antall"],
					$data["dag"],
					$data["starttid"]
				);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $konf;
	}


	// Denne funksjonen returnerer alle utstyrgrupper som en Account har
	// tilgang til, enten man har laget den selv eller den er arvet gjennom
	// DefaultUtstyr.
	function listUtstyr($uid, $sort) {
		$utst = NULL;

		$sorts = array (
				'navn,id',
				'min,navn',
				'ap,navn',
				'af,navn');

		$querystr = 'SELECT *
			FROM (
				SELECT DISTINCT ON (id) id, navn, descr, min, Pcount.ap, FCount.af
				FROM (
					SELECT id, navn, descr, true AS min
					FROM Utstyrgruppe
					WHERE accountid = $1
					UNION
					SELECT
						Utstyrgruppe.id, Utstyrgruppe.navn,
						Utstyrgruppe.descr,
						(Utstyrgruppe.accountid = $1) AS min
					FROM
						Utstyrgruppe, DefaultUtstyr,
						AccountGroup, AccountInGroup
					WHERE
						AccountInGroup.accountid = $1 AND
						AccountInGroup.groupid = AccountGroup.id AND
						AccountGroup.id = DefaultUtstyr.accountgroupid AND
						DefaultUtstyr.utstyrgruppeid = Utstyrgruppe.id
				) AS Tilgjengelig
				LEFT OUTER JOIN (
					SELECT count(tidsperiodeid) AS ap, utstyrgruppeid
					FROM (
						SELECT DISTINCT ON (utstyrgruppeid,tidsperiodeid)
							tidsperiodeid, utstyrgruppeid
						FROM (
							SELECT Varsle.utstyrgruppeid, Varsle.tidsperiodeid
							FROM Varsle, Tidsperiode, Brukerprofil
							WHERE
								Varsle.tidsperiodeid = Tidsperiode.id AND
								Tidsperiode.brukerprofilid = Brukerprofil.id AND
								Brukerprofil.accountid = $1
						) AS MinVarsle, Utstyrgruppe
						WHERE (Utstyrgruppe.id = MinVarsle.utstyrgruppeid)
					) AS X
					GROUP BY utstyrgruppeid
				) AS PCount ON (id = PCount.utstyrgruppeid)
				LEFT OUTER JOIN (
					SELECT count(utstyrfilterid) AS af, utstyrgruppeid
					FROM (
						SELECT utstyrfilterid, utstyrgruppeid
						FROM GruppeTilFilter, Utstyrgruppe
						WHERE (
								Utstyrgruppe.accountid = $1 OR
								Utstyrgruppe.accountid is null
							) AND
							Utstyrgruppe.id = GruppeTilFilter.utstyrgruppeid
					) AS Y
					GROUP BY utstyrgruppeid
				) AS FCount ON (id = FCount.utstyrgruppeid)
			) jalla
			ORDER BY '.pg_escape_string($sorts[$sort]);
		$querypar = array($uid);

		//print "<pre>" . $querystr . "</pre>";

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$utst[] = array(
						$data["id"],
						$data["navn"],
						$data["ap"],
						$data["af"],
						$data["min"],
						$data["descr"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $utst;

	}


	// Denne funksjonen returnerer alle utstyrgrupper som en Account har
	// rettighet til,
	function listUtstyrRettighet($uid, $sort) {
		$utst = NULL;

//		$sorts = array (
//				'time, minutt',
//				'aa, time, minutt',
//				'au, time, minutt',
//				'time, minutt'
//			);

		$querystr = 'SELECT DISTINCT ON (id) utstyrgruppe.id, navn, descr
			FROM accountingroup, Rettighet, Utstyrgruppe
			WHERE
				AccountInGroup.accountid = $1 AND
				AccountInGroup.groupid = Rettighet.accountgroupid AND
				Rettighet.utstyrgruppeid = Utstyrgruppe.id';
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$utst[] = array(
						$data["id"],
						$data["navn"],
						$data["descr"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $utst;
	}


	// Denne funksjonen returnerer alle utstyrgrupper som administrator har
	// rettigheter til
	function listUtstyrAdm($sort) {
		$utst = NULL;

		$sorts = array(
				'navn,id',
				'ap,navn',
				'af,navn'
			);

		$querystr = 'SELECT * FROM (
			SELECT DISTINCT ON (id) id, navn, descr, min, Pcount.ap, FCount.af
			FROM (
				SELECT id, navn, descr, true AS min
				FROM Utstyrgruppe
				WHERE (accountid is null)
			) AS Tilgjengelig
			LEFT OUTER JOIN (
				SELECT count(tidsperiodeid) AS ap, utstyrgruppeid
				FROM (
					SELECT DISTINCT ON (utstyrgruppeid,tidsperiodeid)
						tidsperiodeid, utstyrgruppeid
					FROM Varsle, Utstyrgruppe
					WHERE
						(Utstyrgruppe.accountid is null) AND
						(Utstyrgruppe.id = Varsle.utstyrgruppeid)
				) AS X
				GROUP BY utstyrgruppeid
			) AS PCount ON (id = PCount.utstyrgruppeid)
			LEFT OUTER JOIN (
				SELECT count(utstyrfilterid) AS af, utstyrgruppeid
				FROM (
					SELECT utstyrfilterid, utstyrgruppeid
					FROM GruppeTilFilter, Utstyrgruppe
					WHERE (Utstyrgruppe.accountid is null)
					AND (Utstyrgruppe.id = GruppeTilFilter.utstyrgruppeid)
				) AS Y
				GROUP BY utstyrgruppeid
			) AS FCount ON (id = FCount.utstyrgruppeid)) jalla
			ORDER BY '.pg_escape_string($sorts[$sort]);

		if ($query = pg_query($this->connection, $querystr)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$utst[] = array(
						$data["id"],
						$data["navn"],
						$data["ap"],
						$data["af"],
						$data["min"],
						$data["descr"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, array(), __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $utst;
	}


	// Denne funksjonen returnerer alle utstyrgrupper knyttet til en
	// bestemt periode i en profil
	function listUtstyrPeriode($uid, $pid, $sort) {
		$uts = NULL;

//		$sorts = array(
//				'time, minutt',
//				'aa, time, minutt',
//				'au, time, minutt',
//				'time, minutt'
//			);

		$querystr = 'SELECT DISTINCT ON (id) id, navn, min, Pcount.ap, FCount.af
			FROM (
				SELECT id, navn, descr, true AS min
				FROM Utstyrgruppe
				WHERE (accountid = $1)
				UNION
				SELECT
					Utstyrgruppe.id, Utstyrgruppe.navn, Utstyrgruppe.descr,
					(Utstyrgruppe.accountid = $1) AS min
				FROM Utstyrgruppe, DefaultUtstyr, AccountGroup, AccountInGroup
				WHERE
					(AccountInGroup.accountid = $1) AND
					(AccountInGroup.groupid = AccountGroup.id) AND
					(AccountGroup.id = DefaultUtstyr.accountgroupid) AND
					(DefaultUtstyr.utstyrgruppeid = Utstyrgruppe.id)
			) AS Tilgjengelig
			LEFT OUTER JOIN (
				SELECT count(tidsperiodeid) AS ap, utstyrgruppeid
				FROM (
					SELECT DISTINCT tidsperiodeid, utstyrgruppeid
					FROM Varsle, Tidsperiode, Brukerprofil
					WHERE
						(Varsle.tidsperiodeid = Tidsperiode.id) AND
						(Tidsperiode.brukerprofilid = Brukerprofil.id) AND
						(Brukerprofil.accountid = $1)
				) AS X
				GROUP BY utstyrgruppeid
			) AS PCount ON (id = PCount.utstyrgruppeid)
			LEFT OUTER JOIN (
				SELECT count(utstyrfilterid) AS af, utstyrgruppeid
				FROM (
					SELECT utstyrfilterid, utstyrgruppeid
					FROM GruppeTilFilter, Utstyrgruppe
					WHERE
						(Utstyrgruppe.accountid = $1) AND
						(Utstyrgruppe.id = GruppeTilFilter.utstyrgruppeid)
				) AS Y
				GROUP BY utstyrgruppeid
			) AS FCount ON (id = FCount.utstyrgruppeid)';
		$querypar = array($uid);


		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$utst[] = array(
						$data["id"],
						$data["navn"],
						$data["ap"],
						$data["af"],
						$data["min"]
						//$data["ermed"]
				);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $utst;
	}


	// Denne funksjonen returenrer alle felles filtere samt default utrstyr
	// knyttet til brukergruppene.
	function listGrFilter($uid, $gid, $sort) {
		$utst = NULL;

//		$sorts = array(
//				'time, minutt',
//				'aa, time, minutt',
//				'au, time, minutt',
//				'time, minutt'
//			);

		$querystr = 'SELECT id, navn, (def.utstyrfilterid > 0 ) AS default
			FROM (
					SELECT id, navn
					FROM Utstyrfilter
					WHERE accountid is null
				) AS filter
			LEFT OUTER JOIN (
					SELECT utstyrfilterid
					FROM DefaultFilter
					WHERE accountgroupid = $1
				) AS def ON (filter.id = def.utstyrfilterid)
			ORDER BY navn';
		$querypar = array($gid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$utst[] = array(
						$data["id"],
						$data["navn"],
						$data["default"]
					);
			} 
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $utst;
	}


	// Denne funksjonen returenrer alle utstyrsgruppene samt rettigheter og
	// default utrstyr knyttet til brukergruppene.
	function listGrUtstyr($uid, $gid, $sort) {
		$uts = NULL;

//		$sorts = array(
//				'time, minutt',
//				'aa, time, minutt',
//				'au, time, minutt',
//				'time, minutt'
//			);

		$querystr = 'SELECT id, navn, descr,
				(rett.utstyrgruppeid > 0 ) AS rettighet,
				(def.utstyrgruppeid > 0 ) AS default
			FROM (
					SELECT id, navn, descr
					FROM Utstyrgruppe
					WHERE accountid is null
				) AS grupper
			LEFT OUTER JOIN (
					SELECT utstyrgruppeid
					FROM Rettighet
					WHERE accountgroupid = $1
				) AS rett ON (grupper.id = rett.utstyrgruppeid)
			LEFT OUTER JOIN (
					SELECT utstyrgruppeid
					FROM DefaultUtstyr
					WHERE accountgroupid = $1
				) AS def ON (grupper.id = def.utstyrgruppeid)
			ORDER BY navn';
		$querypar = array($gid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$utst[] = array(
						$data["id"],
						$data["navn"],
						$data["descr"],
						$data["rettighet"],
						$data["default"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $utst;
	}


	// Hent ut info om en brukerid
	function brukerInfo($uid) {
		$br = NULL;

		$querystr = 'SELECT login, name, null as admin, null as sms, activeprofile
			FROM Account, Preference
			WHERE
				id = $1 AND
				account.id = preference.accountid';
		$querypar = array($uid);

		$query = pg_query_params($this->connection, $querystr, $querypar);

		if ($query and pg_num_rows($query) == 1) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$br[0] = $data["login"];
			$br[1] = $data["name"];
			$br[2] = $data["admin"];
			$br[3] = $data["sms"];
			$br[4] = $data["activeprofile"];
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $br;
	}

	// Hent ut info om en gruppeid
	function brukergruppeInfo($gid) {
		$gr = NULL;

		$querystr = 'SELECT name, descr
			FROM AccountGroup
			WHERE id = $1';
		$querypar = array($gid);

		$query = pg_query_params($this->connection, $querystr, $querypar);
		if ($query and pg_num_rows($query) == 1) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$gr[0] = $data["name"];
			$gr[1] = $data["descr"];
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $gr;
	}

	// Hent ut info om en utstyrsgruppeid
	function utstyrgruppeInfo($gid) {
		$gr = NULL;

		$querystr = 'SELECT navn, descr
			FROM Utstyrgruppe
			WHERE id = $1';
		$querypar = array($gid);

		$query = pg_query_params($this->connection, $querystr, $querypar);

		if ($query and pg_num_rows($query) == 1) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$gr[0] = $data["navn"];
			$gr[1] = $data["descr"];
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $gr;
	}

	// Hent ut info om en utstyrsfilterid
	function utstyrfilterInfo($fid) {
		$gr = NULL;

		$querystr = 'SELECT navn
			FROM Utstyrfilter
			WHERE id = $1';
		$querypar = array($fid);

		$query = pg_query_params($this->connection, $querystr, $querypar);

		if ($query and pg_num_rows($query) == 1) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$gr[0] = $data["navn"];
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $gr;
	}


	// Hent ut info om en utstyrsgruppeid
	function utstyrgruppeInfoAdv($gid, $uid) {
		$gr = NULL;

		$querystr = 'SELECT navn, descr, (accountid = $1) AS min
			FROM Utstyrgruppe
			WHERE id = $2';
		$querypar = array($uid, $gid);

		$query = pg_query_params($this->connection, $querystr, $querypar);

		if ($query and pg_num_rows($query) == 1) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$gr[0] = $data["navn"];
			$gr[1] = $data["descr"];
			$gr[2] = $data["min"];
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $gr;
	}


	// Hent ut info om en brukerprofil
	function brukerprofilInfo($pid) {
		$p = NULL;

		$querystr = 'SELECT
				navn, ukedag, extract(HOUR FROM uketid) AS uketidh,
				extract(MINUTE FROM uketid) AS uketidm,
				extract(HOUR FROM tid) AS tidh,
				extract(MINUTE FROM tid) AS tidm
			FROM Brukerprofil
			WHERE id = $1';
		$querypar = array($pid);

		$query = pg_query_params($this->connection, $querystr, $querypar);

		if ($query and pg_num_rows($query) == 1) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$p[0] = $data["navn"];
			$p[1] = $data["ukedag"];
			$p[2] = $data["uketidh"];
			$p[3] = $data["uketidm"];
			$p[4] = $data["tidh"];
			$p[5] = $data["tidm"];
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $p;
	}


	// Denne funksjonen returnerer alle filtrene som en Account har tilgang
	// til, enten man har laget den selv eller den er arvet gjennom
	// DefaultFilter.
	function listFiltre($uid, $sort) {
		$utst = NULL;

		$sorts = array (
				'navn,id',
				'min,navn',
				'am,navn',
				'ag,navn'
			);

		$querystr = 'SELECT * FROM (
			SELECT DISTINCT ON (id) id, navn, min, am, ag
			FROM (
				SELECT id, navn, true AS min
				FROM Utstyrfilter
				WHERE (accountid = $1)
				UNION
				SELECT
					Utstyrfilter.id, Utstyrfilter.navn,
					(Utstyrfilter.accountid = $1) AS min
				FROM Utstyrfilter, DefaultFilter, AccountGroup, AccountInGroup
				WHERE
					(AccountInGroup.accountid = $1) AND
					(AccountInGroup.groupid = AccountGroup.id) AND
					(AccountGroup.id = DefaultFilter.accountgroupid) AND
					(DefaultFilter.utstyrfilterid = Utstyrfilter.id)
			) AS MineFilter
			LEFT OUTER JOIN (
				SELECT count(mid) AS am,  uid
				FROM (
					SELECT FilterMatch.id AS mid, Utstyrfilter.id AS uid
					FROM Utstyrfilter, FilterMatch
					WHERE (Utstyrfilter.id = FilterMatch.utstyrfilterid)
				) AS Mcount
				GROUP BY uid
			) AS match ON (MineFilter.id = match.uid)
			LEFT OUTER JOIN (
				SELECT count(gid) AS ag, uid
				FROM (
					SELECT
						GruppeTilFilter.utstyrgruppeid AS gid,
						Utstyrfilter.id AS uid
					FROM Utstyrfilter, GruppeTilFilter
					WHERE (Utstyrfilter.id = GruppeTilFilter.utstyrfilterid)
				) AS Gcount
				GROUP BY uid
			) AS grupper ON (MineFilter.id = grupper.uid)
		) AS jalla ORDER BY '.pg_escape_string($sorts[$sort]);
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$utst[] = array(
						$data["id"],
						$data["navn"],
						$data["am"],
						$data["ag"],
						$data["min"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $utst;
	}


	// Denne funksjonen returnerer alle filtrene som hører til en bestemt
	// Account.
	function listFiltre_depr($uid, $sort) {
		$filtre = NULL;

		$sorts = array(
				'time, minutt',
				'aa, time, minutt',
				'au, time, minutt',
				'time, minutt'
			);

		$querystr = "SELECT MineFilter.id, MineFilter.navn, match.am, grupper.ag
			FROM (
				SELECT id, navn
				FROM Utstyrfilter
				WHERE (Utstyrfilter.accountid = $1)
			) AS MineFilter
			LEFT OUTER JOIN (
				SELECT count(mid) AS am,  uid
				FROM (
					SELECT FilterMatch.id AS mid, Utstyrfilter.id AS uid
					FROM Utstyrfilter, FilterMatch
					WHERE
						(Utstyrfilter.accountid = $1) AND
						(Utstyrfilter.id = FilterMatch.utstyrfilterid)
				) AS Mcount
				GROUP BY uid
			) AS match ON (MineFilter.id = match.uid)
			LEFT OUTER JOIN (
				SELECT count(gid) AS ag, uid
				FROM (
					SELECT
						GruppeTilFilter.utstyrgruppeid AS gid,
						Utstyrfilter.id AS uid
					FROM Utstyrfilter, GruppeTilFilter
					WHERE
						(Utstyrfilter.accountid = $1) AND
						(Utstyrfilter.id = GruppeTilFilter.utstyrfilterid)
				) AS Gcount
				GROUP BY uid
			) AS grupper ON (MineFilter.id = grupper.uid)
			ORDER BY navn";
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$filtre[] = array(
						$data["id"],
						$data["navn"],
						$data["am"],
						$data["ag"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $filtre;
	}

	// Denne funksjonen returnerer alle filtrene som hører til
	// administratorene.
	function listFiltreAdm($sort) {
		$filtre = NULL;

		$sorts = array(
				'time, minutt',
				'aa, time, minutt',
				'au, time, minutt',
				'time, minutt'
			);

		$querystr = 'SELECT MineFilter.id, MineFilter.navn, match.am, grupper.ag
			FROM (
				SELECT id, navn
				FROM Utstyrfilter
				WHERE (Utstyrfilter.accountid is null)
			) AS MineFilter
			LEFT OUTER JOIN (
				SELECT count(mid) AS am,  uid
				FROM (
					SELECT FilterMatch.id AS mid, Utstyrfilter.id AS uid
					FROM Utstyrfilter, FilterMatch
					WHERE
						(Utstyrfilter.accountid is null) AND
					  	(Utstyrfilter.id = FilterMatch.utstyrfilterid)
				) AS Mcount
				GROUP BY uid
			) AS match ON (MineFilter.id = match.uid)
			LEFT OUTER JOIN (
				SELECT count(gid) AS ag, uid
				FROM (
					SELECT
					 	GruppeTilFilter.utstyrgruppeid AS gid,
						Utstyrfilter.id AS uid
					FROM Utstyrfilter, GruppeTilFilter
					WHERE
						(Utstyrfilter.accountid is null) AND
						(Utstyrfilter.id = GruppeTilFilter.utstyrfilterid)
				) AS Gcount
				GROUP BY uid
			) AS grupper
			ON (MineFilter.id = grupper.uid)
			ORDER BY navn';

		if ($query = pg_query($this->connection, $querystr)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$filtre[] = array(
						$data["id"],
						$data["navn"],
						$data["am"],
						$data["ag"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, array(), __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $filtre;
	}


	// Denne funksjonen returnerer alle filtrene som hører til en bestemt
	// Account uten unødig krimskrams. untatt de som allerede er valgt.
	function listFiltreFast($uid, $gid, $sort) {
		$filtre = NULL;

		$querystr = 'SELECT * FROM (
				SELECT DISTINCT ON (id) id, navn, min
				FROM (
					SELECT id, navn, true AS min
					FROM Utstyrfilter
					WHERE (accountid = $1)
					UNION
					SELECT
						Utstyrfilter.id, Utstyrfilter.navn,
						(Utstyrfilter.accountid = $1) AS min
					FROM
						Utstyrfilter, DefaultFilter,
						AccountGroup, AccountInGroup
					WHERE
						(AccountInGroup.accountid = $1) AND
						(AccountInGroup.groupid = AccountGroup.id) AND
						(AccountGroup.id = DefaultFilter.accountgroupid) AND
						(DefaultFilter.utstyrfilterid = Utstyrfilter.id)
				) AS MineFilter
			) AS jalla ORDER BY min,navn';
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				if ($data["min"] == 't' )
					$name = $data["navn"];
				else
					$name = '(Public) ' . $data["navn"];

				$filtre[] = array(
						$data['id'],
						$name
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $filtre;
	}


	// Denne funksjonen returnerer alle filtrene som hører til admin
	// Account uten unødig krimskrams. untatt de som allerede er valgt.
	function listFiltreFastAdm($gid, $sort) {
		$filtre = NULL;

		$querystr = 'SELECT Utstyrfilter.id, Utstyrfilter.navn
			FROM Utstyrfilter
			WHERE accountid is null
			EXCEPT
			SELECT Utstyrfilter.id, Utstyrfilter.navn
			FROM Utstyrfilter, GruppeTilFilter
			WHERE
				(Utstyrfilter.id = GruppeTilFilter.utstyrfilterid) AND
				(GruppeTilFilter.utstyrgruppeid = $1)
			ORDER BY navn';
		$querypar = array($gid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$filtre[] = array(
						$data["id"],
						$data["navn"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $filtre;
	}


	// Denne funksjonen returnerer alle filtrene som hører til en bestemt
	// utstyrsgruppe.
	function listFiltreGruppe($gid, $sort) {
		$filtre = NULL;

//		$sorts = array(
//				'time, minutt',
//				'aa, time, minutt',
//				'au, time, minutt',
//				'time, minutt'
//			);

		$querystr = 'SELECT Utstyrfilter.id, Utstyrfilter.navn,
					GruppeTilFilter.prioritet, GruppeTilFilter.inkluder,
					GruppeTilFilter.positiv
			FROM Utstyrfilter, GruppeTilFilter
			WHERE
				(Utstyrfilter.id = GruppeTilFilter.utstyrfilterid) AND
				(GruppeTilFilter.utstyrgruppeid = $1)
			ORDER BY prioritet';
		$querypar = array($gid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$filtre[] = array(
						$data["id"],
						$data["navn"],
						$data["prioritet"],
						$data["inkluder"],
						$data["positiv"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $filtre;
	}


	// Denne funksjonen returnerer alle filtermatchene for et filter.
	function listMatch($fid, $sort) {
		$match = NULL;

		$sorts = array (
				'matchfelt',
				'matchtype',
				'verdi'
			);

		$querystr = 'SELECT id, MatchField.name, matchtype, verdi
			FROM FilterMatch, MatchField
			WHERE
				utstyrfilterid = $1 AND
				FilterMatch.matchfelt = MatchField.matchfieldid
			ORDER BY '.pg_escape_string($sorts[$sort]);
		$querypar = array($fid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$match[] = array(
						$data["id"],
						$data["name"],
						$data["matchtype"],
						$data["verdi"]
					);
			}
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $match;
	}


	// Henter ut informasjon om en periode..
	function periodeInfo($tid) {

		$querystr = 'SELECT helg,
					date_part(\'hour\', Tidsperiode.starttid) AS time ,
					date_part(\'minute\', Tidsperiode.starttid) AS minutt
			FROM Tidsperiode WHERE (id = $1)';
		$querypar = array($tid);

		if (
			$query = pg_query_params($this->connection, $querystr, $querypar) and
			pg_num_rows($query) == 1
		) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$perioder[0] = $data["helg"];
			$perioder[1] = $data["time"];
			$perioder[2] = $data["minutt"];
		}  else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasesp&oslash;rring. Fant ikke periode.";
		}
		return $perioder;
	}


	// Henter ut informasjon om en periode..
	function hentwapkey($uid) {

		$querystr = 'SELECT value
			FROM AccountProperty
			WHERE
				(accountid = $1) AND
				(property = \'wapkey\')';
		$querypar = array($uid);

		if (
			$query = pg_query_params($this->connection, $querystr, $querypar) and
			pg_num_rows($query) > 0
		) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$key[0] = $data["value"];
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			$key = null;
		}
		return $key;
	}

	function settwapkey($uid, $key) {
		$oldkey = $this->hentwapkey($uid);

		if ($oldkey == null) {
			$querystr = 'INSERT INTO AccountProperty (accountid, property, value)
				VALUES ($1, \'wapkey\', $2)';
			$querypar = array($uid, $key);
			$query = pg_query_params($this->connection, $querystr, $querypar);
			if (!$query)
				checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		} else {
			$querystr = 'UPDATE AccountProperty
				SET value = $1
				WHERE
					accountid = $2 AND
					property = \'wapkey\'';
			$querypar = array($key, $uid);
			$query = pg_query_params($this->connection, $querystr, $querypar);
			if (!$query)
				checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}

	}


	function slettwapkey($uid) {
		// Spxrring som legger inn i databasen
		$querystr = 'DELETE FROM AccountProperty
			WHERE
				accountid = $1 AND
				property = \'wapkey\'';
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}
	}


	function slettMatchField($mfid) {
		// Spxrring som legger inn i databasen
		$querystr = 'DELETE FROM MatchField
			WHERE (matchfieldid = $1)';
		$querypar = array($mfid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}
	}


	// Endre navn på profil
	function endreProfil($pid, $navn, $ukedag, $uketidh, $uketidm, $tidh, $tidm) {
		$querystr = 'UPDATE Brukerprofil
			SET navn = $1
			WHERE id = $2';
		$querypar = array($navn, $pid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = 'UPDATE Brukerprofil
			SET ukedag = $1
			WHERE id = $2';
		$querypar = array($ukedag, $pid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = 'UPDATE Brukerprofil
			SET uketid = $1
			WHERE id = $2';
		$querypar = array($uketidh.':'.$uketidm, $pid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = 'UPDATE Brukerprofil
			SET tid = $1
			WHERE id = $2';
		$querypar = array($tidh.':'.$tidm, $pid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
	}

	// Endre detaljer om en filter
	function endreFilter($fid, $navn) {
		$querystr = 'UPDATE Utstyrfilter
			SET navn = $1
			WHERE id = $2';
		$querypar = array($navn, $fid);

		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

	}

	// Endre detaljer om en tidsperiode
	function endrePeriodeinfo($tid, $helg, $time, $minutt) {
		$querystr = 'UPDATE Tidsperiode
			SET helg = $1
			WHERE id = $2';
		$querypar = array($helg, $tid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = 'UPDATE Tidsperiode
			SET starttid = $1
			WHERE id = $2';
		$querypar = array($time.':'.$minutt, $tid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
	}

	// Endre detaljer om et utstyrgruppe
	function endreUtstyrgruppe($gid, $navn, $descr) {
		$querystr = 'UPDATE Utstyrgruppe
			SET navn = $1
			WHERE id = $2';
		$querypar = array($navn, $gid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = 'UPDATE Utstyrgruppe
			SET descr = $1
			WHERE id = $2';
		$querypar = array($descr, $gid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
	}


	// Endre detaljer om en brukergruppe
	function endreBrukergruppe($gid, $navn, $descr) {
		$querystr = "UPDATE AccountGroup
			SET name = $1
			WHERE id = $2";
		$querypar = array($navn, $gid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = "UPDATE AccountGroup
			SET descr = $1
			WHERE id = $2";
		$querypar = array($descr, $gid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
	}

	// Endre detaljer om en adresse
	function endreAdresse($aid, $type, $adr) {
		$querystr = "UPDATE Alarmadresse
			SET type = $1
			WHERE id = $2";
		$querypar = array($type, $aid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = "UPDATE Alarmadresse
			SET adresse = $1
			WHERE id = $2";
		$querypar = array($adr, $aid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
	}


	// Endre brukerinfo
	function endreBruker($uid, $brukernavn, $navn, $passord, $admin, $sms, $kolengde) {
		$querystr = "UPDATE Account
			SET login = $1
			WHERE id = $2";
		$querypar = array($brukernavn, $uid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = "UPDATE Account
			SET name = $1
			WHERE id = $2";
		$querypar = array($navn, $uid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = "UPDATE Account
			SET password = $1
			WHERE id = $2";
		$querypar = array($passord, $uid);

		if ($passord != undef && strlen($passord) > 0) {
			$query = pg_query_params($this->connection, $querystr, $querypar);
			if (!$query)
				checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}

		$querystr = "UPDATE Preference
			SET queuelength = $1
			WHERE accountid = $2";
		$querypar = array($kolengde, $uid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

	}

	// Endre passord
	function endrepassord($brukernavn, $passwd) {
		$querystr = "UPDATE Account
			SET password = $1
			WHERE login = $2";
		$querypar = array($passwd, $brukernavn);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
	}


	// Endre språk
	function setlang($brukerid, $lang) {
		$querystr = "DELETE FROM AccountProperty
			WHERE
				property = 'language' AND
				accountid = $1";
		$querypar = array($brukerid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = "INSERT INTO AccountProperty (accountid, property, value)
			VALUES ($1, 'language', $2)";
		$querypar = array($brukerid, $lang);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
	}


	// Legge til eller endre en varslingsadresse for en periode
	function endreVarsleadresse($tid, $adresseid, $utstyrgruppeid, $type) {

		$querystr = "DELETE FROM Varsle
			WHERE
				tidsperiodeid = $1 AND
				alarmadresseid = $2 AND
				utstyrgruppeid = $3";
		$querypar = array($tid, $adresseid, $utstyrgruppeid);

		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		if ($type < 4) {
			$querystr = "INSERT INTO Varsle
				(tidsperiodeid, alarmadresseid, utstyrgruppeid, vent)
				VALUES ($1, $2, $3, $4)";
			$querypar = array($tid, $adresseid, $utstyrgruppeid, $type);
			$query = pg_query_params($this->connection, $querystr, $querypar);
			if (!$query)
				checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			}
		}


		// Legge til eller endre en brukertilgruppe
	function endreBrukerTilGruppe($uid, $gid, $type) {

		$querystr = "DELETE FROM AccountInGroup
			WHERE
				accountid = $1 AND
				groupid = $2";;
		$querypar = array($uid, $gid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		if ($type) {
			$querystr = "INSERT INTO AccountInGroup (accountid, groupid)
				VALUES ($1, $2)";
			$querypar = array($uid, $gid);
			$query = pg_query_params($this->connection, $querystr, $querypar);
			if (!$query)
				checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}
	}

		// Legge til eller endre en rettighet
	function endreRettighet($gid, $ugid, $type) {

		$querystr = "DELETE FROM Rettighet
			WHERE
				accountgroupid = $1 AND
				utstyrgruppeid = $2";
		$querypar = array($gid, $ugid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		if ($type) {
			$querystr = "INSERT INTO Rettighet (accountgroupid, utstyrgruppeid)
				VALUES ($1, $2)";
			$querypar = array($gid, $ugid);
			$query = pg_query_params($this->connection, $querystr, $querypar);
			if (!$query)
				checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}
	}

	// Legge til eller endre en defaultustyr
	function endreDefault($gid, $ugid, $type) {

		$querystr = "DELETE FROM DefaultUtstyr WHERE
			accountgroupid = $1 AND
			utstyrgruppeid = $2";
		$quyerypar = array($gid, $ugid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		if ($type) {
			$querystr = "INSERT INTO DefaultUtstyr (accountgroupid, utstyrgruppeid)
				VALUES ($1, $2)";
			$querypar = array($gid, $ugid);
			$query = pg_query_params($this->connection, $querystr, $querypar);
			if (!$query)
				checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}

	}

	// Legge til eller endre en default filter
	function endreDefaultFilter($gid, $fid, $type) {

		$querystr = "DELETE FROM DefaultFilter WHERE
			accountgroupid = $1 AND
			utstyrfilterid = $2";;
		$querypar = array($gid, $fid);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		if ($type) {
			$querystr = "INSERT INTO DefaultFilter (accountgroupid, utstyrfilterid)
				VALUES ($1, $2)";
			$querypar = array($gid, $fid);
			$query = pg_query_params($this->connection, $querystr, $querypar);
			if (!$query)
				checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}

	}





	// Bytte rekkefølgen på to prioriteter for filtre i en utstyrsgruppe
	function swapFilter($gid, $a, $b, $ap, $bp) {

		$querystr = "UPDATE GruppeTilFilter SET
			prioritet = $1
			WHERE
				(utstyrgruppeid = $2) AND
				(utstyrfilterid = $3";
		$querypar = array($bp, $gid, $a);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

		$querystr = "UPDATE GruppeTilFilter SET
			prioritet = $1
			WHERE
				(utstyrgruppeid = $2) AND
				(utstyrfilterid = $3)";
		$querypar = array($ap, $gid, $b);
		$query = pg_query_params($this->connection, $querystr, $querypar);
		if (!$query)
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
	}


	// opprette ny bruker
	function nyBruker($navn, $brukernavn, $passord, $admin, $sms, $kolengde, $error) {

		// Spxrring som legger inn i databasen
		$querystr = "INSERT INTO Account (name, login, password)
			VALUES ($1, $2, $3)";
		$querypar = array($navn, $brukernavn, $passord);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$lastid_querystr = 'SELECT currval(\'account_id_seq\') AS lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');

			// Spxrring som legger inn i databasen
			$querystr = "INSERT INTO Preference (accountid, queuelength)
				VALUES ($1, $2) ";
			$querypar = array($lastid, "$kolengde days");

			$query = pg_query_params($this->connection, $querystr, $querypar);
			if (!$query)
				checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);

			return $lastid;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			$error = new Error(2);
			$error->SetMessage("Brukernavn allerede i bruk. Forsøk
				på nytt med et annet brukernavn.");
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			return 0;
		}
	}


	// opprette ny brukergruppe
	function nyBrukerGruppe($navn, $descr) {

		// Spxrring som legger inn i databasen
		$querystr = "INSERT INTO AccountGroup (name, descr)
			VALUES ($1, $2)";
		$querypar = array($navn, $descr);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$lastid_querystr = 'SELECT currval(\'accountgroup_id_seq\') AS lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');
			return $lastid;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			$error = new Error(2);
			$error->SetMessage("feil med databaseinnlegging av brukergruppe.");
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			return 0;
		}

	}


	// opprette ny tidsperiode
	function nyTidsperiode($helg, $tid, $profilid) {
		// Spxrring som legger inn i databasen
		$querystr = 'INSERT INTO tidsperiode (helg, starttid, brukerprofilid)
			VALUES ($1, $2, $3)';
		$querypar = array($helg, $tid, $profilid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {

			$lastid_querystring = 'SELECT
				currval(\'tidsperiode_id_seq\') as lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystring);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');
			return $lastid;

		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			return 0;
		}

	}

	// opprette ny adresse
	function nyAdresse($adresse, $adressetype, $brukerid) {

		// Spørring som legger inn i databasen
		$querystr = 'INSERT INTO alarmadresse (accountid, adresse, type)
			VALUES ($1, $2, $3)';
		$querypar = array($brukerid, $adresse, $adressetype);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$lastid_query = pg_query(
					$this->connection,
					'SELECT currval(\'alarmadresse_id_seq\') AS lastid'
				);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');
			return $lastid;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}



	// opprette ny hendelse i loggen
	function nyLogghendelse($brukerid, $type, $descr) {

		// Spxrring som legger inn i databasen
		$querystr = "INSERT INTO Logg (accountid, type, descr, tid)
			VALUES ($1, $2, $3, current_timestamp)";
		$querypar = array($brukerid, $type, $descr);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			return 0;
		}

	}


	// opprette ny profil
	function nyProfil($navn, $brukerid, $ukedag, $uketidh, $uketidm, $tidh, $tidm) {

		// Spørring som legger inn i databasen
		$querystr = 'INSERT INTO brukerprofil (accountid, navn, ukedag, uketid, tid)
			VALUES ($1, $2, $3, $4, $5)';
		$querypar = array(
				$brukerid,
				$navn,
				$ukedag,
				$uketidh.":".$uketidm,
				$tidh.":".$tidm
			);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			// Henter ut object id`n til raden.
			$lastid_querystr = 'SELECT currval(\'brukerprofil_id_seq\') AS lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$last_id = pg_fetch_result($lastid_query, 'lastid');
			return $last_id;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			return 0;
		}

	}



	// opprette nytt filter
	function nyttFilter($navn, $brukerid) {

		// Spxrring som legger inn i databasen
		$querystr = "INSERT INTO Utstyrfilter (accountid, navn)
			VALUES ($1, $2)";
		$querypar = array($brukerid, $navn);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$lastid_querystr = 'SELECT currval(\'utstyrfilter_id_seq\') AS lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');
			return $lastid;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			return 0;
		}
	}


	// opprette nytt adm- filter
	function nyttFilterAdm($navn) {

		// Spxrring som legger inn i databasen
		$querystr = "INSERT INTO Utstyrfilter (accountid, navn)
			VALUES (null, $1)";
		$querypar = array($navn);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			// Henter ut object id`n til raden.
			$lastid_querystr = 'SELECT currval(\'utstyrfilter_id_seq\') AS lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');
			return $lastid;
			// fikk ikke til e legge i databasen
			return 0;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
		}
	}


	function extrval($value) {
		if ($value == "." || $value == 'undef') {
			return null;
		} else {
			return $value;
		}
	}

	// opprette nytt matchfelt
	function nyttMatchFelt($name, $descr, $qvaluehelp, $qvalueid, $qvaluename, $qvaluecategory, $qvaluesort, $listlimit, $showlist, $datatype) {

		$ivalueid 	= $this->extrval($qvalueid);
		$ivaluename 	= $this->extrval($qvaluename);
		$ivaluecategory	= $this->extrval($qvaluecategory);
		$ivaluesort 	= $this->extrval($qvaluesort);
		$ivaluehelp	= $this->extrval($qvaluehelp);
		$idescr		= $this->extrval($descr);
		$iname		= $this->extrval($name);

		// Spxrring som legger inn i databasen
		$querystr = "INSERT INTO MatchField (
				name, descr, valuehelp, valueid, valuename,
				valuecategory, valuesort, listlimit, showlist, datatype
			)
			VALUES (
				$1, $2, $3, $4, $5,
				$6, $7, $8, $9, $10
			)";

		$querypar = array(
				$iname, $idescr, $ivaluehelp, $ivalueid, $ivaluename,
				$ivaluecategory, $ivaluesort, $listlimit, $showlist, $datatype
			);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$lastid_querystr = 'SELECT currval(\'matchfield_id_seq\') AS lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');
			return $lastid;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			return 0;
		}

	}



	// legge til eksisterende filter til utstyrsgruppe
	function nyttGrpFilter($gid, $fid, $inkluder, $positiv) {
		if ($inkluder == 1) { $inkl = "true"; } else { $inkl = "false"; }
		if ($positiv == 1) { $neg = "true"; } else { $neg = "false"; }	

		// Spxrring som legger inn i databasen
		$querystr = "INSERT INTO GruppeTilFilter (
				utstyrgruppeid, utstyrfilterid, inkluder, positiv, prioritet
			)
			SELECT  $1, $2, $3, $4, 1 + max(prioritet)
			FROM (
				SELECT prioritet
				FROM GruppeTilFilter
				WHERE (utstyrgruppeid = $1)
				UNION
				SELECT 0 AS prioritet
			) AS x";
		$querypar = array($gid, $fid, $inkl, $neg);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			// In NAV <= 3.4 GruppeTilFilter have one constraint:
			//   * PRIMARY KEY (utstyrgruppeid, utstyrfilterid)
			// So the following query should return only one row.
			// In NAV >= 3.5 GruppeTilFilter will have an id-column
			// as it's primary key, but also enforce an additional
			// constaint:
			//  * UNIQUE (utstyrgruppeid, utstyrfilterid)
			$lastid_querystr = 'SELECT utstyrfilterid
				FROM GruppeTilFilter
				WHERE
					utstyrgruppeid = $1 AND
					utstyrfilterid = $2';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');
			return $lastid;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			return 0;
		}
	}


	// opprette ny match
	function nyMatch($matchfelt, $matchtype, $verdi, $fid) {
		$querystr = "INSERT INTO FilterMatch
				(matchfelt, matchtype, utstyrfilterid, verdi)
			VALUES ($1, $2, $3, $4)";
		$querypar = array($matchfelt, $matchtype, $fid, $verdi);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$lastid_querystr = 'SELECT currval(\'filtermatch_id_seq\') AS lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');
			return $lastid;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			return 0;
		}
	}


	// opprette ny utstyrsgruppe
	function nyUtstyrgruppe($uid, $navn, $descr, $basertpaa) {
		// Legg inn ny utstyrsgruppe i databasen
		$querystr = "INSERT INTO Utstyrgruppe (accountid, navn, descr)
			VALUES ($1, $2, $3)";
		$querypar = array($uid, $navn, $descr);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$lastid_querystr = 'SELECT currval(\'utstyrgruppe_id_seq\') AS lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$nyutstgrpid = pg_fetch_result($lastid_query, 'lastid');
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			return 0;
		}

		// Legge inn utstyrsfiltre hvis utstyrsgruppen skal være basert på en annen.
		if ($basertpaa > 0) {
			$utstgrinfo = $this->utstyrgruppeInfoAdv($basertpaa, $uid);

			// Hvis utstyrfiltergruppa som den skal baseres på er min egen :
			if ($utstgrinfo[2]) {
				$querystr = "INSERT INTO GruppeTilFilter (
						inkluder, positiv, prioritet,
						utstyrfilterid, utstyrgruppeid
					)
					SELECT
						inkluder, positiv, prioritet,
						utstyrfilterid, $1
					FROM GruppeTilFilter
					WHERE (utstyrgruppeid = $2)";
				$querypar = array($nyutstgrpid, $basertpaa);
				$query = pg_query_params(
						$this->connection,
						$querystr,
						$querypar
					);
				if (!$query) {
					checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
					return 0;
				}
				return 1;
			} else {
				// Hvis ikke utstyrsfiltergruppa som det skal
				// baseres på er egen, må filtermatchene også
				// klones.

				// Legger inn alle utstyrsgrupper som må arves
				$arvefilter = $this->listFiltreGruppe($basertpaa, 0);
				foreach ($arvefilter AS $arvfilterelement) {
					// utstyrfilterid inneholder
					// utstyrfilterid for både den orginale
					// og den klonede utstyrsfilteret.
					$utstyrfilteridlist[] = array(
							$this->nyttFilter(
									$arvfilterelement[1],
									$uid
								),
							$arvfilterelement[0]
						);

				}
				/* Variabler:
				 *  $ustyrfilterid[1]    utstyrfilterid orginalt utstyrsfilter
				 *  $ustyrfilterid[0]    utstyrfilterid nytt/klonet utstyrsfilter
				 *  $basertpaa           utstyrgruppeid orginal utstyrgruppe
				 *  $nyutstgrpid         utstyrgruppeid ny/klonet utstyrgruppe
				 */

				// Legger inn referanser fra den nye
				// utstyrsgruppen til de nye klonede filtrene.
				foreach ($utstyrfilteridlist AS $utstyrfilterid) {
					$querystr = "INSERT INTO GruppeTilFilter (
							inkluder, positiv, prioritet,
							utstyrfilterid, utstyrgruppeid
						)
						SELECT
							inkluder, positiv, prioritet,
							$1, $2
						FROM GruppeTilFilter
						WHERE
							(utstyrgruppeid = $3) AND
							(utstyrfilterid = $4)";
					 $querypar = array(
							$utstyrfilterid[0],
							$nyutstgrpid,
							$basertpaa,
							$utstyrfilterid[1]
						);
					$query = pg_query_params(
							$this->connection,
							$querystr,
							$querypar
						);
					if (!$query)
						checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
				}

				// Traversere utstyrsfiltre som skal arves for
				// å finne filtermatcher som skal arves
				foreach ($utstyrfilteridlist AS $utstyrfilterid) {
					$querystr = "INSERT INTO FilterMatch (
							matchfelt, matchtype,
							verdi, utstyrfilterid
						)
						SELECT matchfelt, matchtype, verdi, $1
						FROM FilterMatch
						WHERE (utstyrfilterid = $2)";
					$querypar = array($utstyrfilterid[0], $utstyrfilterid[1]);
					$query = pg_query_params(
							$this->connection,
							$querystr,
							$querypar
						);
					if (!$query)
						checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
				}
			}
		} else {
			return $nyutstgrpid;
		}
	}

	// opprette ny utstyrsgruppe administrator
	function nyUtstyrgruppeAdm($navn, $descr) {

		// Spxrring som legger inn i databasen
		$querystr = "INSERT INTO Utstyrgruppe (accountid, navn, descr)
			VALUES (null, $1, $2)";
		$querypar = array($navn, $descr);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			$lastid_querystr = 'SELECT currval(\'utstyrgruppe_id_seq\') AS lastid';
			$lastid_query = pg_query($this->connection, $lastid_querystr);
			if (!$lastid_query)
				checkDBError($this->connection, $lastid_querystr, array(), __FILE__, __LINE__);
			$lastid = pg_fetch_result($lastid_query, 'lastid');
			return $lastid;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til e legge i databasen
			return 0;
		}

	}

	// slette en adresse
	function slettAdresse($aid) {

		// Spxrring som legger inn i databasen
		$querystr = "DELETE FROM Alarmadresse
			WHERE (id = $1)";
		$querypar = array($aid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en profil
	function slettProfil($pid) {

		// Spxrring som legger inn i databasen
		$querystr = "DELETE FROM Brukerprofil
			WHERE (id = $1)";
		$querypar = array($pid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}


	// slette en bruker
	function slettBruker($uid) {

		// Spxrring som legger inn i databasen
		$querystr = "DELETE FROM Account
			WHERE (id = $1)";
		$querypar = array($uid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}


	// slette en brukergruppe
	function slettBrukergruppe($gid) {

		// Spxrring som legger inn i databasen
		$querystr = "DELETE FROM AccountGroup
			WHERE (id = $1)";
		$querypar = array($gid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en utstyrsgruppe
	function slettUtstyrgruppe($gid) {

		// Spxrring som legger inn i databasen
		$querystr = "DELETE FROM Utstyrgruppe
			WHERE (id = $1)";
		$querypar = array($gid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en brukergruppe
	function slettPeriode($pid) {

		// Spxrring som legger inn i databasen
		$querystr = "DELETE FROM Tidsperiode
			WHERE (id = $1)";
		$querypar = array($pid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en brukergruppe
	function slettGrpFilter($gid, $fid) {

		// Spxrring som legger inn i databasen
		$querystr = "DELETE FROM gruppetilfilter
			WHERE
				utstyrgruppeid = $1 AND
				utstyrfilterid = $2";
		$querypar = array($gid, $fid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}
	}


	// slette en filter til match relasjon
	function slettFiltermatch($fid, $mid) {

		// Spxrring som legger inn i databasen
		$querystr = "DELETE FROM FilterMatch
			WHERE
				id = $1 AND
				utstyrfilterid = $2";
		$querypar = array($mid, $fid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en brukergruppe
	function slettFilter($fid) {

		// Spxrring som legger inn i databasen
		$querystr = "DELETE FROM Utstyrfilter
			WHERE (id = $1)";
		$querypar = array($fid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// sett en profil som aktiv for en bestemt bruker
	function aktivProfil($brukerid, $profilid) {

		if ($profilid == 0) { $profilid = null; }
		// Spxrring som legger inn i databasen
		$querystr = "UPDATE Preference
			SET activeprofile = $1
			WHERE accountid = $2";
		$querypar = array($profilid, $brukerid);

		if ($query = pg_query_params($this->connection, $querystr, $querypar)) {
			return 1;
		} else {
			checkDBError($this->connection, $querystr, $querypar, __FILE__, __LINE__);
			// fikk ikke til å legge i databasen
			return 0;
		}
	}
}

/*
 * *****************************************************************************
 */

/*
 *	Dette er en klasse for spørringer mot kunnskapsdatabasen til UNINETT
 *
 */
class DBHK {

	// Må ha inn en ferdig oppkoblet databasekobling til postgres
	var $connection;

	// Konstruktor
	function DBHK($connection) {
		$this->connection = $connection;
	}

	function get_table($streng) {
		$r = split('\.', $streng, 2);
		return addslashes($r[0]);
	}

	function get_field($streng) {
		$r = split('\.', $streng, 2);
		return addslashes($r[1]);  
	}

	function listVerdier($valueid, $valuename, $valuecategory, $valuesort, $limit) {

		$verdier = null;
		$vname = split("\|", $valuename);

		/* 	echo '<p>vname:<pre>'; */
		/* 	print_r($vname); */
		/*     echo "</pre>"; */


		$vntemplate = (sizeof($vname) > 1) ? $vname[1] : '[NAME]';
		$vnamestr = (sizeof($vname) > 1) ? $vname[0] : $valuename;

		$vtabell = $this->get_table($valueid);
		$vid = $this->get_field($valueid);
		$vname = $this->get_field($vnamestr);
		$vsort = $this->get_field($valuesort);
		$vcat =  isset($valuecategory) ? $this->get_field($valuecategory) : null;

		if (isset($vcat) && $vcat ) {
			$vc = ", " . $vcat;
		} else {
			$vc = "";
			//$vsort = $this->get_field($vcat) . ', ' . $vsort;
		}
		$querystr = "SELECT $vid, $vname $vc " . 
			"FROM $vtabell " .
			"ORDER BY $vsort LIMIT " . pg_escape_string($limit);

		if ($query = pg_query($this->connection, $querystr)) {
		$numrows = pg_num_rows($query);
		for ($i = 0; $i < $numrows; $i++) {
			$data = pg_fetch_array($query, $i, PGSQL_ASSOC);
				$scat = 0;
				if (isset($vcat) && $vcat && isset($data[$vcat]))
					$cat = $data[$vcat];

				$namestring = $vntemplate;
				$namestring = preg_replace('/(\[NAME\])/', $data[$vname], $namestring);
				$namestring = preg_replace('/(\[ID\])/', $data[$vid], $namestring);
				$namestring = preg_replace('/(\[GROUP\])/', $scat, $namestring);


				if (!isset($verdier[$scat] )) {
					$verdier[$scat] = null;
				}
				$verdier[$scat][] = array($data[$vid], $namestring);
			}

		}  else {
			checkDBError($this->connection, $querystr, array(), __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $verdier;
	}


	function listFelter() {

		$felter = null;

		$querystr = "SELECT c.relname, a.attname, t.typname 
			FROM pg_class c, pg_attribute a, pg_type t, pg_tables tb 
			WHERE a.attnum > 0 AND a.attrelid = c.oid AND a.atttypid = t.oid AND 
			c.relname = tb.tablename AND tablename not like 'pg_%' 
			ORDER BY c.relname, a.attname;";

		if ($query = pg_query($this->connection, $querystr)) {
			$numrows = pg_num_rows($query);
			for ($row = 0; $row < $numrows; $row++) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$felter[$data['relname']][$row][0] = $data['attname'];
				$felter[$data['relname']][$row][1] = $data['typname'];
			}

		}  else {
			checkDBError($this->connection, $querystr, array(), __FILE__, __LINE__);
			$error = new Error(2);
			global $RUNTIME_ERRORS;
			$RUNTIME_ERRORS[][] = $error;
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}


		return $felter;  

	}
}


?>
