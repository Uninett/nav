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

my @felt_swport = ("swportid","boksid","modul","port","ifindex","status","speed","duplex","trunk","portnavn");
my @felt_swportvlan = ("swportid","vlan");
my @felt_swportallowedvlan = ("swportid","hexstring");

my %boks = &db_hent_hash($db,"SELECT boksid,ip,sysName,typegruppe,watch,ro FROM boks join type using (typeid) WHERE kat=\'SW\' order by typegruppe");
my %swport;
my %db_swport = &db_select_hash($db,"swport join boks using (boksid) where kat=\'SW\'",\@felt_swport,1,2,3);

my %swportvlan;
my %swportvlantemp;
my %db_swportvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportvlan)." FROM swportvlan");
my %swportallowedvlan;
my %swportallowedvlantemp;
my %db_swportallowedvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportallowedvlan)." FROM swportallowedvlan");

foreach my $boksid (keys %boks) { #$_ = boksid keys %boks
    if($boks{$boksid}[4] =~ /y|t/i) {
	&skriv("SWERR","\n\n$boks{$boksid}[2] er på watch. Data blir ikke hentet fra denne svitjsen");
    } else {
	if (&snmp_svitsj($boks{$boksid}[1],$boks{$boksid}[5],$boksid,$boks{$boksid}[3]) eq '0') {
	    &skriv("SWERR","Kunne ikke hente data fra $boks{$boksid}[2]\n");
	}
    }
}
#for my $boksid (keys %swport){
#    for my $interf(keys %{$swport{$boksid}}){
	#print "\n".$swport{$boksid}{$interf}[1]."   ".$swport{$boksid}{$interf}[2]."   ".$swport{$boksid}{$interf}[3]."    ".$swport{$boksid}{$interf}[4];
#    }
#}

my $res_begin = $db->exec("begin");

&db_alt($db,3,0,"swport",\@felt_swport,\%swport,\%db_swport);

#skriver bare til skjerm
#foreach my $h (keys %swport2swportid) {
#    foreach my $hu (keys %{$swport2swportid{$h}}) {
#	print "\nSWPORTID $hu = $swport2swportid{$h}{$hu}";
#    }
#}

# må leses inn etter at swport er oppdatert
my @feltswportid = ("boksid","modul","port","swportid");
my %swport2swportid = &db_select_hash($db,"swport",\@feltswportid,0,1,2);

#my %swport2swportid = &db_hent_dobbel($db,"SELECT boksid,ifindex,swportid FROM swport");

#må legge på id fra databasen, ikke bare fake-id som ble brukt i swport.
for my $boks (keys %swportvlantemp) {
    for my $modul (keys %{$swportvlantemp{$boks}}){
	for my $port (keys %{$swportvlantemp{$boks}{$modul}}){
	    my $nyid = $swport2swportid{$boks}{$modul}{$port}[3];
	    $swportvlan{$nyid} = [$nyid,$swportvlantemp{$boks}{$modul}{$port}];
	}
    }
}
for my $boks (keys %swportallowedvlantemp) {
    for my $modul (keys %{$swportallowedvlantemp{$boks}}){
	for my $port (keys %{$swportallowedvlantemp{$boks}{$modul}}){
	    my $nyid = $swport2swportid{$boks}{$modul}{$port}[3];
	    $swportallowedvlan{$nyid} = [$nyid,$swportallowedvlantemp{$boks}{$modul}{$port}];
	}
    }
}
&db_alt($db,1,0,"swportvlan",\@felt_swportvlan,\%swportvlan,\%db_swportvlan);

#&db_endring($db,\%swportvlan, \%db_swportvlan, \@felt_swportvlan, "swportvlan");
&db_alt($db,1,0,"swportallowedvlan",\@felt_swportallowedvlan,\%swportallowedvlan,\%db_swportallowedvlan);

#&db_endring($db,\%swportallowedvlan, \%db_swportallowedvlan, \@felt_swportallowedvlan, "swportallowedvlan");


my $res_commit = $db->exec("commit");


#################################################################
sub hent_snmpdata {
    my $id = $_[0];
    my $typegruppe = $_[1];

    unless (&hent_svitsj($boks{$id}[1],$boks{$id}[5],$id,$typegruppe)) {
	&skriv("SWERR","FEIL: ".$boks{$id}[1].$boks{$id}[5].$id.$typegruppe."\n");
    }
    
}
sub snmp_svitsj{
    my $ip = $_[0];
    my $ro = $_[1];
    my $boksid = $_[2];
    my $typegruppe = $_[3];

    my $includefile = "/usr/local/nav/navme/cron/collect/typer/".$typegruppe.".pl";
    if(-r $includefile){

	do $includefile;
	my %mib = &fil_hent("/usr/local/nav/navme/etc/typegrupper/".$typegruppe.".txt",2);

	&skriv("SWOUT","\nBOKS: $ip, fil $includefile, $typegruppe $ip\n");

	my @temp = &ifindex($ip,$ro,\%mib);
	my %ifindex = %{$temp[0]};
	my %interface = %{$temp[1]};

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
	for my $modul (keys %ifindex) { 
	    for my $port(keys %{$ifindex{$modul}}){
		$swport{$boksid}{$modul}{$port} = [ undef,#$interface{$interface}{swportid}, 
						    $boksid,
						    $modul,
						    $port,
						    $ifindex{$modul}{$port},
						    $status{$modul}{$port},
						    $speed{$modul}{$port},
						    $duplex{$modul}{$port},
						    $trunk{$modul}{$port},
						    undef,# $static{$interface},
						    $portname{$modul}{$port}];
		
		&skriv("SWOUT","\n$ip boksid $boksid, interface $ifindex{$modul}{$port}, modul $modul, port $port, status $status{$modul}{$port}, speed $speed{$modul}{$port}, duplex $duplex{$modul}{$port}, trunk $trunk{$modul}{$port}, portname $portname{$modul}{$port}\n");
		
#		my $id = join ("/", ($boksid,$ifindex{$modul}{$port}));
		if($vlan{$modul}{$port}){
		    $swportvlantemp{$boksid}{$modul}{$port} = $vlan{$modul}{$port};
		}
		if($vlanhex{$modul}{$port}){
		    $swportallowedvlantemp{$boksid}{$modul}{$port} = $vlanhex{$modul}{$port};
		}
		
	    }
	}
	return 1; #feilmelding om snmp ellers
    } else {
	&skriv("SWERR","Dette er ikke en kjent typegruppe: $typegruppe\n");
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
	&db_endring_per_linje($db,\@{$ny{$rad}},\@{$gammel{$rad}},\@felt,$tabell,$id);
    }
}
