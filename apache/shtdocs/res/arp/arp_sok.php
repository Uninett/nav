<?php

require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');
require('/usr/local/nav/local/etc/conf/arp_sok.inc');
require('/usr/local/nav/navme/lib/getdb.php');

$prefixfil = file('/usr/local/nav/local/etc/conf/nav.conf');

foreach ($prefixfil as $linje) {
  if (preg_match("/^IP_PREFIX=(\d+\.\d+\.)/",$linje,$matches)) {
    $prefix = chop($matches[1]);
  }
}

if (!$bruker) {
  $bruker = $PHP_AUTH_USER;
}


$ego = $PHP_SELF;
$dbh = db_get ('status');
$vars = $HTTP_GET_VARS;

if ($vars[prefiksid]) {
  $sok = 'IP';
  $dager = 1;

  list($IPfra,$IPtil) = IPrange($dbh,$prefix,$vars[prefiksid]);
} else {
  $sok    = $vars[sok];
  $dager  = $vars[dager];
  $dns    = $vars[dns];
  $mac    = strtolower ($vars[mac]);
  $IPfra  = $vars[IPfra];
  $IPtil  = $vars[IPtil];
  $alleip = $vars[alleip];
  $nonactive = $vars[nonactive];

  if (!$dager) { $dager = 7; }

}
  
$fra = date("Y-m-d G:i:sO",mktime (0,0,0,date("m")  ,date("d")-$dager,date("Y")));  

navstart("Søk på IP/mac",$bruker);
 
print "<h2>Søk på IP/mac</h2>";

skjema($ego,$prefix,$sok,$dager,$dns,$mac,$IPfra,$IPtil,$alleip,$nonactive);

print "<hr>";

if ($sok == 'IP') {
  ip_sok($ego,$dbh,$prefix,$IPfra,$IPtil,$dns,$dager,$alleip,$nonactive,$fra);
} 

if ($sok == 'mac') {
  mac_sok($ego,$dbh,$mac,$dns,$dager,$prefix,$fra);
}


navslutt();
 

///////////////////////////////////////////////////////////

