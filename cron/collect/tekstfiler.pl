#!/usr/bin/perl
use strict;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $lib = &lib();
my $localkilde = &localkilde();
my $navmekilde = &navmekilde();
require "$lib/database.pl";
require "$lib/fil.pl";
&log_open;
#-------------ALLE-------------
my $db = &db_connect("manage","navall","uka97urgf");
my ($fil,$tabell,@felt);
#--------------ANV-------------
$fil = "$localkilde/anv.txt";
$tabell = "anv";
@felt = ("anvid","descr");
&db_endring_med_sletting($db,$fil,$tabell,join(":",@felt));
#--------------STED------------
$fil = "$localkilde/sted.txt";
$tabell = "sted";
@felt = ("stedid","descr");
&db_endring_med_sletting($db,$fil,$tabell,join(":",@felt));
#--------------ROM-------------
$fil = "$localkilde/rom.txt";
$tabell = "rom";
@felt = ("romid","stedid","descr","rom2","rom3","rom4","rom5");
&db_endring_med_sletting($db,$fil,$tabell,join(":",@felt));
#--------------ORG-------------
$fil = "$localkilde/org.txt";
$tabell = "org";
@felt = ("orgid","forelder","descr","org2","org3","org4");
&spesiell_endring_org($db,$fil,$tabell,join(":",@felt),join(":",@felt));
#--------------TYPE------------
$fil = "$navmekilde/type.txt";
$tabell = "type";
@felt = ("typeid","typegruppe","sysObjectID","descr");
&db_endring_med_sletting($db,$fil,$tabell,join(":",@felt));
#--------------SLUTT-----------
&log_close;

sub spesiell_endring_org {
    my ($db,$fil,$tabell,$felt) = @_;
    my @felt = split(/:/,$felt);
    my %ny = &fil_hent($fil,scalar(@felt));
    #leser fra database
    my %gammel = &db_hent_hash($db,"SELECT ".join(",", @felt )." FROM $tabell ORDER BY $felt[0]");
    for my $feltnull (keys %ny) {
	unless($ny{$feltnull}[1]){
	    &db_endring_per_linje($db,\@{$ny{$feltnull}},\@{$gammel{$feltnull}},\@felt,$tabell,$feltnull);
	}
    }
    &db_endring($db,\%ny,\%gammel,\@felt,$tabell);

    &db_sletting($db,\%ny,\%gammel,\@felt,$tabell);
}
