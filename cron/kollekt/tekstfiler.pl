#!/usr/bin/perl -w
use strict;

my $vei = "/usr/local/nav/navme/lib";
require "$vei/database.pl";
require "$vei/fil.pl";
#-------------ALLE-------------
my $db = &db_connect("manage","navall","uka97urgf");
my ($fil,$tabell,@felt);
#--------------ANV-------------
$fil = "/usr/local/nav/etc/anv.txt";
$tabell = "anv";
@felt = ("anvid","descr");
&db_endring_med_sletting($db,$fil,$tabell,join(":",@felt));
#--------------STED------------
$fil = "/usr/local/nav/etc/sted.txt";
$tabell = "sted";
@felt = ("stedid","descr");
&db_endring_med_sletting($db,$fil,$tabell,join(":",@felt));
#--------------ROM-------------
$fil = "/usr/local/nav/etc/rom.txt";
$tabell = "rom";
@felt = ("romid","stedid","descr","rom2","rom3","rom4","rom5");
&db_endring_med_sletting($db,$fil,$tabell,join(":",@felt));
#--------------ORG-------------
$fil = "/usr/local/nav/etc/org.txt";
$tabell = "org";
@felt = ("orgid","forelder","descr","org2","org3","org4");
&spesiell_endring_org($db,$fil,$tabell,join(":",@felt),join(":",@felt));
#@felt = ("orgid","forelder","descr","org2","org3","org4");
#&db_endring_med_sletting($db,$fil,$tabell,join(":",@felt));
#--------------TYPE------------
$fil = "/usr/local/nav/etc/type.txt";
$tabell = "type";
@felt = ("typeid","typegruppe","sysObjectID","descr");
&db_endring_med_sletting($db,$fil,$tabell,join(":",@felt));
#--------------PREFIKS---------
$fil = "/usr/local/nav/etc/prefiks.txt";
$tabell = "prefiks";
@felt = ("nettadr","maske","nettype","orgid","komm");
&db_endring_uten_sletting($db,$fil,$tabell,join(":",@felt));
#--------------SLUTT-----------


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
