#!/usr/bin/perl

use strict;

my $vei = "/usr/local/nav/navme/lib";
require "$vei/database.pl";
require "$vei/snmplib.pl";
require "$vei/fil.pl";
require "$vei/iplib.pl";

my $db = &db_connect("manage","navall","uka97urgf");

my @felt_swport = ("swportid","boksid","ifindex","modul","port","status","speed","duplex","trunk","static","portnavn");
my @felt_swportvlan = ("swportid","vlan");
my @felt_swportallowedvlan = ("swportid","hexstring");

#.iso.org.dod.internet.private.enterprises.cisco.workgroup.stack...
my $Status_catsw   = "1.3.6.1.4.1.9.5.1.4.1.1.6";
my $portName_catsw = "1.3.6.1.4.1.9.5.1.4.1.1.4";
my $Duplex_catsw   = "1.3.6.1.4.1.9.5.1.4.1.1.10";
my $portType_catsw = "1.3.6.1.4.1.9.5.1.4.1.1.5";
my $IfIndex_catsw  = "1.3.6.1.4.1.9.5.1.4.1.1.11";
#stack.vlanGrp.vlanPortTable.vlanPortEntry.vlanPortVlan
my $vlan_catsw     = "1.3.6.1.4.1.9.5.1.9.3.1.3";  
my $trunk_catsw    = "1.3.6.1.4.1.9.5.1.9.3.1.8";
#my $allevlan_catsw = "1.3.6.1.4.1.9.5.1.9.3.1.5";

#mib-2.interfaces.ifTable.ifEntry.ifSpeed
my $Speed = "1.3.6.1.2.1.2.2.1.5";

# For C35xx:
my $portName_iossw = "1.3.6.1.4.1.9.2.2.1.1.28";
my $Status_iossw   = "1.3.6.1.2.1.2.2.1.8";
my $IfIndex_iossw  = "1.3.6.1.2.1.2.2.1.2";
my $vlan_iossw     = "1.3.6.1.4.1.9.9.68.1.2.2.1.2";
my $Duplex_iossw   = "1.3.6.1.4.1.9.9.87.1.4.1.1.32.0";
my $trunk_iossw    = "1.3.6.1.4.1.9.9.87.1.4.1.1.6.0";
#my $allevlan_iossw = "1.3.6.1.4.1.9.9.46.1.6.1.1.4";

my %boks = &db_hent_hash($db,"SELECT boksid,ip,sysName,typegruppe,watch,ro FROM boks natural join type WHERE kat=\'SW\'");
my %swport;
my %db_swport = &db_hent_hash_konkatiner($db,"SELECT ".join(",", @felt_swport)." FROM swport");
my %swportvlan;
my %swportvlanfeilid;
my %db_swportvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportvlan)." FROM swportvlan");
my %swportallowedvlan;
my %swportallowedvlanfeilid;
my %db_swportallowedvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportallowedvlan)." FROM swportallowedvlan");

foreach my $boksid (keys %boks) { #$_ = boksid keys %boks
    if($boks{$boksid}[4] =~ /y|t/i) {
	print "$boks{$boksid}[2] er på watch.\n";
    } else {
	if (&hent_snmpdata($boksid,$boks{$boksid}[3]) eq '0') {
	    print "Kunne ikke hente data fra $boks{$boksid}[2]\n";
	}
    }
}

my %swport2swportid = &db_hent_dobbel($db,"SELECT boksid,ifindex,swportid FROM swport");
&db_endring_spesiell($db,\%swport, \%db_swport, \@felt_swport, "swport");

#skriver bare til skjerm
#foreach my $h (keys %swport2swportid) {
#    foreach my $hu (keys %{$swport2swportid{$h}}) {
#	print "\nSWPORTID $hu = $swport2swportid{$h}{$hu}";
#    }
#}

# må leses inn på nytt etter at swport er oppdatert
%swport2swportid = &db_hent_dobbel($db,"SELECT boksid,ifindex,swportid FROM swport");

#må legge på id fra databasen, ikke bare fake-id som ble brukt i swport.
foreach my $id (keys %swportvlanfeilid) {
    print $id;
    my ($boksid,$ifindex) =  split /\//,$id;    
    my $nyid = $swport2swportid{$boksid}{$ifindex};
    $swportvlan{$nyid} = [$nyid,$swportvlanfeilid{$id}];
}
foreach my $id (keys %swportallowedvlanfeilid) {
    print $id;
    my ($boksid,$ifindex) =  split /\//,$id;
    my $nyid = $swport2swportid{$boksid}{$ifindex};
    $swportallowedvlan{$nyid} = [$nyid,$swportallowedvlanfeilid{$id}];
}

&db_endring($db,\%swportvlan, \%db_swportvlan, \@felt_swportvlan, "swportvlan");

