#!/usr/bin/perl
####################
#
# $Id: delete.pl,v 1.2 2002/11/25 12:13:56 gartmann Exp $
# This file is part of the NAV project.
# delete reads a config file that defines for how long time data is to be
# stored in the navlog database. delete deletes the data that has passed the
# 'best before' dato.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;
use Time::Local 'timelocal_nocheck';
require '/usr/local/nav/navme/lib/NAV.pm';
import NAV qw(:DEFAULT :collect);

my $path = &get_path("path_localconf");

my $fil = $path."navlog/delete.conf";

my @prioritet;

my $dag = 86400;
my @tid = localtime(time());
my $midnatt = timelocal_nocheck(0,0,0,$tid[3],$tid[4],$tid[5]);

&slettefil($fil);
my $database = &db_get("delete");

for (my $p = 0; $p<@prioritet;$p++) {
#    print "skal slette $p\n";
    if(exists($prioritet[$p])){
	my $grense = &timestampformat($midnatt-$dag*$prioritet[$p]);
	&db_delete($database,"message","id IN (SELECT message.id FROM message JOIN type ON (message.typeid=type.id) WHERE type.priorityid=".($p+1)." and time<\'$grense\')");
    }
#    print"har slettet $p\n";
}

### Brukes for å oversette fra perlformat til database timestamp
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
