#!/usr/bin/perl

use strict;
require '/usr/local/nav/navme/lib/NAV.pm';
import NAV qw(:DEFAULT :collect);

my $lib = get_path("path_lib");
my $path_collect = get_path("path_collect");
require $lib."snmplib.pl";
require $lib."iplib.pl";

&log_open;

my $debug;

my $db = &db_get("swporter");

my @felt_module = ("netboxid","module");
my @felt_swport = ("moduleid","port","ifindex","link","speed","duplex","trunk","portname");
my @felt_swportvlan = ("swportid","vlan");
my @felt_swportallowedvlan = ("swportid","hexstring");

my %boks = &db_hent_hash($db,"SELECT netboxid,ip,sysname,typegroupid,up,ro FROM netbox join type using (typeid) WHERE catid=\'SW\'");
my %swport;
my %db_swport = &db_select_hash($db,"swport join module using (moduleid) join netbox using (netboxid) where catid=\'SW\' AND netboxid NOT IN (SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE typegroupid LIKE '3%' OR typegroupid IN ('cat1900-sw','catmeny-sw'))",\@felt_swport,0,1);

my %swportvlan;
my %swportvlantemp;
my %db_swportvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportvlan)." FROM swportvlan");
my %swportallowedvlan;
my %swportallowedvlantemp;
my %db_swportallowedvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportallowedvlan)." FROM swportallowedvlan");

foreach my $boksid (keys %boks) { #$_ = boksid keys %boks
    if($boks{$boksid}[4] =~ /n|f/i) {
	&skriv("DEVICE-WATCH","ip=".$boks{$boksid}[2]);
    } else {
	if (&snmp_svitsj($boks{$boksid}[1],$boks{$boksid}[5],$boksid,$boks{$boksid}[3],$boks{$boksid}[2]) eq '0') {
	    &skriv("DEVICE-BOXDOWN","ip=".$boks{$boksid}[2]);
	}
    }
}
### MODULE
my %db_module = &get_module;
my %module;
for my $sw (keys %swport){
    for my $mo (keys %{$swport{$sw}}){
	$module{$sw}{$mo} = [ $sw, $mo ];
	print $sw."   ".$mo."\n" if $debug;
    }
}
&db_safe(connection => $db,table => "module",fields => \@felt_module,index=>["netboxid","module"],new => \%module, old => \%db_module, delete => 1, insert => "device");


### skal bruke moduleid
my %moduleid = &db_hent_dobbel($db,"select netboxid,module,moduleid from module");
my %port;
for my $sw (keys %swport){
    for my $mo (keys %{$swport{$sw}}){
	for my $po (keys %{$swport{$sw}{$mo}}){
	    my $moduleid = $moduleid{$sw}{$mo};
	    $port{$moduleid}{$po} = [$moduleid,$po,@{$swport{$sw}{$mo}{$po}}];
	}
    }
}
&db_safe(connection => $db,table => "swport",fields => \@felt_swport,index => ["moduleid","port"], new => \%port, old => \%db_swport, delete => 1);



# swport må leses inn etter at swport er oppdatert for å få med swportid
my %swport2swportid = &get_swportid;

#må legge på id fra databasen, ikke bare fake-id som ble brukt i swport.

for my $boks (keys %swportvlantemp) {
    for my $modul (keys %{$swportvlantemp{$boks}}){
	for my $port (keys %{$swportvlantemp{$boks}{$modul}}){
	    my $nyid = $swport2swportid{$boks}{$modul}{$port};
	    if($modul&&$port&&$nyid){
		$swportvlan{$nyid} = [$nyid,$swportvlantemp{$boks}{$modul}{$port}];
	    } else {
		&skriv("DEBUG-NOID","ip=$boks","module=$modul","port=$port");
	    }
	}
    }
}
for my $boks (keys %swportallowedvlantemp) {
    for my $modul (keys %{$swportallowedvlantemp{$boks}}){
	for my $port (keys %{$swportallowedvlantemp{$boks}{$modul}}){
	    my $nyid = $swport2swportid{$boks}{$modul}{$port};
	    if($modul&&$port&&$nyid){
#		print $nyid."+".$swportallowedvlantemp{$boks}{$modul}{$port}."\n";
		$swportallowedvlan{$nyid} = [$nyid,$swportallowedvlantemp{$boks}{$modul}{$port}];
	    } else {
		&skriv("DEBUG-NOID","ip=$boks","module=$modul","port=$port");
	    }
	}
    }
}

&db_safe(connection => $db,delete => 0,table => "swportvlan",fields => \@felt_swportvlan, new => \%swportvlan,old => \%db_swportvlan);
&db_safe(connection => $db,delete => 0,table => "swportallowedvlan",fields => \@felt_swportallowedvlan,new => \%swportallowedvlan,old => \%db_swportallowedvlan);

#my $res_commit = $db->exec("commit");

&log_close;

#################################################################
sub snmp_svitsj{
    print "hei";
    my $ip = $_[0];
    my $ro = $_[1];
    my $boksid = $_[2];
    my $typegruppe = $_[3];
    my $sysname = $_[4];

    my $includefile = $path_collect."typer/".$typegruppe.".pl";
    if(-r $includefile){

	do $includefile ||  print $!;
	&skriv("DEVICE-COLLECT","ip=$ip");

	my @sw = &bulk($ip,$ro,$boksid);

	$swport{$boksid} = \%{$sw[0]};
	$swportvlantemp{$boksid} = \%{$sw[1]};
	$swportallowedvlantemp{$boksid} = \%{$sw[2]};

	return 1; #feilmelding om snmp ellers
    } else {
	&skriv("SWITCH-TYPEGRP","typegroup=$typegruppe","ip=$ip");
	return 1;
    }
}

sub get_swportid{

    my $sql = "select module.netboxid,module,port,swportid from module inner join swport using (moduleid)";
    my %resultat;
    my $res =  &db_select($db,$sql);
    while(@_ = $res->fetchrow) {
	$resultat{$_[0]}{$_[1]}{$_[2]} = $_[3] ;
    }
    return %resultat;
}

sub get_module{

    my $sql = "select netboxid,module from module";
    my %resultat;
    my $res =  &db_select($db,$sql);
    while(@_ = $res->fetchrow) {
	$resultat{$_[0]}{$_[1]} = [ $_[0],$_[1] ] ;
    }
    return %resultat;
}