&db_endring($db,\%swportallowedvlan, \%db_swportallowedvlan, \@felt_swportallowedvlan, "swportallowedvlan");





#################################################################
sub hent_snmpdata {
    my $id = $_[0];
    my $typegruppe = $_[1];

 if ($typegruppe eq 'cat-sw') {
#	print "Henter normalt fra ".$typegruppe."\n";
#     print "c";
	unless (&hent_catsw($boks{$id}[1],$boks{$id}[5],$id)) {
	    print "FEIL: ".$boks{$id}[1].$boks{$id}[5].$id."\n";
	}
    }
    elsif ($typegruppe eq 'ios-sw') {
#	print "i";
#	print $typegruppe." er ios-sw\n";
	unless (&hent_iossw($boks{$id}[1],$boks{$id}[5],$id)) {
	    print "FEIL: ".$boks{$id}[1].$boks{$id}[5].$id."\n";
	}
    }
    else {
	print $typegruppe." = ukjent typegruppe\n";  
    }
}

sub hent_catsw {
    my $ip = $_[0];
    my $ro = $_[1];
    my $boksid = $_[2];
    my %modulport2ifindex;
    my %interface;

    my @lines = &snmpwalk("$ro\@$ip",$IfIndex_catsw);
    return(0) unless $lines[0];
    foreach my $line (@lines) {
        (my $mp,my $if) = split(/:/,$line);
	$modulport2ifindex{$mp} = $if;
	$interface{$if}{ifindex} = $if;
#	$interface{$if}{mp} = $mp;
	($interface{$if}{modul}, $interface{$if}{port}) = split /\./,$mp;
#	print "$mp hadde ikke mp" unless $interface{$if}{modul};
    }
    my @lines = &snmpwalk("$ro\@$ip",$Duplex_catsw);
    foreach my $line (@lines) {
        (my $mp,my $duplex) = split(/:/,$line);
	if($duplex == 1){
	    $interface{$modulport2ifindex{$mp}}{duplex} = 'half';   
	} else {
	    $interface{$modulport2ifindex{$mp}}{duplex} = 'full';   
	}
    }    
    my @lines = &snmpwalk("$ro\@$ip",$portType_catsw);
    foreach my $line (@lines) {
        (my $mp,my $pt) = split(/:/,$line);
	$interface{$modulport2ifindex{$mp}}{porttype} = $pt;  
    } 
    my @lines = &snmpwalk("$ro\@$ip",$Status_catsw);
    foreach my $line (@lines)    {
	(my $mp,my $status) = split(/:/,$line);
	if ($status == 2) {
	    $interface{$modulport2ifindex{$mp}}{status} = 'up';
	} else {
	    $interface{$modulport2ifindex{$mp}}{status} = 'down'; 
	}
    }
    my @lines = &snmpwalk("$ro\@$ip",$Speed);
    foreach my $line (@lines)    {
	(my $if,my $speed) = split(/:/,$line);
	$speed = ($speed/1e6);
	$speed =~ s/^(.{0,10}).*/$1/; #tar med de 10 første tegn fra speed
	$interface{$if}{speed} = $speed; 
    }
    my @lines = &snmpwalk("$ro\@$ip",$trunk_catsw);
    foreach my $line (@lines)    {
	(my $mp,my $trunk) = split(/:/,$line);
	if ($trunk == 1){
	    $interface{$modulport2ifindex{$mp}}{trunk} = 't';
	    my ($vlanhex) = &snmpget("$ro\@$ip","1.3.6.1.4.1.9.5.1.9.3.1.5.$mp");
	    $vlanhex = unpack "H*", $vlanhex;
	    $interface{$modulport2ifindex{$mp}}{vlanhex} = $vlanhex;
	} else {
	    $interface{$modulport2ifindex{$mp}}{trunk} = 'f';
	    my ($vlan) = &snmpget("$ro\@$ip",$vlan_catsw.".".$mp);
	    $interface{$modulport2ifindex{$mp}}{vlan} = $vlan;
	}
    }
    my @lines = &snmpwalk("$ro\@$ip",$portName_catsw);
    foreach my $line (@lines) {
	(my $mp,my $portnavn) = split(/\:/,$line,2);
#	print "$line - $portnavn\n";
	$interface{$modulport2ifindex{$mp}}{portnavn} = $portnavn; 
    }
    foreach my $if (keys %interface) {
	unless ($interface{$if}{modul} =~ /Null|Vlan|Tunnel/i) {
	    my $id = join ("/", ($boksid,$if));
	#(my $modul, my $port) = split /\./,$interface{$if}{mp};
	    if(defined($interface{$if}{ifindex})) {
		$swport{$id} = [ $interface{$if}{swportid}, 
				 $boksid,
				 $if,
				 $interface{$if}{modul}, 
				 $interface{$if}{port}, 
				 $interface{$if}{status},
				 $interface{$if}{speed},
				 $interface{$if}{duplex},
				 $interface{$if}{trunk},
				 $interface{$if}{static},
				 $interface{$if}{portnavn}];
	    }
	    if($interface{$if}{vlan}) {
		$swportvlanfeilid{$id} = $interface{$if}{vlan};
	    }
	    if($interface{$if}{vlanhex}) {
		$swportallowedvlanfeilid{$id} = $interface{$if}{vlanhex};
	    }
	}
    }
    return 1; #feilmelding om snmp ellers
}
sub hent_iossw {
    my $ip = $_[0];
    my $ro = $_[1];
    my $boksid = $_[2];
    my %interface;

    my @lines = &snmpwalk("$ro\@$ip",$IfIndex_iossw);
    return(0) unless $lines[0];
    foreach my $line (@lines) {
        (my $if,my $mp) = split(/:/,$line);
	$mp =~ s/FastEthernet/Fa/i;
	$mp =~ s/GigabitEthernet/Gi/i;
	$interface{$if}{ifindex} = $if;
	($interface{$if}{modul}, $interface{$if}{port}) = split /\//,$mp;


    }
    my @lines = &snmpwalk("$ro\@$ip",$Duplex_iossw);
    foreach my $line (@lines) {
        (my $ifi,my $duplex) = split(/:/,$line);
	$ifi++;
	if($duplex == 1){
	    $interface{$ifi}{duplex} = 'full';   
	} else {
	    $interface{$ifi}{duplex} = 'half';   
	}
    }    
    # har ikke mib for porttype
    my @lines = &snmpwalk("$ro\@$ip",$Status_iossw);
    foreach my $line (@lines)    {
	(my $ifi,my $status) = split(/:/,$line);
	if ($status == 1) {
	    $interface{$ifi}{status} = 'up';
	} else {
	    $interface{$ifi}{status} = 'down'; 
	}
    }
    my @lines = &snmpwalk("$ro\@$ip",$Speed);
    foreach my $line (@lines)    {
	(my $if,my $speed) = split(/:/,$line);
	$speed = ($speed/1e6);
	$speed =~ s/^(.{0,10}).*/$1/; #tar med de 10 første tegn fra speed
	$interface{$if}{speed} = $speed; 
    }
    my @lines = &snmpwalk("$ro\@$ip",$trunk_iossw);
    foreach my $line (@lines)    {
	(my $ifi,my $trunk) = split(/:/,$line);
	$ifi++;
	if ($trunk == 0){
	    $interface{$ifi}{trunk} = 't';
	    my ($vlanhex) = &snmpget("$ro\@$ip","1.3.6.1.4.1.9.9.46.1.6.1.1.4.$ifi");
	    $vlanhex = unpack "H*", $vlanhex;
	    $interface{$ifi}{vlanhex} = $vlanhex;
	} else {
	    $interface{$ifi}{trunk} = 'f';
	    my ($vlan) = &snmpget("$ro\@$ip",$vlan_iossw.".".$ifi);
	    $interface{$ifi}{vlan} = $vlan;
	}
    }
    my @lines = &snmpwalk("$ro\@$ip",$portName_iossw);
    foreach my $line (@lines) {
	(my $if,my $portnavn) = split(/:/,$line,2);
	$interface{$if}{portnavn} = $portnavn; 
    }
 
    foreach my $if (keys %interface) {
	unless ($interface{$if}{modul} =~ /Null|Vlan|Tunnel/i) {
	    my $id = join ("/", ($boksid,$if));
	    if(defined($interface{$if}{ifindex})) {
		$swport{$id} = [ $interface{$if}{swportid}, 
				 $boksid,
				 $if,
				 $interface{$if}{modul},
				 $interface{$if}{port},
				 $interface{$if}{status},
				 $interface{$if}{speed},
				 $interface{$if}{duplex},
				 $interface{$if}{trunk},
				 $interface{$if}{static},
				 $interface{$if}{portnavn}];
	    }
	    if($interface{$if}{vlan}) {
		$swportvlanfeilid{$id} = $interface{$if}{vlan};
	    }
	    if($interface{$if}{vlanhex}) {
		$swportallowedvlanfeilid{$id} = $interface{$if}{vlanhex};
	    }
	    
	}
    }
    return 1; #feilmelding om snmp ellers
}
sub db_endring_spesiell {

    my $db = $_[0];
    my %ny = %{$_[1]};
    my %gammel = %{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];

    for my $rad (keys %ny) {
	my $id = $swport2swportid{$ny{$rad}[1]}{$ny{$rad}[2]};
#	print "ID=$id\n";
	&db_endring_per_linje($db,\@{$ny{$rad}},\@{$gammel{$rad}},\@felt,$tabell,$id);
    }
}
