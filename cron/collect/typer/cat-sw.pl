#!/usr/bin/perl
####################
#
# $Id: cat-sw.pl,v 1.9 2002/12/19 16:31:02 gartmann Exp $
# This file is part of the NAV project.
# cat-sw is a plugin for swporter that uses SNMP to get information about a
# switch and its modules and ports. The results are returned to the swporter
# script.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;

use SNMP;
# test:
#&bulk("sb-354-sw","******","821");

sub bulk{
    my $host = $_[0];
    my $community = $_[1];
    my $boksid = $_[2];
    my %swport;
    my %swportvlantemp;
    my %swportallowedvlantemp;

    my $debug = 0;

    my $sess = new SNMP::Session(DestHost => $host, Community => $community, Version => 2, UseNumeric=>1, UseLongNames=>1);
    
    my $testvar = '.1.3.6.1.4.1.9.5.1.9.3.1.8';
    my $vb = new SNMP::Varbind([$testvar]);

    my $val = $sess->getnext($vb);
    my @test = @{$vb};

    unless($test[0] =~ /$testvar/){
	&skriv("SNMP-WRONGTYPEGROUP", "typegroup=cat-sw", "sysname=$host");
	return 0;
    } else {
    my $numInts = $sess->get('ifNumber.0');

    if(my $error = $sess->{ErrorStr}){
	&skriv("SNMP-ERROR","ip=$host","message=$error");
    }

    my ($ifindex) = $sess->bulkwalk(0,$numInts+1,[ ['.1.3.6.1.4.1.9.5.1.4.1.1.11']]);

    my ($portname,$status, $duplex) = $sess->bulkwalk(0,$numInts+1,[ ['.1.3.6.1.4.1.9.5.1.4.1.1.4'],['.1.3.6.1.4.1.9.5.1.4.1.1.6'],['.1.3.6.1.4.1.9.5.1.4.1.1.10']]);
    
    my ($speed, $trunk,$vlanhex, $vlan ) = $sess->bulkwalk(0,$numInts+1,[['.1.3.6.1.2.1.2.2.1.5'],['.1.3.6.1.4.1.9.5.1.9.3.1.8'],['.1.3.6.1.4.1.9.5.1.9.3.1.5'],['.1.3.6.1.4.1.9.5.1.9.3.1.3']]);

    my @speed2;
    for my $u (@{$speed}){
	$speed2[$$u[1]] = $$u[2];
    }

    my $i = 0;
    while ($$status[$i]){
	
	$$ifindex[$i][0] =~ /\.(\d+)$/;
	my $modul = $1;
	my $port = $$ifindex[$i][1];
	my $ifindex = $$ifindex[$i][2];
	my $portname = $$portname[$i][2];

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

	my $j = $ifindex;
#	print $j.$ifindex.$speed2[$j];
	my $tempspeed = $speed2[$j];
	$tempspeed  = ($tempspeed/1e6);
	$tempspeed =~ s/^(.{0,10}).*/$1/;
	my $speed = $tempspeed;

	if($modul&&$port){
	    $swport{$modul}{$port} = [ $ifindex, $status, $speed, $duplex,$trunk,$portname];
	}

	print "\n $ifindex modul = $modul port = $port status = ".$status." duplex = ".$duplex." portname = ".$portname." trunk = ".$trunk." speed = ".$tempspeed." vlan = ".$rtemp if $debug;
	
	$i++;

    }
    return \%swport, \%swportvlantemp, \%swportallowedvlantemp;
}
}

sub ifindex{
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});
    my (%returverdi,%interface);
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{ifindex}[1]);
    foreach my $result (@snmpresult){
	my ($modulport,$interface) = split(/:/,$result);
	$interface{$interface} = $modulport;
	my ($modul,$port) = split /\./,$modulport;
	$returverdi{$modul}{$port} = $interface;
    }
    return \%returverdi,\%interface;
}




sub duplex{
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};

    my %returverdi;

    my $mib = $mib{duplex}[1];
    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($modulport,$duplex) = split(/:/,$result);
	    my ($modul,$port) = split /\./,$modulport;
	    if($duplex==1){
		$returverdi{$modul}{$port} = 'half';
	    } else {
		$returverdi{$modul}{$port} = 'full';
	    }
	}
    }
    return \%returverdi;
}

sub porttype {
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};

    my %returverdi;
    my $mib = $mib{porttype}[1];
    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($modulport,$porttype) = split(/:/,$result);
	    my ($modul,$port) = split /\./,$modulport;
	    $returverdi{$modul}{$port} = $porttype;
	}
    }
    return \%returverdi;
}

sub status {
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};

    my %returverdi;
    my $mib = $mib{status}[1];
    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($modulport,$status) = split(/:/,$result);
	    my ($modul,$port) = split /\./,$modulport;
	    if($status==2){
		$returverdi{$modul}{$port} = 'up';
	    } else {
		$returverdi{$modul}{$port} = 'down';
	    }
	}
    }
    return \%returverdi;
}

sub speed{
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %if2mp = %{$_[3]};
    my %returverdi;
    my $mib = $mib{speed}[1];

    if(&verifymib($mib)){

	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($interface,$speed) = split(/:/,$result);
	    my ($modul,$port) = split /\./, $if2mp{$interface};
	    $speed = ($speed/1e6);
	    $speed =~ s/^(.{0,10}).*/$1/;
	    $returverdi{$modul}{$port} = $speed;
	}
    }
    return \%returverdi;
}

sub trunk{
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my (%returverdi,%vlan,%vlanhex);
    my $mib = $mib{trunk}[1];
 
    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($modulport,$trunk) = split(/:/,$result);
	    my ($modul,$port) = split /\./,$modulport;
	    if($trunk==1){
		$returverdi{$modul}{$port} = 't';
		my ($vlanhex) = &snmpget($ro.'@'.$ip,"1.3.6.1.4.1.9.5.1.9.3.1.5.$modulport");
		$vlanhex = unpack "H*", $vlanhex;
		$vlanhex{$modul}{$port} = $vlanhex;
	    } else {
		$returverdi{$modul}{$port} = 'f';
		my ($vlan) = &snmpget($ro.'@'.$ip,$mib{vlan}[1].".".$modulport);
		$vlan{$modul}{$port} = $vlan;
	    }
	}
    }
    return \%returverdi,\%vlan,\%vlanhex;
}

sub portname{
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %returverdi; 
    my $mib = $mib{portname}[1];
    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($modulport,$portname) = split(/:/,$result,2);
	    my ($modul,$port) = split /\./,$modulport;
	    $returverdi{$modul}{$port} = $portname;
	}
    }
    return \%returverdi;
}

#return 1;
