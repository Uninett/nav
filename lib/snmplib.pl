#!/usr/bin/perl -w

use strict;
use SNMP_util;
use Socket;

sub snmp_sysname{
    my ($ip,$ro,$mib,$endelser) = @_;
    my $sys;
    if ($ro) {
	unless(($sys) = &snmpget("$ro\@$ip:161:1:2:4",$mib)) {
	    return 0;
	}
	$sys = &fjern_endelse($sys,$endelser);
	my $dns = &hent_dnsname($ip);
	$dns = &fjern_endelse($dns,$endelser);
	if($dns =~ /$sys/i) {
	    $sys = $dns;
	} else {
	    print "DNSNAME($dns) OG SYSNAME($sys) ER FORSKJELLIGE\n";
	}
    }
    return $sys;
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
#    print $ro;
    my $resultat = 0;
    if ($ro) {
        ($resultat) = &snmpget("$ro\@$ip:161:1:2:4",$mib);
#	print $resultat;
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
#	    print "DNS: $dns\n";
	    $dns = gethostbyaddr($dns,AF_INET);
#	    print "DNS: $dns\n";
	    return $dns;
	} else {
	    return 0;
	}
    } else {
	return 0;
    }   
}


return 1;
