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

my %boks = &db_hent_hash($db,"SELECT boksid,ip,sysName,typegruppe,watch,ro FROM boks join type using (typeid) WHERE kat=\'SW\'");
my %swport;
my %db_swport = &db_select_hash($db,"swport join boks using (boksid) where kat=\'SW\' AND boksid NOT IN (SELECT boksid FROM boks JOIN type USING(typeid) WHERE typegruppe LIKE '3%' OR typegruppe IN ('cat1900-sw','catmeny-sw'))",\@felt_swport,1,2,3);

my %swportvlan;
my %swportvlantemp;
my %db_swportvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportvlan)." FROM swportvlan");
my %swportallowedvlan;
my %swportallowedvlantemp;
my %db_swportallowedvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportallowedvlan)." FROM swportallowedvlan");

foreach my $boksid (keys %boks) { #$_ = boksid keys %boks
    if($boks{$boksid}[4] =~ /y|t/i) {
	&skriv("SWERR","$boks{$boksid}[2] er på watch. Data blir ikke hentet fra denne svitjsen\n");
    } else {
	if (&snmp_svitsj($boks{$boksid}[1],$boks{$boksid}[5],$boksid,$boks{$boksid}[3],$boks{$boksid}[2]) eq '0') {
	    &skriv("SWERR","Kunne ikke hente data fra $boks{$boksid}[2]\n");
	}
    }
}

#for my $boksid (keys %swport){
#    print "\n".$boksid;
#    for my $interf(keys %{$swport{$boksid}}){
#	print "\n".$interf;
#	for my $port(keys %{$swport{$boksid}{$interf}}){
#	    print "\n".$port;
#	    print "\n".$swport{$boksid}{$interf}{$port}[1]."   ".$swport{$boksid}{$interf}{$port}[2]."   ".$swport{$boksid}{$interf}{$port}[3]."    ".$swport{$boksid}{$interf}{$port}[4];
#	}
#    }
#}

#my $res_begin = $db->exec("begin");

&db_alt($db,3,1,"swport",\@felt_swport,\%swport,\%db_swport,[1,2,3]);

# må leses inn etter at swport er oppdatert
my @feltswportid = ("boksid","modul","port","swportid");
my %swport2swportid = &db_select_hash($db,"swport",\@feltswportid,0,1,2);

#må legge på id fra databasen, ikke bare fake-id som ble brukt i swport.

for my $boks (keys %swportvlantemp) {
    for my $modul (keys %{$swportvlantemp{$boks}}){
	for my $port (keys %{$swportvlantemp{$boks}{$modul}}){
	    my $nyid = $swport2swportid{$boks}{$modul}{$port}[3];
	    if($modul&&$port&&$nyid){
		$swportvlan{$nyid} = [$nyid,$swportvlantemp{$boks}{$modul}{$port}];
	    } else {
		&skriv("SWERR","*(mangler nyid)************ $boks.$modul.$port ****************\n");
	    }
	}
    }
}
for my $boks (keys %swportallowedvlantemp) {
    for my $modul (keys %{$swportallowedvlantemp{$boks}}){
	for my $port (keys %{$swportallowedvlantemp{$boks}{$modul}}){
	    my $nyid = $swport2swportid{$boks}{$modul}{$port}[3];
	    if($modul&&$port&&$nyid){
#		print $nyid."+".$swportallowedvlantemp{$boks}{$modul}{$port}."\n";
		$swportallowedvlan{$nyid} = [$nyid,$swportallowedvlantemp{$boks}{$modul}{$port}];
	    } else {
		&skriv("SWERR","*(mangler nyid)************ $boks.$modul.$port ****************\n");
	    }
	}
    }
}

&db_alt($db,1,0,"swportvlan",\@felt_swportvlan,\%swportvlan,\%db_swportvlan,[0]);
&db_alt($db,1,0,"swportallowedvlan",\@felt_swportallowedvlan,\%swportallowedvlan,\%db_swportallowedvlan,[0]);

#my $res_commit = $db->exec("commit");

#################################################################
sub snmp_svitsj{
    my $ip = $_[0];
    my $ro = $_[1];
    my $boksid = $_[2];
    my $typegruppe = $_[3];
    my $sysname = $_[4];

    my $includefile = "/usr/local/nav/navme/cron/collect/typer/".$typegruppe.".pl";
    if(-r $includefile){

	do $includefile;

	&skriv("SWOUT","henter data for boks nummer $boksid ($typegruppe, $ip, $sysname)\n");

	my @sw = &bulk($ip,$ro,$boksid);

	$swport{$boksid} = \%{$sw[0]};
	$swportvlantemp{$boksid} = \%{$sw[1]};
	$swportallowedvlantemp{$boksid} = \%{$sw[2]};

	return 1; #feilmelding om snmp ellers
    } else {
	&skriv("SWERR","Dette er ikke en kjent typegruppe: $typegruppe\n");
	return 0;
    }
}
