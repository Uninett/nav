#!/usr/bin/perl -w
 
use Pg;
use CGI qw /:standard/;
use Time::Local; 

require "/usr/local/nav/navme/cron/felles.pl"; 

$apache_dir = '/usr/local/nav/navme/apache';
$navstart = "$apache_dir/vhtdocs/navstart.pl";
$navslutt = "$apache_dir/vhtdocs/navslutt.pl";

#print header(-Refresh=>'180; URL=./'), start_html("Status - historikk");

print header(), start_html("Status - historikk");
print "<body bgcolor=white>";


$dager = param("dager") || 7;
$sysName = param("sysName") || '';

$rod = '<font color=red>';
$ora = '<font color=darkgoldenrod>';


@MND = ("januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember");  
@DAY = ("Søndag", "Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag");

###########################################
# Kjører filen navstart, og skriver "print-linjene" til web
print `$navstart`;
###########################################
 
print "<h2><center>STATUS - HISTORIKK</center></h2>";
 
$db = "manage";
$conn = db_connect($db);

if ($sysName)
{
    $string = "<a href=./hist_stat.pl?sysName=$sysName&dager=";
}
else
{
    $string = "<a href=./hist_stat.pl?dager=";
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
print "<br>";


print "<p>";

if ($sysName)
{
    $sql = "SELECT fra,til,sysName,ip,trap,til-fra FROM status join boks using (boksid) WHERE (trap =\'boxDown\' OR trap=\'boxShadow\') AND til is not null AND date_part(\'days\',NOW()-fra)<=$dager AND sysName=\'$sysName\' order by fra desc"; 
}
else
{
    $sql = "SELECT fra,til,sysName,ip,trap,til-fra FROM status join boks using (boksid) WHERE (trap =\'boxDown\' OR trap=\'boxShadow\') AND til is not null AND date_part(\'days\',NOW()-fra)<=$dager order by fra desc"; 
}

$sok = db_select($sql,$conn);


$overskrift ="<table cellspacing=1 border=1 cellpadding=2><tr><td colspan=6>$dato</td></tr><tr><th>Fra</th><th>Til</th><th>sysName</th><th>IP</th><th>Info</th></tr>";

$dato='heisann';
$first  = 1;
$totaltid = 0;
$totalsum = 0;
#$teller = 1;


while (@line = $sok->fetchrow)
{
    if ($line[0] !~ /^$dato/)
    {
	
	unless ($first)
	{
	    if ($sysName) {&skrivtotaltid($sysName, $dato, $totaltid)};
	    print "</table><p>";  
	}
	else
	{
	    $first='';
	}
	($dato,undef) = split(/\s+/,$line[0]);
	$teller = 0;
	if ($sysName) {
	    $totalsum += $totaltid;
	    $totaltid = 0;
	}
	&overskrift($dato);
    }
    
    if ($teller)
    {
	print "<tr bgcolor=\#e6e6e6>";
	$teller='';
    }
    else
    { 
	print "<tr bgcolor=\#ffffff>";
	$teller=1;
    }

#    $tid = &sec2tid($line[5]);

    if ($line[5] =~/days/)
    {
	($day,$dummy,$hour,$min,$sec) = split(/\s|:/,$line[5]);
    }
    else
    {
	($hour,$min,$sec) = split(/:/,$line[5]);
	$day=0;
    }

    $tid = "$day d $hour h $min min";

#    $tid = $line[5];

    if ($sysName) 
    {
	
	$seconds = $sec + 60*$min + 3600*$hour + 24*3600*$day;

	$totaltid += $seconds;
    }

    if ($line[4] eq 'boxDown')
    {
	print "<td>$rod$line[0]</td><td>$rod$line[1]</td><td>$rod$tid</td><td>$rod<a href=./hist_stat.pl?sysName=$line[2]&dager=$dager>$line[2]</a></td><td>$rod$line[3]</td><td><a href=./boks_info.pl?sysName=$line[2]><img src=/pic/info.gif></a></td></tr>";
    }
    else
    {
	print "<td>$ora$line[0]</td><td>$ora$line[1]</td><td>$ora$tid</td><td>$ora<a href=./hist_stat.pl?sysName=$line[2]&dager=$dager>$line[2]</a></td><td>$ora$line[3]</td><td><a href=./boks_info.pl?sysName=$line[2]><img src=/pic/info.gif></a></td></tr>";
    }
}


$rows = $sok->ntuples; 

if ($rows > 0) 
{
    if ($sysName) 
    {
	&skrivtotaltid($sysName, $dato, $totaltid);
    }
    print "</table>";
}

if ($sysName) {
    $totalsum += $totaltid;
    if ($totalsum == 0) 
    {
	print "<P><B>$sysName har ikke vært nede siste $dager dager</B>";
    } else
    {
	print "<P><B>Total nedetid for $sysName siste $dager dager er " . &sec2tid($totalsum) . "</B>";
    }
}

# Avslutter $conn "old style":
PQfinish($conn);

###########################################
# Kjører filen navslutt, og skriver "print-linjene" til web
print `$navslutt`;
###########################################

#print end_html;

##############################
sub overskrift
{

($year, $mon, $mday) = split(/\-/, $_[0]);
$mon--;

$time = timelocal("20", "40", "20", $mday, $mon, $year);   
($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($time);

    print "<table cellspacing=1 border=0 cellpadding=2><tr><td colspan=6 bgcolor=\#486591 align=right><font color=\#ffffff><b>$DAY[$wday] $mday\. $MND[$mon]</b></td></tr><tr bgcolor=\#FAEBD7><th>Fra</th><th>Til</th><th width=80>Nedetid</th><th width=110>sysName</th><th width=100>IP</th><th>Info</th></tr>";


}

################################
sub sec2tid
{
    $sec = $_[0] + 30;#Legger til 30 sek for korrekt avrunding

    $dogn   = int $sec/86400;
    $rest1  = $sec-86400*$dogn;
    $timer  = int $rest1/3600; 
    $rest2  = $rest1-3600*$timer;
    $minutt = int $rest2/60;
 
    $dogn   = 0 unless $dogn;
    $timer  = 0 unless $timer;
    $minutt = 0 unless $minutt;

    $tid_ = "$dogn d $timer h $minutt min";
    return ($tid_);
	
}

##############################
sub skrivtotaltid
{
    $sysname = $_[0];
    $total = sec2tid($_[2]);
    
    ($year, $mon, $mday) = split(/\-/, $_[1]);
    $mon--;
    $time = timelocal("20", "40", "20", $mday, $mon, $year);   
    ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($time);
    
    $dag = $DAY[$wday];
    $dag =~ tr/A-Z/a-z/;
    $datomerke = "$dag $mday\. $MND[$mon]";

    print "<tr><td colspan=6 bgcolor=\#7895c1 align=left><font color=\#ffffff><b>Total nedetid for $sysname $datomerke er $total</b></td></tr>";
}
