#!/usr/bin/perl
use strict;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $localkilde = &localkilde();
require "$lib/fil.pl";
&log_open;

my @tid = localtime(time);

my $collect = &collect();

&skriv("RUN-START","program=tekstfiler");
#my $tid = localtime(time); 
#print $tid.": START. Starter først oppdateringer fra tekstfilene.\n";

system    "$collect/tekstfiler.pl";
&skriv("RUN-END","program=tekstfiler");

&skriv("RUN-START","program=bokser");
#$tid = localtime(time); 
#print $tid.": ferdig med tekstfilene, starter oppdatering av boksene.\n";

system    "$collect/bokser.pl";
&skriv("RUN-END","program=bokser");

&skriv("RUN-START","program=gwporter");
#$tid = localtime(time); 
#print $tid.": ferdig med boksene, starter oppdatering av prefiks og gwporter.\n";

system    "$collect/gwporter.pl";
&skriv("RUN-END","program=gwporter");

&skriv("RUN-START","program=swporter");
#$tid = localtime(time); 
#print $tid.": ferdig med gwporter, starter oppdatering av swporter og hjelpetabeller.\n";

system    "$collect/swporter.pl";
&skriv("RUN-END","program=swporter");

&skriv("RUN-START","program=get_boksdata");
#$tid = localtime(time); 
#print $tid.": ferdig med swporter.pl, starter get_boksdata.\n";

system    "$collect/get_boksdata.pl";
&skriv("RUN-END","program=get_boksdata");

&skriv("RUN-START","program=slett_fra_trapdetect_unntak");
#$tid = localtime(time); 
#print $tid.": ferdig med get_boksdata.pl, starter sletting fra trapdetectunntakene.\n";

system "$collect/slett_fra_trapdet_unntak.pl";
&skriv("RUN-END","program=slett_fra_trapdetect_unntak");


#$tid = localtime(time); 
#print $tid.": ferdig med slett_fra_trapdet_unntak.pl, og dermed helt FERDIG!\n";

&log_close;
