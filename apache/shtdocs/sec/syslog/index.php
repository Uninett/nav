<?php
// $id:$

    require("/usr/local/nav/navme/lib/getdb.php");

function tr($a_innhold,$konfigurasjon=""){
    foreach($a_innhold as $innhold){
	$retval .= "\n\t\t\t\t<td $konfigurasjon>$innhold</td>";
    }
    return $retval;
}
function tb($a_innhold,$konfigurasjon=""){
    $retval = "\n\t\t<table $konfigurasjon>";
    foreach($a_innhold as $innhold){
	$retval .= "\n\t\t\t<tr>$innhold</tr>";
    }
    $retval .= "\n\t\t</table>";
    return $retval;
}
function form($innhold,$action="",$method="get"){
    return "<form action=\"$action\" method=\"$method\">$innhold</form>";
}
function form_input($type,$navn,$value="",$length="",$maxlength=""){
    $retval = "<input type=\"$type\" name=\"$navn\" value=\"$value\"";
    if($length){
	$retval .= " size=\"$length\"";
	if($maxlength){
	    $retval .= " maxlength=\"$maxlength\"";
	}
    }
    $retval .= ">";
    return $retval;
}
function form_select($navn,$option,$values="",$selected=""){
    if(!$selected){
	$selected="alle";
    }
    $retval = "<select name=\"$navn\">";
    foreach(array_keys($option) as $a){
	$retval .= "<option value=\"$option[$a]\"";
	if($selected==$values[$a]||$selected==$option[$a]){
	    $retval .= " selected";
	}
	$retval .= ">";
	if($values[$a]) {
	    $retval .= $values[$a];
	} else { 
	    $retval .= $option[$a];
	}
	$retval .= "</option>";
    }
    $retval .= "</select>";
    return $retval;
}


function a($navn,$adresse="#topp",$konfigurasjon=""){
    return "<a href=\"$adresse\" $konfigurasjon>$navn</a>";
}

function h1($tekst){
    return "<h1>$tekst</h1>";
}

function italic($tekst=""){
    return "<i>".$tekst."</i>";
}

function pre($tekst=""){
    return "<pre>".$tekst."</pre>";
}

function db_select($db,$sql,$sum=0){
    $res = pg_exec($db,$sql) or die("<br>Fikk ingenting fra databasen!<br>$sql");
    $ant = pg_numrows($res);
    if(pg_numfields($res)>1){
        for($i=0;$i<$ant;$i++){
	    $resultat[$i]=pg_fetch_row($res,$i);
	}
	
    } else {
	for($i=0;$i<$ant;$i++){
	    $rad = pg_fetch_row($res,$i);
	    $resultat[$i] = $rad[0];
	}
    }
    if($sum){
	return array($resultat,$ant);
    } else {
	return $resultat;
    }
}

function topp($tittel="") {
    $retval = "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">\n<html>\n<head>\n\t<title>NAV";
    if ($tittel) $retval .= ": $tittel";
    $retval .= "</title>";
    $retval .= "<style>body,td,a{font-family:verdana,tahoma,helvetica,sans-serif;}h1{color:#ffffff;font-size:32pt;}</style>";
    $retval .= "\n</head>\n\n<body topmargin=\"0\" leftmargin=\"0\" marginheight=\"0\" marginwidth=\"0\" bgcolor=\"#ffffff\" text=\"#000000\" link=\"#000099\" alink=\"#0000ff\" vlink=\"#000099\"><a name=\"topp\"></a>";
    return $retval;
}

# /* start */

$tittel = "Loggmeldinger fra skript, rutere og svitsjer";
print topp($tittel);

if(!$system) $system = 'cisco';

if(!$tid_fra) $tid_fra=date("Y-m-d",time()-86400)." 00:00:00";
else $tid_fra = rawurldecode($tid_fra);
if(!$tid_til) $tid_til=date("Y-m-d H:i:s");
else $tid_til = rawurldecode($tid_til);


$dbh = db_get("syslog");

$db_tabell = db_select($dbh,"select boks,type from meldinger where system='$system'");
$db_boks[0]="";
$db_type[0]="";
foreach(array_keys($db_tabell) as $rad){
    $db_boks[$db_tabell[$rad][0]] = $db_tabell[$rad][0];
    $db_type[$db_tabell[$rad][1]] = $db_tabell[$rad][1];
}
sort($db_boks);
sort($db_type);

