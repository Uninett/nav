<body topmargin="0" leftmargin="0" marginheight="0" marginwidth="0"
  bgcolor="#ffffff" text="#000000" link="#000099" alink="#0000ff"
  vlink="#000099">
<link rel="STYLESHEET" type="text/css" href="stil.css">
    <?
############
## Databasetilkobling
############
    $db = pg_Connect("dbname=manage user=navall password=uka97urgf");
$fil = les_fil("ragen.conf","r");

list($filparam,$urlparam,$navnparam) = tolk_fil($fil,$rapport);

//print $filparam[skjul];
//    print $QUERY_STRING;

$sql = $filparam[sql];
if(!$sql){
    $overskrift="Det fins ikke en definert rapport for $rapport";
}
$ar_where = array();
//print $sql;
if($sql){
if(preg_match("/SELECT(.*)FROM/is",$sql,$sel)) {
//    print $sel[1];
    $sel[1] = preg_replace("/\,\s+/",",",$sel[1]);//fjerner mellomrom etter komma
    $sel[1] = preg_replace("/^\s+/","",$sel[1]);//fjerner startende mellomrom
	$sel[1] = preg_replace("/\s+$/","",$sel[1]);
    $select = split(",",$sel[1]);
    $urlselect = $select;
    for($i=0;$i<sizeof($urlselect);$i++){
	//print $urlselect[$i];
	if(preg_match("/\ AS\ (\w+)/i",$urlselect[$i],$nysel)){
	    print $urlselect[$i]=$nysel[1];
	} elseif(preg_match("/\.(\w+)/",$urlselect[$i],$nysel)){
	    $urlselect[$i]=$nysel[1];
	}
	$fraselect[$urlselect[$i]] = $i;
	if($$urlselect[$i]){
	    //print $$urlselect[$i];
	    $verdi =  $$urlselect[$i];
	    array_push($ar_where,"$select[$i] like '$verdi'");
	//print $urlselect[$i];
	}
    }
}
if(preg_match("/FROM(.*?)(?:WHERE|ORDER|GROUP|LIMIT|$)/is",$sql,$sel)) {
    //$sel[1] = preg_replace("/\s/","",$sel[1]); blir bare feil her
    $ar_from = split(",",$sel[1]);
}
if(preg_match("/WHERE(.*?)(?:ORDER|GROUP|LIMIT|$)/is",$sql,$sel)) {
    $ar_where = array_merge($ar_where,preg_split("/and/i",$sel[1]));
}
if(preg_match("/GROUP\ BY(.*?)(?:ORDER|LIMIT|$)/is",$sql,$sel)) {
//    print $sel[1];
    $ar_group_by = split(",",$sel[1]);
}
if(preg_match("/ORDER\ BY(.*?)(?:GROUP|LIMIT|$)/is",$sql,$sel)) {
    //print $sel;
    $ar_order_by = split(",",$sel[1]);
}

    //print sizeof($ar_order_by);

if($limit){
#	     print "hadde limit fra før";
    $ar_limit = split(",",$limit);
//    @limit = map rydd($_),@limit;
} elseif(preg_match("/LIMIT(.*?)$/is",$sql,$sel)){
    $ar_limit = split(",",$sel[1]);
}

$sql2 = "SELECT ".join(",",$select)." FROM ".join(",",$ar_from);
$sql_antall = "SELECT $select[0] FROM ".join(",",$ar_from);
if($ar_where){
    $sql2 .= " WHERE ".join(" AND ",$ar_where);
    $sql_antall .= " WHERE ".join(" AND ",$ar_where);
}
if($ar_group_by){
    $sql2 .= " GROUP BY ".join(",",$ar_group_by);
    $sql_antall .= " GROUP BY ".join(",",$ar_group_by);
}

if(!$ar_order_by){
    $ar_order_by = array();
    if($order_by){
	array_push($ar_order_by,$order_by);
    }
    if($filparam[order_by]){
	array_push($ar_order_by,$filparam[order_by]);
    }
}

if($ar_order_by){
    $sql2 .= " ORDER BY ".join(",",$ar_order_by);
}

if($limit){
    $ar_limit = split(",",$limit);
    //@limit = map rydd($_),@limit;
} else {
    $ar_limit = array(100,0);
}
$sql2.= " LIMIT ".join(",",$ar_limit);
//print $sql_antall;
$sql = $sql2;
list($antall_rader,$tabell) = db_2d_array($db,$sql);
$antall_treff = db_antall($db,$sql_antall);

if($filparam[ekstra]) {
    $ekstra_kolonner = split(",",$filparam[ekstra]);
    $urlselect = array_merge($urlselect,$ekstra_kolonner);
    for ($i = 0; $i<sizeof($tabell);$i++ ) {
   	$rad = $tabell[$i];
	$tabell[$i] = array_merge($rad,$ekstra_kolonner);
    }
}    
if($filparam[skjul]) {
//    print "ja";
    $skjul = split(",",$filparam[skjul]);
    for($i=0;$i<sizeof($urlselect);$i++){
//	print $urlselect[$i];
	if($fraselect[$skjul[$i]]){
//	    print $fraselect[$skjul[$i]];
	    //unset($rad[$fraselect[$skul_kolonner[$i]]]);
	    $skjulte_kolonner[$fraselect[$skjul[$i]]] = 1;
	}
    }
}

} //close if $sql
#############
## Skriving til skjerm
#############
print "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\" width=\"100%\"><tr><td background=\"bakgrunn_nav.php\" align=\"left\">";
if(!$overskrift){
    $overskrift = $filparam[overskrift];
}
if(!$overskrift){
    $overskrift = $rapport;
}
$overskrift = urlencode($overskrift);
print "<img src=\"overskrift.php?overskrift=$overskrift\">";
print "</td><td background=\"bakgrunn_nav.php\" valign=\"bottom\" align=\"right\"><font color=\"#ffffff\"><img src=\"bildetekst.php?tekst=".date("j.n.Y")."\"  border=\"0\"></font>";