function mac_sok($ego,$dbh,$mac,$dns,$dager,$prefix,$fra) {
print "<b>MAC: $mac</b><p>";

$mac = ereg_replace (":", "", $mac);
$mac = ereg_replace ("\.", "", $mac);
$mac = ereg_replace ("-", "", $mac);


//////////// Mac-soek: Oppslag i CAM ///////////

$sql = "SELECT boks.sysname,modul,port,mac,fra,til,vlan,boks.ip FROM cam JOIN boks USING (boksid) JOIN prefiks USING (prefiksid) WHERE ";

if ( strlen($mac) == 12 ) {
  $sql = $sql."mac='$mac' ";
} else { 
  $sql = $sql."mac LIKE '$mac%' ";
}

$sql = $sql."and (til='infinity' OR til > '$fra') order by mac,fra DESC";

$result = pg_exec($dbh,$sql);
$rows = pg_numrows($result);

if ($rows == 0) {
  print "<h3>Ikke resultat på søk i cam-tabellen.</h3><p>";
} else {
  print "<h3>Søk i cam-tabellen:</h3><p>";

  print "<font color=red><b>Merk! Også uplinkporter logges.</b></font><br>";
  print "Dette medfører at det kan se ut som om en macadresse er bak flere porter.<p>";

  print "<table>";
  print "<tr><th>mac</th><th>enhet</th><th>unit:port</th><th>fra</th><th>til</th><th></th></tr>";

  for ($i=0;$i < $rows; $i++) {
    $svar = pg_fetch_array($result,$i);


    ereg("(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})",$svar[mac],$regs);
    $mac1 = "$regs[1]:$regs[2]:$regs[3]:$regs[4]:$regs[5]:$regs[6]";

    print "<tr><td><font color=blue><a href=$ego?sok=mac&&type=mac&&dns=$dns&&dager=$dager&&mac=$svar[mac]>$mac1</a></td>";
    print "<td><a href=/res/ragen/?rapport=boks&sysname=$svar[sysname]>$svar[sysname]</a></td>";
    print "<td align=center><a href=/res/ragen/?rapport=swport&sysname=$svar[sysname]>$svar[modul]:$svar[port]</a></td>";
    print "<td><font color=green>$svar[fra]</td><td><font color=red>$svar[til]</td>";

    print "<td>";
    print lenke('mac_cam',$svar);
    print "</td>";

  print "</tr>";
  }
}

print "</table><p>";


/////////////// Mac-soek: Oppslag i ARP //////////////


$sql = "SELECT ip,mac,fra,til FROM arp WHERE ";

if ( strlen($mac) == 12 ) {
  $sql = $sql."mac='$mac' ";
} else { 
  $sql = $sql."mac LIKE '$mac%' ";
}

$sql = $sql."and (til='infinity' OR til > '$fra') order by mac,fra";

  $result = pg_exec($dbh,$sql);
  $rows = pg_numrows($result);
 
  if ($rows == 0) {
    print "<h3>Ingen treff i arp-tabellen</h3>";
  } else {
    print "<h3>Søk i arp-tabellen:</h3><p>";

    $dnsip='heisan';
    print "<TABLE>";
    print "<tr><th>IP</th>";
    if ($dns) { print "<th>dns</th>";}
    print "<th>mac</th><th>fra</th><th>til</th></tr>";

    for ($i=0;$i < $rows; $i++) {
      $svar = pg_fetch_array($result,$i);

      $IPfra = $svar[ip]; 

      print "<tr><td><a href=$ego?sok=IP&&type=IP&&dager=$dager&&dns=$dns&&alleip=$alleip&&IPfra=$IPfra>$svar[ip]</a></td>";
 
      if ($dns) {
         if ($dnsip != $svar[ip]) {
           $dnsip = $svar[ip];
           $dnsname= gethostbyaddr($dnsip);
           if ($dnsname == $dnsip) {
             $dnsname = '-';
           }
         } 
	   
         print "<td><FONT COLOR=chocolate>$dnsname</td>";
      }

      ereg("(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})",$svar[mac],$regs);
      $svar[mac] = "$regs[1]:$regs[2]:$regs[3]:$regs[4]:$regs[5]:$regs[6]";
      
      print "<td><font color=blue><a href=$ego?sok=mac&&type=mac&&dns=$dns&&dager=$dager&&mac=$svar[mac]>$svar[mac]</a></td><td><font color=green>$svar[fra]</td><td><font color=red>$svar[til]</td>";

      print "<td>";
      print lenke('mac_arp',$svar);
      print "</td>";

      print "</tr>";

    }

    print "</TABLE>";

  }
}
//////////////////////////////////////////////////////////////////////////////////////

