#!/usr/bin/perl -w

use strict;
use SNMP;
use SNMP_util;
use Socket;

#ikke i bruk
sub snmp_system{
    my ($antallpunktum,$ip,$ro,$endelser) = @_;
    my ($sys,$type);
    if ($ro) {
	my $dns = &hent_dnsname($ip);
	$dns = &fjern_endelse($dns,$endelser);
	my @snmpresult = &snmpwalk($ro.'@'.$ip.':161:8:1:1',"system");
	(undef,$sys) = split(/:/,$snmpresult[4]);
	(undef,$type) = split(/:/,$snmpresult[1]);
	unless($sys&&$type) { #hvis sysname er tomt
	    $sys = 0;
	    $type = 0;
	} else {
	    $sys = &fjern_endelse($sys,$endelser);
	    if($dns =~ /$sys/i) {
		$sys = $dns;
		($sys,undef) = split(/\./,$sys,$antallpunktum+1);
	    } else {
		&skriv("SNOUT", "\nDNSNAME($dns) OG SYSNAME($sys) ER FORSKJELLIGE for $ip\n");
	    }
	}
    }
    return ($sys,$type);
}
sub snmpsystem{
    my ($host,$community,$endelser) = @_;
    if ($community){
	my ($sys,$type);
	my $dns = &hent_dnsname($host);
	$dns = &fjern_endelse($dns,$endelser);

	my $sess = new SNMP::Session(DestHost => $host, Community => $community, Version => 1);
	my $vars = new SNMP::VarList(['1.3.6.1.2.1.1.5.0'], ['1.3.6.1.2.1.1.2.0']);
	my ($sys, $type) = $sess->get($vars);   
	unless($sys) {
	    my $error = $sess->{ErrorStr};
	    unless($error){
		&skriv("SNMP-DNSNAME", "ip=$host", "dns=$dns");
	    } else {
		&snmperrorcorrect($host,$error);
	    }
	    $sys = 0;
	    $type = 0;
	} else {
	    my $for = $sys = &fjern_endelse($sys,$endelser);
	    if($dns =~ /$sys/i) {
		my $mellom = $sys = $dns;
		($sys,undef) = split(/\./,$sys,2);
		my $etter = $sys;
#	print "\n$for\n$mellom\n$etter\n";
		
	    } else {
		&skriv("DNS-NAMECHAOS", "ip=$host", "sysname=$sys", "dns=$dns");
	    }
	}
	$type =~ s/^\.//; # fjerner punktum fra starten av OID
#	print $sys.$type."\n";
	return ($sys,$type);
    }
}

sub snmperrorcorrect {
    my $error = $_[1];
    my $ip = $_[0];

    if($error =~ /^Timeout/){
	
	&skriv("SNMP-TIMEOUT","ip=$ip");

    } else {

	&skriv("SNMP-ERROR", "ip=$ip", "message=$error");
    }
}

sub verifymib{
    if($_[0]){
	return 1;
    } else {
	return 0;
    }
}

sub fjern_endelse{
    my $sysname = $_[0];
    my @endelser =  split(/:/,$_[1]);
    for my $endelse (@endelser) {
	if ($sysname =~ /$endelse/){
	    $sysname =~ s/$endelse//i;
	}
    }
    return $sysname;
}

sub snmp_type{
    my ($ip,$ro,$mib) = @_;
    my $resultat = 0;
    if ($ro) {
        ($resultat) = &snmpget("$ro\@$ip:161:1:2:4",$mib);
    }
    return $resultat;
}

sub hent_ip{
    if (defined $_[0]){
	if(my $ip = gethostbyname($_[0])){
	    return inet_ntoa($ip);
	} else {
	    return 0;
	}
    } else {
	return "";
    }   
}
sub hent_dnsname{
    if (defined $_[0]){
	my $dns;
	if($dns =&inet_aton($_[0])){
	    $dns = gethostbyaddr($dns,AF_INET);
	    return $dns;
	} else {
	    return 0;
	}
    } else {
	return 0;
    }   
}
sub sigwalk{
    my $session = $_[0];
    my $mib = $_[1];
    my $vb = new SNMP::Varbind([$mib]);
    my @min = ();
    $min[0] = $mib;
    my $teller = 0;
    my @resultat = ();
    while ($min[0] =~ /^$mib/) {

	if(exists $min[1]){
	    $min[0] =~ /$mib\.(\S+)/;
	    my $temp;
	    if($1){
		$temp = $1.".".$min[1];
	    } else {
		$temp = $min[1];
	    }
	    $resultat[$teller] = [$temp,$min[2]];
	    $teller++;
	}
	$session->fgetnext($vb);
	@min = @{$vb};
    }
    return @resultat;
}
sub siget {
    my $session = $_[0];
    my $mib = $_[1];
    return $session->get($mib);
}


return 1;
