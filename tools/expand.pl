#!/usr/bin/env perl
#
# Copyright 2003 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# NAV development tool used to expand environment variable references
# in files during build (not at configure-time).  When used in
# MakefileS, make sure to have your Makefile export all variables to
# the environment.
#
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#
use warnings;
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
