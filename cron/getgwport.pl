#!/usr/bin/perl

use SNMP_util;
use Pg;

use strict;

my $database = "manage";
my $eier = "grohi\@itea.ntnu.no";

my $conn = db_connect($database);
my $sql;
my $resultat;
my @line;
my @lines;
my $line;
my $speed;
my $nettnavn;
my $status;
my $interf;
my %nett = ();
my $nokkel = "gwip";
my %db_gwport = ();
my %gwport = ();
my %db_prefiks = ();
my %prefiks = ();
my @felt_gwport = ("gwip","boksid","prefiksid","ifindeks","interf","speed","ospf","hsrppri");
my %boks;

# Mibs:
my $ip2IfIndex = ".1.3.6.1.2.1.4.20.1.2"; 
my $ip2NetMask = ".1.3.6.1.2.1.4.20.1.3"; 
my $ip2ospf    = ".1.3.6.1.2.1.14.8.1.4";

my $if2AdminStatus = ".1.3.6.1.2.1.2.2.1.7";
my $if2Descr = ".1.3.6.1.2.1.2.2.1.2";
my $if2Speed = ".1.3.6.1.2.1.2.2.1.5";
my $if2Nettnavn = ".1.3.6.1.4.1.9.2.2.1.1.28"; 

#henter fra database
&hent_database(); 

#her er det mye gammelt (fra før GA sin tid)
foreach (keys %boks) { #$_ = boksid
    if($boks{$_}{watch} =~ /y|t/i) {
	print "$boks{$_}{ip} er på watch.\n";
    } else {
	if (&hent_gwdata($_) eq '0') {
	    print "Kunne ikke hente data fra $boks{$_}{ip}\n";
	}
	
    }


}
&oppdat_db();


sub oppdat_db
{
    # To hash; %nett og %db_gwport
    # %gwport er 'naa', %db_gwport er 'forrige'
    # $gwport{$gwip}{xxx}, $db_gwport{$gwip}{xxx}
    # Nettnavn m<E5> splittes i %gwport.
    
    # Vil sammenligne, og evt. legge inn eller slette fra tabell db_gwport i databasen.
    
    # Sammenligne for hver linje i %gwport, slette linjene i %db_gwport etterhvert. Det som ikke er i %gwport, vil v<E6>re
    # igjen i %db_gwport til slutt. Kan da g<E5> gjennom den, og slette linjene.
    
  LINJE: foreach my $f (keys %gwport)
  {
#	print "Start sammenlign $f\n";
      
      if ($db_gwport{$f}[6] eq 't')  #static
      {
	  delete $db_gwport{$f};
	  delete $gwport{$f};
	  next LINJE;
      }

      else # ikke statisk innslag
      {

	  if ($boks{$f}{watch} eq 't')   # har ikke fått samlet inn data fra ruter->la være å sjekke innslag.
	  {
	      delete $db_gwport{$f};
	      delete $gwport{$f};
	      next LINJE;
	  }
	  else # ip ikke på watch
	  {
	      &sammenlikn(\%gwport, \%db_gwport, \@felt_gwport, "gwport", $f);

	  }
      }
  }
}


	      # Eksisterer den i %subnet? ja-> sjekk de forskjellige variablene, nei-> legg inn.
	      # Sjekk og innlegging er avhengig av type nett (link,elink,loopback,lan,stam,hsrp)

#generell ting, bør ligge i modul
sub sammenlikn {

    my %ny = %{$_[0]};
    my %gammel = %{$_[1]};
    my @felt = @{$_[2]};
    my $tabell = $_[3];
    my $f = $_[4];


#eksisterer i databasen?
    if($gammel{$f}[0]) {
#-----------------------
#UPDATE
	for my $i (0..$#felt ) {
	    unless($ny{$f}[$i] eq $gammel{$f}[$i]) {
#oppdatereringer til null må ha egen spørring
		if ($ny{$f}[$i] eq "" && $gammel{$f}[$i] ne ""){
		    print "\nOppdaterer $f felt $felt[$i] fra \"$gammel{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE $tabell SET $felt[$i]=null WHERE $felt[0]=\'$f\'";
		    db_execute($sql,$conn);
		    print $sql;
		} else {
#normal oppdatering
		    print "\nOppdaterer $f felt $felt[$i] fra \"$gammel{$f}[$i]\" til \"$ny{$f}[$i]\"";
		    $sql = "UPDATE $tabell SET $felt[$i]=\'$ny{$f}[$i]\' WHERE $felt[0]=\'$f\'";
		    print $sql;
		    db_execute($sql,$conn);
		}
	    }
	}
    }else{
#-----------------------
#INSERT
	print "\nSetter inn $ny{$f}[0]";
	my @val;
	my @key;
	foreach my $i (0..$#felt) {
	    if (defined($ny{$f}[$i]) && $ny{$f}[$i] ne ""){
		push(@val, "\'".$ny{$f}[$i]."\'");
		push(@key, $felt[$i]);
	    }
	}
	
	$sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	print $sql;
	db_execute($sql,$conn);
    }
    

#-----------------------------------
#DELETE
    for my $g (keys %gammel) {
	unless(exists($ny{$g})) {
	    print "sletter ".$g;
	    $sql = "DELETE FROM $tabell WHERE $nokkel=\'$g\'";
	    print $sql;
	    db_execute($sql,$conn);
	}
    }
}