$db_prioritet = array_merge(array(0=>""),db_select($dbh,"SELECT prioritet from prioriteter"));
$db_bokstype = array(0=>"",1=>"gw",2=>"sw",3=>"na");
$db_system = db_select($dbh,"select distinct system from meldinger");
$lapper_felles = array(0=>"Alle");
$lapper_bokstype = array(0=>"Alle",1=>"Rutere", 2=>"Svitsjer",3=>"Mystiske");
$lapper_prioritet = array(0=>"Alle",1=>"0 - emergencies",2=>"1 - alerts",3=>"2 - critical",4=>"3 - errors",5=>"4 - warnings",6=>"5 - notifications",7=>"6 - informal",8=>"7 - debugging");

$uttrykk = array();
 
if($boks){
    array_push($uttrykk,"boks = '$boks'");
    if($bokstype&&!preg_match("/$bokstype/",$boks)){
	$bokstype="";
	$overstyring = "Bokstype er blitt overstyrt av avsender, $boks blir vist,";
    }
}

if($type){
    array_push($uttrykk,"type = '$type'");
    if($prioritet&&!preg_match("/\-$prioritet\-/",$type)){
	$prioritet="";
	$overstyring="Prioritet er blitt overstyrt av meldingstype, $type blir vist.";
    }
}
if($system){
    array_push($uttrykk,"system = '".$system."'");
}
if($tid_fra){
    array_push($uttrykk,"tid >= '$tid_fra'");
}
if($tid_til){
    array_push($uttrykk,"tid <= '$tid_til'");
}
if($prioritet){
    array_push($uttrykk,"prioritet = '$prioritet'");
}
if($bokstype){
    array_push($uttrykk,"bokstype = '$bokstype'");
}
if($lengde = sizeof($uttrykk)){
    $where = $uttrykk[0];
    for($i = 1; $i < $lengde; $i++){
	$where .= " and ".$uttrykk[$i];
    }
}

# her kommer siden:

print tb(array(
	       tr(array(
			tb(array(
				 tr(array(h1($tittel)),"bgcolor=\"#486591\"")),
			   "width=\"100%\" cellspacing=\"1\" border=\"0\" cellpadding=\"2\" bgcolor=\"#e6e6e6\"")
			)),
	       tr(array(
			tb(array(
				 tr(array(
					  form(
					       tb(array(
							tr(array("System",form_select("system",$db_system,$db_system,$system),form_input("submit","bytt","Bytt system")
)))))), "bgcolor=\"#e6e6e6\""),
				 tr(array(
					  form(
					       tb(array(
							tr(array("Prioritet",form_select("prioritet",$db_prioritet,$lapper_prioritet,$prioritet),a("Meldingstype","http://www.cisco.com/univercd/cc/td/doc/product/software/ios120/12supdoc/12sems/emover.htm#5002","target=\"blank\""),form_select("type",$db_type,$lapper_felles,$type))),
							tr(array("Bokstype",form_select("bokstype",$db_bokstype,$lapper_bokstype,$bokstype),"Avsender",form_select("boks",$db_boks,$lapper_felles,$boks))),
							tr(array("Fra tidspunkt",form_input("text","tid_fra",$tid_fra,"19","19"),"Til tidspunkt",form_input("text","tid_til",$tid_til,"19","19"))),
							tr(array(italic("Format"),pre("ееее-mm-dd TT:MM:SS"),form_input("hidden","system",$system),form_input("submit","send","Send")." ".a("Nullstill",$PHP_SELF)))
							)
						  ))),
				    "bgcolor=\"#e6e6e6\"")),
			   
			   "width=\"100%\" cellspacing=\"1\" border=\"0\" cellpadding=\"7\" bgcolor=\"#fefefe\""),
			
					  
)
		  ))
	 ,"bgcolor=\"#000000\" border=\"0\" cellpadding=\"0\" cellspacing=\"1\" width=\"1000\"");

