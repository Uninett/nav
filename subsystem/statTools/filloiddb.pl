#!/usr/bin/perl -w

##################################################
# FILLOIDDB
# -----------------
# ITEA NTNU © 2003
# Author: John Magne Bredal <bredal@itea.ntnu.no>
##################################################

use strict;
use Pg;
use Getopt::Std;

use vars qw ($opt_l $opt_h);

getopts('hl:');

my $ll = 0;
$ll = $opt_l if $opt_l;

# Global vars
my $oidfile = "cricketoids.txt";
print "Using file $oidfile as sourcefile for oids.\n" if $ll >=1;

# DB-vars
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
#	    print "$query\n";
	    $res = $dbh->exec($query);

	    if ($res->ntuples > 0) {
		my ($key,$oidkey,$snmpoid,$descr,$oidsource) = $res->fetchrow;
		if (($oidsource eq $keyword) || ($oidsource eq $keyword2)) {
		    $foundcounter++;
#		    printf "Found existing row %s,%s,%s,%s\n",$oidkey,$snmpoid,$descr,$oidsource;
		    next;
		} else {
		    print "Found source $oidsource, which is not like $keyword or $keyword2.\n" if $ll>=2;
		    $necounter++;
		}

	    }
	    
	    my $y;
	    if ($oidtext =~ /^if.*/) {$y=$keyword2;} else {$y=$keyword;}

	    $query = "INSERT INTO snmpoid (oidkey,snmpoid,descr,oidsource) VALUES ('$oidtext','$oid','$oiddescr','$y')";
	    print "$query\n";
	    $res = $dbh->exec($query);

	    $counter++;

	    unless ($res->resultStatus) {
		print "Error: $dbh->errorMessage\n";
	    }
	}
    }
    close HANDLE;

    print "Added $counter rows.\n" if $ll>=1;
    print "Found $foundcounter existing snmpoids of which $necounter did not have $keyword or $keyword2 as description.\n" if $ll>=1;

}
