#!/usr/bin/perl

use strict;

use Engine;

BEGIN {require "alertengine.cfg";}

my $tf = time();
print "Running...\n";
my $e = Engine->new($cfg);
$e->checkAlerts();
$e->disconnectDB();

my $te = time();
my $tdiff = $te - $tf;
print "Elapsed time alertsession: " . $tdiff . " seconds.\n\n";
