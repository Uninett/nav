#!/usr/bin/perl

use strict;

my $vei = "/usr/local/nav/navme/lib";
require "$vei/database.pl";
require "$vei/snmplib.pl";
require "$vei/fil.pl";
require "$vei/iplib.pl";

my $ip2IfIndex     = ".1.3.6.1.2.1.4.20.1.2"; 
my $ip2NetMask     = ".1.3.6.1.2.1.4.20.1.3"; 
my $ip2ospf        = ".1.3.6.1.2.1.14.8.1.4";
my $if2AdminStatus = ".1.3.6.1.2.1.2.2.1.7";
my $if2Descr       = ".1.3.6.1.2.1.2.2.1.2";
my $if2Speed       = ".1.3.6.1.2.1.2.2.1.5";
my $ifInOctet      = ".1.3.6.1.2.1.2.2.1.10";
my $ifAlias        = ".1.3.6.1.2.1.31.1.1.1.18";
my $hsrp_status    = ".1.3.6.1.4.1.9.9.106.1.2.1.1.15";
my $hsrp_rootgw    = ".1.3.6.1.4.1.9.9.106.1.2.1.1.11";

my $db = &db_connect("manage","navall","uka97urgf");

my @felt_prefiks =("prefiksid","nettadr","maske","vlan","antmask","maxhosts","nettype","orgid","anvid","nettident","komm");
my @felt_gwport = ("gwportid","boksid","ifindex","gwip","interf","masterindex","speed","ospf");

my (%lan, %stam, %link);
&fil_vlan;

my %prefiksid = &db_hent_dobbel($db,"SELECT nettadr,maske,prefiksid FROM prefiks");
my %boks = &db_hent_hash($db,"SELECT boksid,ip,sysName,watch,ro FROM boks WHERE kat=\'GW\'");

my %boks2prefiks;
my %prefiks;
my %db_prefiks = &db_select_hash($db,"prefiks",\@felt_prefiks,1,2);

my %gwport;
my %db_gwport = &db_select_hash($db,"gwport",\@felt_gwport,1,2,3);

foreach my $boksid (keys %boks) { #$_ = boksid keys %boks
    if($boks{$boksid}[3] =~ /y|t/i) {
	print "$boks{$boksid}[2] er på watch.\n";
    } else {
	if ( &hent_snmpdata($boksid) eq '0' ) {
	    print "Kunne ikke hente data fra $boks{$boksid}[2]\n";
	}
    }
}

for my $nettadr ( keys %prefiks ) {
#    print "\nboks".$boks;
    for my $maske (keys %{$prefiks{$nettadr}}) {
#	print "\nifindex".$ifindex;
	&db_manipulate($db,1,"prefiks",\@felt_prefiks,\@{$prefiks{$nettadr}{$maske}},\@{$db_prefiks{$nettadr}{$maske}},$nettadr,$maske);
    }
}

#nå som alle prefiksene er samlet inn, vil det være på sin plass å sette dem inn i boks.

my %nettadr2prefiksid = &db_hent_enkel($db,"SELECT nettadr,prefiksid FROM prefiks");

&oppdater_prefiks($db,"boks","ip","prefiksid");

#oppdaterer gwport, men tar ikke med prefiksid i denne omgang. Det må gjøres seinere fordi det ikke er snmpinnsamlinga skjedde samtidig med prefiks, og da var det ikke noe prefiksid å få tak i.
for my $boks ( keys %gwport ) {
    for my $ifindex (keys %{$gwport{$boks}}) {
	for my $gwip (keys %{$gwport{$boks}{$ifindex}}) {
#	    for my $innhold (@{$db_gwport{$boks}{$ifindex}{$gwip}}) {
#		print "$innhold|";
#	    }
	    &db_manipulate($db,1,"gwport",\@felt_gwport,\@{$gwport{$boks}{$ifindex}{$gwip}},\@{$db_gwport{$boks}{$ifindex}{$gwip}},$boks,$ifindex,$gwip);
	}
    }
}

#prefiksid i gwport oppdateres her
&oppdater_prefiks($db,"gwport","gwip","prefiksid");

