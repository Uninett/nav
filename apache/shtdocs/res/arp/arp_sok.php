<?php

require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');

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
  $sok   = $vars[sok];
  $dager = $vars[dager];
  $dns   = $vars[dns];
  $mac   = $vars[mac];
  $IPfra = $vars[IPfra];
  $IPtil = $vars[IPtil];
}

navstart("Status nå",$bruker);
 
 
print "<h2>Søk på IP/mac</h2>";

skjema($prefix,$sok,$dager,$dns,$mac,$IPfra,$IPtil);

print "<hr>";

#$dbh = pg_Connect ("dbname=manage user=navall password=uka97urgf");

if ($sok == 'IP')
{
  ip_sok($dbh,$prefix,$IPfra,$IPtil,$dns,$dager);
} 

if ($sok == 'mac')
{
  mac_sok($dbh,$mac,$dns,$dager,$prefix);
}


 
navslutt();
 
######


###### ###### ###### ###### ######

function mac_sok($dbh,$mac,$dns,$dager,$prefix)
{
print "<b>MAC: $mac</b><p>";

$mac = ereg_replace (":", "", $mac);
$mac = ereg_replace ("\.", "", $mac);
$mac = ereg_replace ("-", "", $mac);


# # # # # Oppslag i CAM # # # # #

// Connecting, selecting database
$link = mysql_connect("localhost", "nett", "stotte")
                   or print("Kunne ikke koble opp mot MySQL-databasen.");


mysql_select_db("manage");

$sql = "SELECT hub,up,mac,fra,til FROM cam WHERE (mac LIKE '$mac%' AND (TO_DAYS(NOW())-TO_DAYS(til)< '$dager' OR til IS NULL)) ORDER BY mac,fra DESC";

#print "SQL: $sql<br>";

$result = mysql_query($sql);

if (mysql_num_rows($result) == 0)
{
  print "<h3>Ikke resultat på søk i cam-tabellen.</h3><p>";
}
else
{
  print "<h3>Søk i cam-tabellen:</h3><p>";

  print "<font color=red><b>Merk! Også uplinkporter logges.</b><br>";
  print "Dette medfører at det kan se ut som om en macadresse er bak flere porter.<br>";
  print "Vanligvis brukes port x:24 eller x:26 som uplinkport.</font><p>";

  print "<table>";
  print "<tr><th>mac</th><th>enhet</th><th>unit:port</th><th>fra</th><th>til</th></tr>";

  while ($line = mysql_fetch_array($result, MYSQL_ASSOC)) 
  {
    ereg("(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})",$line[mac],$regs);
    $mac1 = "$regs[1]:$regs[2]:$regs[3]:$regs[4]:$regs[5]:$regs[6]";

    print "<tr><td><font color=blue>$mac1</td><td>$line[hub]</td><td align=center>$line[up]</td><td><font color=green>$line[fra]</td><td><font color=red>$line[til]</td></tr>";
  }
}

print "</table><p>";

mysql_close($link);


# # # # # Oppslag i ARP # # # # #

$sql = $sql = "SELECT ip_inet,mac,fra,til FROM arp WHERE mac LIKE '$mac%' and (til is null or date_part('days',cast (NOW()-fra as INTERVAL))<$dager+1) order by mac,fra";

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
      $svar = pg_fetch_row($result,$i);

      $IPfra = ereg_replace ($prefix, "", $svar[0]); 

      print "<tr><td><a href=./arp_sok.php?sok=IP&&type=IP&&dager=$dager&&dns=$dns&&IPfra=$IPfra>$svar[0]</a></td>";
 
      if ($dns)
      {

         if ($dnsip != $svar[0])
         {
           $dnsip = $svar[0];
           $dnsname= gethostbyaddr($dnsip);
           if ($dnsname == $dnsip)
           {
             $dnsname = '-';
           }
         } 
	   
         print "<td><FONT COLOR=chocolate>$dnsname</td>";
       }

       ereg("(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})",$svar[1],$regs);
       $svar[1] = "$regs[1]:$regs[2]:$regs[3]:$regs[4]:$regs[5]:$regs[6]";

 
      print "<td><font color=blue>$svar[1]</td><td><font color=green>$svar[2]</td><td><font color=red>$svar[3]</td></tr>";


    }

    print "</TABLE>";

  }
}
###### ###### ###### ###### ######

function ip_sok($dbh,$prefix,$IPfra,$IPtil,$dns,$dager)
{

if (!$IPfra) {print "Gi inn en gyldig fra-IP<br>"; }
else
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
  else
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
    else
    {
       $dnsip='heisan';
       print "<TABLE>";
       print "<tr><th>IP</th>";
       if ($dns) { print "<th>dns</th>";}
       print "<th>mac</th><th>fra</th><th>til</th></tr>";

       for ($i=0;$i < $rows; $i++) 
       {
         $svar = pg_fetch_row($result,$i);

         print "<tr><td>$svar[0]</td>"; 

         if ($dns)
         {         
	   if ($dnsip != $svar[0])
           {
             $dnsip = $svar[0];
	     $dnsname= gethostbyaddr($dnsip);
             if ($dnsname == $dnsip)
             {
               $dnsname = '-';
             }
           }
	   
           print "<td><FONT COLOR=chocolate>$dnsname</td>";
         }

        # Setter inn : i mac :)

        ereg("(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})",$svar[1],$regs);
        $svar[1] = "$regs[1]:$regs[2]:$regs[3]:$regs[4]:$regs[5]:$regs[6]";

         print "<td><font color=blue><a href=./arp_sok.php?sok=mac&&type=mac&&dns=$dns&&dager=$dager&&mac=$svar[1]>$svar[1]</a></td><td><font color=green>$svar[2]</td><td><font color=red>$svar[3]</td></tr>";
       }
       print "</table>"; 
    }
  }
}

}
###### ###### ###### ###### ######

function skjema ($prefix,$sok,$dager,$dns,$mac,$IPfra,$IPtil)
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