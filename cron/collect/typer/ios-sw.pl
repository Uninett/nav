#!/usr/bin/perl

use strict;

sub ifindex{
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});
    my (%returverdi,%modul,%port);
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{ifindex}[1]);
    foreach my $result (@snmpresult){
	my ($interface,$modulport) = split(/:/,$result);
	$modulport =~ s/FastEthernet/Fa/i;
	$modulport =~ s/GigabitEthernet/Gi/i;
	($modul{$interface},$port{$interface}) = split /\//,$modulport;
	$returverdi{$interface} = $interface;
    }
    return \%returverdi,\%modul,\%port;
}

sub duplex{
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});
    my %returverdi;
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{duplex}[1]);
    foreach my $result (@snmpresult){
	my ($interface,$duplex) = split(/:/,$result);
	if($duplex==1){
	    $returverdi{$interface} = 'full';
	} else {
	    $returverdi{$interface} = 'half';
	}
    }
    return \%returverdi;
}

sub porttype {
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});
    my %returverdi;
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{porttype}[1]);
    foreach my $result (@snmpresult){
	my ($interface,$porttype) = split(/:/,$result);
	$returverdi{$interface} = $porttype;
    }
    return \%returverdi;
}

sub status {
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});
    my %returverdi;
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{status}[1]);
    foreach my $result (@snmpresult){
	my ($interface,$status) = split(/:/,$result);
	if($status==1){
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
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});
    my (%returverdi,%vlan,%vlanhex);
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{trunk}[1]);
    foreach my $result (@snmpresult){
	my ($interface,$trunk) = split(/:/,$result);
	$interface++;
	if($trunk==0){
	    $returverdi{$interface} = 't';
	    my ($vlanhex) = &snmpget($ro.'@'.$ip,"1.3.6.1.4.1.9.9.46.1.6.1.1.4.$interface");
	    $vlanhex = unpack "H*", $vlanhex;
	    $vlanhex{$interface} = $vlanhex;
	} else {
	    $returverdi{$interface} = 'f';
	    my ($vlan) = &snmpget($ro.'@'.$ip,$mib{vlan}[1].".".$interface);
	    $vlan{$interface} = $vlan;
	}
	
    }
    return \%returverdi,\%vlan,\%vlanhex;
}

sub portname{
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});
    my %returverdi;
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{portname}[1]);
    foreach my $result (@snmpresult){
	my ($interface,$portname) = split(/:/,$result,2);
	$returverdi{$interface} = $portname;
    }
    return \%returverdi;
}

return 1;
