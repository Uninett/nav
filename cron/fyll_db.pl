#!/usr/bin/perl
use strict;

require "/usr/local/nav/navme/etc/conf/path.pl";

my @tid = localtime(time);

#kommer på mail nå.
#pen(STDERR,'>>','/usr/local/nav/local/log/collect/sterr-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');
#pen(STDOUT,'>>','/usr/local/nav/local/log/collect/stout-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');

=cut
open(DBERR,'>>','/usr/local/nav/local/log/collect/collecterror-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');
open(DBOUT,'>>','/usr/local/nav/local/log/collect/collectupdate-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');

open(SNERR,'>>','/usr/local/nav/local/log/collect/snmperror-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');
open(SNOUT,'>>','/usr/local/nav/local/log/collect/sysnameerror-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');

open(GWERR,'>>','/usr/local/nav/local/log/collect/gwporterror-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');
open(GWOUT,'>>','/usr/local/nav/local/log/collect/gwport-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');

open(SWERR,'>>','/usr/local/nav/local/log/collect/swporterror-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');
open(SWOUT,'>>','/usr/local/nav/local/log/collect/swport-'.($tid[5]+1900).'-'.($tid[4]+1).'-'.$tid[3].'-'.$tid[2].'_'.$tid[1].'.log');
=cut

my $collect = &collect();

my $tid = localtime(time); 
print $tid.": START. Starter først oppdateringer fra tekstfilene.\n";

system    "$collect/tekstfiler.pl";
$tid = localtime(time); 
print $tid.": ferdig med tekstfilene, starter oppdatering av boksene.\n";

system    "$collect/bokser.pl";
$tid = localtime(time); 
print $tid.": ferdig med boksene, starter oppdatering av prefiks og gwporter.\n";

system    "$collect/gwporter.pl";
$tid = localtime(time); 
print $tid.": ferdig med gwporter, starter oppdatering av swporter og hjelpetabeller.\n";

system    "$collect/swporter.pl";
$tid = localtime(time); 
print $tid.": ferdig med swporter.pl, starter get_boksdata.\n";

system    "$collect/get_boksdata.pl";
$tid = localtime(time); 
print $tid.": ferdig med get_boksdata.pl, starter sletting fra trapdetectunntakene.\n";

system "$collect/slett_fra_trapdet_unntak.pl";
$tid = localtime(time); 
print $tid.": ferdig med slett_fra_trapdet_unntak.pl, og dermed helt FERDIG!\n";

