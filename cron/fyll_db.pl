#!/usr/bin/perl
use strict;

my $sti = '/usr/local/nav/navme/cron/kollekt/';

my $tid = localtime(time); 
print "START $tid\n";

system $sti."tekstfiler.pl";
print "ferdig med tekstfilene\n";

$tid = localtime(time); 
print "$tid\n";
system $sti."bokser.pl";
print "ferdig med boksene\n";

$tid = localtime(time); 
print "$tid\n";
system $sti."gwporter.pl";
print "ferdig med gwporter\n";

$tid = localtime(time); 
print "$tid\n";
system $sti."swporter.pl";
print "ferdig med swporter.pl\n";

$tid = localtime(time); 
print "$tid\n";
system $sti."get_boksdata.pl";
print "ferdig med get_boksdata.pl\n";

$tid = localtime(time); 
print "$tid\n";
system $sti."slett_fra_trapdet_unntak.pl";
print "ferdig med slett_fra_trapdet_unntak.pl\n";

$tid = localtime(time); 
print " FERDIG: $tid\n";
