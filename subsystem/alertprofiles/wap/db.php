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
SELECT Account.login as al, Account.id as aid, Accountproperty.value, account.name as aname, preference.activeprofile as ap  
FROM AccountProperty, Account, Preference  
WHERE (property = 'wapkey') AND 
	(value = '" . addslashes($wapkey) . "') AND 
	(account.id = accountproperty.accountid) AND
	(account.id = preference.accountid) ";

		#print "<p> " . $querystring . "</p>";

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1) {
			$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
			$uid = $data["aid"];
			$brukernavn = $data["al"];
			$navn = $data["aname"];
			$aktivprofil = $data["ap"];
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

  	$querystring = "
SELECT (Preference.activeProfile = Brukerprofil.id) AS aktiv, 
    Brukerprofil.id, Brukerprofil.navn, Q.antall 
FROM Account, Preference, Brukerprofil LEFT OUTER JOIN 
(SELECT pid, count(tid) AS antall FROM 
    (SELECT Tidsperiode.id AS tid, Brukerprofil.id AS pid FROM Tidsperiode, Brukerprofil 
        WHERE (Brukerprofil.accountid = " . addslashes($uid) . "
        ) AND (Brukerprofil.id = Tidsperiode.brukerprofilid) ) AS Perioder 
    GROUP BY Perioder.pid ) AS Q 
    ON (Brukerprofil.id = Q.pid) 
WHERE (Brukerprofil.accountid = " . addslashes($uid) . ") AND 
(Account.id = Brukerprofil.accountid) AND 
(Account.id = Preference.accountid) 
ORDER BY aktiv DESC, Brukerprofil.navn" ;

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
	}
    
    return $profiler;
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
  

  function aktivProfil($uid, $profilid) {

    // Spxrring som legger inn i databasen
    $querystring = "UPDATE Preference SET activeProfile = " . addslashes($profilid) . " WHERE " .
      " accountid = " . addslashes($uid) . "  ";
    
   //echo "<p>query: $querystring";
    if ( $query = pg_exec( $this->connection, $querystring) ) {
      return 1;
    } else {
      // fikk ikke til å legge i databasen
      return 0;
    }

  }





}

?>
