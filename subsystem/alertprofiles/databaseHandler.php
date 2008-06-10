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

class DBH {

	// Må ha inn en ferdig oppkoblet databasekobling til postgres
	var $connection;


	// Konstruktor
	function DBH($connection) {
		$this->connection = $connection;
	}


	function permissionAddress($uid, $aid) {
		$querystring = "
			SELECT * FROM alarmadresse 
			WHERE (accountid = " . addslashes($uid) . " AND id = " . addslashes($aid) . ")";
		//echo "<pre>" . $querystring . "</pre>";
		if ( $query = @pg_exec($this->connection, $querystring) ) { 
			if (pg_numrows($query) > 0 ) return true;
		}
		return false;
	}

	function permissionProfile($uid, $pid) {
		$querystring = "
			SELECT * FROM brukerprofil 
			WHERE (accountid = " . addslashes($uid) . " AND id = " . addslashes($pid) . ")";
		//echo "<pre>" . $querystring . "</pre>";
		if ( $query = @pg_exec($this->connection, $querystring) ) { 
			if (pg_numrows($query) > 0 ) return true;
		}
		return false;
	}

	function permissionEquipmentGroup($uid, $id) {
		$querystring = "
			SELECT * FROM utstyrgruppe 
			WHERE (accountid = " . addslashes($uid) . " AND id = " . addslashes($id) . ")";
		//echo "<pre>" . $querystring . "</pre>";
		if ( $query = @pg_exec($this->connection, $querystring) ) { 
			if (pg_numrows($query) > 0 ) return true;
		}
		return false;
	}


