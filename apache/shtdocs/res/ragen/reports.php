<?php

require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');
if (!$bruker) {
  $bruker = $PHP_AUTH_USER;
}
navstart("Rapporter",$bruker);
?>


<h1>Rapporter</h1>
 
<ul>
<li> <a href="/res/ragen/?rapport=netbox"> Utstyrsregister</a> (alt
utstyr)
  <ul>
  <li> <a href="/res/ragen/?rapport=type"> Liste over utstyrstyper</a>
  <li> <a href="/res/ragen/?rapport=gw"> Kun rutere (GW/GSW)</a>
  <li> <a href="/res/ragen/?rapport=sw"> Kun svitsjer (SW/GSW)</a>
  <li> <a href="/res/ragen/?rapport=netbox&kat=KANT"> Kun kantutstyr 
(KANT)</a>
  <li> <a href="/res/ragen/?rapport=wlan"> Kun trådløst (WLAN)</a>
  <li> <a href="/res/ragen/?rapport=srv"> Kun servere (SRV)</a>
  <li> <a href="/res/ragen/?rapport=servicemon"> Tjenester som overvåkes </a>
  <li> <a href="/res/ragen/?rapport=oppsop"> Resten</a>
  </ul>
<li> 
     <a href="/res/ragen/?rapport=prefix"> Brukte subnett 
/ prefiks / vlan</a>. Liste over 
<a href="/res/ragen/?rapport=gwport"> ruterporter</a>.
<li> <a href="/res/ragen/?rapport=swportv"> Svitsjeporter</a>, kun
     <a href="/res/ragen/?rapport=swportt"> svitsjeporter som er trunk</a>
<li> 
<a href="/res/ragen/?rapport=modultype"> modultyper</a>,
<a href="/res/ragen/?rapport=modules"> moduler</a>,
     <a href="/res/ragen/?rapport=mem"> minne/flash</a>
<li> <a href="/res/ragen/?rapport=room"> Rom</a>,
 <a href="/res/ragen/?rapport=location"> Sted</a>
<li> <a href="/res/ragen/?rapport=org"> Organisasjon</a>,
 <a href="/res/ragen/?rapport=usage"> Anvendelsestyper for subnett</a>
 
 </ul>

<?php
 /*
Lagt til av Sigurd: Liste over lokale rapporter.
 */
function verify(){
    global $PHP_AUTH_USER;
    $passordfil = "/usr/local/nav/local/apache/htpasswd/.htpasswd-sec";
    $fd = fopen ($passordfil,"r");
    $funnet = 0;
    while (!$funnet&&!feof($fd)) {
	$buffer = fgets($fd, 4096);
	if(preg_match("/^$PHP_AUTH_USER\:/i",$buffer)){
	    $funnet = 1;
	}
    }
    fclose ($fd);
    return $funnet;
}
function les_fil($fil,$var){
##############
## Leser fra fil til en lang tekstreng
##############
    $filinnhold = "";
    if(is_readable($fil)){
	$fp = fopen($fil,$var);
	$filinnhold = fread($fp,filesize($fil));
	fclose($fp);
    }
    return $filinnhold;
}
function tolk_fil($fil,$allowed=0){
#############
## Behandler tekststreng og putter inn i hasher
#############
  $local_reports = array();
    if($allowed){
	if(preg_match_all("/^\s*([\w\ \t]+?)(?:\_sec)?\s*{(.*?)}/sm",$fil,$regs)){
	  for($a=0;$a<sizeof($regs[0]);$a++){
	  $reportid = $regs[1][$a];
	    $var = $regs[2][$a];
	    //print $var;
	    preg_match_all("/^\#{0}\s*\\\$(\S+?)\s*=\W*\"(.+?)\"\s*\;/smi",$var,$para);
	    for ($i = 0; $i<sizeof($para[0]); $i++) {
	      if(!strcasecmp($para[1][$i],"overskrift")){
		$reportname = $para[2][$i];
		$local_reports[$reportid] = $reportname;
	      }
	    }
	  }
	}
    } else {
	if(preg_match_all("/^\s*([\w\ \t]+?)\s*{(.*?)}/sm",$fil,$regs)){
	  for($a=0;$a<sizeof($regs[0]);$a++){
	  $reportid = $regs[1][$a];
	    $var = $regs[2][$a];
	    //print $var;
	    preg_match_all("/\#{0}\s*\\\$(\S+?)\s*=\W*\"(.+?)\"\s*\;/smi",$var,$para);
	    for ($i = 0; $i<sizeof($para[0]); $i++) {
	      if(!strcasecmp($para[1][$i],"overskrift")){
		$reportname = $para[2][$i];
		$local_reports[$reportid] = $reportname;
	      }
	    }
	  }
	}
    }

    return $local_reports;
}
 
$local_file = les_fil("/usr/local/nav/local/etc/conf/ragen/ragen.conf","r");
$global_file = les_fil("/usr/local/nav/navme/etc/conf/ragen/ragen.conf","r");

$allowed = verify();
$local_reports = tolk_fil($local_file,$allowed);
$global_reports = tolk_fil($global_file,$allowed);

foreach (array_keys($local_reports) as $local_key){
  if($global_reports[$local_key]){
    $local_reports[$local_key] = "";
  }

}

print "\n\n<h3>Lokale rapporter</h3>\n<ul>";

foreach($local_reports as $id => $name){
  if($name){
    print "\n\t<li><a href=\"index.php?rapport=$id\">".ucfirst($name)."</a></li>";
  }
}
print "\n</ul>";

?>

<h3>Snarveier</h3>

<b>Søk etter:</b>
<table>
<tr>
  <form action="./?rapport=netbox" method=POST>
  <td>utstyr i telematikkrom:</td>
  <td><input type=text name=roomid size=15></td>
  <td><input type=submit value="Søk"></td>
  </form>
</tr>
<tr>
  <form action="./?rapport=netbox" method=POST>
  <td>ip-adresse (% wildcard):</td>
  <td><input type=text name=host(ip) size=15></td>
  <td><input type=submit value="Søk"></td>
  </form>
</tr>
<tr>
  <form action="./?rapport=swportv" method=POST>
  <td>utbredelse av vlan (ikke wildcard):</td>
  <td><input type=text name=vlan size=15></td>
  <td><input type=submit value="Søk"></td>
  </form>
</tr>
</table>

<?php


navslutt();
?>
