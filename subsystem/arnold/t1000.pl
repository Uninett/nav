#!/usr/bin/env perl
#
# $Id$
#
# This script fetches all blocked ports and checks if the mac-adresses
# has moved to another port.
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
use NAV;
use NAV::Path;
use NAV::Arnold;

use vars qw($opt_h $opt_l);

getopts('hl:');

my $ll = 1; # default loglevel

my $usage = "$0 [-h] [-l loglevel]
\t-h print this
\t-l set loglevel (1 or 2, 1 is default, 2 is debug)
";


my %cfg = readconfig();
my $home = $NAV::Path::bindir;
my $logdir = $NAV::Path::localstatedir."/log/arnold";
my $logfile = "t1000.log";

chomp (my $datetime = `date +%y%m%d-%H%M%S`);
umask (0117);
open (LOG, ">>$logdir/$logfile") or die ("Could not open $logdir/$logfile: $!\n");
print LOG "\n\n========== NEW LOGENTRY $datetime ==========\n\n";


if ($opt_h) {
    print $usage;
    exit;
}

if ($opt_l && $opt_l =~ /[12]/) {
    printf LOG "Setting loglevel to %s\n", $opt_l if $opt_l >= 2;
    $ll = $opt_l;
}

# Connect to database
my $dbh_block = &NAV::connection('arnold','arnold');


# We need a connection to the manage-database to find cam and mac-data
my $dbh_manage = &NAV::connection('arnold','manage');


# Fetch all blocked ports and the mac-address that was behind that
# port. We set a time-limit as the mac-address may still be active in
# the cam-table even though the computer is disconnected.

my $query = "SELECT identityid,mac,blocked_reasonid,swsysname,swmodule,swport,determined FROM identity WHERE blocked_status='disabled' AND lastchanged < now() + '-1 hour'";
my $result = $dbh_block->exec($query);



my $kills = 0; # The number of travelling computers found.


# For each mac-address, check if it is active on another port
while (my ($identityid,$mac,$blocked_reason,$swsysname,$swmodule,$swport,$determined) = $result->fetchrow) {

    print LOG "---------------\n" if $ll >= 2;
    printf LOG "Checking %s.\n", $mac if $ll >= 2;


    # If it is active, block the port it is connected to
    my $q = "SELECT sysname,modul,port FROM cam WHERE mac='$mac' AND end_time='infinity'";
    my $r = $dbh_manage->exec($q);

    if ($r->ntuples == 1) {
	printf LOG "%s has moved.\n", $mac if $ll >= 1;


	my ($sysname,$mod,$port) = $r->fetchrow;
	my $toport = "Unknown";
	my $ip = 0;


	# From port
	my $fromport = "$swsysname $swmodule:$swport";
	print LOG "Setting from-port = $fromport\n" if $ll >= 1;


	# To port
	$toport = "$sysname $mod:$port";
	print LOG "Setting to-port = $toport\n" if $ll >= 1;


	# If from and to port are equal, something is wrong and we
	# skip to the next port.
	if ($toport eq $fromport) {
	    print LOG "$toport == $fromport, this shouldn't happen...getting next.\n\n" if $ll >= 1;
	    next;
	}


	# Find autoenablestep
	my $autoenablestep = 0;

	$q = "SELECT autoenablestep FROM event WHERE blocked_reasonid=$blocked_reason AND identityid=$identityid AND autoenablestep IS NOT NULL order by eventtime DESC";
	$r = $dbh_block->exec($q);
	print LOG "$q\n" if $ll >= 2;

	if ($r->ntuples > 0) {
	    ($autoenablestep) = $r->fetchrow;
	    print LOG "Setting autoenablestep to $autoenablestep.\n" if $ll >= 1;
	} else {
	    print LOG "Could not find autoenablestep.\n" if $ll >= 1;
	}


	# Find the ip-address
	$q = "SELECT ip FROM arp WHERE mac='$mac' AND end_time='infinity'";
	$r = $dbh_manage->exec($q);

	print LOG "$q\n" if $ll >= 2;

	if ($r->ntuples == 1) {
	    ($ip) = $r->fetchrow;
	    print LOG "Setting ip = $ip\n" if $ll >= 1;
	} else {
	    printf LOG "Could not find in cam-table, continuing.\n", $r->ntuples if $ll >= 1;
	    next;
	}


	# Run arnold.pl with the ip-address as input
	&terminate($ip, $determined, $toport, $fromport, $autoenablestep, $blocked_reason);
	$kills++;

	print LOG "\n";

    } elsif ($r->ntuples > 1) {
	printf LOG "%s active: %s ports - do not kill.\n", $mac, $r->ntuples if $ll >= 1;
    } else {
	printf LOG "Inactive.\n", $mac if $ll >= 2;
    }
}


# Write summary, exit.
printf LOG "\nChecked %s identities in %s second(s).\n", $result->ntuples, time - $^T if $ll >= 1;
printf LOG "Kills: %s\n", $kills if $ll >= 1;

close LOG;

# This sub calls arnold.pl and sets the correct options based on the
# information in the database.
sub terminate {
    my ($ip, $determined, $to, $from, $step, $reason) = @_;

    my $exec = "$home/arnold.pl -x disable -a $ip -r$reason -u cron -c \"travelling from $from -> $to\"";

    if ($determined eq 'y') {
	$exec .= " -d";
    }

    if ($step) {
	$exec .= " -t $step";
    }
	
    if ($ll >= 1) {
	print LOG "Running sub-program:\n";
	`$exec`;
	print LOG "$exec\n" if $ll >= 1;
    }


}