#snmp-henting: litt mye krypiske ting her.
sub hent_gwdata {
    my $boksid = $_[0];
    my $prefiksid = $_[1];
    my $ruternavn = $boks{$boksid}{sysName};
    my $ip = $boks{$boksid}{ip};
    my $ro = $boks{$boksid}{ro};


    my %if = ();
    my %tnett = ();
    my $gwip;
    my $if;
    my $netmask;
    my $utv_ip;
    my $ospf;
    my @ip;

    @lines = &snmpwalk("$ro\@$ip",$ip2IfIndex);

    unless ($lines[0]) {
	return(0);
    }
    
    foreach $line (@lines) {
        ($gwip,$if) = split(/:/,$line);
	$tnett{$gwip}{ifindeks}= $if;
    }
    @lines = &snmpwalk("$ro\@$ip",$if2Nettnavn);

    foreach $line (@lines) {
        ($if,$nettnavn) = split(/:/,$line);
	$if{$if}{nettnavn} = $nettnavn;
    }     

    @lines = &snmpwalk("$ro\@$ip",$ip2NetMask);
    
    foreach $line (@lines)
    {
        ($gwip,$netmask) = split(/:/,$line);
	$tnett{$gwip}{nettadr} = &and_ip($gwip,$netmask);
	$tnett{$gwip}{maske} = &mask_bits($netmask);
	$tnett{$gwip}{prefiksid} = &hent_prefiksid($tnett{$gwip}{nettadr},
						   $tnett{$gwip}{maske});

    }

    @lines = &snmpwalk("$ro\@$ip",$ip2ospf);

    foreach $line (@lines)
    {
        ($utv_ip,$ospf) = split(/:/,$line);
        if ($utv_ip =~ /\.0\.0$/)
        {
            (@ip) = split(/\./,$utv_ip);
            $gwip = "$ip[0].$ip[1].$ip[2].$ip[3]";

#	    print "$gwip: OSPF: $ospf\n"; 
            if ($tnett{$gwip}{ifindeks})
            {
		$tnett{$gwip}{ospf} = $ospf;
            }
        }
    }  

    @lines = &snmpwalk("$ro\@$ip",$if2Descr);

    foreach $line (@lines) {
        ($if,$interf) = split(/:/,$line);
#	print "interf: $interf\n";

	$if{$if}{interf} = $interf;
    } 
    
    @lines = &snmpwalk("$ro\@$ip",$if2Speed);

    foreach $line (@lines) {
        ($if,$speed) = split(/:/,$line);
	$speed = ($speed/1e6);
	$speed =~ s/^(.{0,10}).*/$1/; #tar med de 10 første tegn fra speed
	$if{$if}{speed} = $speed;
    }

    @lines = &snmpwalk("$ro\@$ip",$if2AdminStatus);
    
    foreach $line (@lines) {                                             
	($if,$status) = split(/:/,$line); 
	$if{$if}{status} = $status;

    }

    foreach $gwip (sort by_ip keys %tnett)
    {
#	print "$gwip\n";

	if (!($tnett{$gwip}{maske} == 0)                 #  bits ulik 0 
	    && ($if{$tnett{$gwip}{ifindeks}}{status} == 1))# nettet er adm oppe
	{
	#    print "$gwip\n";                        
        # Fjerner "gw nummer 2" fra 23-bits nett.
	    if ($tnett{$gwip}{maske} == 23)
	    {
		my @temp = split(/\./,$gwip);
		
		my $temp = $temp[2] & 254;
		
		if ($temp[2] ne $temp)
		{
		    delete $tnett{$gwip};
#		    print "Sletter $gwip\n";
		}
	    }
	}
	else
	{
	    delete $tnett{$gwip};
	}

	

    }
#tar fra hashene tnett og if og legger i gwport
    foreach $gwip (keys %tnett)
    {
	$tnett{$gwip}{interf}   = $if{$tnett{$gwip}{ifindeks}}{interf};
	$tnett{$gwip}{speed}    = $if{$tnett{$gwip}{ifindeks}}{speed};
	$tnett{$gwip}{maxhosts} = &max_ant_hosts($tnett{$gwip}{maske});
	$tnett{$gwip}{antmask}  = &ant_maskiner($gwip,$tnett{$gwip}{netmask},$tnett{$gwip}{maxhosts});

	$_ = $if{$tnett{$gwip}{ifindeks}}{nettnavn};

	$tnett{$gwip}{hsrppri} = "1";
	if(/^lan(\d*)/i) {
	    $tnett{$gwip}{hsrppri} = $1 if $1;
	}
	$gwport{$gwip} = [$gwip,$boksid,$tnett{$gwip}{prefiksid},$tnett{$gwip}{ifindeks},$tnett{$gwip}{interf},$tnett{$gwip}{speed},$tnett{$gwip}{maxhosts},$tnett{$gwip}{antmask},$tnett{$gwip}{ospf},$tnett{$gwip}{hsrppri}];
    }

}

