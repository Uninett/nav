#!/usr/bin/perl 

############################################################
# $Id$
#
# This file is part of the NAV project.
#
# Takes info from the snmpoid-table, checks it with the
# units that are on the network, and writes the correct
# relations in the typesnmpoid-table.
#
# Copyright (c) 2003 by NTNU, ITEA nettgruppen
# Authors: John Magne Bredal <bredal@itea.ntnu.no>
############################################################

use vars qw($opt_l $opt_h);
use Getopt::Std;

use strict;
use Pg;
use SNMP::Util;

# Loglevels are:
# 1 -> silent
# 2 -> normal
# 3 -> debug
# 4 -> with all the SNMP-queries 
my $loglevel = 2;
my $snmpversion = 1;

my $frequency = 5; # What number to put in the row "frequency" in the typesnmpoid-table

my $usage = "
USAGE: $0 [-h] [-l loglevel]
l : loglevel (1: silent, 2: normal (default), 3: debug)
h : this help
NB! This script takes a LONG time to run (10-20 minutes).
\n";

getopts('hl:');

$SNMP::Util::Max_log_level = 'none'; # Loglevel for the SNMP::Util pm

if ($opt_h) {
    print $usage;
    exit(1);
}

if ($opt_l && $opt_l =~ m/\d/) {
    $loglevel = $opt_l;
    print "Setting loglevel to $loglevel.\n" if $loglevel >= 2;
}

# DB-vars - must not be hardcoded!
my $db_name = "manage";
my $db_user = "manage";
my $db_pass = "eganam";
my $scriptname = "bokser";

my $dbh = Pg::connectdb("dbname=$db_name user=$db_user password=$db_pass");
#my $dbh = &connect($scriptname);

# First of all we want everything that is in the database in the first place.
print "Filling the dbhash" if $loglevel >= 2;
my %dbhash;
my $query = "SELECT * FROM typesnmpoid";
my $res = $dbh->exec($query);
while (my($a,$b,$c) = $res->fetchrow) {
    $dbhash{$a}{$b} = $c;
}
print "...DONE!\n" if $loglevel >= 2;

# Fetches the oids
my %oidhash = &fetchOids();

# Fetches the different unittypes. typehash contains
# the type as key and has two netboxes as value
my %types;
my %typehash = &fetchTypes();

# Lets see what we've got
# Structure: %hash = [ [] .. [] ]
my @boxresult;
my @checkarr;

# For each type check with the boxes stored in the typehash
# to see what oids they match.
for my $type (keys %typehash) {
    @checkarr = ();

    printf "MAIN: Type %s found:\n", $types{$type} if $loglevel >= 2;
    for my $i (0 .. $#{ $typehash{$type} } ) {
	printf "\t-> %s\n", join(", ", @{ $typehash{$type} -> [$i] }) if $loglevel >= 3;
	@boxresult = &checkBox( $type, @{ $typehash{$type} -> [$i] }, %oidhash );
	push @checkarr, [ @boxresult ];
	@boxresult = ();
    }

    if (&checkArrs(@checkarr)) {
	print "\tAll boxes returned similar values.\n" if $loglevel >= 2;
	# Insert the relations in the database
	&insertTypesnmp($type, $checkarr[0]);
    } else {
	print "\tInconsistency in the returnvalues.\n" if $loglevel >= 2;
    }
    print "======================================================================\n";

}

# We have oid's, types and boxes. The goal is to find out
# what oid's the different types answer to, and also to
# check whether two boxes of the same type answers to the
# same oid's

###################### SUBS ######################

##################################################
# fetchOids
# ---------
##################################################
sub fetchOids {
    
    my %oids;

    # What we look for in the description field
    my $keyword = "Cricket";
    my $keyword2 = "mib-II";

    my $query = "SELECT * FROM snmpoid WHERE oidsource = '$keyword' OR oidsource = '$keyword2'";
    my $res = $dbh->exec($query);
    while (my ($snmpoidid,$oidkey,$snmpoid) = $res->fetchrow) {
	$oids{$snmpoidid} = [$oidkey,$snmpoid];
    }

    return %oids;
}

##################################################
# fetchTypes
# ----------
##################################################
sub fetchTypes {
    
    my $numcheckboxes = 2; # The number of boxes to return
    my $counter;
    my %typehash;

    my $query = "SELECT typeid,typename FROM netbox LEFT JOIN type USING (typeid) WHERE (catid='SW' OR catid='GW' OR catid='GSW') AND typeid IS NOT NULL GROUP BY typeid,typename";
    my $res = $dbh->exec($query);

    # For each typeid, select $numcheckboxes boxes from the table for checking.
    while (my ($typeid,$typename) = $res->fetchrow) {
	$types{$typeid} = $typename;
	my $q = "SELECT sysname,ip,ro FROM netbox WHERE typeid=$typeid";
	my $r = $dbh->exec($q);

	my @temparr;
	$counter = 0;
	while ((my ($sysname,$ip,$ro) = $r->fetchrow) && ($counter++ < $numcheckboxes)) {
	    push @temparr, [$sysname,$ip,$ro];
	}

	$typehash{$typeid} = [@temparr];
	
    }

    return %typehash;

}

