<?php

function db_get($myself) {
    $configlist = array();
    exec("/usr/local/nav/navme/lib/getpw.pl /usr/local/nav/local/etc/conf/db.conf",$config);
    
    foreach(array_values($config) as $c){
	
	if(preg_match("/^(.+?)=(.*?)$/",$c,$treff)) {
	    $configlist[$treff[1]] = $treff[2];
	}
    }
    $db_user = $configlist["script_".$myself];
    $db_passwd = $configlist["userpw_".$db_user];
    $db_db = $configlist["db_".$db_user];
    $db_host = $configlist["dbhost"];
    $db_port = $configlist["dbport"];
    
    $dbh = pg_connect("host=$db_host port=$db_port dbname=$db_db user=$db_user password=$db_passwd") or die("<br>Klarte ikke koble til databasen!<br>");
    return $dbh;
}

?>