#!/usr/bin/perl

use strict;

sub ifindex{
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};

    my (%returverdi,%interface);
    my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{ifindex}[1]);
    foreach my $result (@snmpresult){
	my ($interface,$modulport) = split(/:/,$result);
	unless ($modulport =~ /Null|Vlan|Tunnel/i) {
	    $modulport =~ s/FastEthernet/Fa/i;
	    $modulport =~ s/GigabitEthernet/Gi/i;
	    my ($modul,$port) = split /\//,$modulport;
	    $modulport = join '.',($modul,$port);
	    $returverdi{$modul}{$port} = $interface;
	    $interface{$interface} = $modulport;
	}
    }
    return \%returverdi,\%interface;
}

sub duplex{
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %if2mp = %{$_[3]};

    my %returverdi;
    my $mib = $mib{duplex}[1];
    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
#	print "\n";
#	print $result;
	    my ($interface,$duplex) = split(/:/,$result);
	    my ($modul,$port) = split /\./, $if2mp{$interface};
	    if($duplex==1){
		$returverdi{$modul}{$port} = 'full';
	    } else {
		$returverdi{$modul}{$port} = 'half';
	    }
	}
    }
    return \%returverdi;
}

sub porttype {
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %if2mp = %{$_[3]};


    my %returverdi;

    my $mib = $mib{porttype}[1];

    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($interface,$porttype) = split(/:/,$result);
	    my ($modul,$port) = split /\./, $if2mp{$interface};
	    $returverdi{$modul}{$port} = $porttype;
	}
    }

    return \%returverdi;
}

sub status {
    my $ip = $_[0];
    my $ro = $_[1];
    my %mib = %{$_[2]};
    my %if2mp = %{$_[3]};
    my %returverdi;
    my $mib = $mib{status}[1];
    
    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($interface,$status) = split(/:/,$result);
	    my ($modul,$port) = split /\./, $if2mp{$interface};
	    if($status==1){
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
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib{speed}[1]);
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
    my %if2mp = %{$_[3]};
    my (%returverdi,%vlan,%vlanhex);
    my $mib = $mib{trunk}[1];
    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($interface,$trunk) = split(/:/,$result);
	    $interface++;
	    my ($modul,$port) = split /\./, $if2mp{$interface};
	    if($trunk==0){
		$returverdi{$modul}{$port} = 't';
		my ($vlanhex) = &snmpget($ro.'@'.$ip,"1.3.6.1.4.1.9.9.46.1.6.1.1.4.$interface");
		$vlanhex = unpack "H*", $vlanhex;
		$vlanhex{$modul}{$port} = $vlanhex;
	    } else {
		$returverdi{$modul}{$port} = 'f';
		my ($vlan) = &snmpget($ro.'@'.$ip,$mib{vlan}[1].".".$interface);
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
    my %if2mp = %{$_[3]};
    my ($ip,$ro,%mib) = (@_[0..1],%{$_[2]});

    my %returverdi;
    my $mib = $mib{portname}[1];
    if(&verifymib($mib)){
	my @snmpresult = &snmpwalk($ro.'@'.$ip,$mib);
	foreach my $result (@snmpresult){
	    my ($interface,$portname) = split(/:/,$result,2);
	    my ($modul,$port) = split /\./, $if2mp{$interface};
	    $returverdi{$modul}{$port} = $portname;
	}
    }
    return \%returverdi;
}

return 1;