	function permissionEquipmentFilter($uid, $id) {
		$querystring = "
			SELECT * FROM utstyrfilter 
			WHERE (accountid = " . addslashes($uid) . " AND id = " . addslashes($id) . ")";
		//echo "<pre>" . $querystring . "</pre>";
		if ( $query = @pg_exec($this->connection, $querystring) ) { 
			if (pg_numrows($query) > 0 ) return true;
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

		$querystring = "SELECT Account.id, Account.login, Account.name, null as admin, null as sms, Preference.queuelength, " .
			"profiler.pa, adresser.aa FROM Preference, Account LEFT OUTER JOIN " .
			"(SELECT count(Brukerprofil.id) AS pa, Brukerprofil.accountid AS uid " . 
			"FROM Brukerprofil GROUP BY (Brukerprofil.accountid)) AS profiler ON (Account.id = profiler.uid) " .
			"LEFT OUTER JOIN " .
			"(SELECT count(Alarmadresse.id) AS aa, Alarmadresse.accountid AS uid " .
			"FROM Alarmadresse GROUP BY (Alarmadresse.accountid)) AS adresser ON (Account.id = adresser.uid) " .
			"WHERE (Preference.accountid = Account.id) " .
			"ORDER BY " . $sorts[$sort];

		//echo "<p>Query: " . $querystring;
		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$brukere[$row][0] = $data["id"];
				$brukere[$row][1] = $data["login"];
				$brukere[$row][2] = $data["name"];
				$brukere[$row][3] = $data["admin"];
				$brukere[$row][4] = $data["sms"];
				$brukere[$row][5] = $data["pa"];
				$brukere[$row][6] = $data["aa"];
				$brukere[$row][7] = $data["queuelength"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
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

		$querystring = "SELECT id, login, name, (Medlem.groupid > 0) AS medlem 
			FROM Account LEFT OUTER JOIN ( 
					SELECT groupid, accountid 
					FROM AccountInGroup 
					WHERE (groupid = " . addslashes($gid) . ") 
					) AS Medlem 
			ON (Account.id = Medlem.accountid) 
			ORDER BY " . $sorts[$sort];

		//echo "<p>Query: " . $querystring;

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$brukere[$row][0] = $data["id"];
				$brukere[$row][1] = $data["login"];
				$brukere[$row][2] = $data["name"];
				$brukere[$row][3] = $data["medlem"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
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

		$querystring = "SELECT Logg.type, Logg.descr, date_part('epoch', Logg.tid) AS tid, Account.name 
			FROM Account, Logg 
			WHERE (	Account.id = Logg.accountid ) 
			ORDER BY " . $sorts[$sort] . " LIMIT 100";

		//print "<pre>" . $querystring . "</pre>";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$logg[$row][0] = $data["type"];
				$logg[$row][1] = $data["descr"];
				$logg[$row][2] = $data["tid"];
				$logg[$row][3] = $data["name"];
				$row++;
			} 
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

		$querystring = "SELECT matchfieldid, name, valueid 
			FROM MatchField 
			ORDER BY " . $sorts[$sort];

		//print "<pre>" . $querystring . "</pre>";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$fm[$row][0] = $data["matchfieldid"];
				$fm[$row][1] = $data["name"];
				$fm[$row][2] = $data["valueid"];
				$row++;
			} 
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

		$querystring = "SELECT id, name, descr, BCount.ab, Rcount.ar, Dcount.ad, DFCount.adf  
			FROM Accountgroup 
			LEFT OUTER JOIN (
					SELECT count(accountid) AS ab, groupid
					FROM AccountInGroup
					GROUP BY groupid
					) AS BCount 
			ON (id = BCount.groupid)
			LEFT OUTER JOIN (
					SELECT count(utstyrgruppeid) AS ar, accountgroupid 
					FROM Rettighet 
					GROUP BY accountgroupid 
					) AS RCount 
			ON (id = RCount.accountgroupid) 
			LEFT OUTER JOIN (
					SELECT count(utstyrgruppeid) AS ad, accountgroupid
					FROM DefaultUtstyr 
					GROUP BY accountgroupid 
					) AS DCount 
			ON (id = DCount.accountgroupid) 
			LEFT OUTER JOIN (
					SELECT count(utstyrfilterid) AS adf, accountgroupid
					FROM DefaultFilter 
					GROUP BY accountgroupid 	
					) AS DFCount 
			ON (id = DFCount.accountgroupid)    
			ORDER BY " . $sorts[$sort];

		//print "<pre>" . $querystring . "</pre>";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$brukere[$row][0] = $data["id"];
				$brukere[$row][1] = $data["name"];
				$brukere[$row][2] = $data["descr"];
				$brukere[$row][3] = $data["ab"];
				$brukere[$row][4] = $data["ar"];
				$brukere[$row][5] = $data["ad"];
				$brukere[$row][6] = $data["adf"];		
				$row++;
			} 
		}  else {
			$error = new Error(2);
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

		$querystring = "SELECT id, name, descr 
			FROM AccountGroup, AccountInGroup 
			WHERE (AccountInGroup.groupid = Accountgroup.id) AND 
			(AccountInGroup.accountid = " . $uid . ") 
			ORDER BY name ";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$grupper[$row][0] = $data["id"];
				$grupper[$row][1] = $data["name"];
				$grupper[$row][2] = $data["descr"];
				$row++;
			}	 
		}  else {
			$error = new Error(2);
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

		$querystring = "SELECT id, name, descr, BCount.ab, Rcount.ar, Dcount.ad, (Medlem.groupid > 0) AS medl 
			FROM AccountGroup 
			LEFT OUTER JOIN (
					SELECT count(accountid) AS ab, groupid
					FROM AccountInGroup
					GROUP BY groupid
					) AS BCount 
			ON (id = BCount.groupid)
			LEFT OUTER JOIN (
					SELECT count(utstyrgruppeid) AS ar, accountgroupid 
					FROM Rettighet 
					GROUP BY accountgroupid 
					) AS RCount 
			ON (id = RCount.accountgroupid) 
			LEFT OUTER JOIN (
					SELECT count(utstyrgruppeid) AS ad, accountgroupid
					FROM DefaultUtstyr 
					GROUP BY accountgroupid 
					) AS DCount 
			ON (id = DCount.accountgroupid) 
			LEFT OUTER JOIN (
					SELECT accountid, groupid FROM AccountInGroup 
					WHERE (accountid = " . addslashes($uid) . ") 
					) AS Medlem 
			ON (id = Medlem.groupid) 
			ORDER BY " . $sorts[$sort];

		//print "<pre>" . $querystring . "</pre>";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$brukere[$row][0] = $data["id"];
				$brukere[$row][1] = $data["name"];
				$brukere[$row][2] = $data["descr"];
				$brukere[$row][3] = $data["ab"];
				$brukere[$row][4] = $data["ar"];
				$brukere[$row][5] = $data["ad"];
				$brukere[$row][6] = $data["medl"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $brukere;
	}


	function listAdresser($uid, $sort) {

		$adr = NULL;

		$sorts = array ('type, adresse', 'adresse');

		$querystring = "SELECT id, adresse, type " .
			"FROM Alarmadresse " .
			"WHERE (accountid = " . addslashes($uid) . ") " .
			"ORDER BY " . $sorts[$sort];

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$adr[$row][0] = $data["id"];
				$adr[$row][1] = $data["adresse"];
				$adr[$row][2] = $data["type"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $adr;
	}




	// Lister opp alle adresser knyttet til tidsprofiler, og henter ut køvariabel
	function listAlleVarsleAdresser($uid, $tid, $sort) {

		//    print "<p>UID: $uid  - TID: $tid  - GID: $gid   - SORT: $sort";
		$adr = NULL;

		$sorts = array (
				'min, gnavn', 
				'type',
				'adresse, gnavn',
				'vent, adresse'
			       );

		$querystring = '
			SELECT alarmadresse.id AS adrid, adresse, type, vent, utstyrgruppe.id AS gid, utstyrgruppe.navn AS gnavn, 
			       (Utstyrgruppe.accountid = ' . addslashes($uid). ') AS min 
				       FROM Utstyrgruppe, Varsle, Alarmadresse 
				       WHERE (utstyrgruppe.id = varsle.utstyrgruppeid) AND
				       (alarmadresse.id = varsle.alarmadresseid) AND 
				       (varsle.tidsperiodeid = ' . addslashes($tid) . ') 
				       ORDER BY ' . $sorts[$sort];

		//echo '<p>' . $querystring . '<p>';

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$adr[$row][0] = $data["adrid"];
				$adr[$row][1] = $data["adresse"];
				$adr[$row][2] = $data["type"];
				$adr[$row][3] = $data["vent"];
				$adr[$row][4] = $data["gid"];
				$adr[$row][5] = $data["gnavn"];
				$adr[$row][6] = $data["min"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $adr;
	}


	// Lister opp alle adresser knyttet til tidsprofiler for en gitt utstyrsgruppe, 
	// og henter ut køvariabel
	function listVarsleAdresser($uid, $tid, $gid, $sort) {

		//    print "<p>UID: $uid  - TID: $tid  - GID: $gid   - SORT: $sort";
		$adr = NULL;

		$sorts = array ('type, adresse', 'adresse');

		$querystring = "SELECT id, adresse, type, vent 
			FROM (
					SELECT adresse, id, type 
					FROM Alarmadresse
					WHERE (accountid = " . addslashes($uid) . ")
			     ) AS adr LEFT OUTER JOIN (
				     SELECT vent, alarmadresseid 
				     FROM Varsle
				     WHERE (tidsperiodeid = " . addslashes($tid) . ")
				     AND (utstyrgruppeid = " . addslashes($gid) . ") 
				     ) AS periode
			     ON (adr.id = periode.alarmadresseid)
			     ORDER BY " . $sorts[$sort];

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$adr[$row][0] = $data["id"];
				$adr[$row][1] = $data["adresse"];
				$adr[$row][2] = $data["type"];
				$adr[$row][3] = $data["vent"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
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

		$querystring = "SELECT matchfieldid, name, descr, valuehelp " .
			"FROM MatchField " .
			"ORDER BY " . $sorts[$sort];

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$matcher[$row][0] = $data["matchfieldid"];
				$matcher[$row][1] = $data["name"];
				$matcher[$row][2] = $data["descr"];
				$matcher[$row][3] = $data["valuehelp"];
				$row++;
			}

		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}


		return $matcher;
	}


	// Hent ut info om et matchfield felt.
	function matchFieldInfo($mid) {
		$mf = NULL;

		$querystring = "SELECT name, descr, valuehelp, valueid, valuename, 
			valuecategory, valuesort, listlimit, showlist 
			FROM MatchField 
			WHERE matchfieldid = " . addslashes($mid) ;

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
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
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		$querystring = "SELECT operatorid " .
			"FROM Operator " .
			"WHERE matchfieldid = " . addslashes($mid) . " " .
			"ORDER BY operatorid ";

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$operators[] = $data["operatorid"];
				$row++;
			}

		}  else {
			$error = new Error(2);
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

		$querystring = "
			SELECT (Preference.activeprofile = Brukerprofil.id) AS aktiv,
			       Brukerprofil.id, Brukerprofil.navn, Q.antall
				       FROM Preference, Account, Brukerprofil LEFT OUTER JOIN 
				       (SELECT pid, count(tid) AS antall FROM 
					(SELECT Tidsperiode.id AS tid, Brukerprofil.id AS pid FROM Tidsperiode, Brukerprofil 
					 WHERE (Brukerprofil.accountid = " . addslashes($uid) . "
					       ) AND (Brukerprofil.id = Tidsperiode.brukerprofilid) ) AS Perioder 
					GROUP BY Perioder.pid ) AS Q 
				       ON (Brukerprofil.id = Q.pid) 
				       WHERE (Brukerprofil.accountid = " . addslashes($uid) . ") AND (Account.id = Brukerprofil.accountid) AND
				       (Account.id = Preference.accountid) 
				       ORDER BY " . $sorts[$sort];

		//print "<p>$querystring";

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$profiler[$row][0] = $data["id"]; 
				$profiler[$row][1] = $data["navn"];
				$profiler[$row][2] = $data["antall"];
				$profiler[$row][3] = $data["aktiv"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $profiler;
	}



	// Liste alle tidsperiodene til en profil
	function listPerioder($pid, $sort) {
		$perioder = NULL;

#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

		$querystring = "SELECT Tidsper.id, Tidsper.helg, 
			date_part('hour', Tidsper.starttid) AS time, date_part('minute', Tidsper.starttid) AS minutt, 
			adresser.aa, grupper.au 
				FROM (
						SELECT id, helg, starttid 
						FROM Tidsperiode 
						WHERE (Tidsperiode.brukerprofilid = " . addslashes($pid) . ") 
				     ) AS Tidsper LEFT OUTER JOIN ( 
					     SELECT count(aid) AS aa, tid 
					     FROM ( 
						     SELECT DISTINCT Varsle.alarmadresseid AS aid, Varsle.tidsperiodeid AS tid 
						     FROM Varsle, Tidsperiode 
						     WHERE (Tidsperiode.brukerprofilid = " . addslashes($pid) . ") AND (Tidsperiode.id = Varsle.tidsperiodeid) 
						  ) AS Acount 
					     GROUP BY tid 
					     ) AS adresser 
				     ON (Tidsper.id = adresser.tid) 
				     LEFT OUTER JOIN ( 
						     SELECT count(gid) AS au, tid 
						     FROM ( 
							     SELECT DISTINCT Varsle.utstyrgruppeid AS gid, Varsle.tidsperiodeid AS tid 
							     FROM Varsle, Tidsperiode 
							     WHERE (Tidsperiode.brukerprofilid = " . addslashes($pid) . ") AND (Tidsperiode.id = Varsle.tidsperiodeid) 
							  ) AS Gcount 
						     GROUP BY tid 
						     ) AS grupper 
				     ON (Tidsper.id = grupper.tid) 

				     ORDER BY time, minutt";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$perioder[$row][0] = $data["id"]; 
				$perioder[$row][1] = $data["helg"];
				$perioder[$row][2] = $data["time"];
				$perioder[$row][3] = $data["minutt"];
				$perioder[$row][4] = $data["aa"];
				$perioder[$row][5] = $data["au"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $perioder;
	}



	// Denne funksjonen returnerer en liste over alle tidsperioder som kræsjer, altså har samme tid.        
	function listPeriodekonflikter($pid) {
		$konf = NULL;

		$querystring =  "
			SELECT antall, dag, starttid FROM (
					SELECT count(id) AS antall, dag, starttid FROM (
						SELECT id, 'hverdag' AS dag, starttid 
						FROM Tidsperiode 
						WHERE brukerprofilid = " . addslashes($pid) . " AND ((helg = 2) OR (helg = 1) )
						UNION
						SELECT id, 'helg' AS dag, starttid  
						FROM Tidsperiode 
						WHERE brukerprofilid = " . addslashes($pid) . " AND ((helg = 3) OR (helg = 1) )
						) AS subs
					GROUP BY dag, starttid
					) AS subss 
			WHERE antall > 1
			";     
			//print "<pre>" . $querystring . "</pre>";


			if ( $query = pg_exec($this->connection, $querystring) ) {
				$tot = pg_numrows($query); $row = 0;

				while ( $row < $tot) {
					$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
					$konf[$row][0] = $data["antall"];		
					$konf[$row][1] = $data["dag"];
					$konf[$row][2] = $data["starttid"];

					$row++;
				} 
			}  else {
				$error = new Error(2);
				$bruker{'errmsg'}= "Feil med datbasespørring.";
			}

		return $konf;

	}






	// Denne funksjonen returnerer alle utstyrgrupper som en Account har tilgang til, 
	// enten man har laget den selv eller den er arvet gjennom DefaultUtstyr.
	function listUtstyr($uid, $sort) {
		$utst = NULL;

		$sorts = array (
				'navn,id',
				'min,navn',
				'ap,navn',
				'af,navn');

		$querystring = "SELECT * FROM (SELECT DISTINCT ON (id) id, navn, descr, min, Pcount.ap, FCount.af 
			FROM (SELECT id, navn, descr, true AS min
					FROM Utstyrgruppe
					WHERE (accountid = " . addslashes($uid) . ")
					UNION
					SELECT Utstyrgruppe.id, Utstyrgruppe.navn, Utstyrgruppe.descr, (Utstyrgruppe.accountid = " . addslashes($uid). ") AS min
					FROM Utstyrgruppe, DefaultUtstyr, AccountGroup, AccountInGroup
					WHERE (AccountInGroup.accountid = " . addslashes($uid) . ")
					AND (AccountInGroup.groupid = AccountGroup.id)
					AND (AccountGroup.id = DefaultUtstyr.accountgroupid)
					AND (DefaultUtstyr.utstyrgruppeid = Utstyrgruppe.id)
			     ) AS Tilgjengelig LEFT OUTER JOIN
			(    SELECT count(tidsperiodeid) AS ap, utstyrgruppeid
			     FROM (
				     SELECT DISTINCT ON (utstyrgruppeid,tidsperiodeid) tidsperiodeid, utstyrgruppeid
				     FROM (
					     SELECT Varsle.utstyrgruppeid, Varsle.tidsperiodeid FROM Varsle, Tidsperiode, Brukerprofil 
					     WHERE (Varsle.tidsperiodeid = Tidsperiode.id) AND
					     (Tidsperiode.brukerprofilid = Brukerprofil.id) AND
					     (Brukerprofil.accountid = " . addslashes($uid) . ")
					  ) AS MinVarsle, Utstyrgruppe
				     WHERE (Utstyrgruppe.id = MinVarsle.utstyrgruppeid)
				  ) AS X
			     GROUP BY utstyrgruppeid
			) AS PCount
			ON (id = PCount.utstyrgruppeid)
			LEFT OUTER JOIN (
					SELECT count(utstyrfilterid) AS af, utstyrgruppeid
					FROM (
						SELECT utstyrfilterid, utstyrgruppeid
						FROM GruppeTilFilter, Utstyrgruppe
						WHERE ((Utstyrgruppe.accountid = " . addslashes($uid) . ") OR (Utstyrgruppe.accountid is null) )
						AND (Utstyrgruppe.id = GruppeTilFilter.utstyrgruppeid)
					     ) AS Y
					GROUP BY utstyrgruppeid
					) AS FCount
			ON (id = FCount.utstyrgruppeid) ) jalla ORDER BY " . $sorts[$sort];

		//print "<pre>" . $querystring . "</pre>";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$utst[$row][0] = $data["id"];		
				$utst[$row][1] = $data["navn"];
				$utst[$row][2] = $data["ap"];
				$utst[$row][3] = $data["af"];
				$utst[$row][4] = $data["min"];
				$utst[$row][5] = $data["descr"];		

				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $utst;

	}


	// Denne funksjonen returnerer alle utstyrgrupper som en Account har rettighet til, 
	function listUtstyrRettighet($uid, $sort) {
		$utst = NULL;

#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

		$querystring = "SELECT DISTINCT ON (id) utstyrgruppe.id, navn, descr 
			FROM accountingroup, Rettighet, Utstyrgruppe 
			WHERE (AccountInGroup.accountid = " . addslashes($uid) . ") AND 
			(AccountInGroup.groupid = Rettighet.accountgroupid) AND 
			(Rettighet.utstyrgruppeid = Utstyrgruppe.id)";

		//print "<p>$querystring";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$utst[$row][0] = $data["id"]; 
				$utst[$row][1] = $data["navn"];			
				$utst[$row][2] = $data["descr"];	
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $utst;
	}


	// Denne funksjonen returnerer alle utstyrgrupper som administrator har rettigheter til 
	function listUtstyrAdm($sort) {
		$utst = NULL;

		$sorts = array (
				'navn,id',
				'ap,navn',
				'af,navn');

		$querystring = "SELECT * FROM (SELECT DISTINCT ON (id) id, navn, descr, min, Pcount.ap, FCount.af
			FROM (SELECT id, navn, descr, true AS min
					FROM Utstyrgruppe
					WHERE (accountid is null)
			     ) AS Tilgjengelig LEFT OUTER JOIN
			(    SELECT count(tidsperiodeid) AS ap, utstyrgruppeid
			     FROM (
				     SELECT DISTINCT ON (utstyrgruppeid,tidsperiodeid) tidsperiodeid, utstyrgruppeid
				     FROM Varsle, Utstyrgruppe
				     WHERE (Utstyrgruppe.accountid is null)
				     AND (Utstyrgruppe.id = Varsle.utstyrgruppeid)
				  ) AS X
			     GROUP BY utstyrgruppeid
			) AS PCount
			ON (id = PCount.utstyrgruppeid)
			LEFT OUTER JOIN (
					SELECT count(utstyrfilterid) AS af, utstyrgruppeid
					FROM (
						SELECT utstyrfilterid, utstyrgruppeid
						FROM GruppeTilFilter, Utstyrgruppe
						WHERE (Utstyrgruppe.accountid is null)
						AND (Utstyrgruppe.id = GruppeTilFilter.utstyrgruppeid)
					     ) AS Y
					GROUP BY utstyrgruppeid
					) AS FCount
			ON (id = FCount.utstyrgruppeid)) jalla ORDER BY " . $sorts[$sort];

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$utst[$row][0] = $data["id"];		
				$utst[$row][1] = $data["navn"];
				$utst[$row][2] = $data["ap"];
				$utst[$row][3] = $data["af"];
				$utst[$row][4] = $data["min"];
				$utst[$row][5] = $data["descr"];		

				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $utst;
	}





	// Denne funksjonen returnerer alle utstyrgrupper knyttet til en bestemt periode i en profil
	function listUtstyrPeriode($uid, $pid, $sort) {
		$uts = NULL;

#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

		$querystring = "SELECT DISTINCT ON (id) id, navn, min, Pcount.ap, FCount.af 
			FROM ( SELECT id, navn, descr, true AS min 
					FROM Utstyrgruppe
					WHERE (accountid = " . addslashes($uid) . ")
					UNION 
					SELECT Utstyrgruppe.id, Utstyrgruppe.navn, Utstyrgruppe.descr, (Utstyrgruppe.accountid = " . addslashes($uid) . ") AS min 
					FROM Utstyrgruppe, DefaultUtstyr, AccountGroup, AccountInGroup
					WHERE (AccountInGroup.accountid = " . addslashes($uid) . ")
					AND (AccountInGroup.groupid = AccountGroup.id)
					AND (AccountGroup.id = DefaultUtstyr.accountgroupid)
					AND (DefaultUtstyr.utstyrgruppeid = Utstyrgruppe.id) 
			     ) AS Tilgjengelig LEFT OUTER JOIN ( 
				     SELECT count(tidsperiodeid) AS ap, utstyrgruppeid
				     FROM (
					     SELECT DISTINCT tidsperiodeid, utstyrgruppeid
					     FROM Varsle, Tidsperiode, Brukerprofil 
					     WHERE (Varsle.tidsperiodeid = Tidsperiode.id) 
					     AND (Tidsperiode.brukerprofilid = Brukerprofil.id) 
					     AND (Brukerprofil.accountid = " . addslashes($uid) . ") 
					  ) AS X
				     GROUP BY utstyrgruppeid
				     ) AS PCount
			     ON (id = PCount.utstyrgruppeid)
			     LEFT OUTER JOIN (
					     SELECT count(utstyrfilterid) AS af, utstyrgruppeid
					     FROM (
						     SELECT utstyrfilterid, utstyrgruppeid
						     FROM GruppeTilFilter, Utstyrgruppe
						     WHERE (Utstyrgruppe.accountid = " . addslashes($uid) . ")
						     AND (Utstyrgruppe.id = GruppeTilFilter.utstyrgruppeid)
						  ) AS Y
					     GROUP BY utstyrgruppeid
					     ) AS FCount
			     ON (id = FCount.utstyrgruppeid)";


		//print "<p>$querystring";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$utst[$row][0] = $data["id"]; 
				$utst[$row][1] = $data["navn"];
				$utst[$row][2] = $data["ap"];
				$utst[$row][3] = $data["af"];
				$utst[$row][4] = $data["min"];				
				//$utst[$row][5] = $data["ermed"];	
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $utst;
	}




	// Denne funksjonen returenrer alle felles filtere samt default utrstyr knyttet til
	// brukergruppene.
	function listGrFilter($uid, $gid, $sort) {
		$utst = NULL;

#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

		$querystring = "SELECT id, navn,  
			(def.utstyrfilterid > 0 ) AS default 
			FROM (
					SELECT id, navn  
					FROM Utstyrfilter 
					WHERE accountid is null 
			     ) AS filter 
			LEFT OUTER JOIN (
					SELECT utstyrfilterid   
					FROM DefaultFilter  
					WHERE accountgroupid = " . addslashes($gid) . "
					) AS def 
			ON (filter.id = def.utstyrfilterid) 
			ORDER BY navn";

		//print "<p>$querystring";

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$utst[$row][0] = $data["id"]; 
				$utst[$row][1] = $data["navn"];			
				$utst[$row][2] = $data["default"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $utst;
	}




	// Denne funksjonen returenrer alle utstyrsgruppene samt rettigheter og default utrstyr knyttet til
	// brukergruppene.
	function listGrUtstyr($uid, $gid, $sort) {
		$uts = NULL;

#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

		$querystring = "SELECT id, navn, descr, 
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
						WHERE accountgroupid = " . addslashes($gid) . "
						) AS rett 
				ON (grupper.id = rett.utstyrgruppeid) 
				LEFT OUTER JOIN (
						SELECT utstyrgruppeid 
						FROM DefaultUtstyr 
						WHERE accountgroupid = " . addslashes($gid) . "
						) AS def 
				ON (grupper.id = def.utstyrgruppeid) 
				ORDER BY navn";

		//  print "<p>$querystring";

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$utst[$row][0] = $data["id"]; 
				$utst[$row][1] = $data["navn"];			
				$utst[$row][2] = $data["descr"];
				$utst[$row][3] = $data["rettighet"];
				$utst[$row][4] = $data["default"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $utst;
	}



	// Hent ut info om en brukerid
	function brukerInfo($uid) {
		$br = NULL;

		$querystring = "SELECT login, name, null as admin, null as sms, activeprofile  
			FROM Account, Preference  
			WHERE id = " . addslashes($uid) . " AND account.id = preference.accountid";

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$br[0] = $data["login"];
			$br[1] = $data["name"];
			$br[2] = $data["admin"];
			$br[3] = $data["sms"];
			$br[4] = $data["activeprofile"];
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		return $br;
	}


	// Hent ut info om en gruppeid
	function brukergruppeInfo($gid) {
		$gr = NULL;

		$querystring = "SELECT name, descr 
			FROM AccountGroup 
			WHERE id = " . addslashes($gid) ;

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$gr[0] = $data["name"]; 
			$gr[1] = $data["descr"];		
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $gr;
	}

	// Hent ut info om en utstyrsgruppeid
	function utstyrgruppeInfo($gid) {
		$gr = NULL;

		$querystring = "SELECT navn, descr 
			FROM Utstyrgruppe 
			WHERE id = " . addslashes($gid) ;

		//	print "<p>" . $querystring;

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$gr[0] = $data["navn"]; 
			$gr[1] = $data["descr"];		
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $gr;
	}

	// Hent ut info om en utstyrsfilterid
	function utstyrfilterInfo($fid) {
		$gr = NULL;

		$querystring = "SELECT navn 
			FROM Utstyrfilter 
			WHERE id = " . addslashes($fid) ;

		//	print "<p>" . $querystring;

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$gr[0] = $data["navn"]; 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $gr;
	}




	// Hent ut info om en utstyrsgruppeid
	function utstyrgruppeInfoAdv($gid, $uid) {
		$gr = NULL;

		$querystring = "SELECT navn, descr, (accountid = " . $uid . ") AS min 
			FROM Utstyrgruppe WHERE id = " . addslashes($gid) ;

		//	print "<p>" . $querystring;

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
			$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
			$gr[0] = $data["navn"]; 
			$gr[1] = $data["descr"];
			$gr[2] = $data["min"];		
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $gr;
	}






	// Hent ut info om en brukerprofil
	function brukerprofilInfo($pid) {
		$p = NULL;

		$querystring = "SELECT navn, ukedag, extract(HOUR FROM uketid) AS uketidh, extract(MINUTE FROM uketid) AS uketidm, 
			extract(HOUR FROM tid) AS tidh, extract(MINUTE FROM tid) AS tidm 
			FROM Brukerprofil 
			WHERE id = " . addslashes($pid) ;

		//	print "<p>" . $querystring;

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$p[0] = $data["navn"]; 
			$p[1] = $data["ukedag"];		
			$p[2] = $data["uketidh"];		
			$p[3] = $data["uketidm"];		
			$p[4] = $data["tidh"];		
			$p[5] = $data["tidm"];										
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasesørring.";
		}
		return $p;
	}




	// Denne funksjonen returnerer alle filtrene som en Account har tilgang til, 
	// enten man har laget den selv eller den er arvet gjennom DefaultFilter.
	function listFiltre($uid, $sort) {
		$utst = NULL;

		$sorts = array (
				'navn,id',
				'min,navn',
				'am,navn',
				'ag,navn');

		$querystring = "
			SELECT * FROM (
					SELECT DISTINCT ON (id) id, navn, min, am, ag 
					FROM (
						SELECT id, navn, true AS min
						FROM Utstyrfilter
						WHERE (accountid = " . addslashes($uid) . ")
						UNION
						SELECT Utstyrfilter.id, Utstyrfilter.navn, (Utstyrfilter.accountid = " . addslashes($uid). ") AS min 
						FROM Utstyrfilter, DefaultFilter, AccountGroup, AccountInGroup
						WHERE (AccountInGroup.accountid = " . addslashes($uid) . ")
						AND (AccountInGroup.groupid = AccountGroup.id)
						AND (AccountGroup.id = DefaultFilter.accountgroupid)
						AND (DefaultFilter.utstyrfilterid = Utstyrfilter.id)
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
								SELECT GruppeTilFilter.utstyrgruppeid AS gid, Utstyrfilter.id AS uid
								FROM Utstyrfilter, GruppeTilFilter
								WHERE (Utstyrfilter.id = GruppeTilFilter.utstyrfilterid)
							     ) AS Gcount 
							GROUP BY uid 
							) AS grupper ON (MineFilter.id = grupper.uid)
					) AS jalla ORDER BY " . $sorts[$sort];

		// print "<pre>" . $querystring . "</pre>";

		if ( $query = pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$utst[$row][0] = $data["id"];		
				$utst[$row][1] = $data["navn"];
				$utst[$row][2] = $data["am"];
				$utst[$row][3] = $data["ag"];
				$utst[$row][4] = $data["min"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $utst;

	}







	// Denne funksjonen returnerer alle filtrene som hører til en bestemt Account.
	function listFiltre_depr($uid, $sort) {
		$filtre = NULL;

#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

		$querystring = "SELECT MineFilter.id, MineFilter.navn, match.am, grupper.ag
			FROM (
					SELECT id, navn
					FROM Utstyrfilter 
					WHERE (Utstyrfilter.accountid = " . addslashes($uid) . ") 
			     ) AS MineFilter LEFT OUTER JOIN (
				     SELECT count(mid) AS am,  uid
				     FROM (
					     SELECT FilterMatch.id AS mid, Utstyrfilter.id AS uid
					     FROM Utstyrfilter, FilterMatch
					     WHERE (Utstyrfilter.accountid = " . addslashes($uid) . ") AND (Utstyrfilter.id = FilterMatch.utstyrfilterid)
					  ) AS Mcount 
				     GROUP BY uid 
				     ) AS match 
			     ON (MineFilter.id = match.uid) 
			     LEFT OUTER JOIN (
					     SELECT count(gid) AS ag, uid
					     FROM (
						     SELECT GruppeTilFilter.utstyrgruppeid AS gid, Utstyrfilter.id AS uid
						     FROM Utstyrfilter, GruppeTilFilter
						     WHERE (Utstyrfilter.accountid = " . addslashes($uid) . ") AND (Utstyrfilter.id = GruppeTilFilter.utstyrfilterid)
						  ) AS Gcount 
					     GROUP BY uid 
					     ) AS grupper 
			     ON (MineFilter.id = grupper.uid) 
			     ORDER BY navn";


		//  print "<p>$querystring";

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$filtre[$row][0] = $data["id"]; 
				$filtre[$row][1] = $data["navn"];
				$filtre[$row][2] = $data["am"];
				$filtre[$row][3] = $data["ag"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $filtre;
	}



	// Denne funksjonen returnerer alle filtrene som hører til administratorene.
	function listFiltreAdm($sort) {
		$filtre = NULL;

#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

		$querystring = "SELECT MineFilter.id, MineFilter.navn, match.am, grupper.ag
			FROM (
					SELECT id, navn
					FROM Utstyrfilter 
					WHERE (Utstyrfilter.accountid is null) 
			     ) AS MineFilter LEFT OUTER JOIN (
				     SELECT count(mid) AS am,  uid
				     FROM (
					     SELECT FilterMatch.id AS mid, Utstyrfilter.id AS uid
					     FROM Utstyrfilter, FilterMatch
					     WHERE (Utstyrfilter.accountid is null) AND (Utstyrfilter.id = FilterMatch.utstyrfilterid)
					  ) AS Mcount 
				     GROUP BY uid 
				     ) AS match 
			     ON (MineFilter.id = match.uid) 
			     LEFT OUTER JOIN (
					     SELECT count(gid) AS ag, uid
					     FROM (
						     SELECT GruppeTilFilter.utstyrgruppeid AS gid, Utstyrfilter.id AS uid
						     FROM Utstyrfilter, GruppeTilFilter
						     WHERE (Utstyrfilter.accountid is null) AND (Utstyrfilter.id = GruppeTilFilter.utstyrfilterid)
						  ) AS Gcount 
					     GROUP BY uid 
					     ) AS grupper 
			     ON (MineFilter.id = grupper.uid) 
			     ORDER BY navn";


		//  print "<p>$querystring";

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$filtre[$row][0] = $data["id"]; 
				$filtre[$row][1] = $data["navn"];
				$filtre[$row][2] = $data["am"];
				$filtre[$row][3] = $data["ag"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $filtre;
	}




	// Denne funksjonen returnerer alle filtrene som hører til en bestemt Account uten unødig krimskrams. untatt de som allerede er valgt.
	function listFiltreFast($uid, $gid, $sort) {
		$filtre = NULL;

		$querystring = "
			SELECT * FROM (
					SELECT DISTINCT ON (id) id, navn, min 
					FROM (
						SELECT id, navn, true AS min
						FROM Utstyrfilter
						WHERE (accountid = " . addslashes($uid) . ")
						UNION
						SELECT Utstyrfilter.id, Utstyrfilter.navn, (Utstyrfilter.accountid = " . addslashes($uid). ") AS min 
						FROM Utstyrfilter, DefaultFilter, AccountGroup, AccountInGroup
						WHERE (AccountInGroup.accountid = " . addslashes($uid) . ")
						AND (AccountInGroup.groupid = AccountGroup.id)
						AND (AccountGroup.id = DefaultFilter.accountgroupid)
						AND (DefaultFilter.utstyrfilterid = Utstyrfilter.id)
					     ) AS MineFilter 
				      ) AS jalla ORDER BY min,navn ";

		//  print "<p>Spørring fast: $querystring";
		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;
			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$filtre[$row][0] = $data["id"];
				if ($data["min"] == 't' ) {
					$filtre[$row][1] = $data["navn"];
				} else {
					$filtre[$row][1] = '(Public) ' . $data["navn"];
				}
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $filtre;
	}



	// Denne funksjonen returnerer alle filtrene som hører til admin Account 
	// uten unødig krimskrams. untatt de som allerede er valgt.
	function listFiltreFastAdm($gid, $sort) {
		$filtre = NULL;

		$querystring = "SELECT Utstyrfilter.id, Utstyrfilter.navn 
			FROM Utstyrfilter 
			WHERE accountid is null 
			EXCEPT SELECT Utstyrfilter.id, Utstyrfilter.navn 
			FROM Utstyrfilter, GruppeTilFilter 
			WHERE (Utstyrfilter.id = GruppeTilFilter.utstyrfilterid) 
			AND (GruppeTilFilter.utstyrgruppeid = " . $gid . ")
			ORDER BY navn";

		//  print "<p>Spørring fast: $querystring";
		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;
			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$filtre[$row][0] = $data["id"]; 
				$filtre[$row][1] = $data["navn"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $filtre;
	}



	// Denne funksjonen returnerer alle filtrene som hører til en bestemt utstyrsgruppe.
	function listFiltreGruppe($gid, $sort) {
		$filtre = NULL;

#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

		$querystring = "SELECT Utstyrfilter.id, Utstyrfilter.navn, GruppeTilFilter.prioritet, GruppeTilFilter.inkluder, GruppeTilFilter.positiv 
			FROM Utstyrfilter, GruppeTilFilter 
			WHERE (Utstyrfilter.id = GruppeTilFilter.utstyrfilterid)
			AND (GruppeTilFilter.utstyrgruppeid = " . addslashes($gid) . ") 
			ORDER BY prioritet";

		//print "<p>$querystring";

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;
			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$filtre[$row][0] = $data["id"]; 
				$filtre[$row][1] = $data["navn"];
				$filtre[$row][2] = $data["prioritet"];
				$filtre[$row][3] = $data["inkluder"];
				$filtre[$row][4] = $data["positiv"];
				$row++;
			} 

		}  else {
			$error = new Error(2);
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
				'verdi');

		$querystring = "SELECT id, MatchField.name, matchtype, verdi 
			FROM FilterMatch, MatchField 
			WHERE utstyrfilterid = " . addslashes($fid) . 
			" AND FilterMatch.matchfelt = MatchField.matchfieldid" .
			" ORDER BY " . $sorts[$sort];

		//print "<p>$querystring";

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$match[$row][0] = $data["id"]; 
				$match[$row][1] = $data["name"];
				$match[$row][2] = $data["matchtype"];
				$match[$row][3] = $data["verdi"];
				$row++;
			} 
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}

		return $match;
	}


	// Henter ut informasjon om en periode..
	function periodeInfo($tid) {

		$querystring = "SELECT helg, date_part('hour', Tidsperiode.starttid) AS time , date_part('minute', Tidsperiode.starttid) AS minutt " .
			"FROM Tidsperiode WHERE (id = " . addslashes($tid) . ")"; 

		//    print "<p>$querystring";

		if ( $query = @pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
			$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
			$perioder[0] = $data["helg"];
			$perioder[1] = $data["time"];
			$perioder[2] = $data["minutt"];
		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasesp&oslash;rring. Fant ikke periode.";
		}

		return $perioder;
	}

	// Henter ut informasjon om en periode..
	function hentwapkey($uid) {

		$querystring = "SELECT value FROM AccountProperty 
			WHERE (accountid = " . addslashes($uid) . ") AND (property = 'wapkey')"; 

			//    print "<p>$querystring";

			if ( $query = @pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1) {
				$data = pg_fetch_array($query, 0, PGSQL_ASSOC);
				$key[0] = $data["value"];
			} else {
				$key = null;
			}

		return $key;
	}

	function settwapkey($uid, $key) {
		$oldkey = $this->hentwapkey($uid);
		//	$oldkey = "null";
		if ($oldkey == null) {
			// Spxrring som legger inn i databasen
			$querystring = "INSERT INTO AccountProperty (accountid, property, value) VALUES (" . addslashes($uid) . ", 'wapkey', '" . addslashes($key) . "')";    
			$query = pg_exec( $this->connection, $querystring);

		} else {
			$querystr = "UPDATE AccountProperty SET value = '" . addslashes($key) . "' WHERE accountid = " . addslashes($uid) . " AND property = 'wapkey' ";
			@pg_exec($this->connection, $querystr);
		}

	}

	function slettwapkey($uid) {
		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM AccountProperty WHERE ( accountid = " . addslashes($uid) . " AND property = 'wapkey')";
#    print "<p>QUERY:$querystring:";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	function slettMatchField($mfid) {
		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM MatchField WHERE ( matchfieldid = " . addslashes($mfid) . " )";
#    print "<p>QUERY:$querystring:";
#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}


	// Endre navn på profil
	function endreProfil($pid, $navn, $ukedag, $uketidh, $uketidm, $tidh, $tidm) {
		$querystr = "UPDATE Brukerprofil SET navn = '" . addslashes($navn) . "' WHERE id = " . addslashes($pid);
		@pg_exec($this->connection, $querystr);

		$querystr = "UPDATE Brukerprofil SET ukedag = " . addslashes($ukedag) . " WHERE id = " . addslashes($pid);	
		@pg_exec($this->connection, $querystr);

		$querystr = "UPDATE Brukerprofil SET uketid = '" . 
			addslashes($uketidh) . ":" . addslashes($uketidm) .
			"' WHERE id = " . addslashes($pid);		
		@pg_exec($this->connection, $querystr);

		$querystr = "UPDATE Brukerprofil SET tid = '" . 
			addslashes($tidh) . ":" . addslashes($tidm) .
			"' WHERE id = " . addslashes($pid);
		@pg_exec($this->connection, $querystr);
	}

	// Endre detaljer om en filter
	function endreFilter($fid, $navn) {
		$querystr = "UPDATE Utstyrfilter SET navn = '" . addslashes($navn) . "' WHERE id = " . addslashes($fid);
		@pg_exec($this->connection, $querystr);

	}

	// Endre detaljer om en tidsperiode
	function endrePeriodeinfo($tid, $helg, $time, $minutt) {
		$querystr = "UPDATE Tidsperiode SET helg = " . addslashes($helg) . " WHERE id = " . addslashes($tid);
		@pg_exec($this->connection, $querystr);
		$querystr = "UPDATE Tidsperiode SET starttid = '" . addslashes($time) . ":" . addslashes($minutt) . "' WHERE id = " . addslashes($tid);
		@pg_exec($this->connection, $querystr);
	}

	// Endre detaljer om et utstyrgruppe
	function endreUtstyrgruppe($gid, $navn, $descr) {
		$querystr = "UPDATE Utstyrgruppe SET navn = '" . addslashes($navn) . "' WHERE id = " . addslashes($gid);
		//print "<p>" . $querystr;
		@pg_exec($this->connection, $querystr);
		$querystr = "UPDATE Utstyrgruppe SET descr = '" . addslashes($descr) . "' WHERE id = " . addslashes($gid);
		//print "<p>" . $querystr;	
		@pg_exec($this->connection, $querystr);
	}


	// Endre detaljer om en brukergruppe
	function endreBrukergruppe($gid, $navn, $descr) {
		$querystr = "UPDATE AccountGroup SET name = '" . addslashes($navn) . "' WHERE id = " . addslashes($gid);
		@pg_exec($this->connection, $querystr);
		$querystr = "UPDATE AccountGroup SET descr = '" . addslashes($descr) . "' WHERE id = " . addslashes($gid);
		@pg_exec($this->connection, $querystr);
	}

	// Endre detaljer om en adresse
	function endreAdresse($aid, $type, $adr) {
		$querystr = "UPDATE Alarmadresse SET type = '" . addslashes($type) . "' WHERE id = " . addslashes($aid);
		@pg_exec($this->connection, $querystr);
		$querystr = "UPDATE Alarmadresse SET adresse = '" . addslashes($adr) . "' WHERE id = " . addslashes($aid);
		@pg_exec($this->connection, $querystr);
	}


	// Endre brukerinfo
	function endreBruker($uid, $brukernavn, $navn, $passord, $admin, $sms, $kolengde) {
		$querystr = "UPDATE Account SET login = '" . addslashes($brukernavn) . "' WHERE id = " . addslashes($uid);
		@pg_exec($this->connection, $querystr);

		$querystr = "UPDATE Account SET name = '" . addslashes($navn) . "' WHERE id = " . addslashes($uid);
		@pg_exec($this->connection, $querystr);

		$querystr = "UPDATE Account SET password = '" . addslashes($passord) . "' WHERE id = " . addslashes($uid);
		if ($passord != undef && strlen($passord) > 0) {
			@pg_exec($this->connection, $querystr);
		}	
		/*	
			if ($sms == 1) $s = "true"; else $s = "false";
			$querystr = "UPDATE Preference SET sms = " . addslashes($s) . " WHERE accountid = " . addslashes($uid);
			@pg_exec($this->connection, $querystr);

			$querystr = "UPDATE Preference SET admin = " . addslashes($admin) . " WHERE accountid = " . addslashes($uid);
			@pg_exec($this->connection, $querystr);	
		 */
		$querystr = "UPDATE Preference SET queuelength = '" . addslashes($kolengde) . " days' WHERE accountid = " . addslashes($uid);
		@pg_exec($this->connection, $querystr);

	}

	// Endre passord
	function endrepassord($brukernavn, $passwd) {
		$querystr = "UPDATE Account SET password = '" . addslashes($passwd) . 
			"' WHERE login = '" . addslashes($brukernavn) . "'";
		@pg_exec($this->connection, $querystr);


	}


	// Endre språk
	function setlang($brukerid, $lang) {
		$querystr = "DELETE FROM AccountProperty WHERE property = 'language' AND accountid = '" . addslashes($brukerid) . "'";
		@pg_exec($this->connection, $querystr);

		$querystr = "INSERT INTO AccountProperty (accountid, property, value) VALUES (" . 
			addslashes($brukerid) . ", 'language', '" . addslashes($lang) . "')";
		@pg_exec($this->connection, $querystr);

	}


	// Legge til eller endre en varslingsadresse for en periode
	function endreVarsleadresse($tid, $adresseid, $utstyrgruppeid, $type) {

		$querystr = "DELETE FROM Varsle WHERE tidsperiodeid = " . addslashes($tid) . " AND alarmadresseid = " . addslashes($adresseid) .
			" AND utstyrgruppeid = " . addslashes($utstyrgruppeid);

		pg_exec($this->connection, $querystr);

		if ( $type < 4 ) {
			$querystr = "INSERT INTO Varsle (tidsperiodeid, alarmadresseid, utstyrgruppeid, vent) VALUES (" . 
				addslashes($tid) . ", " . addslashes($adresseid) . ", " . $utstyrgruppeid . ", " . $type . ")";
			pg_exec($this->connection, $querystr);
		}

	}


	// Legge til eller endre en brukertilgruppe
	function endreBrukerTilGruppe($uid, $gid, $type) {

		$querystr = "DELETE FROM AccountInGroup WHERE accountid = " . addslashes($uid) . " AND groupid = " . addslashes($gid);
		@pg_exec($this->connection, $querystr);

		//	print "<p>Query: $querystr";
		if ( $type ) {
			$querystr = "INSERT INTO AccountInGroup (accountid, groupid) VALUES (" . addslashes($uid) . ", " . addslashes($gid) . ") ";
			//	print "<p>Query: $querystr<p>&npsp;$gid ---";		
			@pg_exec($this->connection, $querystr);
		}

	}

	// Legge til eller endre en rettighet
	function endreRettighet($gid, $ugid, $type) {


		$querystr = "DELETE FROM Rettighet WHERE accountgroupid = " . addslashes($gid) . " AND utstyrgruppeid = " . addslashes($ugid);
		@pg_exec($this->connection, $querystr);
		//	print "<p>Query: $querystr";	
		if ( $type ) {
			$querystr = "INSERT INTO Rettighet (accountgroupid, utstyrgruppeid) VALUES (" . addslashes($gid) . ", " . addslashes($ugid) . " )";		
			@pg_exec($this->connection, $querystr);
		}

	}

	// Legge til eller endre en defaultustyr
	function endreDefault($gid, $ugid, $type) {


		$querystr = "DELETE FROM DefaultUtstyr WHERE accountgroupid = " . addslashes($gid) . " AND utstyrgruppeid = " . addslashes($ugid);
		@pg_exec($this->connection, $querystr);
		//	print "<p>Query: $querystr";	
		if ( $type ) {
			$querystr = "INSERT INTO DefaultUtstyr (accountgroupid, utstyrgruppeid) VALUES (" . addslashes($gid) . ", " . addslashes($ugid) . " )";
			//	print "<p>Query: $querystr";			
			@pg_exec($this->connection, $querystr);
		}

	}

	// Legge til eller endre en default filter
	function endreDefaultFilter($gid, $fid, $type) {


		$querystr = "DELETE FROM DefaultFilter WHERE accountgroupid = " . addslashes($gid) . " AND utstyrfilterid = " . addslashes($fid);
		@pg_exec($this->connection, $querystr);
		/* 	print "<p>Query: $querystr";	 */
		if ( $type ) {
			$querystr = "INSERT INTO DefaultFilter (accountgroupid, utstyrfilterid) VALUES (" . addslashes($gid) . ", " . addslashes($fid) . " )";
			/* 	print "<p>Query: $querystr";			 */
			@pg_exec($this->connection, $querystr);
		}

	}





	// Bytte rekkefølgen på to prioriteter for filtre i en utstyrsgruppe
	function swapFilter($gid, $a, $b, $ap, $bp) {

		$querystr = "UPDATE GruppeTilFilter SET prioritet = " . addslashes($bp) . 
			" WHERE (utstyrgruppeid = " . $gid . ") AND (utstyrfilterid = " . $a . ") ";
		pg_exec($this->connection, $querystr);

		//	print "<p>Query: $querystr";

		$querystr = "UPDATE GruppeTilFilter SET prioritet = " . addslashes($ap) . 
			" WHERE (utstyrgruppeid = " . $gid . ") AND (utstyrfilterid = " . $b . ") ";
		pg_exec($this->connection, $querystr);

		//	print "<p>Query: $querystr";

	}


	// opprette ny bruker
	function nyBruker( $navn, $brukernavn, $passord, $admin, $sms, $kolengde, $error ) {

		//if ( $sms   == 1 ) { $sms = 'true'; } else { $sms = 'false'; }

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Account (name, login, password) VALUES ('" . 
			addslashes($navn) . "', '" . addslashes($brukernavn) . "', '" .
			addslashes($passord) . "') ";

#    print "<p>query: $querystring";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM Account WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);

			// Spxrring som legger inn i databasen
			$querystring = "INSERT INTO Preference (accountid, queuelength) VALUES (" . 
				$idrow[0] . ", '" . addslashes($kolengde) . " days') ";

			pg_exec( $this->connection, $querystring);

			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			$error = new Error(2);
			$error->SetMessage("Brukernavn allerede i bruk. Forsøk på nytt med et annet brukernavn.");
			return 0;
		}

	}



	// opprette ny brukergruppe
	function nyBrukerGruppe( $navn, $descr ) {

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO AccountGroup (name, descr) VALUES ('" . 
			addslashes($navn) . "', '" . addslashes($descr) . "') ";

#    print "<p>query: $querystring";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM AccountGroup WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			$error = new Error(2);
			$error->SetMessage("feil med databaseinnlegging av brukergruppe.");
			return 0;
		}

	}




	// opprette ny tidsperiode
	function nyTidsperiode($helg, $tid, $profilid) {
		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Tidsperiode (id, helg, starttid, brukerprofilid) VALUES (" . 
			"nextval('tidsperiode_id_seq'), " . addslashes($helg) . ", '" . 
			addslashes($tid) ."', " . addslashes($profilid) . ")";

		//print '<p>Nytidsperiode:' . $querystring;

		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM Tidsperiode WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			return 0;
		}

	}

	// opprette ny adresse
	function nyAdresse($adresse, $adressetype, $brukerid) {

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Alarmadresse (id, accountid, adresse, type) VALUES (" . 
			"nextval('alarmadresse_id_seq'), " . addslashes($brukerid) . ", '" . 
			addslashes($adresse) ."', " . addslashes($adressetype) . " )";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM Alarmadresse WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}



	// opprette ny hendelse i loggen
	function nyLogghendelse($brukerid, $type, $descr) {

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Logg (accountid, type, descr, tid) VALUES (" . 
			addslashes($brukerid) . ", " . addslashes($type) .", '" . 
			addslashes($descr) . "', current_timestamp )";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}




	// opprette ny profil
	function nyProfil($navn, $brukerid, $ukedag, $uketidh, $uketidm, $tidh, $tidm) {

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Brukerprofil (id, accountid, navn, ukedag, uketid, tid) VALUES (" . 
			"nextval('brukerprofil_id_seq'), " . $brukerid . ", '" . 
			addslashes($navn) ."', " . addslashes($ukedag) . ", '" . 
			addslashes($uketidh) . ":" . addslashes($uketidm) . "', '" .
			addslashes($tidh) . ":" . addslashes($tidm) . "' " .
			" )";

		//echo "<p>query: $querystring";
		if ($query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_last_oid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM Brukerprofil WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			return 0;
		}

	}



	// opprette nytt filter
	function nyttFilter($navn, $brukerid) {

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Utstyrfilter (id, accountid, navn) VALUES (" . 
			"nextval('utstyrfilter_id_seq'), " . addslashes($brukerid) . ", '" . 
			addslashes($navn) ."' )";

#    print "<p>query: $querystring";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM Utstyrfilter WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			return 0;
		}

	}


	// opprette nytt adm- filter
	function nyttFilterAdm($navn) {

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Utstyrfilter (id, accountid, navn) VALUES (" . 
			"nextval('utstyrfilter_id_seq'), null, '" . 
			addslashes($navn) ."' )";

#    print "<p>query: $querystring";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM Utstyrfilter WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			return 0;
		}

	}


	function extrval($value) {
		if ($value == "." || $value == 'undef') {
			return "null";
		} else {
			return "'" . addslashes($value) . "'";
		}
	}

	// opprette nytt matchfelt
	function nyttMatchFelt($name, $descr, $qvaluehelp, $qvalueid, $qvaluename, $qvaluecategory, $qvaluesort, $listlimit, $showlist, $datatype) {

		$ivalueid 		= $this->extrval($qvalueid);
		$ivaluename 	= $this->extrval($qvaluename);
		$ivaluecategory 	= $this->extrval($qvaluecategory);
		$ivaluesort 	= $this->extrval($qvaluesort);
		$ivaluehelp		= $this->extrval($qvaluehelp);
		$idescr		= $this->extrval($descr);
		$iname		= $this->extrval($name);

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO MatchField (name, descr, valuehelp, valueid, valuename, valuecategory, valuesort, listlimit, showlist, datatype) VALUES (" .
			$iname . ", " . $idescr . ", " . $ivaluehelp . ", " . $ivalueid . ", " . 
			$ivaluename . ", " . $ivaluecategory . ", " . $ivaluesort . ", " .
			addslashes($listlimit) . ", " . $showlist . ", " . addslashes($datatype) . " )";

		// print "<p>query: $querystring";

		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT matchfieldid FROM MatchField WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			return 0;
		}

	}



	// legge til eksisterende filter til utstyrsgruppe
	function nyttGrpFilter($gid, $fid, $inkluder, $positiv) {


		if ($inkluder == 1) { $inkl = "true"; } else { $inkl = "false"; }
		if ($positiv == 1) { $neg = "true"; } else { $neg = "false"; }	

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO GruppeTilFilter (utstyrgruppeid, utstyrfilterid, inkluder, positiv, prioritet) 
			SELECT " . addslashes($gid) . ", " . addslashes($fid) . ", " . $inkl . ", " . $neg . 
			" ,1 + max(prioritet) 
			FROM ( SELECT prioritet FROM GruppeTilFilter WHERE (utstyrgruppeid = " . addslashes($gid) . ")
					UNION SELECT 0 AS prioritet) AS x";

#print "<p>query: $querystring";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT utstyrfilterid FROM GruppeTilFilter WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			return 0;
		}

	}



	// opprette ny match
	function nyMatch($matchfelt, $matchtype, $verdi, $fid) {
		/* 	addslashes($verdi); */
		/* 	$v = preg_replace('/\\{2}/', '-', $verdi); */
		/* 	print "<pre>før:$verdi \n slashed:" . $verdi . "\n stripped: $v \n</pre>"; */
		/* 	print "Magic" .  get_magic_quotes_gpc() ; */
		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO FilterMatch (id, matchfelt, matchtype, utstyrfilterid, verdi) VALUES (" . 
			"nextval('filtermatch_id_seq'), " . addslashes($matchfelt) . ", " . 
			addslashes($matchtype) .", " . addslashes($fid) . ", '" . 
			$verdi . "' )";

		// echo "<p>query: $querystring";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM FilterMatch WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			return 0;
		}

	}


	// opprette ny utstyrsgruppe
	function nyUtstyrgruppe($uid, $navn, $descr, $basertpaa) {


		// Legg inn ny utstyrsgruppe i databasen

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Utstyrgruppe (id, accountid, navn, descr) VALUES (" . 
			"nextval('filtermatch_id_seq'), " . addslashes($uid) . ", '" . 
			addslashes($navn) ."', '" . addslashes($descr) . "' )";

		// print "<p>query: $querystring";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM Utstyrgruppe WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);

			$nyutstgrpid = $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			return 0;
		}


		// Legge inn utstyrsfiltre hvis utstyrsgruppen skal være basert på en annen.
		if ($basertpaa > 0 ) {
			$utstgrinfo = $this->utstyrgruppeInfoAdv($basertpaa, $uid);

			// Hvis utstyrfiltergruppa som den skal baseres på er min egen :
			if ($utstgrinfo[2] ) {
				$querystring = "INSERT INTO 
					GruppeTilFilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) 
					SELECT inkluder, positiv, prioritet, utstyrfilterid, " . $nyutstgrpid . "  
					FROM GruppeTilFilter WHERE (utstyrgruppeid = " . addslashes($basertpaa) . ")";

				//echo "<pre>" . $querystring . "</pre>";
				if ( $query = pg_exec( $this->connection, $querystring)) { 
					//echo "<p>funka fint dette (12)...";
					return 1;
				}
			} else {
				// Hvis ikke utstyrsfiltergruppa som det skal baseres på er egen,
				// må filtermatchene også klones.

				// Legger inn alle utstyrsgrupper som må arves
				$arvefilter = $this->listFiltreGruppe($basertpaa, 0);
				foreach ($arvefilter AS $arvfilterelement) {
					//echo "<p>Kloner utstyrsfilter " . $arvfilterelement[0];

					// utstyrfilterid inneholder utstyrfilterid for både den orginale og 
					// den klonede utstyrsfilteret.
					$utstyrfilteridlist[] = array(
							$this->nyttFilter($arvfilterelement[1], $uid) ,
							$arvfilterelement[0]
							);

				}
				/* Variabler:
				 *  $ustyrfilterid[1]    utstyrfilterid orginalt utstyrsfilter
				 *  $ustyrfilterid[0]    utstyrfilterid nytt/klonet utstyrsfilter
				 *  $basertpaa           utstyrgruppeid orginal utstyrgruppe
				 *  $nyutstgrpid         utstyrgruppeid ny/klonet utstyrgruppe
				 */

				// Legger inn referanser fra den nye utstyrsgruppen til de nye klonede filtrene.
				foreach ($utstyrfilteridlist AS $utstyrfilterid) {
					/*
					   echo "<p>DEBUG<br>Lager referanse til utstyrsfilter<br>" . 
					   "gammel: " . $utstyrfilterid[1] . 
					   "<br>ny: " . $utstyrfilterid[0] . 
					   "<br>utstyrgruppe gammel : " .  $basertpaa .
					   "<br>utstyrgruppe ny : " . $nyutstgrpid;
					 */
					$querystring = "INSERT INTO 
						GruppeTilFilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) 
						SELECT inkluder, positiv, prioritet, " . $utstyrfilterid[0] . ", " . $nyutstgrpid . "  
						FROM GruppeTilFilter WHERE (utstyrgruppeid = " . addslashes($basertpaa) . ") AND 
						(utstyrfilterid = " . $utstyrfilterid[1] . ")";
					//echo "<p>Query:<br><PRE>" . $querystring . "</PRE>";
					if ( $query = pg_exec( $this->connection, $querystring)) { 
						// echo "<p>funka fint dette (13)...";
					}

				}

				// Traversere utstyrsfiltre som skal arves for å finne filtermatcher som skal arves
				foreach ($utstyrfilteridlist AS $utstyrfilterid) {
					//echo "<p>Henter inn match fra utstyrfilter:" . $utstyrfilterid[1];
					//$arvematcher = $this->listMatch($utstyrfilterid[1],0);
					//foreach ($arvematcher AS $arvematch) {
					//echo "<p>Kloner matcher... ";
					$querystring = "INSERT INTO 
						FilterMatch (matchfelt, matchtype, verdi, utstyrfilterid) 
						SELECT matchfelt, matchtype, verdi, " . $utstyrfilterid[0] . " 
						FROM FilterMatch WHERE (utstyrfilterid = " . $utstyrfilterid[1] . ")";
					//echo "<p> Query:<br><PRE>" . $querystring . "</PRE>";
					if ( $query = pg_exec( $this->connection, $querystring)) { 
						//    echo "<p>funka fint dette (14)...";
					}                    
					//}
				}

				// 

			}


		} else {
			return $nyutstgrpid;
		}

	}

	// opprette ny utstyrsgruppe administrator
	function nyUtstyrgruppeAdm($navn, $descr) {

		// Spxrring som legger inn i databasen
		$querystring = "INSERT INTO Utstyrgruppe (id, accountid, navn, descr) VALUES (" . 
			"nextval('filtermatch_id_seq'), null, '" . 
			addslashes($navn) ."', '" . addslashes($descr) . "' )";

		//    print "<p>query: $querystring";
		if ( $query = pg_exec( $this->connection, $querystring)) {

			// Henter ut object id`n til raden.
			$oid = pg_getlastoid($query);

			// Henter ut id`n til raden og returnerer den.
			$idres = pg_exec( $this->connection, "SELECT id FROM Utstyrgruppe WHERE oid = $oid");
			$idrow = pg_fetch_row($idres, 0);
			return $idrow[0];
		} else {
			// fikk ikke til e legge i databasen
			return 0;
		}

	}




	// slette en adresse
	function slettAdresse($aid) {

		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM Alarmadresse WHERE ( id = " . addslashes($aid) . " )";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en profil
	function slettProfil($pid) {

		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM Brukerprofil WHERE ( id = " . addslashes($pid) . " )";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}


	// slette en bruker
	function slettBruker($uid) {

		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM Account WHERE ( id = " . addslashes($uid) . " )";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}  


	// slette en brukergruppe
	function slettBrukergruppe($gid) {

		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM AccountGroup WHERE ( id = " . addslashes($gid) . " )";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en utstyrsgruppe
	function slettUtstyrgruppe($gid) {

		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM Utstyrgruppe WHERE ( id = " . addslashes($gid) . " )";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en brukergruppe
	function slettPeriode($pid) {

		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM Tidsperiode WHERE ( id = " . addslashes($pid) . " )";
#    print "<p>QUERY:$querystring:";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en brukergruppe
	function slettGrpFilter($gid, $fid) {

		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM gruppetilfilter WHERE ( utstyrgruppeid = " . addslashes($gid) . 
			"AND  utstyrfilterid = " . $fid . ")";
#    print "<p>QUERY:$querystring:";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}


	// slette en filter til match relasjon
	function slettFiltermatch($fid, $mid) {

		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM FilterMatch WHERE ( id = " . addslashes($mid) . 
			"AND  utstyrfilterid = " . $fid . ")";
#    print "<p>QUERY:$querystring:";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// slette en brukergruppe
	function slettFilter($fid) {

		// Spxrring som legger inn i databasen
		$querystring = "DELETE FROM Utstyrfilter WHERE ( id = " . addslashes($fid) . " )";
#    print "<p>QUERY:$querystring:";

#print "<p>query: $querystring\n brukerid: $brukerid";
		if ( $query = pg_exec( $this->connection, $querystring)) {
			return 1;
		} else {
			// fikk ikke til å legge i databasen
			return 0;
		}

	}

	// sett en profil som aktiv for en bestemt bruker
	function aktivProfil($brukerid, $profilid) {

		if ($profilid == 0) { $profilid = "null"; }
		// Spxrring som legger inn i databasen
		$querystring = "UPDATE Preference SET activeprofile = " . addslashes($profilid) . " WHERE " .
			"accountid = " . addslashes($brukerid) . "  ";

#print "<p>query: $querystring";
		if ( $query = pg_exec( $this->connection, $querystring) ) {
			return 1;
		} else {
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
		$querystring = "SELECT $vid, $vname $vc " . 
			"FROM $vtabell " .
			"ORDER BY $vsort LIMIT " . addslashes($limit);

		//echo "<p>query: " . $querystring;

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);

				$scat = (isset($vcat) && $vcat && isset($data[$vcat])) ? $data[$vcat] : 0;

				$namestring = $vntemplate;
				$namestring = preg_replace('/(\[NAME\])/', $data[$vname], $namestring);
				$namestring = preg_replace('/(\[ID\])/', $data[$vid], $namestring);
				$namestring = preg_replace('/(\[GROUP\])/', $scat, $namestring);


				if (!isset($verdier[$scat] )) { $verdier[$scat] = null; }
				$verdier[$scat][$row] = array($data[$vid], $namestring);
				$row++;
			}

		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}
		/* 	echo '<pre>'; */
		/*     print_r($verdier); */
		/*    echo '</pre>'; */

		return $verdier;  

	}


	function listFelter() {

		$felter = null;

		$querystring = "SELECT c.relname, a.attname, t.typname 
			FROM pg_class c, pg_attribute a, pg_type t, pg_tables tb 
			WHERE a.attnum > 0 AND a.attrelid = c.oid AND a.atttypid = t.oid AND 
			c.relname = tb.tablename AND tablename not like 'pg_%' 
			ORDER BY c.relname, a.attname;";

		//echo "<p>query: " . $querystring;

		if ( $query = @pg_exec($this->connection, $querystring) ) {
			$tot = pg_numrows($query); $row = 0;

			while ( $row < $tot) {
				$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
				$felter[$data['relname']][$row][0] = $data['attname'];
				$felter[$data['relname']][$row][1] = $data['typname'];
				$row++;
			}

		}  else {
			$error = new Error(2);
			$bruker{'errmsg'}= "Feil med datbasespørring.";
		}


		return $felter;  

	}




}


?>
