<?php

require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');
require('/usr/local/nav/local/etc/conf/arp_sok.inc');

$prefixfil = file('/usr/local/nav/local/etc/conf/prefiks.txt');

foreach ($prefixfil as $linje)
{
  $prefix = chop($linje);
}

if (!$bruker) {
  $bruker = $PHP_AUTH_USER;
}

$dbh = pg_Connect ("dbname=manage user=navall password=uka97urgf");


$vars = $HTTP_GET_VARS;

if ($vars[prefiksid])
{
  $sok = 'IP';
  $dager = 7;

  list($IPfra,$IPtil) = IPrange($dbh,$prefix,$vars[prefiksid]);
}
else
{
  $sok    = $vars[sok];
  $dager  = $vars[dager];
  $dns    = $vars[dns];
  $mac    = $vars[mac];
  $IPfra  = $vars[IPfra];
  $IPtil  = $vars[IPtil];
  $alleip = $vars[alleip];
}

navstart("Søk på IP/mac",$bruker);
 
 
print "<h2>Søk på IP/mac</h2>";

skjema($prefix,$sok,$dager,$dns,$mac,$IPfra,$IPtil,$alleip);

print "<hr>";

if ($sok == 'IP')
{
  ip_sok($dbh,$prefix,$IPfra,$IPtil,$dns,$dager,$alleip);
} 

if ($sok == 'mac')
{
  mac_sok($dbh,$mac,$dns,$dager,$prefix);
}


 navslutt();
 

###### ###### ###### ###### ######

function mac_sok($dbh,$mac,$dns,$dager,$prefix)
{
print "<b>MAC: $mac</b><p>";

$mac = ereg_replace (":", "", $mac);
$mac = ereg_replace ("\.", "", $mac);
$mac = ereg_replace ("-", "", $mac);


# # # # # Mac-soek: Oppslag i CAM # # # # #

$sql = "SELECT boks.sysname,modul,port,mac,fra,til,vlan,boks.ip FROM cam JOIN boks USING (boksid) JOIN prefiks USING (prefiksid) WHERE mac LIKE '$mac%' and (til='infinity' or date_part('days',cast (NOW()-fra as INTERVAL))<$dager+1) order by mac,fra DESC";

$result = pg_exec($dbh,$sql);
$rows = pg_numrows($result);

if ($rows == 0)
{
  print "<h3>Ikke resultat på søk i cam-tabellen.</h3><p>";
}
else
{
  print "<h3>Søk i cam-tabellen:</h3><p>";

  print "<font color=red><b>Merk! Også uplinkporter logges.</b></font><br>";
  print "Dette medfører at det kan se ut som om en macadresse er bak flere porter.<br>";
  print "Vanligvis brukes port x:24 eller x:26 som uplinkport.<p>";

  print "<table>";
  print "<tr><th>mac</th><th>enhet</th><th>unit:port</th><th>fra</th><th>til</th><th></th></tr>";

  for ($i=0;$i < $rows; $i++) 
  {
    $svar = pg_fetch_array($result,$i);


    ereg("(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})",$svar[mac],$regs);
    $mac1 = "$regs[1]:$regs[2]:$regs[3]:$regs[4]:$regs[5]:$regs[6]";

    print "<tr><td><font color=blue><a href=./arp_sok.php?sok=mac&&type=mac&&dns=$dns&&dager=$dager&&mac=$svar[mac]>$mac1</a></td><td>$svar[sysname]</td><td align=center>$svar[modul]:$svar[port]</td><td><font color=green>$svar[fra]</td><td><font color=red>$svar[til]</td>";

  print "<td>";
  print lenke('mac_cam',$svar);
  print "</td>";

  print "</tr>";
  }
}

print "</table><p>";


# # # # # Mac-soek: Oppslag i ARP # # # # #

$sql = "SELECT ip_inet,mac,fra,til FROM arp WHERE mac LIKE '$mac%' and (til is null or date_part('days',cast (NOW()-fra as INTERVAL))<$dager+1) order by mac,fra";

  $result = pg_exec($dbh,$sql);
  $rows = pg_numrows($result);
 
  if ($rows == 0)
  {
    print "<h3>Ingen treff i arp-tabellen</h3>";
  }
  else
  {
    print "<h3>Søk i arp-tabellen:</h3><p>";

    $dnsip='heisan';
    print "<TABLE>";
    print "<tr><th>IP</th>";
    if ($dns) { print "<th>dns</th>";}
    print "<th>mac</th><th>fra</th><th>til</th></tr>";

    for ($i=0;$i < $rows; $i++) 
    {
      $svar = pg_fetch_array($result,$i);

      $IPfra = ereg_replace ($prefix, "", $svar[ip_inet]); 

      print "<tr><td><a href=./arp_sok.php?sok=IP&&type=IP&&dager=$dager&&dns=$dns&&alleip=$alleip&&IPfra=$IPfra>$svar[ip_inet]</a></td>";
 
      if ($dns)
      {

         if ($dnsip != $svar[ip_inet])
         {
           $dnsip = $svar[ip_inet];
           $dnsname= gethostbyaddr($dnsip);
           if ($dnsname == $dnsip)
           {
             $dnsname = '-';
           }
         } 
	   
         print "<td><FONT COLOR=chocolate>$dnsname</td>";
       }

       ereg("(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})",$svar[mac],$regs);
       $svar[mac] = "$regs[1]:$regs[2]:$regs[3]:$regs[4]:$regs[5]:$regs[6]";

 
      print "<td><font color=blue><a href=./arp_sok.php?sok=mac&&type=mac&&dns=$dns&&dager=$dager&&mac=$svar[mac]>$svar[mac]</a></td><td><font color=green>$svar[fra]</td><td><font color=red>$svar[til]</td>";

        print "<td>";
        print lenke('mac_arp',$svar);
        print "</td>";

	print "</tr>";

    }

    print "</TABLE>";

  }
}
###### ###### ###### ###### ######