if(!$feil){
    print tb(array(
		   tr(array($overstyring))
		   ));
if(($boks&&$type)||($boks&&$logg)||($type&&$logg)){
    #/*logg*/

	list($logg,$ant) = db_select($dbh,"SELECT tid,boks,type,beskrivelse FROM meldinger WHERE $where order by tid desc",1);

	print tb(array(
		       tr(array("Totalt $ant rader funnet i databasen etter gitte kriterier."))
		       ));
	if($ant){
	    print "<table>";
	    foreach(array_keys($logg) as $l){
		print "<tr><td>".$logg[$l][0]."</td><td>".$logg[$l][1]."</td><td>".$logg[$l][2]."</td><td>".$logg[$l][3]."</td></tr>";
	    }
	    print "</table>";
	} else {
	    print "Ingenting е vise";
	}
} elseif($boks||$type||$prioritet){
    #/*statistikk*/
	$boksetabell = db_select($dbh,"SELECT boks, count(*) as count FROM meldinger WHERE $where GROUP BY boks ORDER BY count DESC");

	$meldingstabell = db_select($dbh,"SELECT count(*) FROM meldinger WHERE $where");
	

	$typetabell = db_select($dbh,"SELECT type, count(*) as count FROM meldinger WHERE $where GROUP BY type ORDER BY count DESC");

	$linje = $meldingstabell[0];

	print "<table width=\"100%\"><tr><td align=\"center\" colspan=\"2\">Totalt $linje meldinger";
	if($system){
	    $systemlink = "&system=$system";
	}
	if($prioritet){
	    print " av prioritet $prioritet";
	    $prioritetlink = "&prioritet=$prioritet";
	}
	if($type){
	    $typelink = "&type=$type";
	    print " av type $type";
	}
	if($boks){
	    print " fra boks $boks";
	    $bokslink = "&boks=$boks";
	}
	if($bokstype){
	    print " av bokstype $bokstype";
	    $bokstypelink = "&bokstype=$bokstype";
	}
	$tidlink = "&tid_til=".rawurlencode($tid_til)."&tid_fra=".rawurlencode($tid_fra);


	print ".</td></tr>";

	print "<tr><td width=\"50%\" valign=\"top\"><table>";
	    
	if(sizeof($boksetabell)){

	    foreach(array_keys($boksetabell) as $b){
		print "<tr><td>".a($boksetabell[$b][0],"?vis=tell$tidlink$systemlink$prioritetlink$typelink&boks=".$boksetabell[$b][0])."</td><td>".a($boksetabell[$b][1],"?logg=1$tidlink$systemlink$prioritetlink$typelink&boks=".$boksetabell[$b][0])."</td></tr>";
	    }
	} 

	print "</table></td><td width=\"50%\" valign=\"top\"><table>";

	if(sizeof($typetabell)){

	    foreach(array_keys($typetabell) as $b){
		print "<tr><td>".a($typetabell[$b][0],"?vis=tell$tidlink$systemlink$bokslink$bokstypelink&type=".$typetabell[$b][0])."</td><td>".a($typetabell[$b][1],"?logg=1$tidlink$systemlink$bokslink$bokstypelink&type=".$typetabell[$b][0])."</td></tr>";
	    }
	    
	}

	print "</table></td></tr></table>";

    } else {
	#/*prioritet*/
	if($system){
	    $systemlink = "&system=$system";
	}
	if($bokstype){
	    print " av bokstype $bokstype";
	    $bokstypelink = "&bokstype=$bokstype";
	}
	if($logg = db_select($dbh,"SELECT  prioriteter.prioritet, prioriteter.stikkord, prioriteter.beskrivelse, count(meldinger.id) as count FROM meldinger inner join prioriteter on meldinger.prioritet = prioriteter.prioritet WHERE $where GROUP BY prioriteter.prioritet,prioriteter.stikkord,prioriteter.beskrivelse ORDER BY prioriteter.prioritet")){

	    $tidlink = "&tid_til=".rawurlencode($tid_til)."&tid_fra=".rawurlencode($tid_fra);
	    print "<table>";
	    foreach(array_keys($logg) as $l){
		print "<tr><td>".a("Prioritet ".$logg[$l][0]." - ".$logg[$l][1],"?vis=tell$tidlink$systemlink$bokstypelink&prioritet=".$logg[$l][0])."</td><td>".$logg[$l][2]."</td><td>".$logg[$l][3]."</td></tr>";
	    }
	    print "</table>";
	} else {
	    print "Ingen treff i databasen";
	}

    }
}


print tb(array(
	       tr(array(
			tb(array(
				 tr(array("Juni 2001 - Januar 2002, Sigurd Gartmann, Itea Nett, NTNU"),"bgcolor=\"#e6e6e6\""),
				 ),"width=\"100%\" cellspacing=\"1\" border=\"0\" cellpadding=\"7\" bgcolor=\"#fefefe\"")
		  ))
	       ),"bgcolor=\"#000000\" border=\"0\" cellpadding=\"0\" cellspacing=\"1\" width=\"1000\"");


pg_close($dbh);

print $where;

?>
