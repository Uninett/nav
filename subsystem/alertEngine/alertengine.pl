#!/usr/bin/perl

use strict;

use lib "$ENV{'NAV_PREFIX'}/lib/perl" ; 

use Engine;

my $tf = time();
my $e = Engine->new($Log::cfg);
$e->checkAlerts();
$e->disconnectDB();

my $te = time();
my $tdiff = $te - $tf;
