#!/usr/bin/perl

use strict;

use Engine;

my $tf = time();
my $e = Engine->new($Log::cfg);
$e->checkAlerts();
$e->disconnectDB();

my $te = time();
my $tdiff = $te - $tf;
