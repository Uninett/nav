#!/usr/bin/env perl

use Pg;
use CGI qw(:standard);

require "/usr/local/nav/navme/etc/conf/path.pl";
my $lib = &lib();
require "$lib/database.pl";

print header,start_html("Subnett - grafisk"); 
print "<body bgcolor=white>";

$ovre_gr  = 80;
$nedre_gr = 10;

$adresserom = param('adresserom');

#######################################
# DEFINISJONER

$colspan{23}=8;
$colspan{24}=8;
$colspan{25}=4;
$colspan{26}=2;
$colspan{27}=1;

@liste = (0,32,64,96,128,160,192,224);

$width='11%';

###############################

$conn = &db_connect("manage","navall","uka97urgf");


unless ($adresserom)
{
    $sql = "SELECT nettadr,maske FROM prefiks WHERE nettype='adresserom'";
    
    $ant_adresserom = 0;
    
    $resultat = db_select($conn,$sql);
    
    while(@svar = $resultat->fetchrow)
    {
	$ant_adresserom++;
	
	$adresserom{$ant_adresserom}{nettadr} = $svar[0];
	$adresserom{$ant_adresserom}{maske}   = $svar[1];
    }
    
    if ($ant_adresserom == 1 )
    {
	skriv_adresserom($adresserom{1}{nettadr},$adresserom{1}{maske});
    }
    else
    {
	print "<form action=./subnet2web.pl method=POST>"; 
	print "Velg adresserom som skal vises:";
	print "<select name=adresserom>";
	foreach $key (keys %adresserom)
	{
	    $value = "$adresserom{$key}{nettadr}/$adresserom{$key}{maske}";
	    print "<option value=$value>$value</option>";
	}
	print "</select>";
	print "<input type=submit value=Send>";
	print "</form>";
	
    }
}
else # Det fulgte med adresserom inn, gå direkte til utskrift
{
    ($nettadr,$maske) = split(/\//,$adresserom);
    skriv_adresserom($nettadr,$maske);

}

print end_html;

####################################

sub skriv_adresserom
{
    $nettadr = $_[0];
    $maske   = $_[1];

    $sql = "SELECT prefiksid,nettadr,maske,vlan,antmask,maxhosts,nettype,komm,orgid FROM prefiks";
    
    $res = db_select($conn,$sql);

    @net = split(/\./,$nettadr);
    @netmask = split(/\./,bits_mask($maske));

    for (0..$#net) 
    {
        $b1[$_] = int($net[$_]) & int($netmask[$_]);
    }
    $b1 = join(".",@b1);

    $start = $net[2];
    $slutt = 255 - $netmask[2];

    $bnett = "$net[0].$net[1]";
    
    while (@line=$res->fetchrow)
    {
	@ip=split(/\./,$line[1]);

	for (0..$#ip) 
	{
	    $tip[$_] = int($ip[$_]) & int($netmask[$_]);

	}
	$a1 = join(".",@tip);

	
	if (($a1 eq $b1) && ($line[2] >= $maske))
	{
	    @ipmask = split(/\./,bits_mask($line[2]));
	    
	    $tip[2] = $ip[2] & $ipmask[2];
	    $tip[3] = $ip[3] & $ipmask[3];
	    
	    if ($line[2] > 27)
	    {
		$unntak{$tip[2]}++;
		
	    }

	    if ($line[2] =~ /23|24|25|26|27/)
	    {

		$subnet{$tip[2]}{$tip[3]}{bits} = $line[2];
		$subnet{$tip[2]}{$tip[3]}{vlan} = $line[3];
		$subnet{$tip[2]}{$tip[3]}{mask} = $line[4]||0;
		$subnet{$tip[2]}{$tip[3]}{max}  = $line[5]||1;
		$subnet{$tip[2]}{$tip[3]}{ipadr} = $line[1];
		$subnet{$tip[2]}{$tip[3]}{prefiksid} = $line[0];
		$subnet{$tip[2]}{$tip[3]}{nettype}  = $line[6];
		$subnet{$tip[2]}{$tip[3]}{komm}  = $line[7]||$line[8]||'?';
		
		$subnet{$tip[2]}{$tip[3]}{pros} = int 100*$subnet{$tip[2]}{$tip[3]}{mask}/ $subnet{$tip[2]}{$tip[3]}{max}; 
		
		if ($line[2] == 23)
		{
		    $dob_net{$tip[2]}++;
		}
	    }
	}
    }
    &skriv_tabell;
}


######################################


sub skriv_tabell
{
    
    print "<h2>Adresserom $nettadr/$maske - grafisk</h2>";
    print "Tabellen viser ledige subnett i hvitt.<br>";
    print "Lysgrønn og rosa indikerer hhv utnyttelse på under 10 % eller over 80%.<br>";
    print "Syntax i feltene er nett/maske (aktive maskiner/maxhost/prosent)<p>";
    
    print "Bruk linken til venstre for mer info, statistikk osv.<p>";
    

    print "<table border=1><tr><td width=$width>-</td><td width=$width>0</td><td width=$width>32</td><td width=$width>64</td><td width=$width>96</td><td width=$width>128</td><td width=$width>160</td><td width=$width>192</td><td width=$width>224</td></tr>\n";
    
    
  LINJE: for ($x=$start;$x<=$slutt;$x++)
  {
      
      if ($unntak{$x})
      {
	  print "<tr><td>",&netlink($bnett,$x),"</td><td colspan=8 bgcolor=skyblue>Inneholder nett med maske større enn 27.</td></tr>\n";
	  next LINJE;
      }
      
      if ($dob_net{$x})
      {
	  $y=$liste[0];
	  print "<tr><td>",&netlink($bnett,$x),"</td><td rowspan=2 colspan=8 ";
	  
	  if ($subnet{$x}{$y}{pros}>80)
	  { print "bgcolor=pink "}
	  elsif ($subnet{$x}{$y}{pros}<10)
	  { print " bgcolor=palegreen "}
	  else { print "bgcolor=skyblue "}
	  
	  print "align=center>",&nettinfo($x,$y),"</td></tr>\n";
	  
	  $x++;
	  print "<tr><td>$bnett.$x</td></tr>\n";
	  next LINJE;
      }
      
      # nett på 24,25,26,27 bit.
      
      print "<tr><td>",&netlink($bnett,$x),"</td>";
      for ($i=0;$i<=$#liste;$i++)
      {
	  $y=$liste[$i];
	  
	  if ($subnet{$x}{$y})
	  {
	      print "<td colspan=$colspan{$subnet{$x}{$y}{bits}}";
	      
	      if ($subnet{$x}{$y}{nettype} =~ /statisk|tildelt/)
	      {
		  print " bgcolor=cornsilk align=center>";
		  print &nettinfo($x,$y)," ($subnet{$x}{$y}{nettype}: $subnet{$x}{$y}{komm})";
		  $i = $i + $colspan{$subnet{$x}{$y}{bits}}-1;
		  print "</td>";
	      }
	      else
	      {
		  if ($subnet{$x}{$y}{pros}>80)
		  { print " bgcolor=pink align=center>"}
		  elsif ($subnet{$x}{$y}{pros}<10)
		  { print " bgcolor=palegreen align=center>"}
		  else { print " bgcolor=skyblue align=center>"}
		  
		  print &nettinfo($x,$y);
		  $i = $i + $colspan{$subnet{$x}{$y}{bits}}-1;
		  print "</td>";
	      }
	  }
	  else
	  {
	      print "<td></td>";
	  }
      }
      print "</tr>\n";
      
  }
    print "</table>";
    
}

####################
sub by_number
{
    if ($a < $b)
    { return -1 }
    elsif ($a == $b)
    { return 0 }
    elsif ($a > $b)
    { return 1 }
}
###################

sub netlink
{
    $net="$_[0].$_[1].";

    return "<a href=/ragen/?rapport=prefiks&nettadr=$net%>$net</a>";
}

####################
sub nettinfo
{
    $a = $_[0];
    $b = $_[1];
    return "<a href=/ragen/?rapport=prefiks&prefiksid=$subnet{$a}{$b}{prefiksid}>$subnet{$a}{$b}{ipadr}/$subnet{$a}{$b}{bits} ($subnet{$a}{$b}{mask}/$subnet{$a}{$b}{max}/$subnet{$a}{$b}{pros}\%)</a>";
}

##################################
sub bits_mask
{
    $_ = $_[0];

    if    (/32/)  {return '255.255.255.255';}
    elsif (/31/)  {return '255.255.255.254';}
    elsif (/30/)  {return '255.255.255.252';}
    elsif (/29/)  {return '255.255.255.248';}
    elsif (/28/)  {return '255.255.255.240';}
    elsif (/27/)  {return '255.255.255.224';}
    elsif (/26/)  {return '255.255.255.192';}
    elsif (/25/)  {return '255.255.255.128';}
    elsif (/24/)  {return '255.255.255.0';}
    elsif (/23/) {return '255.255.254.0';}
    elsif (/22/) {return '255.255.252.0';}
    elsif (/21/) {return '255.255.248.0';}
    elsif (/20/) {return '255.255.240.0';}
    elsif (/19/) {return '255.255.224.0';}
    elsif (/18/) {return '255.254.192.0';}
    elsif (/17/) {return '255.255.128.0';}
    elsif (/16/) {return '255.255.0.0';}
    elsif (/15/) {return '255.254.0.0';}
    elsif (/14/) {return '255.252.0.0';}
    elsif (/13/) {return '255.248.0.0';}
    elsif (/12/) {return '255.240.0.0';}
    elsif (/11/) {return '255.224.0.0';}
    elsif (/10/) {return '255.192.0.0';}
    elsif (/9/) {return '255.128.0.0';}
    elsif (/8/) {return '255.0.0.0';}
    elsif (/7/) {return '254.0.0.0';}
    elsif (/6/) {return '252.0.0.0';}
    elsif (/5/) {return '248.0.0.0';}
    elsif (/4/) {return '240.0.0.0';}
    elsif (/3/) {return '224.0.0.0';}
    elsif (/2/) {return '192.0.0.0';}
    elsif (/1/) {return '128.0.0.0';}
    elsif (/0/) {return '0.0.0.0';}
    else  { return 0 ;}
}
