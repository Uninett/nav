#!/usr/bin/perl
use strict;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $collect = &collect();

my $tid = localtime(time); 
print "START $tid\n";

system "$collect/tekstfiler.pl";
print "ferdig med tekstfilene\n";

$tid = localtime(time); 
print "$tid\n";
system "$collect/bokser.pl";
print "ferdig med boksene\n";

$tid = localtime(time); 
print "$tid\n";
system "$collect/gwporter.pl";
print "ferdig med gwporter\n";

$tid = localtime(time); 
print "$tid\n";
system "$collect/swporter.pl";
print "ferdig med swporter.pl\n";

$tid = localtime(time); 
print "$tid\n";
system "$collect/get_boksdata.pl";
print "ferdig med get_boksdata.pl\n";

$tid = localtime(time); 
print "$tid\n";
system "$collect/slett_fra_trapdet_unntak.pl";
print "ferdig med slett_fra_trapdet_unntak.pl\n";

$tid = localtime(time); 
print " FERDIG: $tid\n";
