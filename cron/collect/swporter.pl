#!/usr/bin/perl

use strict;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $lib = &lib();
require "$lib/database.pl";
require "$lib/snmplib.pl";
require "$lib/fil.pl";
require "$lib/iplib.pl";

my $debug;

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

my %boks = &db_hent_hash($db,"SELECT boksid,ip,sysName,typegruppe,watch,ro FROM boks natural join type WHERE kat=\'SW\' order by typegruppe");
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
	print "\n\n$boks{$boksid}[2] er på watch. Data blir ikke hentet fra denne svitjsen";
    } else {
	if (&snmp_svitsj($boks{$boksid}[1],$boks{$boksid}[5],$boksid,$boks{$boksid}[3]) eq '0') {
	    warn "Kunne ikke hente data fra $boks{$boksid}[2]\n";
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
    my ($boksid,$ifindex) =  split /\//,$id;    
    my $nyid = $swport2swportid{$boksid}{$ifindex};
    $swportvlan{$nyid} = [$nyid,$swportvlanfeilid{$id}];
}
foreach my $id (keys %swportallowedvlanfeilid) {
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

    unless (&hent_svitsj($boks{$id}[1],$boks{$id}[5],$id,$typegruppe)) {
	print "FEIL: ".$boks{$id}[1].$boks{$id}[5].$id.$typegruppe."\n";
    }
    
}
sub snmp_svitsj{
    my $ip = $_[0];
    my $ro = $_[1];
    my $boksid = $_[2];
    my $typegruppe = $_[3];

    my $includefile = "typer/".$typegruppe.".pl";
    if(-r $includefile){

	do $includefile;
	my %mib = &fil_hent("/usr/local/nav/navme/etc/typegrupper/".$typegruppe.".txt",2);

	print "\nfil $includefile $typegruppe $ip\n";

	my @temp = &ifindex($ip,$ro,\%mib);
	my %interface = %{$temp[0]};
	my %modul = %{$temp[1]};
	my %port = %{$temp[2]};

	my %duplex = %{&duplex($ip,$ro,\%mib,\%interface)};
	my %porttype = %{&porttype($ip,$ro,\%mib,\%interface)};
	my %portname = %{&portname($ip,$ro,\%mib,\%interface)};
	my %status = %{&status($ip,$ro,\%mib,\%interface)};
	my %speed = %{&speed($ip,$ro,\%mib,\%interface)};

	my @temp  = &trunk($ip,$ro,\%mib,\%interface);
	my %trunk = %{$temp[0]};
	my %vlan = %{$temp[1]};
	my %vlanhex = %{$temp[2]};

# hvorfor modul? fordi interface inneholder oversettelsen modulport2interface
	foreach my $i (keys %modul) { 
	    unless ($modul{$i} =~ /Null|Vlan|Tunnel/i) {
		my $id = join ("/", ($boksid,$i));
		#(my $modul, my $port) = split /\./,$interface{$i}{mp};
		if(defined($interface{$i})) {
		    $swport{$id} = [ undef,#$interface{$i}{swportid}, 
				     $boksid,
				     $i,
				     $modul{$i},
				     $port{$i},
				     $status{$i},
				     $speed{$i},
				     $duplex{$i},
				     $trunk{$i},
				     undef,# $static{$i},
				     $portname{$i}];
		}

		print "\n boksid $boksid, interface $i, modul $modul{$i}, port $port{$i}, status $status{$i}, speed $speed{$i}, duplex $duplex{$i}, trunk $trunk{$i}, portname $portname{$i}\n";
		
		if($vlan{$i}){
		    $swportvlanfeilid{$id} = $vlan{$i};
		}
		if($vlanhex{$i}){
		    $swportallowedvlanfeilid{$id} = $vlanhex{$i};
		}
	    }
	    
	}
	return 1; #feilmelding om snmp ellers
    } else {
	warn "Dette er ikke en kjent typegruppe: $typegruppe\n";
	return 0;
    }
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
