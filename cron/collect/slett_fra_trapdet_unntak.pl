#!/usr/bin/perl -w
 
use Pg;
use strict;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $lib = &lib();
require "$lib/database.pl";

my %dbconf = &db_readconf();
my $db_nav = $dbconf{db_nav}; # Skal være manage
my $db_trap = $dbconf{db_trapdetect};
my ($user_m, $user_t) = split(/\s*,\s*/, $dbconf{script_slett_fra_trapdet_unntak});
my ($userpw_m, $userpw_t) = ($dbconf{'userpw_' . $user_m}, $dbconf{'userpw_' . $user_t});

my $dbh_m = &db_connect($db_nav, $user_m, $userpw_m);
my $dbh_t = &db_connect($db_trap, $user_t, $userpw_t);
 
#Henter alle enheter fra unntak.
my $sporring = "SELECT boksid FROM unntak";
my $hentboks = &db_select($dbh_t,$sporring);
while (my ($boks) = $hentboks->fetchrow) {
    $sporring = "SELECT sysname FROM boks WHERE boksid=$boks";
    my $finnes = &db_select($dbh_m,$sporring);
    if ($finnes->ntuples == 0) {
        print "Boks $boks finnes ikke, sletter innlegg i unntak\n";
        $sporring = "DELETE FROM unntak WHERE boksid=$boks";
        &db_execute($dbh_t,$sporring);
    } 
#    else {
#        print "Boks $boks finnes\n";
#    }
}