function ip_sok($dbh,$prefix,$IPfra,$IPtil,$dns,$dager,$alleip)
{

if (!$IPfra) {print "Gi inn en gyldig fra-IP<br>"; }
else # ip-fra gyldig
{
  list($a,$b) = split("\.",$IPfra,2);
  list($c,$d) = split("\.",$IPtil,2);
  $alist = array($a,$b,$c,$d);
  $feil = 'false';
  foreach ($alist as $tall) {
    if ($tall >= '256') { $feil = 'true'; }
  }

  if ($feil == 'true')
  { 
    print "<b>En eller begge IPadressene er ugyldige. Prøv på nytt!</b><br>";
  }
  else # feil er false
  {
    $IPfra = $prefix.$IPfra;
    if  (!$IPtil)
    { $IPtil = $IPfra; }
    else
    { $IPtil = $prefix.$IPtil; }

    print "<b>IP fra $IPfra til $IPtil siste $dager dager</b><br>"; 

    $sql = "SELECT ip_inet,mac,fra,til FROM arp WHERE (ip_inet BETWEEN '$IPfra' AND '$IPtil') AND (til is null or date_part('days',cast (NOW()-fra as INTERVAL))<$dager+1) order by ip_inet,fra";

    $result = pg_exec($dbh,$sql);

    $rows = pg_numrows($result);
 
    if ($rows == 0)
    {
      print "<b>Ingen treff</b><br>";
    }
    else # treff i ip-soek
    {
      list ($start[0],$start[1],$start[2],$start[3]) = split("\.",$IPfra,4);
      list ($slutt[0],$slutt[1],$slutt[2],$slutt[3]) = split("\.",$IPtil,4);

      $ip = 'heidu';  
      $dnsip = 'heisann';
      for ($i=0;$i < $rows; $i++) 
      {	
        $svar = pg_fetch_array($result,$i);

        if ($ip != $svar[0])
        {
          $ip = $svar[ip_inet];
          $teller = 0;
        }

	$data[$svar[0]][$teller][mac] = $svar[mac];
	$data[$svar[0]][$teller][fra] = $svar[fra];
	$data[$svar[0]][$teller][til] = $svar[til];
	$teller++;

      }

      # Skrive resultatet til skjerm!

      print "<table>";
      print "<tr><th>IP</th>";
      if ($dns) { print "<th>dns</th>";}
      print "<th>mac</th><th>fra</th><th>til</th></tr>";

      for ($i1=$start[0];$i1 <= $slutt[0]; $i1++)
      {
       for ($i2=$start[1];$i2 <= $slutt[1]; $i2++)
       {
        for ($i3=$start[2];$i3 <= $slutt[2]; $i3++)
        {
         for ($i4=$start[3];$i4 <= $slutt[3]; $i4++)
         {
           $ip = "$i1.$i2.$i3.$i4";

           if ($dns)
           {         
	     if ($dnsip != $ip)
             {
               $dnsip = $ip;
      	       $dnsname= gethostbyaddr($dnsip);
               if ($dnsname == $dnsip)
               {
                 $dnsname = '-';
               }
             }
           }


           if ($data[$ip][0][mac])
           {
             $teller = 0;
	     while ($data[$ip][$teller][mac])
             {         
               print "<tr><td>".$ip."</td><td>";

	       if ($dns)
               {
	         print "<FONT COLOR=chocolate>$dnsname";
                 print "</td><td>";
               }

	       # Setter inn : i mac :)

               ereg("(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})",$data[$ip][$teller][mac],$regs);
               $mac = "$regs[1]:$regs[2]:$regs[3]:$regs[4]:$regs[5]:$regs[6]";

               print "<font color=blue><a href=./arp_sok.php?sok=mac&&type=mac&&dns=$dns&&dager=$dager&&mac=$mac>";
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
           else
           {
             if ($alleip)
             {
  	       print "<tr><td>$ip</td><td>";
               if ($dns)
               {
	         print "<FONT COLOR=chocolate>$dnsname";
                 print "</td><td>";
               }
               print "-</td></tr>";
             }
           }
         } # for nr 4
        }  # for nr 3
       }   # for nr 2
      }    # for nr 1
      print "</table>";
    }      # else treff i ip-soek
  }
 }
}  # end function ip_sok

  
###### ###### ###### ###### ######

function skjema ($prefix,$sok,$dager,$dns,$mac,$IPfra,$IPtil,$alleip)
{

$dagarray = array(1,2,3,4,5,6,7,10,15,20,25,30);
$defaultdager = '7';

if ($dager)
{
  $defaultdager = $dager;
}

print "<form action=arp_sok.php method=GET>";

if ($sok == 'mac')
{
  print "<b>Søk på IP <input type=radio name=sok value=IP>";
  print " mac <input type=radio name=sok value=mac checked></b><br>";
}
else
{
  print "<b>Søk på IP <input type=radio name=sok value=IP checked>";
  print " mac <input type=radio name=sok value=mac></b><br>";
}

print "<p><b>IP</b> fra $prefix<input type=text size=7 name=IPfra";

if ($IPfra) { print " value=$IPfra";}

print "> til $prefix<input type=text size=7 name=IPtil";
if ($IPtil) { print " value=$IPtil";}

print "><br>";

print "<b>Mac</b> <input type=text size=20 name=mac";
if ($mac) { print " value=$mac";}

print "><br>";

print "Vis DNS <input type=checkbox name=dns";

if ($dns) { print " checked";}

print "><br>";

print "Vis alle IP <input type=checkbox name=alleip";

if ($alleip) { print " checked";}

print "><br>";


print "Vis siste ";

print "<select name=dager>";

foreach ($dagarray as $element) {
    if ($element == $defaultdager) {
      print "<option value=$element selected>$element</option>\n";
    } else {
      print "<option value=$element>$element</option>\n";
    }
  }
print "</select>";
print " dager<br>";

print "<input type=submit value=Søk>";
#print "<input type=reset value=Reset>";

print "</form>";

}

############################################

function IPrange($dbh,$prefix,$prefiksid)
{

  $sql = "SELECT nettadr,maske FROM prefiks WHERE prefiksid='$prefiksid'"; 

  $result = pg_exec($dbh,$sql);
  $rows = pg_numrows($result);
 
  if ($rows == 0)
  {
    print "<b>Ukjent prefiksid</b><br>";
  }
  else
  {
    for ($i=0;$i < $rows; $i++) 
    {
      $svar = pg_fetch_row($result,$i);

      $fra = ereg_replace ($prefix, "", $svar[0]); 

      list ($bcast[0],$bcast[1],$bcast[2],$bcast[3]) = split("\.",$svar[0],4);

      if ($svar[1] == 23)
      {
        $bcast[2] = $bcast[2] + 1;
        $bcast[3] = $bcast[3] + 255; 
      }

      if ($svar[1] == 24)
      { $bcast[3] = $bcast[3] + 255; }
      if ($svar[1] == 25)
      { $bcast[3] = $bcast[3] + 127; }
      if ($svar[1] == 26)
      { $bcast[3] = $bcast[3] + 63; }
      if ($svar[1] == 27)
      { $bcast[3] = $bcast[3] + 31; }
      if ($svar[1] == 28)
      { $bcast[3] = $bcast[3] + 15; }
      if ($svar[1] == 29)
      { $bcast[3] = $bcast[3] + 7; }
      if ($svar[1] == 30)
      { $bcast[3] = $bcast[3] + 3; }
      if ($svar[1] == 31)
      { $bcast[3] = $bcast[3] + 1; }

      $til = "$bcast[2].$bcast[3]";

     return array($fra,$til);

    }
  }
}
?> 