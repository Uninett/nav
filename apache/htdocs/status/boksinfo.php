<?php

require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');

if (!$bruker) {
  $bruker = $PHP_AUTH_USER;
}

$vars = $HTTP_GET_VARS;

$sysName = $vars[sn];

if (!$sysName)
{
  navstart("Boksinfo",$bruker);
  print "SysName mangler!<br>";
}
else
{

  navstart("Boksinfo for $sysName",$bruker);
#  print "SysName: $sysName<br>";

  $dbh = pg_Connect ("dbname=manage user=navall password=uka97urgf");

  boksdata($dbh,$sysName);

}

?>


<?php

navslutt();

?>

<?php

function boksdata($dbh_,$sysName)
{
  
    $sql = "SELECT ip,typeid,boks.romid,rom.descr,sted.descr,kat,kat2,orgid,boksid FROM boks join rom USING (romid) join sted USING (stedid) WHERE sysName='$sysName'";


  $result = pg_exec($dbh_,$sql);
  $rows = pg_numrows($result);

    if ($rows == 0)
  {
    print "<b>Ingen treff på $sysName</b><br>";
  }  
  else
  {
     print "<h2><b>$sysName</b></h2><p>";

     print "<table border=0 cellpadding=2 cellspacing=1>";

     for ($i=0;$i < $rows; $i++) {
       $svar = pg_fetch_row($result,$i);

       $kat = $svar[5];

       print "<tr><td>IP:</td><td>$svar[0]</td></tr>";
       print "<tr><td>Type:</td><td>$svar[1]</td></tr>";
       print "<tr><td>Plassering:</td><td>$svar[2]: $svar[3], $svar[4]</td></tr>";
       print "<tr><td>Kategori:</td><td>$svar[5]</td></tr>";
       print "<tr><td>Kategori2:</td><td>$svar[6]</td></tr>";
       print "<tr><td>Eier/drifter:</td><td>$svar[7]</td></tr>";
     }
     print "</table>";

     print "<a href=./historikk.php?sn=$sysName>Historikk siste 7 dager</a>";

     print "<hr>";

     if ($kat == 'GW')
     {
       gwinfo($dbh_,$sysName,$svar[8]);
     }
     if ($kat == 'SW')
     {
       swinfo($dbh_,$sysName,$svar[8]);
     }


  }
}

#################################
#################################
#################################

function swinfo($dbh_,$sysName,$boksid)
{
  $sql = "SELECT distinct anv.descr,org.descr,vlan FROM swport JOIN swportvlan USING (swportid) JOIN prefiks USING (vlan) JOIN org USING (orgid) JOIN anv USING (anvid) WHERE status='up' AND boksid=$boksid";

  $result = pg_exec($dbh_,$sql);
  $rows = pg_numrows($result);

  if ($rows == 0)
  {
    print "<b>Ingen treff på brukere bak $sysName</b><br>";
  }  
  else
  {
    print "<b>brukere bak $sysName</b><p>";

    print "<table border=0 cellpadding=2 cellspacing=1>";
    print "<tr><th>brukergruppe</th><th>organisasjon</th><th>vlan</th></tr>";
    for ($i=0;$i < $rows; $i++) {
      $svar = pg_fetch_row($result,$i);
      print "<tr><td>$svar[0]</td><td align=center>$svar[1]</td><td align=right>$svar[2]</td></tr>";
    }
    print "</table>";
  }

}
#################################

function gwinfo($dbh_,$sysName,$boksid)
{

  $sql = "SELECT anv.descr,org.descr,nettadr,maske FROM gwport JOIN prefiks USING (prefiksid) JOIN anv USING (anvid) JOIN org USING (orgid) WHERE rootgwid=gwportid AND boksid=$boksid";

  $result = pg_exec($dbh_,$sql);
  $rows = pg_numrows($result);

  if ($rows == 0)
  {
    print "<b>Ingen treff på brukere/nett bak $sysName</b><br>";
  }  
  else
  {
    print "<b>brukere/nett bak $sysName</b><p>";

    print "<table border=0 cellpadding=2 cellspacing=1>";
    print "<tr><th>brukergruppe</th><th>organisasjon</th><th>nett/maske</th></tr>";
    for ($i=0;$i < $rows; $i++) {
      $svar = pg_fetch_row($result,$i);
      print "<tr><td>$svar[0]</td><td align=center>$svar[1]</td><td>$svar[2]/$svar[3]</td></tr>";
    }
    print "</table>";
  }
}

?>