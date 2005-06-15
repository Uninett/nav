#!/usr/bin/env perl
#
# $Id$
# This perl-script uses a file named cricketoids.txt to fill the oid
# database with some initial oids that is used in relation to Cricket.
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

use strict;
use warnings;
use Pg;
use Getopt::Std;

use NAV;

use vars qw ($opt_l $opt_h $opt_f);

getopts('hl:f:');

&usage if $opt_h;

# Setting loglevel
my $ll = 2;
$ll = $opt_l if $opt_l;

my $oidfile = "cricketoids.txt";
$oidfile = $opt_f if $opt_f;

print "Using file $oidfile as sourcefile for oids.\n" if $ll >= 2;

# Connecting to database.
my $dbh = &NAV::connection('statTools', 'manage');

my $keyword = "Cricket";
my $keyword2 = "mib-II";

&fillfromfile();


##################################################
# Fetching the oid's from file, and inserts them 
# in the database.
##################################################
sub fillfromfile {

    my $query;
    my $res;
    my $counter = 0;
    my $necounter = 0;
    my $foundcounter = 0;

    open (HANDLE, $oidfile) or die "Could not open $oidfile: $!\n";
    while (<HANDLE>) {
	if (/^\w+/) {
	    my @splitresult = split /\s+/;
	    my $oidtext = shift @splitresult;
	    my $oid = shift @splitresult;
	    my $oiddescr = join " ", @splitresult;
	    
	    $query = "SELECT * FROM snmpoid WHERE oidkey='$oidtext' AND snmpoid='$oid'";
	    print "$query\n" if $ll >= 3;
	    $res = $dbh->exec($query);

	    if ($res->ntuples > 0) {

		# I want a perlmodule which fills hashes with db-output...
		my @result = $res->fetchrow;

		my $oidkey = $result[$res->fnumber('oidkey')];
		my $snmpoid = $result[$res->fnumber('snmpoid')];
		my $descr = $result[$res->fnumber('descr')];
		my $oidsource = $result[$res->fnumber('oidsource')];

		if (($oidsource eq $keyword) || ($oidsource eq $keyword2)) {
		    $foundcounter++;
		    printf "Found existing row %s,%s,%s,%s\n",$oidkey,$snmpoid,$descr,$oidsource if $ll >= 3;
		    next;
		} else {
		    print "Found source $oidsource, which is not like $keyword or $keyword2.\n" if $ll>=2;
		    $necounter++;
		    next;
		}

	    }
	    
	    my $oidsource;
	    my $getnext;
	    
	    # Sets correct paramaters based on if this is a interface or not.
	    if ($oidtext =~ /^if.*/) {
		$oidsource = $keyword2;
		$getnext = 't';
	    } else {
		$oidsource = $keyword;
		$getnext = 'f';
	    }

	    $query = "INSERT INTO snmpoid (oidkey,snmpoid,descr,oidsource,getnext) VALUES ('$oidtext','$oid','$oiddescr','$oidsource','$getnext')";
	    print "$query\n" if $ll >= 3;
	    $res = $dbh->exec($query);

	    $counter++;

	    unless ($res->resultStatus) {
		print "Error: $dbh->errorMessage\n" if $ll >= 1;
	    }
	}
    }
    close HANDLE;

    print "Added $counter rows.\n" if $ll >= 2;
    print "Found $foundcounter existing snmpoids of which $necounter did not have $keyword or $keyword2 as description.\n" if $ll >= 2;

}

sub usage {
    print "Usage: $0 [-h] [-l loglevel]\n";
    print "\t-h: this helptext\n";
    print "\t-l: specify loglevel (1=silent, 2=normal, 3=debug)\n";
    
    exit(0);
       
}
