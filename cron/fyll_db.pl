#!/usr/bin/perl
####################
#
# $Id: fyll_db.pl,v 1.9 2003/06/05 11:18:30 gartmann Exp $
# This file is part of the NAV project.
# fyll_db is a starts a sequence of cron-tasks, each defined in their 
# respective code. fyll_db's primary task is to start the scripts that
# collects SNMP information and updates the database according to this.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;

require '/usr/local/nav/navme/lib/NAV.pm';
import NAV;

my $localkilde = get_path("path_localkilde");
my $collect = get_path("path_collect");

my @tid = localtime(time);

# tar inn en parameter som er en ip-adresse på formen bokser.pl ip=123.456.789.0
my $one_and_only = shift;

if($one_and_only){ #har sann verdi
    if($one_and_only =~ /^(\d+\.\d+\.\d+\.\d+)$/i){
	$one_and_only = $1;
    } else {
	die("Invalid ip-address: $one_and_only\n");
    }
}

system    "/usr/local/nav/navme/cron/navlog/defaults.pl";

&log_open;
&skriv("RUN-START","program=tekstfiler");
&log_close;

system    "$collect/tekstfiler.pl";

&log_open;
&skriv("RUN-END","program=tekstfiler");

&skriv("RUN-START","program=bokser");
&log_close;

system    "$collect/bokser.pl $one_and_only";

&log_open;
&skriv("RUN-END","program=bokser");

&skriv("RUN-START","program=gwporter");
&log_close;

system    "$collect/gwporter.pl $one_and_only";

&log_open;
&skriv("RUN-END","program=gwporter");

&skriv("RUN-START","program=swporter");
&log_close;

system    "$collect/swporter.pl $one_and_only";

&log_open;
&skriv("RUN-END","program=swporter");

unless($one_and_only){
    &skriv("RUN-START","program=get_boksdata");
    &log_close;
    
    system    "$collect/get_boksdata.pl";
    
    &log_open;
    &skriv("RUN-END","program=get_boksdata");

    &skriv("RUN-START","program=slett_fra_trapdetect_unntak");
    &log_close;

    system "$collect/slett_fra_trapdet_unntak.pl";
    
    &log_open;
    &skriv("RUN-END","program=slett_fra_trapdetect_unntak");

}
&log_close;

