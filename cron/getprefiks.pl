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
my @felt_gwport = ("gwip","boksid","prefiksid","indeks","interf","speed","maxhosts","antmask","ospf","hsrppri","static");
my @felt_prefiks;
my @felt_prefiks_alle =("id","nettadr","maske","vlan","nettype","org","anv","samband","komm");

my %boks;

# Mibs:
my $ip2IfIndex = ".1.3.6.1.2.1.4.20.1.2"; 
my $ip2NetMask = ".1.3.6.1.2.1.4.20.1.3"; 
my $ip2ospf    = ".1.3.6.1.2.1.14.8.1.4";

my $if2AdminStatus = ".1.3.6.1.2.1.2.2.1.7";
my $if2Descr = ".1.3.6.1.2.1.2.2.1.2";
my $if2Speed = ".1.3.6.1.2.1.2.2.1.5";
my $if2Nettnavn = ".1.3.6.1.4.1.9.2.2.1.1.28"; 

my (%lan, %stam, %link);
open VLAN, "</usr/local/nav/etc/vlan.txt";
foreach (<VLAN>){ #peller ut vlan og putter i nettypehasher
    if(/^(\d+)\:lan\,(\S+?)\,(\S+?)$/) {
	$lan{$2}{$3} = $1;
    } elsif (/^(\d+)\:stam\,(\S+?)$/) {
	$stam{$2} = $1;
    } elsif (/^(\d+)\:link\,(\S+?)\,(\S+?)$/) {
	$link{$2}{$3} = $1;
    } else {
	print "\ngikk feil: $_";
    }
    print "\n$1:$2:$3";    
}
close VLAN;

#henter fra database
&hent_prefiksdatabase(); 

