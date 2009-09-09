#!/usr/bin/env perl
#
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# Authors: John Magne Bredal <bredal@itea.ntnu.no>
#
# The purpose of this script is to search the cricket-data
# directory for rrd-files that are not in use anymore, and
# let the user delete these files if he wants.
#
# To accomplish this, we use find to locate the files, and
# then either lists them or deletes them in according to
# the users wishes.
#
# cleanrrds -h for help.
#

use warnings;
use vars qw($opt_l $opt_d $opt_t $opt_f $opt_h  $opt_p $opt_r);
use Getopt::Std;
use Pg;
use strict;

use NAV;

my $dbh = &NAV::connection('statTools', 'manage');

my $deletelimit = 30;
my $usage = "
cleanrrds finds rrd-files that has not been written to for a specified time,
and lists them or deletes them according to your wishes.

usage: $0 [-hld] [-t days] [-f string] [-p path]
\th : this helpstring
\tl : flag to list files
\td : flag to delete files (CAUTION! This will actually DELETE the files.)
\tr : flag to reverse-search, do a lookup in the database and delete entry if no rrd-file is found
\tt days     : selects files that has not been written to in t days
\tf string   : selects files that match the string
\tp path     : sets the path where we start looking\n";

getopts('rhldt:f:p:');

# Prints the help-text.
if ($opt_h) {
    print $usage;
    exit(0);
}

my $path = $opt_p;
$path = "/home/navcron/cricket/cricket-data/" unless $path;


if ($opt_r) {
    &reverseSearch();
    exit(0);
}

# Checking if both -d and -l option is selected
if ($opt_d && $opt_l) {
    print "You have selected both list and delete. The files will only be listed.\n";
}

# Setting default value of days if not set.
my $days = $opt_t;
$days = 30 unless $days;

# Checking if day is formatted correctly.
unless ($days =~ m/^\d+$/) {
    print $usage;
    exit(0);
}

# The list contains the output from the find-program.
my @list;
unless ($opt_f) {
    @list = `find $path -type f -mtime +$days -printf '%p %t %s\n' | grep '\\.rrd'`;
} else {
    @list = `find $path -type f -mtime +$days -printf '%p %t %s\n' | grep '\\.rrd' | grep $opt_f`;
}

my $teller = 0; # The number of files found
my $existteller = 0; # The number of files found also in the database
my $totalsize = 0; # The total size of all files in bytes.

# The general idea is this:
# If the file has been changed in the specified timeinterval, leave it.
# Otherwise delete

foreach my $line (@list) {

    chomp $line;
    $teller++;
    
    my $exists = 0;

    # Selects filepath,filename, time and size from the output.
    $line =~ m/(^\/.*)\/(.*\.rrd)\s(.*\d{2}:\d{2}:\d{2}(\.\d{10})?\s\d{4})\s(\d+)/;
    chomp (my $filepath = $1);
    chomp (my $filename = $2);
    chomp (my $time = $3);
    chomp (my $size = $5);

    #printf ("%s,%s,%s,%s\n", $1, $2, $3, $4);

    # calculates total size of all files.
    $totalsize += $size;

    # Looks in the database for the file.
    my $query = "SELECT rrd_fileid FROM rrd_file WHERE path='$filepath' AND filename='$filename'";
    my $r = $dbh->exec($query);
    
    my ($rrd_fileid) = $r->fetchrow;
    if ($r->ntuples > 0) {
	printf "%s,%s eksisterer i db.\n",$filepath,$filename;
	$exists = 1;
	$existteller++;
    }

    my $totalpath = "$filepath/$filename";

    # Lists the files
    if ($opt_l) {
	printf "%-70s %10s\n", $totalpath,$time;
    } elsif ($opt_d) {
	# Deletes the files.
	if (-e "$totalpath") {
	    print "Deleting $totalpath\n";
	    `rm -f \"$totalpath\"`;
	    
	    # Finds metafile
	    $totalpath =~ s/\.rrd/\.meta/; # somefile.rrd -> somefile.meta
	    if (-e "$totalpath") {
		print "Deleting $totalpath\n";
		`rm -f \"$totalpath\"`;
	    }
	}
	# Deleting from the database
	my $deleteq = "DELETE FROM rrd_file WHERE rrd_fileid = $rrd_fileid";
	my $deleter = $dbh->exec($deleteq);
    }
}
    
my $mbytes = int ($totalsize / (1024 * 1024));
if ($opt_f) {
    print "\n$teller rrd-files found that has not been modified in $days days, and matches string \"$opt_f\". $existteller of these are also in the database.\n";
} else {
    print "\n$teller rrd-files found that has not been modified in $days days. $existteller of these are also in the database.\n";
}
print "Total size = $totalsize bytes (~$mbytes MB).\n";


sub reverseSearch() {
    my $q = "SELECT rrd_fileid, path, filename FROM rrd_file WHERE subsystem='cricket'";
    my $r = $dbh->exec($q);

    my $existcounter = 0;
    my $deletedcounter = 0;

    while (my ($rrd_fileid, $path, $filename) = $r->fetchrow) {
	my $totalpath = "$path/$filename";
	if (-e $totalpath) {
	    $existcounter++;
	    print "$totalpath exists.\n";
	} else {
	    $deletedcounter++;
	    print "Could not find $totalpath, deleting it from db.\n";
	    my $deleteq = "DELETE FROM rrd_file WHERE rrd_fileid=$rrd_fileid";
	    print "$deleteq\n";
	    my $deleter = $dbh->exec($deleteq);
	}
    }

    printf "%s tuples checked, %s deleted, kept %s\n", $existcounter + $deletedcounter, $deletedcounter, $existcounter;

}
