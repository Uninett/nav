<?php
/*
 * databasehandler.php
 * (c) Andreas Åkre Solberg (andrs@uninett.no) - Juli, 2002
 *
 * Dette er et bibliotek for aksessering av databasen for bruk for administrering av brukerdatabasen og
 * profilene til brukerne.
 *
 */

class DBH {

  // MÂ ha inn en ferdig oppkoblet databasekobling til postgres
  var $connection;

  // Konstruktor
  function DBH($connection) {
    $this->connection = $connection;
  }
  
  function listBrukere($sort) {
    
    $brukere = NULL;
    
    $sorts = array ('brukernavn',
		    'navn',
		    'admin, navn',
		    'sms, navn',
		    'kolengde, navn',
		    'pa, navn',
		    'aa, navn');
		    
    $querystring = "SELECT Bruker.id, Bruker.brukernavn, Bruker.navn, Bruker.admin, Bruker.sms, Bruker.kolengde, " .
      "profiler.pa, adresser.aa FROM Bruker LEFT OUTER JOIN " .
      "(SELECT count(Brukerprofil.id) AS pa, Brukerprofil.brukerid AS uid " . 
      "FROM Brukerprofil GROUP BY (Brukerprofil.brukerid)) AS profiler ON (Bruker.id = profiler.uid) " .
      "LEFT OUTER JOIN " .
      "(SELECT count(Alarmadresse.id) AS aa, Alarmadresse.brukerid AS uid " .
      "FROM Alarmadresse GROUP BY (Alarmadresse.brukerid)) AS adresser ON (Bruker.id = adresser.uid) " .
      "ORDER BY " . $sorts[$sort];

    if ( $query = @pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

	while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$brukere[$row][0] = $data["id"];
		$brukere[$row][1] = $data["brukernavn"];
		$brukere[$row][2] = $data["navn"];
		$brukere[$row][3] = $data["admin"];
		$brukere[$row][4] = $data["sms"];
		$brukere[$row][5] = $data["pa"];
		$brukere[$row][6] = $data["aa"];
		$brukere[$row][7] = $data["kolengde"];
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
    
   		$sorts = array ('brukernavn',
			'navn',
		    'admin, navn',
		    'sms, navn',
		    'pa, navn',
		    'aa, navn');
		    
    	$querystring = "SELECT id, brukernavn, navn, (Medlem.gruppeid > 0) AS medlem 
FROM Bruker LEFT OUTER JOIN ( 
	SELECT gruppeid, brukerid 
	FROM BrukerTilGruppe 
	WHERE (gruppeid = " . addslashes($gid) . ") 
) AS Medlem 
ON (Bruker.id = Medlem.brukerid) 
ORDER BY " . $sorts[$sort];

    if ( $query = @pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

	while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$brukere[$row][0] = $data["id"];
		$brukere[$row][1] = $data["brukernavn"];
		$brukere[$row][2] = $data["navn"];
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
		    'Bruker.navn, tid DESC',
		    'tid DESC',
		    'Logg.descr, tid DESC');
		    
	$querystring = "SELECT Logg.type, Logg.descr, date_part('epoch', Logg.tid) AS tid, Bruker.navn 
FROM Bruker, Logg 
WHERE (	Bruker.id = Logg.brukerid ) 
ORDER BY " . $sorts[$sort] . " LIMIT 100";

	//print "<pre>" . $querystring . "</pre>";

    if ( $query = pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

	while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$logg[$row][0] = $data["type"];
		$logg[$row][1] = $data["descr"];
		$logg[$row][2] = $data["tid"];
		$logg[$row][3] = $data["navn"];
		$row++;
      } 
    } 
    
    return $logg;
  }






