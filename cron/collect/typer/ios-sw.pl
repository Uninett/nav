#!/usr/bin/perl

use strict;
use SNMP;
#&bulk("musikk-sw","gotcha","404");

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

# må fordeles, resultatet med vlanhex fyller et slags buffer.    
    my ($ifindex,$portname,$duplex,$status,$trunk,$vlan) = $sess->bulkwalk(0,$numInts+1,[ ['.1.3.6.1.2.1.2.2.1.2'],['.1.3.6.1.4.1.9.2.2.1.1.28'],['.1.3.6.1.4.1.9.9.87.1.4.1.1.32.0'],['.1.3.6.1.2.1.2.2.1.8'],['.1.3.6.1.4.1.9.9.87.1.4.1.1.6.0'],['.1.3.6.1.4.1.9.9.68.1.2.2.1.2']]);
    my ($speed,$vlanhex) = $sess->bulkwalk(0,$numInts+1,[['.1.3.6.1.2.1.2.2.1.5'],['.1.3.6.1.4.1.9.9.46.1.6.1.1.4']]);

    # k er vlanhex, som av en eller annen grunn starter på 0 her, men i cat-sw blir alle lagret.
    my $k = my $i = 0;
    while (defined($$speed[$i])){

	$$ifindex[$i][2] =~ /^(\w+)\/(\d+)$/;
	my $modul = $1;
	my $port = $2;
    
	$modul =~ s/FastEthernet/Fa/i;
	$modul =~ s/GigabitEthernet/Gi/i;

	my $ifindex = $$ifindex[$i][1];
	my $portname = $$portname[$i][2];

	my $tempstatus = $$status[$i][2];
	my $status;
	if($tempstatus == 1){
	    $status = 'up';
	} else {
	    $status = 'down';
	}

	my $j = $i-1;

	my $tempduplex = $$duplex[$j][2];
	my $duplex;
	if($tempduplex==1){
	    $duplex = 'full';
	} else {
	    $duplex = 'half';
	}

	my $temptrunk = $$trunk[$j][2];
	my $trunk;
	if($temptrunk==0){
	    $trunk = 't';
	    if($modul&&$port){
		$swportallowedvlantemp{$modul}{$port} = unpack "H*", $$vlanhex[$k-1][2];
	    }
	    $k++;
	} else {
	    $trunk = 'f';
	    if($modul&&$port){
		$swportvlantemp{$modul}{$port} = $$vlan[$j][2];
	    }
	}

	my $speed = ($$speed[$i][2]/1e6);
	$speed =~ s/^(.{0,10}).*/$1/;

	if($modul&&$port){
	    $swport{$modul}{$port} = [ undef, $boksid, $modul, $port, $ifindex, $status, $speed, $duplex,$trunk,undef,$portname];
	    print "lagt til: " if $debug;
	}
	

	print "$modul/$port status = ".$status." duplex = ".$duplex." speed = ".$speed."\n" if $debug;


	$i++;
    }
    
#    for my $m (keys %swport){
#	    print $m;
#	    for my $n (keys %{$swport{$m}}){
#		print $n;
#	    }
#	}

    return \%swport, \%swportvlantemp, \%swportallowedvlantemp;
}

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
	    $interface++;
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

#return 1;
