#!/usr/bin/perl -w

use strict;
require "felles.pl";

#-------------ALLE-------------
my $db = "manage";
my $conn = db_connect($db);
my ($fil,$tabell,@felt);
#--------------ANV-------------
$fil = "/usr/local/nav/etc/anv.txt";
$tabell = "anv";
@felt = ("anvid","descr");
&db_endring($fil,$tabell,\@felt);
#--------------STED------------
$fil = "/usr/local/nav/etc/sted.txt";
$tabell = "sted";
@felt = ("stedid","descr");
&db_endring($fil,$tabell,\@felt);
#--------------ROM-------------
$fil = "/usr/local/nav/etc/rom.txt";
$tabell = "rom";
@felt = ("romid","stedid","descr","rom2","rom3","rom4","rom5");
&db_endring($fil,$tabell,\@felt);
#--------------ORG-------------
$fil = "/usr/local/nav/etc/org.txt";
$tabell = "org";
@felt = ("orgid","forelder","descr","org2","org3","org4");
&db_endring($fil,$tabell,\@felt);
@felt = ("orgid","forelder","descr","org2","org3","org4");
&db_endring($fil,$tabell,\@felt);
#--------------FELLES_KODE-----
sub db_endring {
    my $fil = $_[0];
    my $tabell = $_[1];
    my @felt = @{$_[2]};
    my @gen = (); my $sql = ""; my $resultat = ""; my %ny = (); my %gammel = ();

    %ny = &fil_hent($fil,scalar(@felt));
    #leser fra database
    %gammel = &db_hent($conn,"SELECT ".join(",", @felt )." FROM $tabell ORDER BY $felt[0]");

    #alle nøklene i hashen ny
    for my $f (keys %ny) {

	#eksisterer i databasen?
	if($gammel{$f}[0]) {
#-----------------------
#UPDATE
	    for my $i (0..$#felt ) {
		if(defined( $gammel{$f}[$i] ) && defined( $ny{$f}[$i] )){
		    unless($ny{$f}[$i] eq $gammel{$f}[$i]) {
			#oppdatereringer til null må ha egen spørring
			if ($ny{$f}[$i] eq "" && $gammel{$f}[$i] ne ""){
			    &oppdater($conn,$tabell,$felt[$i],$gammel{$f}[$i],"null",$felt[0],$f);
			} else {

			    &oppdater($conn,$tabell,$felt[$i],"\'$gammel{$f}[$i]\'","\'$ny{$f}[$i]\'",$felt[0],$f);
			}
		    }
		}
	    }
	}else{
#-----------------------
#INSERT
	    &db_sett_inn($conn,$tabell,join(":",@felt),join(":",@{$ny{$f}}));

	}
    }
#-----------------------------------
#DELETE
    #hvis den ikke ligger i fila
    for my $f (keys %gammel) {
	unless(exists($ny{$f})) {
	    &slett($conn,$tabell,$felt[0],$f);
	}
    }

}
return 1;