sub hent_database {

    $sql = "SELECT boksid,ip,sysName,watch,ro FROM boks WHERE kat=\'GW\'";
    $resultat = db_select($sql,$conn);

    while (@line=$resultat->fetchrow)
    {
	@line = map rydd($_), @line;

	$boks{$line[0]}{ip}      = $line[1];
        $boks{$line[0]}{sysName} = $line[2];
        $boks{$line[0]}{watch}   = $line[3];
        $boks{$line[0]}{ro}      = $line[4];

    }


    $sql = "SELECT ".join(",", @felt_gwport)." FROM gwport";
    $resultat = db_select($sql,$conn);

    while (@line=$resultat->fetchrow)
    {
	@line = map rydd($_), @line;

	$db_gwport{$line[0]} = [ @line ];

    }
}
sub hent_prefiksid {
    my $id = "";

    $sql = "SELECT distinct prefiksid FROM prefiks WHERE nettadr=\'$_[0]\' and maske=\'$_[1]\'";
    $resultat = db_select($sql,$conn);

    while (@line=$resultat->fetchrow)
    {
	@line = map rydd($_), @line;
	$id = $line[0];
    }
    return $id;
}

#en del gamle smårutinger som kanskje ikke blir brukt en gang.
sub max_ant_hosts
{
    return 0 if($_[0] == 0);
    return(($_ = 2**(32-$_[0])-2)>0 ? $_ : 0);
} 

#ikke akkurat fullstendig
sub ant_maskiner {
    return 1;
}

sub by_ip {
# sorterer paa ip "i samarbeid med" sort-funksjonen
# typisk kall: sort by_ip <...>
    (my $aa,my $ab,my $ac,my $ad)=split(/\./,$a);
    (my $ba,my $bb,my $bc,my $bd)=split(/\./,$b);
 
    if ($ac < $bc){
        return -1;}
    elsif ($ac == $bc)
    {
        if ($ad < $bd)
        {return -1;}
        elsif ($ad == $bd)
        {return 0;}
        elsif ($ad > $bd)
        {return 1;}
    }
    elsif ($ac > $bc) 
    {
        return 1;
    }
 
} # end sub by_ip  
sub and_ip {
    my @a =split(/\./,$_[0]);
    my @b =split(/\./,$_[1]);

    for (0..$#a) {
	$a[$_] = int($a[$_]) & int($b[$_]);
    }
    
    return join(".",@a);
}
sub mask_bits {
    $_ = $_[0];
    if    (/255.255.254.0/)   { return 23; }
    elsif (/255.255.255.0/)   { return 24; }
    elsif (/255.255.255.128/) { return 25; }
    elsif (/255.255.255.192/) { return 26; }
    elsif (/255.255.255.224/) { return 27; }
    elsif (/255.255.255.240/) { return 28; }
    elsif (/255.255.255.248/) { return 29; }
    elsif (/255.255.255.252/) { return 30; }
    elsif (/255.255.255.255/) { return 32; }
    else
    {
        return 0;
    }
}      
sub db_connect {
    my $db = $_[0];
    my $conn = Pg::connectdb("dbname=$db user=navall password=uka97urgf");
    die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
}

sub db_select {
    my $sql = $_[0];
    my $conn = $_[1];
    my $resultat = $conn->exec($sql);
    die "DATABASEFEIL: $sql\n".$conn->errorMessage
	unless ($resultat->resultStatus eq PGRES_TUPLES_OK);
    return $resultat;
}
sub db_execute {
    my $sql = $_[0];
    my $conn = $_[1];
    my $resultat = $conn->exec($sql);
    print "DATABASEFEIL: $sql\n".$conn->errorMessage
	unless ($resultat->resultStatus eq PGRES_COMMAND_OK);
    return $resultat;
}
sub rydd {    
    if (defined $_[0]) {
	$_ = $_[0];
	s/\s*$//;
	s/^\s*//;
    return $_;
    } else {
	return "";
    }
}


