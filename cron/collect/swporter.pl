#!/usr/bin/perl
####################
#
# $Id: swporter.pl,v 1.13 2002/11/26 11:14:07 gartmann Exp $
# This file is part of the NAV project.
# swporter gets a list of devices from the database. If the devices are central
# switches, plugin-scripts which aquire SNMP-information are started according
# to the switch's typegroup. The results from these plugins are used when
# updating the database.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;
require '/usr/local/nav/navme/lib/NAV.pm';
import NAV qw(:DEFAULT :collect :snmp);

my $path_collect = get_path("path_collect");

&log_open;

my $debug =1;

# tar inn en parameter som er en ip-adresse på formen bokser.pl ip=123.456.789.0
my $one_and_only = shift;

if($one_and_only){ #har sann verdi
    if($one_and_only =~ /^(\d+\.\d+\.\d+\.\d+)$/i){
	$one_and_only = $1;
    } else {
	die("Invalid ip-address: $one_and_only\n");
	$one_and_only = "no";
    }
}
print $one_and_only."\n" if $debug;

my $db = &db_get("swporter");

my @felt_module = ("netboxid","module");
my @felt_swport = ("moduleid","port","ifindex","link","speed","duplex","trunk","portname");
my @felt_swportvlan = ("swportid","vlan");
my @felt_swportallowedvlan = ("swportid","hexstring");

my %boks;
if($one_and_only){
    %boks = &db_hent_hash($db,"SELECT netboxid,ip,sysname,typegroupid,up,ro FROM netbox join type using (typeid) WHERE (catid=\'SW\' OR catid=\'GSW\' OR catid=\'KANT\') AND up='y' AND ip='$one_and_only' AND netboxid NOT IN (SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE typegroupid LIKE '3%' OR typegroupid IN ('cat1900-sw','catmeny-sw','hpsw'))");
} else {
    %boks = &db_hent_hash($db,"SELECT netboxid,ip,sysname,typegroupid,up,ro FROM netbox join type using (typeid) WHERE (catid='SW' OR catid='GSW' OR catid='KANT') AND up='y' AND netboxid NOT IN (SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE typegroupid LIKE '3%' OR typegroupid IN ('cat1900-sw','catmeny-sw','hpsw'))");
}
my (%swport,%db_swport,%swportvlan,%db_swportvlan,%swportallowedvlan,%db_swportallowedvlan,%swportvlantemp,%swportallowedvlantemp);

if($one_and_only){
    %db_swport = &db_select_hash($db,"swport join module using (moduleid) join netbox using (netboxid) WHERE (catid=\'SW\' OR catid=\'GSW\' OR catid=\'KANT\') AND ip='$one_and_only' AND netboxid NOT IN (SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE typegroupid LIKE '3%' OR typegroupid IN ('cat1900-sw','catmeny-sw','hpsw'))",\@felt_swport,0,1);

    %db_swportvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportvlan)." FROM swportvlan join swport using (swportid) join module using (moduleid) join netbox using (netboxid) WHERE ip='$one_and_only'");

    %db_swportallowedvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportallowedvlan)." FROM swportallowedvlan join swport using (swportid) join module using (moduleid) join netbox using (netboxid) WHERE ip='$one_and_only'");
    

} else {
    %db_swport = &db_select_hash($db,"swport join module using (moduleid) join netbox using (netboxid) WHERE (catid=\'SW\' OR catid=\'GSW\' OR catid=\'KANT\') AND netboxid NOT IN (SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE typegroupid LIKE '3%' OR typegroupid IN ('cat1900-sw','catmeny-sw','hpsw'))",\@felt_swport,0,1);

    %db_swportvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportvlan)." FROM swportvlan");

    %db_swportallowedvlan = &db_hent_hash($db,"SELECT ".join(",", @felt_swportallowedvlan)." FROM swportallowedvlan");

}

foreach my $boksid (keys %boks) { #$_ = boksid keys %boks
    if($boks{$boksid}[4] =~ /n|f/i) {
	&skriv("DEVICE-WATCH","ip=".$boks{$boksid}[2]);
    } else {
	if (&snmp_svitsj($boks{$boksid}[1],$boks{$boksid}[5],$boksid,$boks{$boksid}[3],$boks{$boksid}[2]) eq '0') {
	    &skriv("DEVICE-BOXDOWN","ip=".$boks{$boksid}[2]);
	}
    }
}
my $teller = 0;
for my $t (keys %boks){
    $teller++;
}
print "bokser $teller\n" if $debug;
#$teller = 0;
#for my $t (keys %db_module){
#    $teller++;
#}
#print "moduler $teller\n" if $debug;
$teller = 0;
for my $t (keys %db_swport){
    $teller++;
}
print "swport $teller\n" if $debug;



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
    my $ip = $_[0];
    my $ro = $_[1];
    my $boksid = $_[2];
    my $typegruppe = $_[3];
    my $sysname = $_[4];

    print $ip." får samlet data\n";

    my $includefile = $path_collect."typer/".$typegruppe.".pl";
    print $includefile."\n";
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
