#!/usr/bin/perl -w
#
# NAV development tool used to expand environment variable references
# in files during build (not at configure-time).  When used in
# MakefileS, make sure to have your Makefile export all variables to
# the environment.
#
# Copyright (C) 2003 NTNU ITEA
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#

my @vars = keys %ENV;

sub expand {
    my $param = shift;
    return $ENV{$param};
}

for my $line (<>) {
    for my $var (@vars) {
	$line =~ s/\@($var)\@/&expand($1)/eg;
    }
    print $line;
}