  function listBrukerGrupper($sort) {
    
    $brukere = NULL;
    
    $sorts = array ('navn',
		    'ab, navn',
		    'ar, navn',
		    'ad, navn');
		    
	$querystring = "SELECT id, navn, descr, BCount.ab, Rcount.ar, Dcount.ad 
FROM Brukergruppe 
LEFT OUTER JOIN (
	SELECT count(brukerid) AS ab, gruppeid
	FROM BrukerTilGruppe
	GROUP BY gruppeid
) AS BCount 
ON (id = BCount.gruppeid)
LEFT OUTER JOIN (
	SELECT count(utstyrgruppeid) AS ar, brukergruppeid 
	FROM Rettighet 
	GROUP BY brukergruppeid 
) AS RCount 
ON (id = RCount.brukergruppeid) 
LEFT OUTER JOIN (
	SELECT count(utstyrgruppeid) AS ad, brukergruppeid
	FROM DefaultUtstyr 
	GROUP BY brukergruppeid 
) AS DCount 
ON (id = DCount.brukergruppeid) 		    
ORDER BY " . $sorts[$sort];

	//print "<pre>" . $querystring . "</pre>";

    if ( $query = pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

	while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$brukere[$row][0] = $data["id"];
		$brukere[$row][1] = $data["navn"];
		$brukere[$row][2] = $data["descr"];
		$brukere[$row][3] = $data["ab"];
		$brukere[$row][4] = $data["ar"];
		$brukere[$row][5] = $data["ad"];
		$row++;
      } 
    }  else {
      $error = new Error(2);
      $bruker{'errmsg'}= "Feil med datbasespørring.";
    }
    
