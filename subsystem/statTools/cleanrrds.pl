#!/usr/bin/perl -w
#############################################################
# This file is part of the NAV project.
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
# Copyright (c) 2003 by NTNU, ITEA nettgruppen
# Authors: John Magne Bredal <bredal@itea.ntnu.no>
############################################################

use vars qw($opt_l $opt_d $opt_t $opt_f $opt_h  $opt_p);
use Getopt::Std;
use Pg;
use strict;

my $pathtonav = "/usr/local/nav/navme/lib";
require "$pathtonav/NAV.pm";
import NAV;

my $dbh = &db_get('statTools');

my $deletelimit = 30;
my $usage = "
cleanrrds finds rrd-files that has not been written to for a specified time,
and lists them or deletes them according to your wishes.

usage: $0 [-hld] [-t days] [-f string] [-p path]
\th : this helpstring
\tl : flag to list files
\td : flag to delete files (CAUTION! This will actually DELETE the files.)
\tt days     : selects files that has not been written to in t days
\tf string   : selects files that match the string
\tp path     : sets the path where we start looking\n";

getopts('hldt:f:p:');

# Prints the help-text.
if ($opt_h) {
    print $usage;
    exit(0);
}

my $path = $opt_p;
$path = "/home/navcron/cricket/cricket-data/" unless $path;

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
# If the file has not been changed during the specified timeinterval, but is 
# in the database, leave it. Otherwise delete.

foreach my $line (@list) {

    chomp $line;
    $teller++;
    
    my $exists = 0;

    # Selects filepath,filename, time and size from the output.
    $line =~ m/(^\/.*)\/(.*\.rrd)\s(.*\d{2}:\d{2}:\d{2}\s\d{4})\s(\d+)/;
    chomp (my $filepath = $1);
    chomp (my $filename = $2);
    chomp (my $time = $3);
    chomp (my $size = $4);

    #printf ("%s,%s,%s,%s\n", $1, $2, $3, $4);

    # calculates total size of all files.
    $totalsize += $size;

    # Looks in the database for the file.
    my $query = "SELECT * FROM rrd_file WHERE path='$filepath' AND filename='$filename'";
    my $r = $dbh->exec($query);
    
    if ($r->ntuples > 0) {
	printf "%s,%s eksisterer i db.\n",$filepath,$filename;
	$exists = 1;
	$existteller++;
    }

    my $totalpath = "$filepath/$filename";

    # Lists the files
    if ($opt_l) {
	printf "%-70s %10s\n", $totalpath,$time;
    } elsif ($opt_d && !$exists) {
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
    }
}
    
my $mbytes = int ($totalsize / (1024 * 1024));
if ($opt_f) {
    print "\n$teller rrd-files found that has not been modified in $days days, and matches string \"$opt_f\". $existteller of these are also in the database.\n";
} else {
    print "\n$teller rrd-files found that has not been modified in $days days. $existteller of these are also in the database.\n";
}
print "Total size = $totalsize bytes (~$mbytes MB).\n";