my %prefiksid2rootgwid = &db_hent_enkel($db,"SELECT prefiksid,rootgwid FROM prefiks");
my %gwip2gwportid = &db_hent_enkel($db,"SELECT gwip,gwportid FROM gwport");
my %prefiksid2gwip =  &db_hent_enkel($db,"select prefiksid,min(gwip) from gwport natural join prefiks where nettadr < gwip group by prefiksid");

foreach my $prefiksid (keys %prefiksid2gwip) {
    my $gammel = $prefiksid2rootgwid{$prefiksid};
    my $ny = $gwip2gwportid{$prefiksid2gwip{$prefiksid}};
    unless ($ny eq $gammel) {
	&db_oppdater($db,"prefiks","rootgwid",$gammel,$ny,"prefiksid",$prefiksid);
    }
}

######################################
sub hent_snmpdata {
    my $boksid = $_[0];
    my $ip = $boks{$boksid}[1];
    my $ro = $boks{$boksid}[4];
    my %interface = ();
    my %gatewayip = ();
    my %id;
    my %boks;

    my @lines = &snmpwalk("$ro\@$ip",$ip2IfIndex);
    return(0) unless $lines[0];
    foreach my $line (@lines) {
        (my $gwip,my $if) = split(/:/,$line);
#	print "\n$boksid:$if:gwip:",
	$interface{$if}{gwip} = $gwip;
	$gatewayip{$gwip}{ifindex} = $if;
    }
    my @lines = &snmpwalk("$ro\@$ip",$ifAlias);
    foreach my $line (@lines) {
        (my $if,my $nettnavn) = split(/:/,$line);
#	print "nettnavn $nettnavn\n\n";
	$interface{$if}{nettnavn} = $nettnavn;
    }    
    my @lines = &snmpwalk("$ro\@$ip",$if2Descr);
    my %description;
    foreach my $line (@lines) {
        (my $if,my $interf) = split(/:/,$line);
	$interface{$if}{interf} = $interf;
	my ($masterinterf,$subinterf) = split/\./,$interf;
	if($subinterf){
	    $interface{$if}{master} = $description{$masterinterf};
	} else {
	    $description{$masterinterf} = $if;
	}
    } 
    my @lines = &snmpwalk("$ro\@$ip",$ip2NetMask);
    foreach my $line (@lines)
    {
        (my $gwip,my $netmask) = split(/:/,$line);
	$gatewayip{$gwip}{netmask} = $netmask;
	$gatewayip{$gwip}{nettadr} = &and_ip($gwip,$netmask);
	$gatewayip{$gwip}{maske} = &mask_bits($netmask);
	$gatewayip{$gwip}{prefiksid} = 
	    &hent_prefiksid($gatewayip{$gwip}{nettadr},
			    $gatewayip{$gwip}{maske});
    }
#over: prefiks& under: gwport
    my @lines = &snmpwalk("$ro\@$ip",$if2Speed);
    foreach my $line (@lines) {
        (my $if,my $speed) = split(/:/,$line);
	$speed = ($speed/1e6);
	$speed =~ s/^(.{0,10}).*/$1/; #tar med de 10 første tegn fra speed
	$interface{$if}{speed} = $speed;
    }
    my @lines = &snmpwalk("$ro\@$ip",$if2AdminStatus);
    foreach my $line (@lines) {                                             
	(my $if,my $status) = split(/:/,$line); 
	$interface{$if}{status} = $status;
    }
    my @lines = &snmpwalk("$ro\@$ip",$ifInOctet);
    foreach my $line (@lines) {                                             
	(my $if,my $octet) = split(/:/,$line); 
	$interface{$if}{octet} = $octet;
#	$gatewayip{0.0.0.0}{ifindex} = $if;
    }
    my @lines = &snmpwalk("$ro\@$ip",$ip2ospf);
    foreach my $line (@lines) {
        (my $utv_ip,my $ospf) = split(/:/,$line);
        if ($utv_ip =~ /\.0\.0$/){
            my (@ip) = split(/\./,$utv_ip);
            my $gwip = "$ip[0].$ip[1].$ip[2].$ip[3]";
            if ($gatewayip{$gwip}{ifindex}){
		$gatewayip{$gwip}{ospf} = $ospf;
#	    print "OSPF $gwip\t$ospf\n";
	    }
        }
    }  
# hsrpgw-triksing
    my @lines = &snmpwalk("$ro\@$ip",$hsrp_status);
    foreach my $line (@lines) {
	(my $if,undef,my $hsrpstatus) = split(/:|\./,$line);    
	if($hsrpstatus == 6) {
	    my ($rootgwip) = &snmpget("$ro\@$ip",$hsrp_rootgw.".".$if.".0");
#	    print "\n$boksid:$if:nhsrp:",
	    $interface{$if}{gwip} = $rootgwip;
	}
    }


#GA må svare for denne
#går ut på å slette gw2 fra 23-bits nett
    foreach my $gwip (keys %gatewayip) {
		if (!($gatewayip{$gwip}{maske} == 0))  #  bits ulik 0 
#ikke ennå	    && ($interface{$gatewayip{$gwip}{index}}{status} == 1))# nettet er adm oppe
	{
        # Fjerner "gw nummer 2" fra 23-bits nett.
	    if ($gatewayip{$gwip}{maske} == 23) {
		my @temp = split(/\./,$gwip);
		my $temp = $temp[2] & 254;
		if ($temp[2] ne $temp){
		    delete $gatewayip{$gwip};
#		    print "Sletter $gwip\n";
		}
	    }
	}
	else
	{
	    delete $gatewayip{$gwip};
	}
    }
    foreach my $if ( keys %interface ) {
	if($interface{$if}{octet}&&!$interface{$if}{gwip}){
	    $gwport{$boksid}{$if}{""} = [ undef,
					  $boksid,
					  $if,
					  undef,
					  $interface{$if}{interf},
					  $interface{$if}{master},
					  $interface{$if}{speed},
					  undef];
	}
    }
    foreach my $gwip ( keys %gatewayip ) {
	print "$gwip\n";
	my $if = $gatewayip{$gwip}{ifindex};
	my $interf = $interface{$if}{interf};
	my $ospf = $gatewayip{$gwip}{ospf};
	print "m|".$interface{$if}{master}."|\n";
	$gwport{$boksid}{$if}{$gwip} = [ undef,
					 $boksid,
					 $if,
					 $gwip,
					 $interf,
					 $interface{$if}{master},
					 $interface{$if}{speed},
					 $ospf];
    }


    foreach my $if (keys %interface)
    {
	my $nettadr = $gatewayip{$interface{$if}{gwip}}{nettadr};
	my $maske = $gatewayip{$interface{$if}{gwip}}{maske};
	my $netmask = $gatewayip{$interface{$if}{gwip}}{netmask};
	my $vlan = &finn_vlan($interface{$if}{nettnavn},$boksid);
	my $maxhosts = &max_ant_hosts($maske);
	my $antmask= &ant_maskiner($interface{$if}{gwip},
						  $netmask,
						  $maxhosts);
#	$boks2prefiks{$boksid} = $id if $nettadr && $maske;

	my $interf = $interface{$if}{interf};
	$_ = $interface{$if}{nettnavn};
	
	if(/^lan/i) {
	    my ($nettype,$org,$anv,$komm) = split /,/;
	    $nettype = &rydd($nettype);
	    $nettype =~ s/lan(\d*)/lan/i;
	    $org = &rydd($org);
	    $org =~ s/^(\w*?)\d*$/$1/;
#	    print "Q$org";
	    $anv = &rydd($anv);
	    $anv =~ s/^(\w*?)\d*$/$1/;
#	    print "W$anv";
	    $prefiks{$nettadr}{$maske} = [ undef, $nettadr, $maske, 
					   $vlan, $antmask, $maxhosts, 
					   $nettype,$org,$anv,
					   &rydd($interface{$if}{nettnavn}),
					   &rydd($interface{$if}{komm})];

	} elsif (/^stam/i) {
	    my ($nettype,$stamnavn,$komm) = split /,/;
	    $prefiks{$nettadr}{$maske} = [ undef, $nettadr, $maske,
					   $vlan, $antmask, $maxhosts,
					   $nettype, undef, undef,
					   &rydd($interface{$if}{stamnavn}),
					   &rydd($interface{$if}{komm})];

	} elsif (/^link/i) {
	    my ($nettype,$samband,$komm) = split /,/;
	    $prefiks{$nettadr}{$maske} = [ undef, $nettadr, $maske,
					   $vlan, $antmask, $maxhosts,
					   $nettype, undef, undef,
					   &rydd($interface{$if}{samband}),
					   &rydd($interface{$if}{komm})];

	} elsif (/^elink/i) {
	    my ($nettype,$org,$samband,$komm) = split /,/;
	    $prefiks{$nettadr}{$maske} = [ undef, $nettadr, $maske,
					   $vlan, $antmask, $maxhosts,
					   $nettype, $org, undef,
					   &rydd($interface{$if}{samband}),
					   &rydd($interface{$if}{komm})];

	} elsif ($interf =~ /loopback/i) {
#	    print "har funnet loopback";
	    my $nettype = "loopback";
	    $prefiks{$nettadr}{$maske} = [ undef, $nettadr, $maske,
					   $vlan, $antmask, $maxhosts,
					   $nettype, undef, undef,
					   undef, undef ];
	}
	else {
#	    print "har funnet ukjent $_";
	    my $nettype = "ukjent";
	    $prefiks{$nettadr}{$maske} = [ undef, $nettadr, $maske,
					   $vlan, $antmask, $maxhosts,
					   $nettype, undef, undef,
					   undef, undef ];
	}

    }
}



 


