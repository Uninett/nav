<?php

class dbinit {

    var $dbh;
    var $dbh_dbcon;
    
    var $dbhk;
    var $dbhk_dbcon;
    
    // Constructor
    function dbinit() {
        //dl("pgsql.so");
        
        $this->dbh = null;
        $this->dbh_dbcon = null;
        
        $this->dbhk = null;
        $this->dbhk_dbcon = null;
    }

    function get_dbh() {
        if ($this->dbh == null) {
            $filename = PATH_DB . "/db.conf";
            
           
            if (!file_exists($filename)) {
                print "<h1>" . gettext("File access error") . "</h1>";
                print "<p>" . gettext("Could not find the database configuration file.");
                exit(0);
            }
            
            // Get fileconfiglines            
            $conffile = file($filename);
            
            // Init variables, in case they dont exist in config file...
            $dhost = "localhost";
            $dport = "5432";
            $ddb = "navprofiles_";
            $duser = "navprofile_";
            $dpass = "";
            
            foreach ($conffile as $confline) {
                $tvar = split('=', trim($confline));
                if (sizeof($tvar) > 1) {
					$prop = trim($tvar[0]); $value = trim($tvar[1]);
	
					switch ($prop) {
						case 'dbhost'		: $dhost = $value; break;
						case 'dbport'		: $dport = $value; break;
						case 'db_navprofile'	: $ddb   = $value; break;
						case 'script_navprofile' 	: $duser = $value; break;
						case 'userpw_' . $duser  	: $dpass = $value; break;
					}
                }
            }
            
            $cstr = "user=$duser password=$dpass dbname=$ddb";         
            //echo "<p>" . $cstr;
   
            if (! $this->dbh_dbcon = pg_connect($cstr) ) {
                print "<h1>" . gettext("Database error") . "</h1>";
                print "<p>" . gettext("Could not connect to the navprofiles database. The database server could be down, or the logininfo could be corrupt in the database configuration file.");
                exit(0);
            } 

            $this->dbh = new DBH($this->dbh_dbcon);

        }
        return $this->dbh;
    }



    function get_dbhk() {
        if ($this->dbhk == null) {
            // Get fileconfiglines
            $filename = PATH_DB . "/db.conf";

            if (!file_exists($filename)) {
                print "<h1>" . gettext("File access error") . "</h1>";
                print "<p>" . gettext("Could not find the database configuration file.");
                exit(0);
            }

            
            $conffile = file($filename);
            
            // Init variables, in case they dont exist in config file...
            $dhost = "localhost";
            $dport = "5432";
            $ddb = "manage_";
            $duser = "navprofilemanage_";
            $dpass = "";
            
            foreach ($conffile as $confline) {
                $tvar = split('=', trim($confline));
                if (sizeof($tvar) > 1) {
					
					$prop = trim($tvar[0]); $value = trim($tvar[1]);
	
					switch ($prop) {
						case 'dbhost'			: $dhost = $value; break;
						case 'dbport'			: $dport = $value; break;
						case 'db_navprofilemanage'		: $ddb   = $value; break;
						case 'script_navprofilemanage' 	: $duser = $value; break;
						case 'userpw_' . $duser 	: $dpass = $value; break;
					}
				}
                
            }
            
            $cstr = "user=$duser password=$dpass dbname=$ddb";          
            //echo "<p>" . $cstr;
   
            if (! $this->dbhk_dbcon = pg_connect($cstr) ) {
                print "<h1>" . gettext("Database error") . "</h1>";
                print "<p>" . gettext("Could not connect to the manage database. The database server could be down, or the logininfo could be corrupt in the database configuration file.");
                exit(0);
            } 

            $this->dbhk = new DBHK($this->dbhk_dbcon);

        }
        return $this->dbhk;
    }





    function closeall() {
        if (! is_null($this->dbh_con)) {
            pg_close($this->dbh_con);
        }
        
        if (! is_null($this->dbhk_con)) {
            pg_close($this->dbhk_con);
        }        
    }

}


$dbinit = new dbinit();

$dbh = $dbinit->get_dbh();



?>
