#!/usr/bin/perl -w
 
use Pg;
use strict;

my $vei = "/usr/local/nav/navme/lib";
require "$vei/database.pl";
 
my $dbh_m = &db_connect("manage", "navall", "uka97urgf");
my $dbh_t = &db_connect("trapdetect", "varsle", "lgagikk5p");
 
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


