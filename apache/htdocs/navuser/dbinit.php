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
            $filename = "/usr/local/nav/local/etc/conf/db.conf";
            
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
                $prop = trim($tvar[0]); $value = trim($tvar[1]);

                switch ($prop) {
                    case 'dbhost'		: $dhost = $value; break;
                    case 'dbport'		: $dport = $value; break;
                    case 'db_navprofile'	: $ddb   = $value; break;
                    case 'script_navprofile' 	: $duser = $value; break;
                    case 'userpw_navprofile' 	: $dpass = $value; break;
                }
            }
            
            $cstr = "user=$duser password=$dpass dbname=$ddb";         
            //echo "<p>" . $cstr;
   
            if (! $this->dbh_dbcon = pg_connect($cstr) ) {
                print "<h1>" . gettext("Databasefeil") . "</h1>";
                print "<p>" . gettext("Hele portalen blir sperret når ikke databasen er tilgjenglig.");
                exit(0);
            } 

            $this->dbh = new DBH($this->dbh_dbcon);

        }
        return $this->dbh;
    }



    function get_dbhk() {
        if ($this->dbhk == null) {
            // Get fileconfiglines
            $filename = "/usr/local/nav/local/etc/conf/db.conf";
            
            $conffile = file($filename);
            
            // Init variables, in case they dont exist in config file...
            $dhost = "localhost";
            $dport = "5432";
            $ddb = "manage";
            $duser = "navprofilemanage";
            $dpass = "";
            
            foreach ($conffile as $confline) {
                $tvar = split('=', trim($confline));
                $prop = trim($tvar[0]); $value = trim($tvar[1]);

                switch ($prop) {
                    case 'dbhost'			: $dhost = $value; break;
                    case 'dbport'			: $dport = $value; break;
                    case 'db_navprofilemanage'		: $ddb   = $value; break;
                    case 'script_navprofilemanage' 	: $duser = $value; break;
                    case 'userpw_navprofilemanage' 	: $dpass = $value; break;
                }
                
            }
            
            $cstr = "user=$duser password=$dpass dbname=$ddb";          
            //echo "<p>" . $cstr;
   
            if (! $this->dbhk_dbcon = pg_connect($cstr) ) {
                print "<h1>" . gettext("Databasefeil") . "</h1>";
                print "<p>" . gettext("Hele portalen blir sperret når ikke databasen er tilgjenglig.");
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
