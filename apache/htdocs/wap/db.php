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
		$querystring = "SELECT brukernavn, wapkey.brukerid, bruker.navn FROM wapkey, bruker WHERE (key = '" . addslashes($wapkey) . "') " .
			"AND (bruker.id = wapkey.brukerid) "; 

		#print "<p> " . $querystring . "</p>";

		if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1) {
			$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
			$uid = $data["brukerid"];
			$brukernavn = $data["brukernavn"];
			$navn = $data["navn"];
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

  	$querystring = "SELECT (Bruker.aktivprofil = Brukerprofil.id) AS aktiv, " .
      "Brukerprofil.id, Brukerprofil.navn, Q.antall " .
  	  "FROM Bruker, Brukerprofil LEFT OUTER JOIN " .
      "(SELECT pid, count(tid) AS antall FROM " .
      "(SELECT Tidsperiode.id AS tid, Brukerprofil.id AS pid FROM Tidsperiode, Brukerprofil " .
      "WHERE (Brukerprofil.brukerid = " . addslashes($uid) . 
      ") AND (Brukerprofil.id = Tidsperiode.brukerprofilid) ) AS Perioder " .
      "GROUP BY Perioder.pid ) AS Q " .
      "ON (Brukerprofil.id = Q.pid) " .
      "WHERE (Brukerprofil.brukerid = " . addslashes($uid) . ") AND (Bruker.id = Brukerprofil.brukerid)" .
      "ORDER BY aktiv DESC, Brukerprofil.navn" ;

#    print "<p>$querystring";

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

  // opprette ny hendelse i loggen
  function nyLogghendelse($brukerid, $type, $descr) {

    // Spxrring som legger inn i databasen
    $querystring = "INSERT INTO Logg (brukerid, type, descr, tid) VALUES (" . 
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
    $querystring = "UPDATE Bruker SET aktivProfil = " . addslashes($profilid) . " WHERE " .
      " id = " . addslashes($uid) . "  ";
    
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