function ip_sok($ego,$dbh,$prefix,$IPfra,$IPtil,$dns,$dager,$alleip,$nonactive,$fra) {

  if (!$IPfra) {
    print "Gi inn en gyldig fra-IP<br>"; 
  } else { // ip-fra gyldig
    list($a,$b,$c,$d) = split("\.",$IPfra);
    list($e,$f,$g,$h) = split("\.",$IPtil);
    $alist = array($a,$b,$c,$d);
    $blist = array($e,$f,$g,$h);
    $afeil = 'false';
    $bfeil = 'false';

    // Sjekker alle feilmuligheter.
    foreach ($alist as $tall) {
      // Sjekker om det er et tall, og om det er større enn eller lik 256
      if (!preg_match("/\d+/",$tall) or $tall >= '256') { $afeil = 'true'; }
    }
    // Hvis det bare er prefix skal vi videre.
    if ($IPtil != $prefix && $IPtil) {
      foreach ($blist as $tall) {
	// Sjekker om det er et tall, og om det er større enn eller lik 256
	if (!preg_match("/\d+/",$tall) or $tall >= '256') { $bfeil = 'true'; }
      }
    }

    if ($afeil == 'true') {
      print "<b>Det er feil i fra-ip adressen, prøv på nytt.</b><br>";
    } elseif ($bfeil == 'true') {
      print "<b>Det er feil i til-ip adressen, prøv på nytt.</b><br>";
    } else { // feil er false
      if  (!$IPtil or $IPtil == $prefix) {
	$IPtil = $IPfra;
      }

      print "<b>IP fra $IPfra til $IPtil siste $dager dager</b><br>"; 

      $sql = "SELECT ip,mac,fra,til FROM arp WHERE (ip BETWEEN '$IPfra' AND '$IPtil') AND (til='infinity' or til > '$fra') order by ip,fra";
 
      $result = pg_exec($dbh,$sql);
      $rows = pg_numrows($result);
 
      if ($rows == 0) {
	print "<b>Ingen treff</b><br>";
      } else { // treff i ip-soek
	list ($start[0],$start[1],$start[2],$start[3]) = split("\.",$IPfra,4);
	list ($slutt[0],$slutt[1],$slutt[2],$slutt[3]) = split("\.",$IPtil,4);

	$ip = 'heidu';  
	$dnsip = 'heisann';
	for ($i=0;$i < $rows; $i++) {	
	  $svar = pg_fetch_array($result,$i);

	  if ($ip != $svar[0]) {
	    $ip = $svar[ip];
	    $teller = 0;
	  }

	  $data[$svar[0]][$teller][mac] = $svar[mac];
	  $data[$svar[0]][$teller][fra] = $svar[fra];
	  $data[$svar[0]][$teller][til] = $svar[til];
	  $teller++;

	}

	// Skrive resultatet til skjerm!

	print "<table>";
	print "<tr><th>IP</th>";
	if ($dns) { print "<th>dns</th>";}
	print "<th>mac</th><th>fra</th><th>til</th></tr>";

	for ($i1=$start[0];$i1 <= $slutt[0]; $i1++) {
	  for ($i2=$start[1];$i2 <= $slutt[1]; $i2++) {
	    for ($i3=$start[2];$i3 <= $slutt[2]; $i3++) {
	      for ($i4=$start[3];$i4 <= $slutt[3]; $i4++) {
		$ip = "$i1.$i2.$i3.$i4";
		 
		if ($dns) {         
		  if ($dnsip != $ip) {
		    $dnsip = $ip;
		    $dnsname= gethostbyaddr($dnsip);
		    if ($dnsname == $dnsip) {
		      $dnsname = '-';
		    }
		  }
		}
		 
		if ($data[$ip][0][mac]) {
		  if (!$nonactive) {
		    $teller = 0;
		    while ($data[$ip][$teller][mac]) {         
		      print "<tr><td>".$ip."</td><td>";
		       
		      if ($dns) {
			print "<FONT COLOR=chocolate>$dnsname";
			print "</td><td>";
		      }

		      // Setter inn : i mac :)

		      ereg("(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})",$data[$ip][$teller][mac],$regs);
		      $mac = "$regs[1]:$regs[2]:$regs[3]:$regs[4]:$regs[5]:$regs[6]";
		       
		      print "<font color=blue><a href=$ego?sok=mac&&type=mac&&dns=$dns&&dager=$dager&&mac=$mac>";
		      print $mac;
		      print "</td><td>";
		      print "<font color=green>";
		      print $data[$ip][$teller][fra];
		      print "</td><td>";
		      print "<font color=red>";
		      print $data[$ip][$teller][til];
		      print "</td><td>";
		      print lenke('ip_arp',$svar);
		      print "</td></tr>";  
		      $teller++;
		    }
		  }
		} else {
		  if ($alleip == 'on' || $nonactive == 'on') {
		    print "<tr><td>$ip</td><td>";
		    if ($dns) {
		      print "<FONT COLOR=chocolate>$dnsname";
		      print "</td><td>";
		    }
		    print "-</td></tr>";
		  }
		}
	      } // for nr 4
	    } // for nr 3
	  } // for nr 2
	} // for nr 1
	print "</table>";
      } // else treff i ip-soek
    }
  }
} // end function ip_sok

  
//////////////////////////////////////////////////