    return $brukere;
  }


	// list alle gruppene en bruker er medlem av.
  function listBrukersGrupper($uid, $sort) {
    
    $bruker = NULL;
    
    $sorts = array ('navn',
		    'navn',
		    'admin, navn',
		    'sms, navn',
		    'pa, navn',
		    'aa, navn');
		    
	$querystring = "SELECT id, navn, descr 
FROM Brukergruppe, BrukerTilGruppe 
WHERE (BrukerTilGruppe.gruppeid = Brukergruppe.id) AND 
(BrukerTilGruppe.brukerid = " . $uid . ") 
ORDER BY navn ";

    if ( $query = pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

		while ( $row < $tot) {
			$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
			$grupper[$row][0] = $data["id"];
			$grupper[$row][1] = $data["navn"];
			$grupper[$row][2] = $data["descr"];
			$row++;
      	}	 
    }  else {
      $error = new Error(2);
      $bruker{'errmsg'}= "Feil med datbasespørring.";
    }
    
    return $grupper;
  }


	// Lister alle gruppene en bruker er medlem av med avansert visning (tellere)
  function listBrukersGrupperAdv($sort, $uid) {
    
    $brukere = NULL;
    
    $sorts = array ('navn',
		    'ab, navn',
		    'ar, navn',
		    'ad, navn');
		    
	$querystring = "SELECT id, navn, descr, BCount.ab, Rcount.ar, Dcount.ad, (Medlem.gruppeid > 0) AS medl 
FROM Brukergruppe 
LEFT OUTER JOIN (
	SELECT count(brukerid) AS ab, gruppeid
	FROM BrukerTilGruppe
	GROUP BY gruppeid
) AS BCount 
ON (id = BCount.gruppeid)
LEFT OUTER JOIN (
	SELECT count(utstyrgruppeid) AS ar, brukergruppeid 
	FROM Rettighet 
	GROUP BY brukergruppeid 
) AS RCount 
ON (id = RCount.brukergruppeid) 
LEFT OUTER JOIN (
	SELECT count(utstyrgruppeid) AS ad, brukergruppeid
	FROM DefaultUtstyr 
	GROUP BY brukergruppeid 
) AS DCount 
ON (id = DCount.brukergruppeid) 
LEFT OUTER JOIN (
	SELECT brukerid, gruppeid FROM BrukerTilGruppe 
	WHERE (brukerid = " . addslashes($uid) . ") 
) AS Medlem 
ON (id = Medlem.gruppeid) 
ORDER BY " . $sorts[$sort];

	//print "<pre>" . $querystring . "</pre>";

    if ( $query = pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

	while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$brukere[$row][0] = $data["id"];
		$brukere[$row][1] = $data["navn"];
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
    	"WHERE (brukerid = " . addslashes($uid) . ") " .
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
  function listVarsleAdresser($uid, $tid, $gid, $sort) {
    
//    print "<p>UID: $uid  - TID: $tid  - GID: $gid   - SORT: $sort";
    $adr = NULL;
    
    $sorts = array ('type, adresse', 'adresse');

    $querystring = "SELECT id, adresse, type, vent 
		FROM (
     		SELECT adresse, id, type 
     		FROM Alarmadresse
     		WHERE (brukerid = " . addslashes($uid) . ")
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


  // Liste alle profilene til en bruker
  function listProfiler($uid, $sort) {
    
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
      "ORDER BY " . $sorts[$sort];

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

//   print "<p>$querystring";

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



	// Denne funksjonen returnerer alle utstyrgrupper som en bruker har tilgang til, 
	// enten man har laget den selv eller den er arvet gjennom DefaultUtstyr.
  function listUtstyr($uid, $sort) {
    $uts = NULL;
    
    $sorts = array (
    	'navn,id',
    	'min,navn',
    	'ap,navn',
    	'af,navn');

    $querystring = "SELECT * FROM (SELECT DISTINCT ON (id) id, navn, descr, min, Pcount.ap, FCount.af 
FROM (SELECT id, navn, descr, true AS min
     FROM Utstyrgruppe
     WHERE (brukerid = " . addslashes($uid) . ")
     UNION
     SELECT Utstyrgruppe.id, Utstyrgruppe.navn, Utstyrgruppe.descr, (Utstyrgruppe.brukerid = " . addslashes($uid). ") AS min
     FROM Utstyrgruppe, DefaultUtstyr, Brukergruppe, BrukerTilGruppe
     WHERE (BrukerTilGruppe.brukerid = " . addslashes($uid) . ")
           AND (BrukerTilGruppe.gruppeid = Brukergruppe.id)
           AND (Brukergruppe.id = DefaultUtstyr.brukergruppeid)
           AND (DefaultUtstyr.utstyrgruppeid = Utstyrgruppe.id)
     ) AS Tilgjengelig LEFT OUTER JOIN
     (    SELECT count(tidsperiodeid) AS ap, utstyrgruppeid
            FROM (
                 SELECT DISTINCT ON (utstyrgruppeid,tidsperiodeid) tidsperiodeid, utstyrgruppeid
                 FROM (
                 	SELECT Varsle.utstyrgruppeid, Varsle.tidsperiodeid FROM Varsle, Tidsperiode, Brukerprofil 
                 	WHERE (Varsle.tidsperiodeid = Tidsperiode.id) AND
                 		(Tidsperiode.brukerprofilid = Brukerprofil.id) AND
                 		(Brukerprofil.brukerid = " . addslashes($uid) . ")
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
               WHERE ((Utstyrgruppe.brukerid = " . addslashes($uid) . ") OR (Utstyrgruppe.brukerid is null) )
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
    
    
	// Denne funksjonen returnerer alle utstyrgrupper som en bruker har rettighet til, 
  function listUtstyrRettighet($uid, $sort) {
    $uts = NULL;
    
#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

    $querystring = "SELECT DISTINCT ON (id) id, navn, descr 
FROM BrukerTilGruppe, Rettighet, Utstyrgruppe 
WHERE (BrukerTilGruppe.brukerid = " . addslashes($uid) . ") AND 
	(BrukerTilGruppe.gruppeid = Brukergruppe.id) AND 
	(Brukergruppe.id = Rettighet.brukergruppeid) AND 
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
    $uts = NULL;
    
   $sorts = array (
    	'navn,id',
    	'ap,navn',
    	'af,navn');
    	
    $querystring = "SELECT * FROM (SELECT DISTINCT ON (id) id, navn, descr, min, Pcount.ap, FCount.af
FROM (SELECT id, navn, descr, true AS min
     FROM Utstyrgruppe
     WHERE (brukerid is null)
     ) AS Tilgjengelig LEFT OUTER JOIN
     (    SELECT count(tidsperiodeid) AS ap, utstyrgruppeid
            FROM (
                 SELECT DISTINCT ON (utstyrgruppeid,tidsperiodeid) tidsperiodeid, utstyrgruppeid
                 FROM Varsle, Utstyrgruppe
                 WHERE (Utstyrgruppe.brukerid is null)
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
               WHERE (Utstyrgruppe.brukerid is null)
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
	WHERE (brukerid = " . addslashes($uid) . ")
	UNION 
	SELECT Utstyrgruppe.id, Utstyrgruppe.navn, Utstyrgruppe.descr, (Utstyrgruppe.brukerid = " . addslashes($uid) . ") AS min 
	FROM Utstyrgruppe, DefaultUtstyr, Brukergruppe, BrukerTilGruppe
	WHERE (BrukerTilGruppe.brukerid = " . addslashes($uid) . ")
		AND (BrukerTilGruppe.gruppeid = Brukergruppe.id)
		AND (Brukergruppe.id = DefaultUtstyr.brukergruppeid)
		AND (DefaultUtstyr.utstyrgruppeid = Utstyrgruppe.id) 
) AS Tilgjengelig LEFT OUTER JOIN ( 
	SELECT count(tidsperiodeid) AS ap, utstyrgruppeid
	FROM (
		SELECT DISTINCT tidsperiodeid, utstyrgruppeid
		FROM Varsle, Tidsperiode, Brukerprofil 
		WHERE (Varsle.tidsperiodeid = Tidsperiode.id) 
			AND (Tidsperiode.brukerprofilid = Brukerprofil.id) 
			AND (Brukerprofil.brukerid = " . addslashes($uid) . ") 
	) AS X
	GROUP BY utstyrgruppeid
) AS PCount
ON (id = PCount.utstyrgruppeid)
LEFT OUTER JOIN (
	SELECT count(utstyrfilterid) AS af, utstyrgruppeid
	FROM (
		SELECT utstyrfilterid, utstyrgruppeid
		FROM GruppeTilFilter, Utstyrgruppe
		WHERE (Utstyrgruppe.brukerid = " . addslashes($uid) . ")
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
		$utst[$row][5] = $data["ermed"];	
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
	WHERE brukerid is null 
) AS grupper 
LEFT OUTER JOIN (
	SELECT utstyrgruppeid 
	FROM Rettighet 
	WHERE brukergruppeid = " . addslashes($gid) . "
) AS rett 
ON (grupper.id = rett.utstyrgruppeid) 
LEFT OUTER JOIN (
	SELECT utstyrgruppeid 
	FROM DefaultUtstyr 
	WHERE brukergruppeid = " . addslashes($gid) . "
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

    $querystring = "SELECT brukernavn, navn, admin, sms, aktivProfil  
FROM Bruker 
WHERE id = " . addslashes($uid) ;

    if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$br[0] = $data["brukernavn"];
		$br[1] = $data["navn"];
		$br[2] = $data["admin"];
		$br[3] = $data["sms"];
		$br[4] = $data["aktivprofil"];
    }  else {
      $error = new Error(2);
      $bruker{'errmsg'}= "Feil med datbasespørring.";
    }
    return $br;
  }


	// Hent ut info om en gruppeid
  function brukergruppeInfo($gid) {
    $gr = NULL;

    $querystring = "SELECT navn, descr 
FROM Brukergruppe 
WHERE id = " . addslashes($gid) ;

    if ( $query = pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1 ) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$gr[0] = $data["navn"]; 
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
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$gr[0] = $data["navn"]; 
		$gr[1] = $data["descr"];		
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
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
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



	// Denne funksjonen returnerer alle filtrene som hører til en bestemt bruker.
  function listFiltre($uid, $sort) {
    $filtre = NULL;
    
#    $sorts = array ('time, minutt', 'aa, time, minutt', 'au, time, minutt', 'time, minutt');

    $querystring = "SELECT MineFilter.id, MineFilter.navn, match.am, grupper.ag
FROM (
	SELECT id, navn
	FROM Utstyrfilter 
	WHERE (Utstyrfilter.brukerid = " . addslashes($uid) . ") 
) AS MineFilter LEFT OUTER JOIN (
     SELECT count(mid) AS am,  uid
     FROM (
          SELECT FilterMatch.id AS mid, Utstyrfilter.id AS uid
          FROM Utstyrfilter, FilterMatch
          WHERE (Utstyrfilter.brukerid = " . addslashes($uid) . ") AND (Utstyrfilter.id = FilterMatch.utstyrfilterid)
     ) AS Mcount 
     GROUP BY uid 
) AS match 
ON (MineFilter.id = match.uid) 
LEFT OUTER JOIN (
     SELECT count(gid) AS ag, uid
     FROM (
          SELECT GruppeTilFilter.utstyrgruppeid AS gid, Utstyrfilter.id AS uid
          FROM Utstyrfilter, GruppeTilFilter
          WHERE (Utstyrfilter.brukerid = " . addslashes($uid) . ") AND (Utstyrfilter.id = GruppeTilFilter.utstyrfilterid)
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
	WHERE (Utstyrfilter.brukerid is null) 
) AS MineFilter LEFT OUTER JOIN (
     SELECT count(mid) AS am,  uid
     FROM (
          SELECT FilterMatch.id AS mid, Utstyrfilter.id AS uid
          FROM Utstyrfilter, FilterMatch
          WHERE (Utstyrfilter.brukerid is null) AND (Utstyrfilter.id = FilterMatch.utstyrfilterid)
     ) AS Mcount 
     GROUP BY uid 
) AS match 
ON (MineFilter.id = match.uid) 
LEFT OUTER JOIN (
     SELECT count(gid) AS ag, uid
     FROM (
          SELECT GruppeTilFilter.utstyrgruppeid AS gid, Utstyrfilter.id AS uid
          FROM Utstyrfilter, GruppeTilFilter
          WHERE (Utstyrfilter.brukerid is null) AND (Utstyrfilter.id = GruppeTilFilter.utstyrfilterid)
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




	// Denne funksjonen returnerer alle filtrene som hører til en bestemt bruker uten unødig krimskrams. untatt de som allerede er valgt.
  function listFiltreFast($uid, $gid, $sort) {
    $filtre = NULL;

    $querystring = "SELECT Utstyrfilter.id, Utstyrfilter.navn 
FROM Utstyrfilter 
WHERE brukerid = " . addslashes($uid) . " 
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



	// Denne funksjonen returnerer alle filtrene som hører til admin bruker 
	// uten unødig krimskrams. untatt de som allerede er valgt.
  function listFiltreFastAdm($gid, $sort) {
    $filtre = NULL;

    $querystring = "SELECT Utstyrfilter.id, Utstyrfilter.navn 
FROM Utstyrfilter 
WHERE brukerid is null 
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

//  print "<p>$querystring";

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

    $querystring = "SELECT id, matchfelt, matchtype, verdi 
    FROM FilterMatch 
    WHERE utstyrfilterid = " . addslashes($fid) . " ORDER BY " . $sorts[$sort];

//	print "<p>$querystring";

    if ( $query = @pg_exec($this->connection, $querystring) ) {
      $tot = pg_numrows($query); $row = 0;

      while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$match[$row][0] = $data["id"]; 
		$match[$row][1] = $data["matchfelt"];
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
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$perioder[0] = $data["helg"];
		$perioder[1] = $data["time"];
		$perioder[2] = $data["minutt"];
		$row++;
    }  else {
    	$error = new Error(2);
    	$bruker{'errmsg'}= "Feil med datbasesp&oslash;rring. Fant ikke periode.";
    }
    
    return $perioder;
}

// Henter ut informasjon om en periode..
function hentwapkey($uid) {
    
    $querystring = "SELECT key FROM wapkey WHERE (brukerid = " . addslashes($uid) . ")"; 

//    print "<p>$querystring";

    if ( $query = @pg_exec($this->connection, $querystring) AND pg_numrows($query) == 1) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$key[0] = $data["key"];
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
		$querystring = "INSERT INTO Wapkey (brukerid, key) VALUES (" . addslashes($uid) . ", '" . addslashes($key) . "')";    
		$query = pg_exec( $this->connection, $querystring);

    } else {
		$querystr = "UPDATE wapkey SET key = '" . addslashes($key) . "' WHERE brukerid = " . addslashes($uid);
		@pg_exec($this->connection, $querystr);
    }

}

function slettwapkey($uid) {
    // Spxrring som legger inn i databasen
    $querystring = "DELETE FROM Wapkey WHERE ( brukerid = " . addslashes($uid) . " )";
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
	$querystr = "UPDATE Brukergruppe SET navn = '" . addslashes($navn) . "' WHERE id = " . addslashes($gid);
	@pg_exec($this->connection, $querystr);
	$querystr = "UPDATE Brukergruppe SET descr = '" . addslashes($descr) . "' WHERE id = " . addslashes($gid);
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
	$querystr = "UPDATE Bruker SET brukernavn = '" . addslashes($brukernavn) . "' WHERE id = " . addslashes($uid);
	@pg_exec($this->connection, $querystr);
	
	$querystr = "UPDATE Bruker SET navn = '" . addslashes($navn) . "' WHERE id = " . addslashes($uid);
	@pg_exec($this->connection, $querystr);
	
 	$querystr = "UPDATE Bruker SET passord = '" . addslashes($passord) . "' WHERE id = " . addslashes($uid);
	if ($passord != undef && strlen($passord) > 0) {
		@pg_exec($this->connection, $querystr);
	}	
	
	if ($sms == 1) $s = "true"; else $s = "false";
	$querystr = "UPDATE Bruker SET sms = " . addslashes($s) . " WHERE id = " . addslashes($uid);
	@pg_exec($this->connection, $querystr);
	
	$querystr = "UPDATE Bruker SET admin = " . addslashes($admin) . " WHERE id = " . addslashes($uid);
	@pg_exec($this->connection, $querystr);	
	
	$querystr = "UPDATE Bruker SET kolengde = " . addslashes($kolengde) . " WHERE id = " . addslashes($uid);
	@pg_exec($this->connection, $querystr);

}

// Endre passord
function endrepassord($brukernavn, $passwd) {
	$querystr = "UPDATE Bruker SET passord = '" . addslashes($passwd) . 
		"' WHERE brukernavn = '" . addslashes($brukernavn) . "'";
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
	
	$querystr = "DELETE FROM BrukerTilGruppe WHERE brukerid = " . addslashes($uid) . " AND gruppeid = " . addslashes($gid);
	@pg_exec($this->connection, $querystr);
	
//	print "<p>Query: $querystr";
	if ( $type ) {
		$querystr = "INSERT INTO BrukerTilGruppe (brukerid, gruppeid) VALUES (" . addslashes($uid) . ", " . addslashes($gid) . ") ";
//	print "<p>Query: $querystr<p>&npsp;$gid ---";		
		@pg_exec($this->connection, $querystr);
	}

}

// Legge til eller endre en rettighet
function endreRettighet($gid, $ugid, $type) {

	
	$querystr = "DELETE FROM Rettighet WHERE brukergruppeid = " . addslashes($gid) . " AND utstyrgruppeid = " . addslashes($ugid);
	@pg_exec($this->connection, $querystr);
//	print "<p>Query: $querystr";	
	if ( $type ) {
		$querystr = "INSERT INTO Rettighet (brukergruppeid, utstyrgruppeid) VALUES (" . addslashes($gid) . ", " . addslashes($ugid) . " )";		
		@pg_exec($this->connection, $querystr);
	}

}

// Legge til eller endre en defaultustyr
function endreDefault($gid, $ugid, $type) {

	
	$querystr = "DELETE FROM DefaultUtstyr WHERE brukergruppeid = " . addslashes($gid) . " AND utstyrgruppeid = " . addslashes($ugid);
	@pg_exec($this->connection, $querystr);
//	print "<p>Query: $querystr";	
	if ( $type ) {
		$querystr = "INSERT INTO DefaultUtstyr (brukergruppeid, utstyrgruppeid) VALUES (" . addslashes($gid) . ", " . addslashes($ugid) . " )";
//	print "<p>Query: $querystr";			
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

    if ( $sms   == 1 ) { $sms = 'true'; } else { $sms = 'false'; }

    // Spxrring som legger inn i databasen
    $querystring = "INSERT INTO Bruker (id, navn, brukernavn, passord, admin, sms, kolengde) VALUES (" . 
      "nextval('brukerid'), '" . addslashes($navn) . "', '" . addslashes($brukernavn) . "', '" .
      addslashes($passord) . "', " . addslashes($admin) . ", " . addslashes($sms) . ", " . addslashes($kolengde) . ") ";
    
#    print "<p>query: $querystring";
    if ( $query = pg_exec( $this->connection, $querystring)) {
      
      // Henter ut object id`n til raden.
      $oid = pg_getlastoid($query);
      
      // Henter ut id`n til raden og returnerer den.
      $idres = pg_exec( $this->connection, "SELECT id FROM Bruker WHERE oid = $oid");
      $idrow = pg_fetch_row($idres, 0);
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
    $querystring = "INSERT INTO BrukerGruppe (id, navn, descr) VALUES (" . 
      "nextval('brukergruppeid'), '" . addslashes($navn) . "', '" . addslashes($descr) . "') ";
    
#    print "<p>query: $querystring";
    if ( $query = pg_exec( $this->connection, $querystring)) {
      
      // Henter ut object id`n til raden.
      $oid = pg_getlastoid($query);
      
      // Henter ut id`n til raden og returnerer den.
      $idres = pg_exec( $this->connection, "SELECT id FROM BrukerGruppe WHERE oid = $oid");
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
      "nextval('tidsperiodeid'), " . addslashes($helg) . ", '" . 
      addslashes($tid) ."', " . addslashes($profilid) . ")";
    
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
    $querystring = "INSERT INTO Alarmadresse (id, brukerid, adresse, type) VALUES (" . 
      "nextval('alarmadresseid'), " . addslashes($brukerid) . ", '" . 
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
  
  


  // opprette ny profil
  function nyProfil($navn, $brukerid, $ukedag, $uketidh, $uketidm, $tidh, $tidm) {

    // Spxrring som legger inn i databasen
    $querystring = "INSERT INTO Brukerprofil (id, brukerid, navn, ukedag, uketid, tid) VALUES (" . 
      "nextval('brukerprofilid'), " . $brukerid . ", '" . 
      addslashes($navn) ."', " . addslashes($ukedag) . ", '" . 
      addslashes($uketidh) . ":" . addslashes($uketidm) . "', '" .
      addslashes($tidh) . ":" . addslashes($tidm) . "' " .
      " )";
    
    #print "<p>query: $querystring";
    if ( $query = pg_exec( $this->connection, $querystring)) {
      
      // Henter ut object id`n til raden.
      $oid = pg_getlastoid($query);
      
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
    $querystring = "INSERT INTO Utstyrfilter (id, brukerid, navn) VALUES (" . 
      "nextval('utstyrfilterid'), " . addslashes($brukerid) . ", '" . 
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
    $querystring = "INSERT INTO Utstyrfilter (id, brukerid, navn) VALUES (" . 
      "nextval('utstyrfilterid'), null, '" . 
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

    // Spxrring som legger inn i databasen
    $querystring = "INSERT INTO FilterMatch (id, matchfelt, matchtype, utstyrfilterid, verdi) VALUES (" . 
      "nextval('filtermatchid'), " . addslashes($matchfelt) . ", " . 
      addslashes($matchtype) .", " . addslashes($fid) . ", '" . 
      addslashes($verdi) . "' )";
    
//    print "<p>query: $querystring";
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
  function nyUtstyrgruppe($uid, $navn, $descr) {

    // Spxrring som legger inn i databasen
    $querystring = "INSERT INTO Utstyrgruppe (id, brukerid, navn, descr) VALUES (" . 
      "nextval('filtermatchid'), " . addslashes($uid) . ", '" . 
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

  // opprette ny utstyrsgruppe administrator
  function nyUtstyrgruppeAdm($navn, $descr) {

    // Spxrring som legger inn i databasen
    $querystring = "INSERT INTO Utstyrgruppe (id, brukerid, navn, descr) VALUES (" . 
      "nextval('filtermatchid'), null, '" . 
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
    $querystring = "DELETE FROM Bruker WHERE ( id = " . addslashes($uid) . " )";
    
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
    $querystring = "DELETE FROM Brukergruppe WHERE ( id = " . addslashes($gid) . " )";
    
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
  function aktivProfil($brukernavn, $profilid) {

    // Spxrring som legger inn i databasen
    $querystring = "UPDATE Bruker SET aktivProfil = " . addslashes($profilid) . " WHERE " .
      " brukernavn = '" . addslashes($brukernavn) . "'  ";
    
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
 *	Dette er en klasse for spørringer mot kunnskapsdatabasen
 *
 */
class DBHK {

  // Må ha inn en ferdig oppkoblet databasekobling til postgres
  var $connection;

  // Konstruktor
  function DBHK($connection) {
    $this->connection = $connection;
  }
  
  
  function listSted($sort) {
    
    $steder = NULL;
    
    $sorts = array ('brukernavn',
		    'navn',
		    'admin, navn',
		    'sms, navn',
		    'pa, navn',
		    'aa, navn');
		    
    $querystring = "SELECT locationid, org, descr FROM location ORDER BY org, descr";

    if ( $query = @pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

	while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$steder[$row][0] = utf8_encode($data["locationid"]);
		$steder[$row][1] = utf8_encode($data["org"] . " " . $data["descr"]);
		$row++;
      } 
    }  else {
      $error = new Error(2);
    }
    
    return $steder;
  }
  
  
  
  function listOmraade($sort) {
    
    $steder = NULL;
    
    $sorts = array ('brukernavn',
		    'navn',
		    'admin, navn',
		    'sms, navn',
		    'pa, navn',
		    'aa, navn');
		    
    $querystring = "SELECT areaid, descr FROM area ORDER BY descr";

    if ( $query = @pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

	while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$steder[$row][0] = utf8_encode($data["areaid"]);
		$steder[$row][1] = utf8_encode($data["descr"]);
		$row++;
      } 
    }  else {
      $error = new Error(2);
    }
    
    return $steder;
  }  
  
  
  function listType($sort) {
    
    $typer = NULL;
    
    $sorts = array ('brukernavn',
		    'navn',
		    'admin, navn',
		    'sms, navn',
		    'pa, navn',
		    'aa, navn');
		    
    $querystring = "SELECT typeid, descr FROM type ORDER BY descr";

    if ( $query = @pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

	while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$typer[$row][0] = utf8_encode( $data["typeid"] );
		$typer[$row][1] = utf8_encode( $data["descr"] );
		$row++;
      } 
    }  else {
      $error = new Error(2);
    }
    
    return $typer;
  }    
  
  
 function listTypegruppe($sort) {
    
    $typer = NULL;
    
    $sorts = array ('brukernavn',
		    'navn',
		    'admin, navn',
		    'sms, navn',
		    'pa, navn',
		    'aa, navn');
		    
    $querystring = "SELECT typegroupid, descr FROM typegroup ORDER BY descr";

    if ( $query = @pg_exec($this->connection, $querystring) ) {
		$tot = pg_numrows($query); $row = 0;

	while ( $row < $tot) {
		$data = pg_fetch_array($query, $row, PGSQL_ASSOC);
		$typer[$row][0] = $data["typegroupid"];
		$typer[$row][1] = $data["descr"];
		$row++;
      } 
    }  else {
      $error = new Error(2);
    }
    
    return $typer;
  }      
  
  
function listEventtypes($sort) {

    $typer = NULL;

    $sorts = array ('brukernavn',
                    'navn',
                    'admin, navn',
                    'sms, navn',
                    'pa, navn',
                    'aa, navn');

    $querystring = "SELECT eventtypeid FROM eventtype ORDER BY
    eventtypeid";

    if ( $query = @pg_exec($this->connection, $querystring) ) {
                $tot = pg_numrows($query); $row = 0;

        while ( $row < $tot) {
                $data = pg_fetch_array($query, $row, PGSQL_ASSOC);
                $typer[$row][0] = $data["eventtypeid"];
                $row++;
      }
    }  else {
      $error = new Error(2);
    }

    return $typer;
  }  
  
  
}


?>