##################################################
# checkBox
# --------
# format string = oOnNtvei\n"
# o = oid with index
# O = oid without index
# n = name with index
# N = name without index
# t = type
# v = value
# e = enumeration
# i = instance of the mib variable
##################################################
sub checkBox {
    my ($type,$sysname,$ip,$community,%oids) = @_;
    my $snmpobjectok;
    my @returnarr;

    my $errorstr;
    my $errordet;
    
    printf "CHECKBOX: %s\n", join(",", $type,$sysname,$ip,$community) if $loglevel >= 2;
    
    # Creating the snmp object.
    print "\tCreating SNMP-object..."  if $loglevel >= 3;
    my $session = new SNMP::Util(-device => $ip,
				 -community => $community,
				 -timeout => 5,             
				 -retry => 1,             
				 -poll => 'off',            
				 -poll_timeout => 5,        
				 -verbose => 'off',         
				 -errmode => 'return',    
				 -delimiter => ' ', 
				 );

    unless ($session->error) {
	print "OK\n" if $loglevel >= 3;
	$snmpobjectok = 1;
    } else {
	$errorstr = $session->errmsg;
	$errordet = $session->errmsg_detail;
	print "not OK, $errorstr, $errordet\n" if $loglevel >= 3;
	print "Error when creating SNMP-object.\n" if $loglevel >= 2;
	$snmpobjectok = 0;
    }

    if ($snmpobjectok) {
	# %oids format: keytotable -> [ text, oid ]
	for my $oidid (keys %oids) {
	    my $exist = 0;
	    my ($text, $oid) = @{ $oids{$oidid} };
	    printf "\tQuerying %s with %s (%s)\n", $sysname, $text, $oid if $loglevel >= 2;

	    # We first try with get. This works for values like cpu, memory and so on.
	    my @ret = $session->get(-format => 'ne',
				    -oids   => [ "$oid" ],
				    );

	    if ($ret[0]) {
 		printf "\tYES GET -> OID %s (%s) exists, first values returned: %s, %s\n", $text, $oid, $ret[0], $ret[1] if $loglevel >= 3;
		$exist = 1;
	    } else {
		# If get doesn't work we try with walk, which should return values if we are talking about interfaces.
		@ret = $session->walk(-format => 'ne',
				      -oids   => [ "$oid" ],
				      );
		if ($ret[0]) {
		    printf "\tYES WALK -> OID %s (%s) exists, first values returned: %s, %s\n", $text, $oid, $ret[0], $ret[1] if $loglevel >= 3;
		    $exist = 1;
		}
	    }
	    
	    if ($exist) {
		push @returnarr, $oidid;
	    } else {
 		printf "\tNO! -> OID %s (%s) DOES NOT EXIST\n", $text, $oid if $loglevel >= 3;
	    }
	}
	print "CHECKBOX END\n" if $loglevel >= 2;
    }

    return @returnarr;
}

##################################################
# checkArrs
# ---------
# only checks if everything is similar, must be
# improved.
##################################################
sub checkArrs {

    # format: [ []...[] ]
    my @arrs = @_;
    my $returnval = 1;

    print "CHECKARRS:\n";

    my $a1 = shift @arrs;
    my $number = @arrs;
    
    print "\t-> $number <-\n" if $loglevel >= 3;

    if ($number > 0) {
	for my $i (0 .. $#{ @arrs } ) {
	    if (@{ $a1 } eq @{ $arrs[$i] } ) {
		print "\t@{ $a1 } EQ @{ $arrs[$i] }\n" if $loglevel >= 3;
	    } else {
		print "\t@{ $a1 } NEQ @{ $arrs[$i] }\n" if $loglevel >= 3;
		$returnval = 0;
		last;
	    }
	}
    }

    print "CHECKARRS END\n";
    return $returnval;

}

##################################################
# insertTypesnmp
# --------------
# Inserts the relation between type and snmpoid
##################################################
sub insertTypesnmp {

    my $type = shift;
    my $ref = shift;

    my $query;

    print "INSERTTYPESNMP:\n" if $loglevel >= 2;
    
    foreach my $key ( @{ $ref } ) {
	if ($dbhash{$type}{$key}) {

	    print "\tThis record already exists" if $loglevel >= 3;

	    if ($dbhash{$type}{$key} != $frequency) {
		print ", updating frequency." if $loglevel >= 3;

		$query = "UPDATE typesnmpoid SET frequency=$frequency WHERE typeid=$type AND snmpoidid=$key";
 		my $r = $dbh->exec($query);

 		unless ($r->resultStatus eq PGRES_COMMAND_OK) {
 		    printf "ERROR DURING UPDATE: %s", $dbh->errorMessage if $loglevel >= 3;
 		}
	    }

	    print ".\n" if $loglevel >= 3;

	} else {
	    $query = "INSERT INTO typesnmpoid (typeid,snmpoidid,frequency) VALUES ($type,$key,$frequency)";
 	    my $r = $dbh->exec($query);

 	    unless ($r->resultStatus eq PGRES_COMMAND_OK) {
 		printf "ERROR DURING INSERT: %s", $dbh->errorMessage if $loglevel >=2;
 	    }

	    print "\t$query - @{ $oidhash{$key} }\n" if $loglevel >= 2;

	}
    }

    print "INSERTTYPESNMP END\n" if $loglevel >= 2;

}
