#!/usr/bin/perl

use strict;

sub ifindex{
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});
    my (%returverdi,%modul,%port);
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{ifindex}[1]);
    foreach my $result (@snmpresult){
	my ($modulport,$interface) = split(/:/,$result);
	($modul{$interface},$port{$interface}) = split /\./,$modulport;
	$returverdi{$modulport} = $interface;
    }
    return \%returverdi,\%modul,\%port;
}

sub duplex{
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %mp2if = %{$_[3]};

    my %returverdi;
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{duplex}[1]);
    foreach my $result (@snmpresult){
	my ($modulport,$duplex) = split(/:/,$result);
	my $interface = $mp2if{$modulport}; 
	if($duplex==1){
	    $returverdi{$interface} = 'half';
	} else {
	    $returverdi{$interface} = 'full';
	}
    }
    return \%returverdi;
}

sub porttype {
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %mp2if = %{$_[3]};

    my %returverdi;
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{porttype}[1]);
    foreach my $result (@snmpresult){
	my ($modulport,$porttype) = split(/:/,$result);
	my $interface = $mp2if{$modulport};
	$returverdi{$interface} = $porttype;
    }
    return \%returverdi;
}

sub status {
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %mp2if = %{$_[3]};

    my %returverdi;
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{status}[1]);
    foreach my $result (@snmpresult){
	my ($modulport,$status) = split(/:/,$result);
	my $interface = $mp2if{$modulport}; 
	if($status==2){
	    $returverdi{$interface} = 'up';
	} else {
	    $returverdi{$interface} = 'down';
	}
    }
    return \%returverdi;
}

sub speed{
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});
    my %returverdi;
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{speed}[1]);
    foreach my $result (@snmpresult){
	my ($interface,$speed) = split(/:/,$result);
	$speed = ($speed/1e6);
	$speed =~ s/^(.{0,10}).*/$1/;
	$returverdi{$interface} = $speed;
    }
    return \%returverdi;
}

sub trunk{
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %mp2if = %{$_[3]};

    my (%returverdi,%vlan,%vlanhex);
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{trunk}[1]);
    foreach my $result (@snmpresult){
	my ($modulport,$trunk) = split(/:/,$result);
	my $interface = $mp2if{$modulport}; 

	if($trunk==1){
	    $returverdi{$interface} = 't';
	    my ($vlanhex) = &snmpget($ro.'@'.$ip,"1.3.6.1.4.1.9.5.1.9.3.1.5.$modulport");
	    $vlanhex = unpack "H*", $vlanhex;
	    $vlanhex{$interface} = $vlanhex;
	} else {
	    $returverdi{$interface} = 'f';
	    my ($vlan) = &snmpget($ro.'@'.$ip,$mib{vlan}[1].".".$modulport);
	    $vlan{$interface} = $vlan;
	}
	
    }
    return \%returverdi,\%vlan,\%vlanhex;
}

sub portname{
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %mp2if = %{$_[3]};

    my %returverdi;
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{portname}[1]);
    foreach my $result (@snmpresult){
	my ($modulport,$portname) = split(/:/,$result,2);
	my $interface = $mp2if{$modulport};
	$returverdi{$interface} = $portname;
    }
    return \%returverdi;
}

return 1;
