#!/usr/bin/perl
####################
#
# $Id: cL3-sw.pl,v 1.2 2002/12/19 16:31:02 gartmann Exp $
# This file is part of the NAV project.
# cL3-sw is a plugin for swporter that uses SNMP to get information about a
# switch and its modules and ports. The results are returned to the swporter
# script.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;
use SNMP;
#&bulk("129.241.161.45","****","404");

sub bulk{
    my $host = $_[0];
    my $community = $_[1];
    my $boksid = $_[2];
    my %swport;
    my %swportvlantemp;
    my %swportallowedvlantemp;

    my $debug = 0;
    
    my $sess = new SNMP::Session(DestHost => $host, Community => $community, Version => 2, UseNumeric=>1, UseLongNames=>1);
    
    my $testvar = '.1.3.6.1.4.1.9.9.46.1.6.1.1.13';
    my $vb = new SNMP::Varbind([$testvar]);

    my $val = $sess->getnext($vb);
    my @test = @{$vb};

    unless($test[0] =~ /$testvar/){
	&skriv("SNMP-WRONGTYPEGROUP", "typegroup=cL3-sw", "sysname=$host");
	return 0;
    } else {
	my $numInts = $sess->get('ifNumber.0');

# må fordeles, resultatet med vlanhex fyller et slags buffer.    
	my ($ifindex,$portname,$status,$trunk,$vlan) = $sess->bulkwalk(0,$numInts+1,[ ['.1.3.6.1.2.1.2.2.1.2'],['.1.3.6.1.4.1.9.2.2.1.1.28'],['.1.3.6.1.2.1.2.2.1.8'],['.1.3.6.1.4.1.9.9.46.1.6.1.1.13'],['.1.3.6.1.4.1.9.9.68.1.2.2.1.2']]);
	my ($speed,$vlanhex) = $sess->bulkwalk(0,$numInts+1,[['.1.3.6.1.2.1.2.2.1.5'],['.1.3.6.1.4.1.9.9.46.1.6.1.1.4']]);


	my $i = 0;

	my %snmpresult;

	while (defined($$speed[$i])){

	    my $ifno = $$ifindex[$i][1];
	    my $ifi = $$ifindex[$i][2];
	    $ifi =~ /^(\w+)\/(\d+)$/;
	    my $modul = $1;
	    my $port = $2;
	    
	    $modul =~ s/FastEthernet/Fa/i;
	    $modul =~ s/GigabitEthernet/Gi/i;

	    $snmpresult{$ifno}{modul} = $modul;
	    $snmpresult{$ifno}{port} = $port;

	    $snmpresult{$ifno}{ifindex} = $ifno;

	    $snmpresult{$$portname[$i][1]}{portname} = $$portname[$i][2];

	    $snmpresult{$$status[$i][1]}{status} = $$status[$i][2];

#	my $j = $i-1;

#	my $tempduplex = $$duplex[$j][2];
#	my $duplex;
#	if($tempduplex==1){
#	    $duplex = 'full';
#	} else {
#	    $duplex = 'half';
#	}
	    $snmpresult{$$speed[$i][1]}{speed} = $$speed[$i][2];

	    $snmpresult{$$trunk[$i][1]}{trunk} = $$trunk[$i][2];

	    $snmpresult{$$vlanhex[$i][1]}{vlanhex} = $$vlanhex[$i][2];
	    $snmpresult{$$vlan[$i][1]}{vlan} = $$vlan[$i][2];

	    $i++;
	}

	foreach my $k (sort keys %snmpresult){

	    my $modul = $snmpresult{$k}{modul};
	    my $port = $snmpresult{$k}{port};
	    my $ifindex = $k;
	    my $portname = $snmpresult{$k}{portname};
	    my $tempstatus = $snmpresult{$k}{status};
	    my $status;
	    if($tempstatus == 1){
		$status = 'y';
	    } else {
		$status = 'n';
	    }

	    my $rtemp;
	    my $trunk;
	    if($snmpresult{$k}{trunk} == 1){
		$trunk = 't';
		if($modul&&$port){
		    $rtemp = $swportallowedvlantemp{$modul}{$port} = unpack "H*", $snmpresult{$k}{vlanhex};
		}
	    } else {
		$trunk = 'f';
		if($modul&&$port){
		    $rtemp = $swportvlantemp{$modul}{$port} = $snmpresult{$k}{vlan};
		}
	    }

	    my $speed = ($snmpresult{$k}{speed}/1e6);
	    $speed =~ s/^(.{0,10}).*/$1/;

	    if($modul&&$port){
		$swport{$modul}{$port} = [ $ifindex, $status, $speed, "f",$trunk,$portname];
		print "lagt til: " if $debug;
	    }
	    

	    print "$ifindex:$modul/$port $portname status = ".$status." duplex =  speed = ".$speed." trunk = ".$trunk." vlan = ".$rtemp."\n" if $debug;

	}
	
	return \%swport, \%swportvlantemp, \%swportallowedvlantemp;
    }
}