sub fil_vlan{

    open VLAN, "</usr/local/nav/etc/vlan.txt";
    foreach (<VLAN>){ #peller ut vlan og putter i nettypehasher
	if(/^(\d+)\:lan\,(\S+?)\d*\,(\S+?)\d*$/) {
	    $lan{$2}{$3} = $1;
	} elsif (/^(\d+)\:stam\,(\S+?)$/) {
	    $stam{$2} = $1;
	} elsif (/^(\d+)\:link\,(\S+?)\,(\S+?)$/) {
	    $link{$2}{$3} = $1;
	} else {
#	    print "\ngikk feil: $_";
	}
#	print "\n$1:$2:$3";    
    }
    close VLAN;
}
sub finn_vlan
{
    my $vlan = "";
    my ($boks,undef) = split /\./,$boks{$_[1]}[2],2;
    $_ = $_[0];
    if(/^lan\d*\,(\S+?)\,(\S+?)(?:\,|$)/i) {
	$vlan = $lan{$1}{$2};
    } elsif(/^stam\,(\S+?)$/i) {
	$vlan = $stam{$1};
    }elsif(/^link\,(\S+?)(?:\,|$)/i) {
	if (defined($boks)){
	    $vlan = $link{$1}{$boks} || $link{$boks}{$1};
#	    print "\n:$vlan:$1:$boks";
	}
    }
    return $vlan;
}

