#!/usr/bin/perl -w
##################################################
# This file is part of the NAV project.
#
# This perl-script uses a file named cricketoids.txt
# to fill the oid database with some initial oids
# that is used in relation to Cricket.
#
# Copyright (c) 2003 by NTNU, ITEA nettgruppen
# Authors: John Magne Bredal <bredal@itea.ntnu.no>
##################################################

use strict;
use Pg;
use Getopt::Std;

use vars qw ($opt_l $opt_h, $opt_f);

getopts('hl:f:');

&usage if $opt_h;

# Setting loglevel
my $ll = 2;
$ll = $opt_l if $opt_l;

my $oidfile = "cricketoids.txt";
$oidfile = $opt_f if $opt_f;

print "Using file $oidfile as sourcefile for oids.\n" if $ll >= 2;

# DB-vars
# Need to write a module to get password
my $db_name = "manage";
my $db_user = "manage";
my $db_pass = "eganam";

my $dbh = Pg::connectdb("dbname=$db_name user=$db_user password=$db_pass");

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
		my ($key,$oidkey,$snmpoid,$descr,$oidsource) = $res->fetchrow;
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
