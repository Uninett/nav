#!/usr/bin/perl
####################
#
# $Id: bokser.pl,v 1.15 2003/01/10 11:57:25 gartmann Exp $
# This file is part of the NAV project.
# bokser reads the files nettel.txt (containing network devices) and server.txt
# and does SNMPget to require information. This information is updated in the 
# database, where devices are added, updated or deleted.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use SNMP_util;
use strict;

require '/usr/local/nav/navme/lib/NAV.pm';
import NAV qw(:DEFAULT :collect :snmp);

my $debug = 0;

my $localkilde = get_path("path_localkilde");
my $localconf = get_path("path_localconf");
my $lib = get_path("path_lib");

my %nav_conf = &hash_conf($localconf."nav.conf");

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

&log_open;

my $conn = &db_get("bokser");

my (%sysnamehash,%server,%db_server,%nettel,%db_nettel,%alle,%db_alle);

#sysname-endelser
#leses inn fra fil og legges i kolonseparert skalar
my $endelser = $nav_conf{"DOMAIN_SUFFIX"};
my %type = &db_hent_enkel($conn,"SELECT sysobjectid,typeid FROM type");
#-----------------------
#FILLESING: server.txt
my %temp_netboxcategory; # blir brukt for å samle tjenetekategorier per ip
my @felt_server = ("ip","sysname","roomid","orgid","catid","subcat","ro");
my $fil_server = "$localkilde/server.txt";
%server = &fil_server($fil_server,scalar(@felt_server)+2,$endelser,\%sysnamehash);
#----------------------------------
#DATABASELESING

#hadde tenkt å ha med watch her, men vi bruker ikke snmp på servere per dags dato. Kan bare settes på når de ikke blir tatt med da de ikke svarer på snmp.
%db_server = &db_hent_hash($conn,"SELECT ".join(",", @felt_server )." FROM netbox where catid = 'SRV'");
#legge til alle
for my $a (keys %db_server) {
    my $ip = $db_server{$a}[0];
    $db_alle{$ip} = 1;
}
#&device_endring($conn,\%server,\%db_server,\@felt_server,"netbox");
#&db_device($conn,"netbox",\@felt_server,[0],[0,1,2,3,4,5,6],\%server,\%db_server,0);
&db_safe(connection => $conn,table => "netbox",fields => \@felt_server, new => \%server, old => \%db_server,delete => 0,insert => "device");

my %ip2netboxid = &db_select_hash($conn,"netbox",["ip","netboxid"],0);
my %old_netboxcategory = &db_select_hash($conn,"netboxcategory",["netboxid","category"],0,1);
my %new_netboxcategory;
for my $ip (keys %temp_netboxcategory) {
    my $netboxid = $ip2netboxid{$ip}[1];
    for my $value (keys %{$temp_netboxcategory{$ip}}) {
	my @temp = ($netboxid,$value);
	$new_netboxcategory{$netboxid}{$value} = \@temp;
    }
}
my @fields_netboxcategory = ("netboxid","category");
&db_safe(connection => $conn, table => "netboxcategory", fields => \@fields_netboxcategory, new => \%new_netboxcategory, old => \%old_netboxcategory, index => ["netboxid","category"], delete => 1);

#------------------------------
#FILLESING: nettel.txt
my @felt_nettel = ("ip","sysname","typeid","roomid","orgid","catid","subcat","ro","rw");
my $fil_nettel = "$localkilde/nettel.txt";
%nettel = &fil_nettel($fil_nettel,scalar(@felt_nettel),$endelser,\%sysnamehash);

#----------------------------------
#DATABASELESING
#felter som skal leses ut av databasen
if($one_and_only){
    %db_nettel = &db_hent_hash($conn,"SELECT ".join(",", @felt_nettel )." FROM netbox where catid <> 'SRV' and ip='$one_and_only'");
} else {
    %db_nettel = &db_hent_hash($conn,"SELECT ".join(",", @felt_nettel )." FROM netbox where catid <> 'SRV'");
}
#legge til i alle
for my $a (keys %db_nettel) {
    my $ip = $db_nettel{$a}[0];
    $db_alle{$ip} = 1;
}
&db_safe(connection => $conn,table => "netbox",fields => \@felt_nettel, new => \%nettel, old => \%db_nettel,delete => 0,insert => "device");