function skjema ($ego,$prefix,$sok,$dager,$dns,$mac,$IPfra,$IPtil,$alleip,$nonactive) {

  print "<form action=$ego method=GET>";

  if ($sok == 'mac') {
    print "<b>Søk på IP <input type=radio name=sok value=IP>";
    print " mac <input type=radio name=sok value=mac checked></b><br>";
  } else {
    print "<b>Søk på IP <input type=radio name=sok value=IP checked>";
  print " mac <input type=radio name=sok value=mac></b><br>";
  }
  
  if ($IPfra) {
    print "<p><b>IP</b> fra <input type=text size=15 name=IPfra value=$IPfra";
  } else {
    print "<p><b>IP</b> fra <input type=text size=15 name=IPfra value=$prefix";
  }

  if ($IPtil) {
    print "> til <input type=text size=15 name=IPtil value=$IPtil"; 
  } else {
    print "> til <input type=text size=15 name=IPtil value=$prefix"; 
  }

  print "><br>";

  print "<b>Mac</b> <input type=text size=20 name=mac";
  if ($mac) { print " value=$mac";}

  print "><br>";

  print "<table>";

  print "<tr><td>Vis DNS</td><td><input type=checkbox name=dns";
  if ($dns) { print " checked";}
  print "></td></tr>";

  print "<tr><td>Vis alle IP</td><td><input type=checkbox name=alleip";
  if ($alleip) { print " checked";}
  print "></td></tr>";

  print "<tr><td>Vis ikke aktive IP</td><td><input type=checkbox name=nonactive";
  if ($nonactive) { print " checked";}
  print "></td></tr>";

  print "</table>";

  print "Vis siste ";
  print "<input type=text size=3 name=dager value=$dager>  ";
  print " dager<br>";


  print "<input type=submit value=Søk>";

  print "</form>";

}

//////////////////////////////////////////////////

function IPrange($dbh,$prefix,$prefiksid) {

  $sql = "SELECT netaddr FROM prefiks WHERE prefiksid='$prefiksid'"; 

  $result = pg_exec($dbh,$sql);
  $rows = pg_numrows($result);
 
  if ($rows == 0) {
    print "<b>Ukjent prefiksid</b><br>";
  } else {
    for ($i=0;$i < $rows; $i++) {
      $svar = pg_fetch_row($result,$i);
      $svarliste = split("/",$svar[0]);
      if(sizeof($svarliste)<2) {
	$svarliste = array($svarliste[0],32);
      }
      $svar = $svarliste;
      $fra = ereg_replace ($prefix, "", $svar[0]); 
      
      list ($bcast[0],$bcast[1],$bcast[2],$bcast[3]) = split("\.",$svar[0],4);

      if ($svar[1] == 23) {
        $bcast[2] = $bcast[2] + 1;
        $bcast[3] = $bcast[3] + 255; 
      }

      if ($svar[1] == 24) { $bcast[3] = $bcast[3] + 255; }
      if ($svar[1] == 25) { $bcast[3] = $bcast[3] + 127; }
      if ($svar[1] == 26) { $bcast[3] = $bcast[3] + 63; }
      if ($svar[1] == 27) { $bcast[3] = $bcast[3] + 31; }
      if ($svar[1] == 28) { $bcast[3] = $bcast[3] + 15; }
      if ($svar[1] == 29) { $bcast[3] = $bcast[3] + 7; }
      if ($svar[1] == 30) { $bcast[3] = $bcast[3] + 3; }
      if ($svar[1] == 31) { $bcast[3] = $bcast[3] + 1; }

      $til = "$bcast[2].$bcast[3]";

      return array($fra,$til);
     
    }
  }
}
?> 
