#!/usr/bin/perl

use SNMP_util;
use Pg;

use strict;

require "felles.pl";

my $ip2NetMask = ".1.3.6.1.2.1.4.20.1.3"; 
my $hsrp_status = ".1.3.6.1.4.1.9.9.106.1.2.1.1.15";
my $hsrp_rootgw = ".1.3.6.1.4.1.9.9.106.1.2.1.1.11";

my $database = "manage";
my $conn = &db_connect($database);
my %boks = &db_hent($conn,"SELECT ip,ro,prefiksid,boksid from boks where kat='GW'");
my %db_gwport = &db_hent_en($conn,"SELECT gwip,gwportid from gwport");
my %rootgwip;
my %rootgw;
my %rootgwip2id;
my %gwport;
my %ip2netmask;
my %ruterportip2id = &db_hent_en($conn,"SELECT gwip,gwportid FROM gwport");
my %prefiksdb = &db_hent_en($conn,"SELECT nettadr,prefiksid from prefiks");

for my $boksip  ( keys %boks ) {
    print "\n", my @hsrp_status = &snmp_active($boksip,$boks{$boksip}[1],$hsrp_status);
    my $ro = $boks{$boksip}[1];

    if (scalar @hsrp_status) {
	for my $l (@hsrp_status) { 
	    (my $tempifi,undef,my $status) = split(/:|\./,$l);
	    if ($status == 6) {
		my ($rootgwip) = &snmpget("$ro\@$boksip",$hsrp_rootgw.".".$tempifi.".0");

		
		print my $prefiksid = &getprefiks($rootgwip);
		print "$rootgwip \t$prefiksid\n";
		$rootgwip{$prefiksid} = $rootgwip;
		print my $boksid = $boks{$boksip}[3],"\n";
		$gwport{$rootgwip} = [$boksid,$tempifi,$rootgwip];
#		}
	    }
	}
    }
}
for my $hei (keys %gwport) {
    print $hei."g\t".$gwport{$hei}."\n";
    print join(":",@{$gwport{$hei}}),"\n";
}
for my $hei (keys %prefiksdb) {
    print $hei."r\t".$prefiksdb{$hei}."\n";

}

for my $boksid (keys %gwport) {
    unless(exists $db_gwport{$boksid}) {
	&db_sett_inn($conn,"gwport","boksid:ifindex:gwip",join(":",@{$gwport{$boksid}}));
    }
}
%rootgwip2id = &db_hent_en($conn,"SELECT gwip,gwportid from gwport");

for my $hei (keys %rootgwip) {
    print $hei."p\t".$rootgwip{$hei}."\n";
}

for my $prefiksid (keys %rootgwip) {
    print my $p = $rootgwip{$prefiksid};
    $rootgw{$prefiksid} = $rootgwip2id{$p};
    print "\n".$p."\t".$p."\n";

}
my %db_rootgw = &db_hent_en($conn,"SELECT prefiksid,rootgwid FROM prefiks");
for my $hei (keys %rootgw) {
    print $hei."g\t".$rootgw{$hei}."\n";
}
for my $prefiksid (keys %db_rootgw) {
    my $db_rootgw = $db_rootgw{$prefiksid};
    my $rootgw = $rootgw{$prefiksid};
    unless ($db_rootgw =~ /$rootgw/i) {
	&oppdater($conn,"prefiks","rootgwid","\'$db_rootgw\'","\'$rootgw\'","prefiksid",$prefiksid);
    }
}

sub snmp_active {
    print my ($ip,$ro,$mib) = @_;
    my @svar = &snmpwalk("$ro\@$ip",$mib);
    return @svar;
}

sub getprefiks
{
    # Tar inn ip, splitter opp og and'er med diverse
    # nettmasker. Målet er å finne en match med en allerede innhentet
    # prefiksid (hash over alle), som så returneres.
 
    my $ip = $_[0];
 
    my @masker = ("255.255.255.255","255.255.255.254","255.255.255.252","255.255.255.248","255.255.255.240","255.255.255.224","255.255.255.192","255.255.255.128","255.255.255.0","255.255.254.0","255.255.252.0");
 
    my $netadr;
    my $maske;
 
    foreach $maske (@masker)
    {
        $netadr = and_ip($ip,$maske);
 
        return $prefiksdb{$netadr} if (defined $prefiksdb{$netadr});
    }
 
#    print "Fant ikke prefiksid for $ip\n";
    return 0;
}
return 1;