print "<table><tr><td>";

print "<a href=\"../web.pl?side=reports\"><img src=\"bildetekst.php?tekst=Hjem\" border=\"0\"\"></a></td><td>";
## husker gammel querystring
$peker = lag_peker($urlselect,$QUERY_STRING);
if($begrenset){
        print "<form action=\"?$peker&begrenset=0\" method=\"post\"><hidden name=\"begrenset\" value=\"0\"><input type=\"image\" src=\"bildetekst.php?tekst=Skjul skjema\"></form>";
} else {
print "<form action=\"?$peker&begrenset=1\" method=\"post\"><hidden name=\"begrenset\" value=\"1\"><input type=\"image\" src=\"bildetekst.php?tekst=Søkeskjema\"></form>";
}
print "</td></tr></table></td></tr></table>";

//print "<p>$sql</p>";

if($begrenset){
//skriv_skjemainnhold
//kan ikke kommenteres bort, da ingen vet hva variablene heter

    skriv_skjemainnhold($urlselect,$navnparam,$rapport,$skjulte_kolonner);
}

lag_peker($urlselect,$QUERY_STRING);


## bla
if(!$grense){
    $grense = 100;
}
$neste = $ar_limit[1]+$grense;
$forrige = $ar_limit[1]-$grense;
print "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\" width=\"100%\"><tr><td align=\"left\" width=\"100\">";
if($ar_limit[1]!=0){ 
print "<a href=\"?rapport=$rapport&limit=".$ar_limit[0]."%2c".$forrige."\">Forrige</a> ";
} else {
    print "&nbsp;";
}

