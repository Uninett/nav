<?php
 
require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');
 
if (!$bruker) {
  $bruker = $PHP_AUTH_USER;
}
 
$vars = $HTTP_GET_VARS;
 

$sysName = $vars[sn];
$dager   = $vars[dager];

if (!$sysName)
{ $sysName = ''; }

if (!$dager)
{ $dager = 7; }


navstart("Status - historikk",$bruker); 

print "<h2>Status - historikk</h2>";
print "<body bgcolor=white>";

#print "Dager: $dager<br>sysName: $sysName<br>";

#$rod = '<font color=red>';
#$ora = '<font color=darkgoldenrod>';


intro($sysName);

resultat($sysName,$dager);

navslutt();


####################################################

function intro($sn)
{
  $string = "<a href=./historikk.php?";

  if ($sn)
  {
    $string = $string."sn=$sn&dager=";
  }
  else
  {
    $string = $string."dager=";
  }

  print "<i>Antall dager tilbake er default=7.";
  print "Bokser som har vært nede pga skygge er i <font color=darkgoldenrod>oransje</font>.</i><br>Vis siste X dager; X= ";

  print $string.'1>1</a> ';
  print $string.'2>2</a> ';
  print $string.'3>3</a> ';
  print $string.'4>4</a> ';
  print $string.'5>5</a> ';
  print $string.'6>6</a> ';
  print $string.'7>7</a> ';
  print $string.'10>10</a> ';
  print $string.'15>15</a> ';
  print $string.'20>20</a> ';
  print $string.'25>25</a> ';
  print $string.'30>30</a>';
  print "<p>";

}

#############################################

function resultat($sysName,$dager)
{

#@MND = ("januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember");  
#@DAY = ("Søndag", "Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag");


  if ($sysName)
  {
    $sql = "SELECT fra,til,sysName,ip,trap,til-fra FROM status join boks using (boksid) WHERE (trap ='boxDown' OR trap='boxShadow') AND til is not null AND date_part('days',NOW()-fra)<=$dager AND sysName='$sysName' order by fra desc"; 
  }
  else
  {
    $sql = "SELECT fra,til,sysName,ip,trap,til-fra FROM status join boks using (boksid) WHERE (trap ='boxDown' OR trap='boxShadow') AND til is not null AND date_part('days',NOW()-fra)<=$dager order by fra desc"; 
  }

  $dbh = pg_Connect ("dbname=manage user=navall password=uka97urgf"); 

  $result = pg_exec($dbh,$sql);
  $rows = pg_numrows($result);

  if ($rows == 0)
  {
    if ($sysName)
    {
      print "<b>Ingen treff på $sysName siste $dager dager</b><br>";
    }
    else
    {
      print "<b>Ingen treff i nedestatistikken siste $dager dager</b><br>";
    }  
  }
  else
  {
    $dato_ ='heisann';
    $start  = 1;
    $first  = 1;
    $totaltid = 0;
    $totalsum = 0;


    for ($i=0;$i < $rows; $i++) 
    {
       $svar = pg_fetch_row($result,$i);

      # Fjerne tidssone fra 'fra' og 'til'
 
       list($svar[0],$dummy) = split("\+",$svar[0],2);
       list($svar[1],$dummy) = split("\+",$svar[1],2);

       list($dato,$dummy) = split(" ",$svar[0],2);

#       list($year,$month,$day) = split("-",$dato,3);

       if ($dato_ != $dato)
       {
         # Skal ikke avslutte tabell aller første gang.
         if (!$start)
         {
           if ($sysName)
           {
             nedetid($sysName,$dato_,$totaltid);
             $totalsum = $totalsum + $totaltid;
             $totaltid = 0;
           }

           print "</table>";
          

           print "<p>";
         }  
         else
         {
           $start = '';

         }

         $dato_ = $dato;

         overskrift($dato);

       }

       if ($svar[4] == 'boxDown')
       {
         $color = '<font color=red>';
       }
       else
       {
         $color= '<font color=darkgoldenrod>';
       }

# Nedetid:
      if (ereg ("days",$svar[5]))
      {
        list($day,$dummy) = split("days",$svar[5],2);
        list($hour,$min,$dummy) = split(":",$dummy,3);
      }
      else
      {
        $day = '0';
        list($hour,$min,$dummy) = split(":",$svar[5],3);
      }

      $tid = "$day d $hour h $min min";
      if ($sysName)
      {
        $tid_s = $sec + 60*$min + 3600*$hour + 24*3600*$day;
        $totaltid = $totaltid + $tid_s;
      }

       print "<td>$color$svar[0]</td><td>$color$svar[1]</td><td>$color$tid</td><td>$color<a href=./historikk.php?sn=$svar[2]&dager=$dager>$svar[2]</a></td><td>$color$svar[3]</td><td><a href=./boksinfo.php?sn=$svar[2]><img src=/pic/info.gif></a></td></tr>";


     }
   # Avslutte siste tabell:

    if ($sysName)
    {
      nedetid($sysName,$dato_,$totaltid);

      $totalsum = $totalsum + $totaltid;    
      print "</table><p>";
      print "<b>Total nedetid for $sysName siste $dager dager: ";
      sec2tid($totalsum);
      print "<br>";
    }
    else
    {
      print "</table>";
    }



  }
}

###################

function overskrift($dato)
{
#  print "<table cellspacing=1 border=0 cellpadding=2><tr><td colspan=6 bgcolor=\#486591 align=right><font color=\#ffffff><b>$DAY[$wday] $mday\. $MND[$mon]</b></td></tr><tr bgcolor=\#FAEBD7><th>Fra</th><th>Til</th><th width=80>Nedetid</th><th width=110>sysName</th><th width=100>IP</th><th>Info</th></tr>";

  print "<table cellspacing=1 border=0 cellpadding=2><tr><td colspan=6 bgcolor=#486591 align=right><font color=#ffffff><b>$dato</b></td></tr><tr bgcolor=#FAEBD7><th>Fra</th><th>Til</th><th width=80>Nedetid</th><th width=110>sysName</th><th width=100>IP</th><th>Info</th></tr>";

}

function nedetid($sysName,$dato,$sec)
{
      print "<tr><td colspan=6 bgcolor=#7895c1 align=left><font color=#ffffff><b>Nedetid for $sysName $dato: ";
      sec2tid($sec);
      print "</b></td></tr>";
}

function sec2tid($sec)
{
    $sec = $sec + 30;  #Legger til 30 sek for korrekt avrunding

    $dogn   = intval($sec/86400);
    $rest1  = $sec-86400*$dogn;
    $timer  = intval($rest1/3600); 
    $rest2  = $rest1-3600*$timer;
    $minutt = intval($rest2/60);
 
    print "$dogn d $timer h $minutt min";

}
?>