<?php
/*
 * db.php
 * (c) Andreas Åkre Solberg (andrs@uninett.no) - Januar, 2003
 *
 * Dette er et bibliotek for aksessering av databasen for bruk for administrering av brukerdatabasen og
 * profilene til brukerne.
 *
 */

class WDBH {

	// MÂ ha inn en ferdig oppkoblet databasekobling til postgres
	var $connection;

	// Konstruktor
	function WDBH($connection) {
		$this->connection = $connection;
	}
  
	// Henter ut informasjon om en periode..
	function sjekkwapkey($wapkey) {
    
            $uid = 0;
            $querystring = "SELECT Account.login as al, Account.id as aid, Accountproperty.value, account.name as aname FROM AccountProperty WHERE (property = 'wapkey') AND 
(value = '" . addslashes($wapkey) . "') AND 
(account.id = accountproperty.accountid) ";

		#print "<p> " . $querystring . "</p>";

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1) {
			$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
			$uid = $data["aid"];
			$brukernavn = $data["al"];
			$navn = $data["aname"];
		}
    
	 	return array($uid, $brukernavn, $navn);
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
    
   #print "<p>query: $querystring";
    if ( $query = pg_exec( $this->connection, $querystring) ) {
      return 1;
    } else {
      // fikk ikke til å legge i databasen
      return 0;
    }

  }





}

?>