$fra = $ar_limit[1] +1;
$til = $ar_limit[1] + $ar_limit[0];
print "</td><td align=\"center\">";
if($antall_treff){
    if($grense>$antall_treff){
	print "Totalt $antall_treff treff i databasen";
    } elseif ($til>$antall_treff){
	print "Viser nå treff $fra til $antall_treff av totalt $antall_treff treff i databasen";
    } else {
	print "Viser nå treff $fra til $til av totalt $antall_treff treff i databasen";
    }
} else {
    print "Dette ga null treff i databasen";
}
print "</td><td align=\"right\" width=\"100\">";

if($antall_rader == $ar_limit[0]){
    print " <a href=\"?rapport=$rapport&limit=".$ar_limit[0]."%2c".$neste."\">Neste</a>";
} else {
    print "&nbsp;";
}
print "</td></tr></table>";
## bla slutt

if($antall_rader){
    skriv_tabell($tabell,$urlparam,$urlselect,$fraselect,$navnparam,$rapport,$skjulte_kolonner);
}
print "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\" width=\"100%\"><tr><td background=\"bakgrunn_nav.php\" align=\"right\">";
print "<font color=\"#ffffff\"><a href=\"mailto:gartmann@stud.ntnu.no\"><font color=\"#ffffff\">Sigurd Gartmann</font></a>, ITEA, NTNU</font>";
print "</td></tr></table>";
print "<p><font color=\"#ffffff\">$sql</font></p>";
pg_close($db);

/*
skrivhash($filparam);
skrivhash($urlparam);
skrivhash($navnparam);
skrivhash($select);
skrivhash($where);
skrivhash($from);
skrivhash($order_by);
*/



function skrivhash($hash){
########
## Tar inn en hash og skriver den som en htmltabell
########
    if($hash){
	print "<table border>";
	foreach ($hash as $key => $value) {
	    print "<tr><td>|$key|</td><td>|$value|</td></tr>";
	}
	print "</table>";
    }
}
function tolk_fil($fil,$rapport){
#############
## Behandler tekststreng og putter inn i hasher
#############
    if(preg_match("/^\s*$rapport\s*{(.*?)}/sm",$fil,$regs)){
	$var = $regs[1];
	//print $var;
	preg_match_all("/\W*\\\$(\w+?)\W*=\W*\"(.+?)\"\s*\;/smi",$var,$para);
	for ($i = 0; $i<sizeof($para[0]); $i++) {
	    $key = $para[1][$i];
	    $value = $para[2][$i];
	    $filparam[$key] = $value;
	    //echo "<br>".$key." = ".$value;
	    if(preg_match("/url_(\w+)/i",$key,$newkey)){
		$urlparam[$newkey[1]] = $value;
		//print $newkey[1];
	    } elseif(preg_match("/navn_(\w+)/i",$key,$newkey)) {
		$navnparam[$newkey[1]] = $value;
		//print $newkey[1];
	    }
	}

    }
    return array($filparam,$urlparam,$navnparam);
}
function les_fil($fil,$var){
##############
## Leser fra fil til en lang tekstreng
##############

    $fp = fopen($fil,$var);
    $fil = fread($fp,filesize($fil));
    fclose($fp);
    return $fil;
}

function db_antall($db,$sql) {
    $res = pg_exec($db,$sql);
//    $rad = pg_numrows($res);
    return pg_numrows($res);
}

function db_2d_array($db,$sql){
    $res = pg_exec($db,$sql);
    $rader = pg_numrows($res);
    $resultat = array();
    for ($i=0;$i<$rader;$i++){
	$rad = pg_fetch_row($res,$i);
	$resultat[$i] = $rad;
    }
    return array($rader,$resultat);
}
function lag_peker($urlselect,$querystring){
    $peker = $querystring;
    for($i=0;$i<sizeof($urlselect);$i++) {
		$this = $urlselect[$i];
		global $$this;
		$that = $$this;
		if($that){
		    $peker .= "&$this=$that";
		}
	    }
    return $peker;
}