sub hent_prefiksid {
    my ($nettadr,$maske) = @_;
    return $prefiksid{$nettadr}{$maske};
}
sub max_ant_hosts
{
    return 0 if($_[0] == 0);
    return(($_ = 2**(32-$_[0])-2)>0 ? $_ : 0);
} 
sub ant_maskiner {
    return 1;
}

sub finn_prefiksid {
    # Tar inn ip, splitter opp og and'er med diverse
    # nettmasker. Målet er å finne en match med en allerede innhentet
    # prefiksid (hash over alle), som så returneres.
    my $ip = $_[0];
    my @masker = ("255.255.255.255","255.255.255.254","255.255.255.252","255.255.255.248","255.255.255.240","255.255.255.224","255.255.255.192","255.255.255.128","255.255.255.0","255.255.254.0","255.255.252.0");
    foreach my $maske (@masker) {
	my $nettadr = &and_ip($ip,$maske);
	return $nettadr2prefiksid{$nettadr} if (defined $nettadr2prefiksid{$nettadr});
    }
    # print "Fant ikke prefiksid for $ip\n";
    return 0;
}

sub oppdater_prefiks{
    my ($db,$tabell,$felt_fast,$felt_endres) = @_;
    my %iper = &db_hent_enkel($db,"SELECT $felt_fast,$felt_endres FROM $tabell");
    foreach my $ip (keys %iper) {
	my $prefiksid = &finn_prefiksid($ip);
#	print "$iper{$ip} eq $prefiksid\n";
	unless ($iper{$ip} eq $prefiksid || $iper{$ip} == 0) {
#	    print "$tabell - $felt_endres - $iper{$ip} - $prefiksid - $felt_fast - $ip\n";
	     &db_oppdater($db,$tabell,$felt_endres,$iper{$ip},$prefiksid,$felt_fast,$ip);
	 }
    }
}

return 1;

