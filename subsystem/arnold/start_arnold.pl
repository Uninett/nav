#!/usr/bin/env perl
#
# $Id$
#
# This script is used to call arnold.pl from either the commandline or
# another computer using ssh. Note that public_keys must be exchanged
# and there must be a trust-relationship between the computers for
# this to work. It takes two options as input - what blocktype to run
# and a list of ip-addresses. The list of ip-addresses may come from
# either STDIN or a file.
#
# Copyright 2003-2005 Norwegian University of Science and Technology
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
# Authors: John Magne Bredal <john.m.bredal@ntnu.no>
#

use strict;
use Pg;
use Getopt::Std;
use vars qw($opt_h $opt_i $opt_f);
use NAV;
use NAV::Path;
use NAV::Arnold;
use Fcntl;

my %cfg = readconfig();
my $home = $NAV::Path::bindir;
my $logdir = $NAV::Path::localstatedir."/log/arnold";
my $logfile = "start_arnold.log";

chomp (my $datetime = `date +%y%m%d-%H%M%S`);
umask (0117);
open (LOG, ">>$logdir/$logfile") or die ("Could not open $logdir/$logfile: $!\n");
print LOG "\n\n========== NEW LOGENTRY $datetime ==========\n\n";

my $usage = "$0 [-h] [-i <id>] [-f <list of ip-adresses>]
-h this helpstring
-i id of blockrun to run
-f specify path to file with list of ip-adresses

NOTE - you can pipe in a list of ip-adresses if you want. This
script will read from STDIN and parse the input.
";


# Connect to the arnold-database.
my $dbh_block = &NAV::connection('arnold','arnold');


# Get options from the commandline
getopts('hi:f:');

unless ($opt_i) {
    print $usage;
    exit(1);
}


# Get blocktype-variables from the database.
my @options = &getBlockOptions($opt_i);


# Use either the ip-addresses from STDIN or from file.
my $ipstring = "";
if ($opt_f) {
    print LOG "Got option $opt_f\n";
    push @options, "-f$opt_f";
} else {
    $ipstring = &fixInput();
    unless ($ipstring) {
	print "Could not understand input, exiting.\n";
	exit(1);
    }
    push @options, "-a$ipstring";
    print LOG "Got list of ip-adresses: $ipstring\n";
}

printf LOG "$home/arnold.pl %s\n", join(" ", @options);
system ("$home/arnold.pl", @options);

close LOG;

##################################################
# sub getBlockOptions
##################################################
sub getBlockOptions {
    my $id = shift;

    my @options;
    push @options, "-xdisable";


    # Get data from the database where blocktype = id
    my $query = "SELECT * FROM block WHERE blockid=$id";
    my $res = $dbh_block->exec($query);

    # The fields in the block-table look like this:
    # 0 - blockid
    # 1 - blocktitle
    # 2 - blockdesc
    # 3 - mailfile
    # 4 - reasonid
    # 5 - private
    # 6 - determined
    # 7 - incremental
    # 8 - blocktime
    # 9 - userid
    # 10 - active
    # 11 - lastedited
    # 12 - lastedituser


    # If it does not exists, exit
    if ($res->ntuples == 0) {
	print LOG "No id in the database matches $id, exiting.\n";
	exit(1);
    }


    # If there, for some obscure reason, are more than 1 with this id, exit.
    if ($res->ntuples > 1) {
	print LOG "Several tuples in the database matches $id, exiting.\n";
	exit(1);
    }

    my ($blockid, $blocktitle, $blockdesc, $mailfile, $reasonid, $private, $determined, $incremental, $blocktime, $userid, $active, $lastedited, $lastedituser) = $res->fetchrow;


    # Start building the textstring we use to run arnold.pl

    # mailfile
    if ($mailfile) {
	push @options, "-m$mailfile";
    }

    # reason (mandatory)
    if ($reasonid) {
	push @options, "-r$reasonid";
    } else {
	print LOG "No reason for block found in database, cannot continue with block. Exiting.\n";
	exit(1);
    }

    # time for autoenable (mandatory)
    if ($blocktime && $incremental eq 'n') {
	push @options, "-t$blocktime";
    } elsif ($blocktime && $incremental eq 'y') {
	push @options, "-e$blocktime";
    } else {
	print LOG "Blocktime not set, can not continue with block, exiting.\n";
	exit(1);
    }

    # determined
    if ($determined eq 'y') {
	push @options, "-d";
    }

    # user
    if ($userid) {
	push @options, "-u$userid";
    }

    return @options;

}

##################################################
# sub fixInput
# Parses input from STDIN and returns it as an option
# to arnold.pl
##################################################
sub fixInput {

    my @lines = <STDIN>;

    if ($#lines < 0) {
	return 0;
    }


    # At the moment we assume one ip-adress for each line. 
    my @adresses;
    for (@lines) {
	if (/^(\d+\.\d+\.\d+\.\d+)/) {
	    push @adresses, $1;
	}
    }

    return join (",",@adresses);

}
