#!/usr/bin/perl
####################
#
# $Id: cgsw.pl,v 1.2 2002/12/19 16:31:02 gartmann Exp $
# This file is part of the NAV project.
# cgsw is a plugin for swporter that uses SNMP to get information about a
# switch and its modules and ports. The results are returned to the swporter
# script.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;

use SNMP;
#&bulk("129.241.0.103","****","821");

sub bulk{
    my $host = $_[0];
    my $community = $_[1];
    my $boksid = $_[2];
    my %swport;
    my %swportvlantemp;
    my %swportallowedvlantemp;

    my $debug = 0;

    my $sess = new SNMP::Session(DestHost => $host, Community => $community, Version => 2, UseNumeric=>1, UseLongNames=>1);
    
    my $numInts = $sess->get('ifNumber.0');

    if(my $error = $sess->{ErrorStr}){
#	&skriv("SNMP-ERROR","ip=$host","message=$error");
	print $error;
    }

    my ($ifindex,$portname,$status, $duplex, $trunk) = $sess->bulkwalk(0,$numInts+1,[ ['.1.3.6.1.4.1.9.5.1.4.1.1.11'],['.1.3.6.1.4.1.9.2.2.1.1.28'],['.1.3.6.1.4.1.9.5.1.4.1.1.6'],['.1.3.6.1.4.1.9.5.1.4.1.1.10'],['.1.3.6.1.4.1.9.5.1.9.3.1.8']]);
    
    my ($speed,$vlanhex, $vlan ) = $sess->bulkwalk(0,$numInts+1,[['.1.3.6.1.2.1.2.2.1.5'],['.1.3.6.1.4.1.9.5.1.9.3.1.5'],['.1.3.6.1.4.1.9.5.1.9.3.1.3']]);

    my @speed2;
    for my $u (@{$speed}){
	$speed2[$$u[1]] = $$u[2];
    }

    my %snmpresult;
    my $a = 0;
    while (defined($$portname[$a])){

	$snmpresult{$$portname[$a][1]}{portname} = $$portname[$a][2];
	$a++;
    }

    my $i = 0;
    while (defined($$status[$i])){
	
	$$ifindex[$i][0] =~ /\.(\d+)$/;
	my $modul = $1;
	my $port = $$ifindex[$i][1];
	my $ifno = $$ifindex[$i][2];
	my $portname = $snmpresult{$ifno}{portname};

	my $tempstatus = $$status[$i][2];
	my $status;
	if($tempstatus==2){
	    $status = 'y';
	} else {
	    $status = 'n';
	}

	my $tempduplex = $$duplex[$i][2];
	my $duplex;
	if($tempduplex==1){
	    $duplex = 'h';
	} else {
	    $duplex = 'f';
	}

#	print " porttype = ".$$porttype[$i][2];	

	my $temptrunk = $$trunk[$i][2];
	my $trunk;
	my $rtemp;
	if($temptrunk==1){
	    $trunk = 't';
	    if($modul&&$port){
		$rtemp = $swportallowedvlantemp{$modul}{$port} = unpack "H*", $$vlanhex[$i][2];
	    }
	} else {
	    $trunk = 'f';
	    if($modul&&$port){
		$rtemp = $swportvlantemp{$modul}{$port} = $$vlan[$i][2];
	    }
	}

	my $j = $ifno;
#	print $j.$ifindex.$speed2[$j];
	my $tempspeed = $speed2[$j];
	$tempspeed  = ($tempspeed/1e6);
	$tempspeed =~ s/^(.{0,10}).*/$1/;
	my $speed = $tempspeed;
	my $ifindex = $ifno;

	if($modul&&$port){
	    $swport{$modul}{$port} = [ $ifindex, $status, $speed, $duplex,$trunk,$portname];
	}

	print "\n $ifno modul = $modul port = $port status = ".$status." duplex = ".$duplex." portname = ".$portname." trunk = ".$trunk." speed = ".$tempspeed." vlan = ".$rtemp if $debug;
	
	$i++;

    }
    return \%swport, \%swportvlantemp, \%swportallowedvlantemp;
}
