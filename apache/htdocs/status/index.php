<?php
 
#require('meldingssystem.inc');
require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');
 
if (!$bruker) {
#  $bruker = $REMOTE_USER;
  $bruker = $PHP_AUTH_USER; 
}

navstart("Status nå",$bruker);
 
?>


<CENTER><h2>STATUS</h2>


<?php

$dbh = pg_Connect ("dbname=manage user=navall password=uka97urgf");

box($dbh,'boxDown','BOKSER NEDE','red');
box($dbh,'boxShadow','BOKSER I SKYGGE','darkgoldenrod');

?>
<p>
Se <a href="./historikk.php">historikk</a>
<p>
<hr>

<?php
service($dbh);
?>


</CENTER>




<?php

navslutt();

######

function service($dbh_)
{
  $sql = "SELECT sysName,ip,watch FROM boks where active='N'";
  $result = pg_exec($dbh_,$sql);
  $rows = pg_numrows($result);

  $color='blue';

  if ($rows == 0)
  {
    print "<b>INGEN BOKSER PÅ SERVICE</b><br>";
  }
  else
  {
    print "<h3><b>BOKSER PÅ SERVICE</b></h3>";
    print "<table border=0 cellpadding=2 cellspacing=1><caption='Bokser nede'><tr bgcolor=e6e6e6><th>navn</th><th>ip</th><th>Status</th><th>info</th></tr>";

    for ($i=0;$i < $rows; $i++) {
      $svar = pg_fetch_row($result,$i);

      if ($svar[2] == 'f')
      {     
        $svar[2] = 'Up';  # ikke på watch
      }

      if ($svar[2] == 't')
      {     
        $svar[2] = 'Down';  # på watch
      }

      print "<tr>";
      print "<td><font color=$color><a href='./historikk.php?sn=$svar[0]'>$svar[0]</a></td>";
      print "<td><font color=$color>$svar[1]</td>";
      print "<td><font color=$color>$svar[2]</td>";
      print "<td><a href='./boksinfo.php?sn=$svar[0]'><img src='../../pic/info.gif'></a></td>";
      print "</tr>";

    }
    print "</table>"; 
  }
}



###########################################

function box($dbh_,$trap,$header,$color)
{

  $sql = "SELECT sysName,ip,fra,NOW()-fra FROM status join boks using (boksid) WHERE trap='$trap' AND til IS NULL AND boks.active='Y'";

#  print "*$sql*<br>";

  $result = pg_exec($dbh_,$sql);
  $rows = pg_numrows($result);

  if ($rows == 0)
  {
    print "<b>INGEN $header</b><br>";
  }
  else
  {
    print "<h3><b>$header</b></h3>";
    print "<table border=0 cellpadding=2 cellspacing=1><tr bgcolor=e6e6e6><th>navn</th><th>ip</th><th>nede siden</th><th>nedetid</th><th>info</th></tr>";
    for ($i=0;$i < $rows; $i++) {
      $svar = pg_fetch_row($result,$i);

#    $color='red';

      list($svar[2],$dummy) = split("\+",$svar[2],2);

#ereg ("abc", $string);            
#                     /* Returns true if "abc"
#                        is found anywhere in $string. */

#$hour = '17';
#$min  = '45';

      if (ereg ("days",$svar[3]))
      {
        list($day,$dummy) = split("days",$svar[3],2);
        list($hour,$min,$dummy) = split(":",$dummy,3);
      }
      else
      {
        $day = '0';
        list($hour,$min,$dummy) = split(":",$svar[3],3);
      }

    $svar[3] = "$day d $hour h $min min";

    print "<tr>";
    print "<td><font color=$color><a href='./historikk.php?sysName=$svar[0]'>$svar[0]</a></td>";
    print "<td><font color=$color>$svar[1]</td>";
    print "<td><font color=$color>$svar[2]</td>";
    print "<td><font color=$color>$svar[3]</td>";
    print "<td><a href='./boksinfo.php?sn=$svar[0]'><img src='../../pic/info.gif'></a></td>";
    print "</tr>";

    }
    print "</table>"; 
  }
}
 
?>