#-----------------------------------
#DELETE
    my @felt_alle = ("ip"); # felt som fungerer som sletteindex, i.e. ip
    &db_sletting($conn,\%alle,\%db_alle,\@felt_alle,"netbox");


&log_close;

# end main
#-----------------------------------------------------------------------

sub fil_endelser {
    my $fil = $_[0];
    open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
    my @endelser;
    while (<FIL>) {
	next unless /^\./; 
	my $endelse = rydd($_);
	@endelser=(@endelser,$endelse);
    }
    close FIL;
    return join(":",@endelser);
}
sub fil_nettel{
    my ($fil,$felt,$endelser) = @_[0..2];
    my %sysnamehash = %{$_[3]};
    my $one_and_only = $_[4];
    open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
    while (<FIL>) {
	@_ = &fil_hent_linje($felt+1,$_);
	my $ip = $_[1];
	if((!$one_and_only && $ip)||($one_and_only && $ip eq $one_and_only)){
	    my $ro = $_[5];
	    if (my @passerr = $ro =~ /(\W)/g){ #sier fra hvis det finnes non-alfanumeriske tegn i passordet, og skriver ut (bare) disse tegnene.
		my $passerr = join "",@passerr;
		&skriv("TEXT-COMMUNITY", "ip=$ip","illegal=$passerr");
	    }
	    if (my @passerr = $_[6] =~ /(\W)/g){ #sier fra hvis det finnes non-alfanumeriske tegn i passordet, og skriver ut (bare) disse tegnene.
		my $passerr = join "",@passerr;
		&skriv("TEXT-COMMUNITY", "ip=$ip","illegal=$passerr");
	    }
	    my $temptype;
	    my $sysname;
	    ($sysname,$temptype) = &snmpsystem($ip,$ro,$endelser);
	    ($sysname,%sysnamehash) = &sysnameuniqueify($sysname,\%sysnamehash);
	    my $type = $type{$temptype};
	    if($sysname){
		unless($type){
		    &skriv("TEXT-TYPE","ip=$ip","type=$temptype");
		}
		@_ = ($ip,$sysname,$type,$_[0],$_[2],@_[3..6]);
		@_ = map rydd($_), @_;

		unless (exists($alle{$ip})){
		    $nettel{$ip} = [ @_ ];
		}
	    }
	    # må legges inn så lenge den eksisterer i fila, uavhengig av snmp
	    unless (exists($alle{$ip})){
		$alle{$ip} = 1;
	    } else {
		&skriv("IP-ALREADY","ip=$ip","last=".$nettel{$ip}[1]);
	    }
#	    print $sysname.$type."\n";
	}
	
    }
    close FIL;
    return %nettel;
}
sub fil_server{
    my ($fil,$felt,$endelser) = @_;
    my %sysnamehash = %{$_[3]};
    open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
    while (<FIL>) {

	@_ = &fil_hent_linje($felt,$_);
	my $ip;
	if($ip = &hent_ip($_[1])) {

	    for my $value (split /,/, $_[7]){
		$temp_netboxcategory{$ip}{$value} = 1;
	    }

	    @_ = ($ip,@_[0..1],$_[2],uc($_[3]),@_[4..5]);
	    @_ = map rydd($_), @_;
	    my $sysname = &fjern_endelse($_[2],$endelser);
	    ($sysname,%sysnamehash) = &sysnameuniqueify($sysname,\%sysnamehash);
	    &skriv("DEVICE-COLLECT","ip=$sysname");
	    unless (exists($alle{$ip})){
		$server{$ip} = [ $ip,$sysname,$_[1],@_[3..6] ];
	    }
	    unless (exists($alle{$ip})){
		$alle{$ip} = 1;
	    } else {
		&skriv("IP-ALREADY","ip=$ip","last=".$server{$ip}[1]);
	    }
	}
    }
    close FIL;
    return %server;
}

sub sysnameuniqueify {
    my $sysnameroot = $_[0];
    my %sysnamehash = %{$_[1]};
    
    my $ok = 0; #intern
    my $v = 1;
    my $sysname = $sysnameroot;

    until($ok){

	unless(exists($sysnamehash{$sysname})){
	    $sysnamehash{$sysname} = 1;
	    $ok = 1;
	} else {
	    $v++;
	    $sysname = $sysnameroot.",v".$v;
	}
    }
    &skriv("DEVICE-COLLECT","ip=$sysname");
    return ($sysname,\%sysnamehash);

}

