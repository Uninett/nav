#!/usr/bin/perl

use strict;
use Time::Local 'timelocal_nocheck';

require "/usr/local/nav/navme/lib/database.pl";
require "/usr/local/nav/navme/lib/fil.pl";

my $fil = "/usr/local/nav/local/etc/conf/syslog/databaseslett.txt";

my @prioritet;

my $dag = 86400;
my @tid = localtime(time());
my $midnatt = timelocal_nocheck(0,0,0,$tid[3],$tid[4],$tid[5]);

&slettefil($fil);
my $database = &db_get("syslogslett");

for (my $p = 0; $p<@prioritet;$p++) {
    if(exists($prioritet[$p])){
	my $grense = &timestampformat($midnatt-$dag*$prioritet[$p]);
	&db_delete($database,"meldinger","prioritet=$p and tid<\'$grense\'");
    }
}

sub timestampformat {
    my @timestamp = localtime($_[0]);
    return ($timestamp[5]+1900)."-".($timestamp[4]+1)."-".$timestamp[3]." ".$timestamp[2].":".$timestamp[1].":".$timestamp[0];
}

sub slettefil {
    my $fil = $_[0];
    my @linje;

    open (FIL, "<$fil") || die ("KUNNE IKKE ÅPNE FILA: $fil");
    foreach (<FIL>) {
	if(@linje = &fil_hent_linje(2,$_)){
	    if($linje[0] ne "" && $linje[1] ne ""){
		$prioritet[$linje[0]] = $linje[1];
	    }
	}
    }
    close FIL;
}