function skriv_skjemainnhold($urlselect,$navnparam,$rapport,$skjulte_kolonner){
    print "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\" width=\"600\" align=\"center\"><tr><td><form action=\"?rapport=$rapport\" method=\"post\"><table border=\"0\" cellspacing=\"0\" cellpadding=\"0\">";
    for($i=0;$i<sizeof($urlselect);$i++) {
	//if(!$skjulte_kolonner[$i]){
		$this = $urlselect[$i];
		print "<tr><td background=\"bakgrunn_nav.php\"><img src=\"bildetekst.php?tekst=";
//<font color=\"#ffffff\">";
		if($navnparam[$this]){
		    print $navnparam[$this];
		} else {
		    print $this;
		}
//		print "</font>";
		print "\" border=\"0\"></td>";
	   // }
	global $$this;
	$skjemaverdi = $$this;
	
	 print "<td><input type=\"text\" name=\"$this\" value=\"$skjemaverdi\"></td></tr>";
    }
    print "<tr><td></td><td background=\"bakgrunn_nav.php\"><input type=\"image\" src=\"bildetekst.php?tekst=Søk\" name=\"send\" value=\"Send\"></td></tr></table></form></td><td><p>Fyll inn det du vil søke etter i ønskede felt. Du kan bruke % for wildcard.</p></td></tr></table>";
}


function skriv_tabelloverskrift($urlselect,$navnparam,$rapport,$skjulte_kolonner) {
    print "<tr>";
    for($i=0;$i<sizeof($urlselect);$i++) {
	    if(!$skjulte_kolonner[$i]){
		$this = $urlselect[$i];
		global $QUERY_STRING;
		$peker = lag_peker($urlselect,$QUERY_STRING);
		print "<td bgcolor=\"#486591\"><form action=\"?$peker&order_by=$this\" method=\"post\"><input type=\"image\" src=\"bildetekst.php?tekst=";
//<font color=\"#ffffff\">";
		if($navnparam[$this]){
		    print $navnparam[$this];
		} else {
		    print $this;
		}
//		print "</font>";
		print "\"></form></td>";
	    }
    }
    print "</tr>";
}
function skriv_tabell($tabell,$urlparam,$urlselect,$fraselect,$navnparam,$rapport,$skjulte_kolonner){
    print "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\" width=\"100%\">";
    $teller = 0;
    skriv_tabelloverskrift($urlselect,$navnparam,$rapport,$skjulte_kolonner);

    for($i=0;$i<sizeof($tabell);$i++){
	$rad = $tabell[$i];
	print "<tr>";
	list($teller,$farge) = farge($teller);
	for($j=0;$j<sizeof($rad);$j++){
	    if(!$skjulte_kolonner[$j]){
		print "<td bgcolor=\"$farge\">";
		$rute = $j;
		if($link = $urlparam[$urlselect[$rute]]){
		    //print $link;
		    //$link = $urlparam[$urlselect[$rute]];
		    preg_match("/\\\$(\w+)/",$link,$res);
/*
		    print $res[1];
		    print $fraselect[$res[1]];
		    print $rad[$fraselect[$res[1]]];
*/
		    $link = preg_replace("/(\\\$\w+)/",$rad[$fraselect[$res[1]]],$link);
		    //		$link = $rad[$fraselect[$res[1]]];
		    if($link){
			print "<a href=\"$link\">";
			skriv_rute($rad[$rute]);
			print "</a>";
		    } else {
			skriv_rute($rad[$rute]);
		    }
		    
		} else {
		    skriv_rute($rad[$rute]);
		}
	    }	    
	    print "</td>";
	}
	print "</tr>";
    }
    print "</table>";
}
function skriv_rute($innhold){
    if ($innhold) {
	print $innhold;
    } else {
	print "&nbsp";
    }
}
function farge($teller) {
    if ($teller == 0) {
	return array(1,"#fafafa");
    } else {
	return array(0,"#efefef");
    }
}

?>