foreach (keys %boks) { #$_ = boksid
    if($boks{$_}{watch} =~ /y/i ||$boks{$_}{ip} eq "129.241.194.4") {
	print "$boks{$_}{ip} er på watch.\n";
    } else {
	if (&hent_prefiksdata($_) eq '0') {
	    print "Kunne ikke hente prefiksdata fra $boks{$_}{ip}\n";
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
    
#    print "Hei alle sammen!!!\n";
   
  LINJE: foreach my $f (keys %prefiks)
  {
#	print "Start sammenlign $f\n";
      
      if ($db_prefiks{$f}[6] eq 'Y')  #static
      {
	  delete $db_prefiks{$f};
	  delete $prefiks{$f};
	  next LINJE;
      }

      else # ikke statisk innslag
      {

	  if ($boks{$f}{watch} eq 'Y')   # har ikke fått samlet inn data fra ruter->la være å sjekke innslag.
	  {
	      delete $db_prefiks{$f};
	      delete $prefiks{$f};
	      next LINJE;
	  }
	  else # ip ikke på watch
	  {
	      &sammenlikn_prefiks(\%prefiks, \%db_prefiks, \@felt_prefiks_alle, "prefiks", $f);
	  }
      }
  }
    
}


	      # Eksisterer den i %subnet? ja-> sjekk de forskjellige variablene, nei-> legg inn.
	      # Sjekk og innlegging er avhengig av type nett (link,elink,loopback,lan,stam,hsrp)
sub sammenlikn_prefiks {

    my %ny = %{$_[0]};
    my %gammel = %{$_[1]};
    my @felt = @{$_[2]};
    my $tabell = $_[3];
    my $f = $_[4];
    my $id;

    (my $nettadr, my $maske) = split /:/,$f;
    
    $sql = "select distinct id from prefiks where nettadr=\'$nettadr\' and maske=\'$maske\'";
    $resultat = db_select($sql,$conn);
	
    while (@line=$resultat->fetchrow)
    {
	@line = map rydd($_), @line;
	
	$id = $line[0];
    }
    if (defined($id) && $id ne ""){
#-----------------------
#UPDATE
	for my $i (0..$#felt) {
	    unless($ny{$f}[$i] eq $gammel{$f}[$i]) {
#oppdatereringer til null må ha egen spørring
		if ($ny{$f}[$i] eq "" && $gammel{$f}[$i] ne ""){
		    print "\nOppdaterer $f felt $felt[$i] fra \"$gammel{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE $tabell SET $felt[$i]=null WHERE $felt[0]=\'$ny{$f}[0]\'";
		    db_execute($sql,$conn);
		    print $sql;
		} else {
#normal oppdatering
		    print "\nOppdaterer $f felt $felt[$i] fra \"$gammel{$f}[$i]\" til \"$ny{$f}[$i]\"";
		    $sql = "UPDATE $tabell SET $felt[$i]=\'$ny{$f}[$i]\' WHERE $felt[0]=\'$ny{$f}[0]\'";
		    print $sql;
		    db_execute($sql,$conn);
		}
	    }
	}

    } else {
	
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
#OBS: KAN IKKE SLETTE FRA DATABASEN (pga fillesing)
}


sub hent_prefiksdata {
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
	$tnett{$gwip}{indeks}= $if;
    }
    @lines = &snmpwalk("$ro\@$ip",$if2Nettnavn);

    foreach $line (@lines) {
        ($if,$nettnavn) = split(/:/,$line);
	$if{$if}{nettnavn} = $nettnavn;
#	print $nettnavn."\n" if $nettnavn;

    }    
 
    @lines = &snmpwalk("$ro\@$ip",$if2Descr);

    foreach $line (@lines) {
        ($if,$interf) = split(/:/,$line);
#	print "interf: $interf\n";
	$if{$if}{interf} = $interf;
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


    foreach $gwip (sort by_ip keys %tnett)
    {
#	print "$gwip\n";

	if (!($tnett{$gwip}{maske} == 0))                 #  bits ulik 0 
#ikke ennå	    && ($if{$tnett{$gwip}{indeks}}{status} == 1))# nettet er adm oppe
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

    foreach $gwip (sort by_ip keys %tnett)
    {
	my $id = join (":", ($tnett{$gwip}{nettadr},$tnett{$gwip}{maske}));
	$tnett{$gwip}{vlan} = &finn_vlan( $if{$tnett{$gwip}{indeks}}{nettnavn},$boksid);
#	print $id;
#	print "\n";
	$_ = $if{$tnett{$gwip}{indeks}}{nettnavn};
	
	if(/^lan/i) {
	    ($tnett{$gwip}{nettype},$tnett{$gwip}{org},$tnett{$gwip}{anv},$tnett{$gwip}{komm}) = split /,/;
	    $tnett{$gwip}{nettype} =~ /lan(\d*)/;
	    $tnett{$gwip}{hsrppri} = $1 if defined $1;
	    $prefiks{$id} = [ $tnett{$gwip}{prefiksid},
			      $tnett{$gwip}{nettadr},
			      $tnett{$gwip}{maske},
			      $tnett{$gwip}{vlan},
			      $tnett{$gwip}{nettype}, 
			      $tnett{$gwip}{org}, 
			      $tnett{$gwip}{anv},
			      undef,
			      $tnett{$gwip}{komm}];

	} elsif (/^stam/i) {
	    ($tnett{$gwip}{nettype},$tnett{$gwip}{komm}) = split /,/;
	    $prefiks{$id} = [ $tnett{$gwip}{prefiksid},
			      $tnett{$gwip}{nettadr},
			      $tnett{$gwip}{maske},
			      $tnett{$gwip}{vlan},
			      $tnett{$gwip}{nettype}, 
			      $tnett{$gwip}{org},
			      undef,
			      undef,
			      $tnett{$gwip}{komm}];

	} elsif (/^link/i) {
	    ($tnett{$gwip}{nettype},undef,$tnett{$gwip}{samband},$tnett{$gwip}{komm}) = split /,/;
	    $prefiks{$id} = [ $tnett{$gwip}{prefiksid},
			      $tnett{$gwip}{nettadr},
			      $tnett{$gwip}{maske},
			      $tnett{$gwip}{vlan},
			      $tnett{$gwip}{nettype},
			      undef,
			      undef,
			      $tnett{$gwip}{samband},
			      $tnett{$gwip}{komm}];

	} elsif (/^elink/i) {
	    ($tnett{$gwip}{nettype},undef,$tnett{$gwip}{org},$tnett{$gwip}{samband},$tnett{$gwip}{komm}) = split /,/;
	    $prefiks{$id} = [ $tnett{$gwip}{prefiksid},
			      $tnett{$gwip}{nettadr},
			      $tnett{$gwip}{maske},
			      $tnett{$gwip}{vlan},
			      $tnett{$gwip}{nettype}, 
			      $tnett{$gwip}{org}, 
			      undef,
			      $tnett{$gwip}{samband},
			      $tnett{$gwip}{komm}];

	} elsif (/loopback/i) {
	    $tnett{$gwip}{nettype} = "loopback";
	    $prefiks{$id} = [ $tnett{$gwip}{prefiksid},
			      $tnett{$gwip}{nettadr},
			      $tnett{$gwip}{maske},
			      $tnett{$gwip}{vlan},
			      $tnett{$gwip}{nettype},
			      undef,
			      undef,
			      undef];
	}


    }
}


sub hent_prefiksdatabase {

    $sql = "SELECT id,ip,sysName,watch,ro FROM boks WHERE kat=\'GW\'";
    $resultat = db_select($sql,$conn);

    while (@line=$resultat->fetchrow)
    {
	@line = map rydd($_), @line;

	$boks{$line[0]}{ip}      = $line[1];
        $boks{$line[0]}{sysName} = $line[2];
        $boks{$line[0]}{watch}   = $line[3];
        $boks{$line[0]}{ro}      = $line[4];

    }


 
    $sql = "SELECT ".join(",", @felt_prefiks_alle)." FROM prefiks";
    $resultat = db_select($sql,$conn);

    while (@line=$resultat->fetchrow)
    {
	@line = map rydd($_), @line;
#	print "@line\n";
	my $id = join(":",@line[1..2]);
	$db_prefiks{$id} = [ @line ];

    }


}

sub hent_prefiksid {
    my $id = "";

    $sql = "SELECT distinct id FROM prefiks WHERE nettadr=\'$_[0]\' and maske=\'$_[1]\'";
    $resultat = db_select($sql,$conn);

    while (@line=$resultat->fetchrow)
    {
	@line = map rydd($_), @line;
	$id = $line[0];
    }
    return $id;
}
sub finn_vlan
{
    my $vlan = "";
    my ($boks,undef) = split /\./,$boks{$_[1]}{sysName},2;
    $_ = $_[0];
    if(/^lan\d*\,(\S+?)\,(\S+?)(?:\,|$)/i) {
	$vlan = $lan{$1}{$2};
    } elsif(/^stam\,(\S+?)$/i) {
	$vlan = $stam{$1};
    }elsif(/^link\,(\S+?)(?:\,|$)/i) {
	if (defined($boks)){
	    $vlan = $link{$1}{$boks} || $link{$boks}{$1};
	    print "\n:$vlan:$1:$boks";
	}
    }
    return $vlan;
}


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
#die er byttet med print

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


