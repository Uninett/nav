#!/usr/bin/perl

use SNMP_util;
use Pg;

use strict;

require "felles.pl";

my $database = "manage";
my $conn = db_connect($database);
my %rootgw;

my %ruterporter = &db_hent_en($conn,"select gwportid,rootgwid from gwport natural join prefiks");
my %db_rootgw = &db_hent_en($conn,"SELECT prefiksid,rootgwid FROM prefiks");
my %ruterportip2id = &db_hent_en($conn,"SELECT gwip,gwportid FROM gwport");
my %ruterportprefiks = &db_hent_en($conn,"SELECT gwportid,prefiksid FROM gwport");
my %prefiksid2gwip =  &db_hent_en($conn,"select prefiksid,min(gwip) from gwport natural join prefiks where nettadr < gwip group by prefiksid");

for my $ruterportid (keys %ruterporter) {
    $ruterportid.$ruterporter{$ruterportid};
    my $prefiksid = $ruterportprefiks{$ruterportid};
    my $laveste_ip  = $prefiksid2gwip{$prefiksid};
    my $rootgwid = $ruterportip2id{$laveste_ip};
    $rootgw{$prefiksid} = $rootgwid;
}

for my $prefiksid (keys %db_rootgw) {
    my $db_rootgw = $db_rootgw{$prefiksid};
    my $rootgw = $rootgw{$prefiksid};
    unless ($db_rootgw =~ /$rootgw/i) {
	&oppdater($conn,"prefiks","rootgwid","\'$db_rootgw\'","\'$rootgw\'","prefiksid",$prefiksid);
    }
}
return 1;
