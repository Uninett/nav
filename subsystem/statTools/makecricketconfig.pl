#!/usr/bin/env perl
#
# $Id$
# This script makes the config to Cricket based on data in the
# manage-db.
#
# Copyright 2001-2004 Norwegian University of Science and Technology
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

# TODO:
# - use config.db to see target-types too.
# - make views automatically

# Loglevels:
# 1 -> silent
# 2 -> default
# 3 -> debug
use warnings;

BEGIN {

    $cricketdir = 0;
    $ll = 2;

    use vars qw ($opt_h $opt_l $opt_c);

    use Pg;
    use Cwd;
    use Getopt::Std;

    getopts('hl:c:');

    # Checking for Cricket if c-option not set.
    my @defaultcricketdirs = ("/home/navcron/cricket","/usr/local/cricket","/usr/local/nav/cricket");
    if ($opt_c) {
	print "Setting cricketdir to $opt_c.\n";
	$cricketdir = $opt_c;
    } else {
	print "No path to Cricket specified, searching default paths...\n" if $ll >= 2;
	foreach my $dir (@defaultcricketdirs) {
	    print "Searching in $dir.\n" if $ll >= 2;
	    if (-e $dir) {
		print "Found cricket in $dir.\n" if $ll >= 2;
		$cricketdir = $dir;
		last;
	    }
	}
	unless ($cricketdir) {
	    print "Didn't find Cricket, if you know where it is use the -c parameter.\n";
	    exit;
	}
    }

    eval "require '$cricketdir/cricket/cricket-conf.pl'";

}

our $ll;
our $cricketdir;
our ($opt_l,$opt_h,$opt_c);

# Imports the config-db from Cricket
use lib "$Common::global::gInstallRoot/lib";

use ConfigTree::Cache;
use Common::global;

$Common::global::gCT = new ConfigTree::Cache;
$gCT = $Common::global::gCT;
$gCT->Base($Common::global::gConfigRoot);
$gCT->Warn(\&Warn);

if (! $gCT->init()) {
    die("Failed to open compiled config tree from gConfigRoot/config.db: $!\n If this is the first time you run makecricketconfig, try compile cricket ($cricketdir/cricket/compile)\n");
}

umask 007;

use strict;
use NAV;

my $usage = "USAGE: $0 [-h] [-l loglevel] [-c pathtocricket]
This script makes the config-tree for Cricket
\th: help, prints this
\tc: location of Cricket, if not set we search in default directories
\t\t(/usr/local/cricket /home/navcon/cricket /usr/local/nav/cricket) 
\tl: loglevel (1 - silent, 2 - default, 3 - debug)

Made by John Magne Bredal - ITEA NTNU 2003
";

if ($opt_h) {
    print $usage;
    exit;
}

# some vars
my $cricketconfigdir = "$cricketdir/cricket-config";
my $compiledir = "$cricketdir/cricket";
my $configfile = ".nav";
my $changelog = "$cricketdir/cricket-logs/changelog";

my $viewfile = "$compiledir/view-groups";

my %config; # stores navconfig for the configtree
my %dshash; # stores the mapping between ds and ds-type
my %targetoidhash;
my %rtargetoidhash; # temporar hash for servers
my %rrdhash;

my $step = 300;
my $subsystem = "cricket";

if ($opt_l && $opt_l =~ m/\d/) {
    $ll = $opt_l;
    print "Setting loglevel to $ll\n" if $ll >= 2;
}

# DB-vars
my $dbh = &NAV::connection('statTools', 'manage');

# Must have the cricket-rows of the snmpoid-table in memory.
my %oidhash;
my %roidhash;
my $q = "SELECT snmpoidid,oidkey FROM snmpoid WHERE oidsource LIKE 'Cricket' OR oidsource LIKE 'mib-II'";
my $r = $dbh->exec($q);
print "Filling hashes\n";
while (my ($id,$txt) = $r->fetchrow) {
    $oidhash{$id} = $txt;
    $roidhash{$txt} = $id;
    print "\t$id <-> $txt\n" if $ll >= 3;
}
print "Done\n" if $ll >= 3;


# Read the different view-groups into a hash
my %viewarr;
if (-e $viewfile) {
    open (VIEW, $viewfile) or die ("Could not open $viewfile: $!\n");
    while (<VIEW>) {
	next unless /^view/;
	m/view (\w+):(.*)/;
	my $view = $1;
	my @ds = split (" ", $2);
	$viewarr{$view} = [ @ds ];
    }
    close VIEW;
} else {
    print "Could not find $viewfile, it should be in $compiledir...no views will be made.\n";
}

########################################
# Description of hashes
########################################
# config
# --------------------------------------
# Contains the info read from the .nav-config-files
# dirs: contains all the dirs that we will edit defaults-files
#       and make targets for
# $dir->$key: we parse the .nav-files for config for each dir
#             specified in {dirs}. The possible values are specified
#             in the .nav config-file. We just fetch everything here,
#             no check on content

# dshash{ds} = rrd-ds-type
# --------------------------------------
# for all the ds (that is everything in the config-files that come after datasource)
# we know what rrd-ds-type that is defined. Filled by using the parseDefaults sub.
# Example: dshash{ifinctets} = COUNTER

# targetoidhash{targettype} = [datasources]
# --------------------------------------
# For each netbox we store the array of 
# datasources used to collect data.
# Example (may be incorrect): kjemi-gsw->[cpu1min,cpu5min,mem5minUsed,mem5minFree]

# oidhash{id} = txt
# --------------------------------------
# for all the id's in the snmpoid-table we know the textual description
# Example (may be incorrect): oidhash{164} = ifinoctets

# roidhash{txt} = id
# --------------------------------------
# The reverse of oidhash
# Example (may be incorrect): oidhash{ifinoctets} = 164

# rrdhash{path}{filename} with the following (possible) keys:
# --------------------------------------
# This array is used only when filling the rrd-database (rrd_file and rrd_datasource)
# ds: an array consisting of the snmpoidid's that we are collecting for this target
# netboxid: the netboxid of the unit we are collecting data from
# interface: set to 1 if this is an interface
# table: set only for interfaces, the table that we fetch interfaces from
# id: set only for interfaces, the key-field of the table

# Lets start working.

# Rotating changelogs
unless (-e $changelog) {
    `touch $changelog`;
}

for (my $counter = 8; $counter > 0;$counter--) {
    if (-e $changelog.".".$counter) {
	my $tmp = $counter+1;
	`mv $changelog.$counter $changelog.$tmp`;
    }
}
`mv $changelog $changelog.1`;
open (CHANGELOG, ">$changelog") or warn ("Could not open $changelog for writing: $!\n");

chdir ($cricketconfigdir);
my $cwd = cwd;

# First of all, stop the subsystem - MUST BE IMPLEMENTED (not critical)
my $ok = 1;
print "Stopping Cricket..." if $ll >= 2;
if ($ok) {
    print "stopped.\n" if $ll >= 2;
} else {
    print "could not stop it, error-messages will occur!\n" if $ll >= 2;
}

# parse main config so we know where to work.
&parseMainConfig();

# for each dir mentioned in the main config, treat them
foreach my $dir (@{ $config{'dirs'} } ) {
    printf "---------- %s ----------\n", "$dir" if $ll >= 2;
    printf "Treating %s.\n", $dir if $ll >= 3;

    my $continue = &parseConfig($dir);
    next unless $continue;

    # Making serverconfig...it's still under testing.
#    if ($dir eq 'servers') {
#	&makeservers('servers');
#	next;
#    }

    # interfaces are kinda standard so we have a fixed config for them.
    if ($config{$dir}{'interface'}) {
	print "---------- MAKING TARGETS ----------\n" if $ll >= 2;
	&makeinterfaceTargets($dir);
    } else {
	print "---------- MAKING TARGETTYPES ----------\n" if $ll >= 2;
	&createTargetTypes($dir);
	print "---------- MAKING TARGETS ----------\n" if $ll >= 2;
	&makeTargets($dir);
    }
}

# Ok, we are done with editing config, making targettypes,
# making targets and so on. Now lets fill the rrd-database
# with the new info we have gathered. For this we use the
# rrdhash that we have built.


# &fillRRDdatabase();

#compiling
umask 002;
system("$compiledir/compile");


$ok = 1;
print "Starting Cricket..." if $ll >= 2;
if ($ok) {
    print "done.\n" if $ll >= 2;
} else {
    print "did not seem to work, check manually if Cricket is running please.\n" if  $ll >= 2;
}

close CHANGELOG;

printf ("$0 executed in %s seconds.\n", time-$^T) if $ll >= 2;

##################################################
# SUBS
##################################################

##################################################
# parseMainConfig
# --------------------
# Parses the main nav-configfile to see what dirs
# we are supposed to look in. Stores that info
# in the main hash.
# INPUT: nada
# RETURNS: nada, uses global hash.
##################################################
sub parseMainConfig {

    my $me = "parseMainConfig";

    print "\n=> Running $me <=\n" if $ll >= 2;

    unless (-e $configfile) {
	printf "Could not find nav-configfile in %s, exiting.\n", $cricketconfigdir if $ll >= 2;
	exit(0);
    }

    unless (-r $configfile) {
	printf "nav-configfile is not readable in %s, exiting.\n", $cricketconfigdir if $ll >= 2;
	exit(0);
    }

    printf "Found nav-configfile in %s, good!\n", $cwd if $ll >= 2;
    open (NAV, $configfile) or die ("Could not open $cwd/$configfile.\n");
    while (<NAV>) {
	my @dirs;

	next if /^\s*\#/; # Skipping comments

	# We find the dirs which we will descend into
	if (m/\s*dirs\s*=\s*(\S+)/) {
	    my @dirs;
	    my @tmp = split ",", $1;
	    
	    foreach my $dir (@tmp) {
		print "Pushing >$dir<\n" if $ll >= 3;
		push @dirs, $dir if (-e $dir);
	    }
	    
	    $config{'dirs'} = [@dirs];
	}
	
	# more to come?
    }
    close NAV;

    print "\n=> Done running $me<=\n" if $ll >= 2;
    return 1;

}

##################################################
# parseConfig
# --------------------
# Parses the nav-configfile found in the dir
# specified. Puts info in the global hash $config.
#
# INPUT: the dir we will work in
# RETURNS: nada, uses global hash
##################################################
sub parseConfig {
    my $dir = shift;
    my $path = "$dir/$configfile";
    my $me = "parseConfig";

    print "\n=> Running $me with dir=$dir <=\n" if $ll >= 2;

    unless (-e $path) {
	printf "%s had no config-file.\n", $dir if $ll >= 3;
	print "\n=> Done running $me <=\n";
	return 0;
    }
    
    open (HANDLE, $path) or die ("Could not open $path: $!");
    while (<HANDLE>) {
	next if /^\s*\#/;
	if (m/^\s*(\S*)\s*=\s*(.+)$/) {
	    $config{$dir}{$1} = $2;
	    print "Setting $dir -> $1 = $2\n" if $ll >= 3;
	}
    }
    close HANDLE;

    print "\n=> Done running $me <=\n" if $ll >= 2;
    return 1;

}

##################################################
# parseDefaults
# --------------------
# parsing the existing defaults-file to find the
# targettypes that already exists. Also store the
# datasources found in a global hash $dshash, as
# these are of interest later.
#
# INPUT: the dir we work in
# RETURNS: the name of the defaults file (scalar)
##################################################
sub parseDefaults {
    my $dir = shift;
    my $file;
    my $found = 0;
    my $me = "parseDefaults";


    print "\n=> Running $me with dir=$dir <=\n" if $ll >= 2;

    my %returnhash;
    
    my @filenamearr = qw(Defaults defaults Default default);
    
    print "Searching for defaultsfile in $dir.\n" if $ll >= 3;

    foreach my $filename (@filenamearr) {
	if (-e "$dir/$filename") {
	    $file = $filename;
	    $found = 1;
	    last;
	}
    }

    unless ($found) {
	print "Could not find defaults-file in $dir, returning.\n" if $ll >= 3;
	$returnhash{'found'} = 0;
	print "\n=> Done running $me <=\n" if $ll >= 2;
	return %returnhash;
    }

    my $tt;

    my $default;
    my $datasource;
    my $dstype;

    print "Parsing file $dir/$file\n" if $ll >= 3;
    open (HANDLE, "$dir/$file") or die ("Could not open $dir/$file, exiting: $!\n");
    while (<HANDLE>) {
	next if /^\s*\#/;

	# This is the targettype part
	# ---------------------------

	# we first look for a targettype
	if (m/^\s*targettype\s*(\S+)/i) {
	    print "Found targettype >$1<.\n" if $ll >= 3;
	    $tt = $1;
	}

	# we assume that ds will come after a targettype
	# as we control the config-files this should not be a problem
	if (m/^\s*ds\s*=\s*\"(.+)\"/i) {
	    print "Found ds's: $1.\n" if $ll >= 3;
	    my @tmp = split (",", $1);
	    foreach my $ds (@tmp) {
		$ds =~ s/^\s*(.*)?\s*$/$1/;
	    }

	    my @dsarr = map $roidhash{$_}, @tmp;
	    print "Pushing @dsarr on $tt\n" if $ll >= 3;
	    $targetoidhash{$tt} = [@dsarr];
	    $rtargetoidhash{$tt} = [@tmp];
	    @dsarr = ();

	}

    }
    close HANDLE;

    print "\n=> Done running $me <=\n" if $ll >= 2;

    return $file;

}

##################################################
# createTargetTypes
# --------------------
# fetches all the netboxes we are to make config
# for and  makes a targetType for every type based
# on the data we find in the netboxsnmpoid-table.
#
# Help functions: &parseDefaults, &compare, &makeTTs
#
# INPUT: Directory of work (scalar)
##################################################
sub createTargetTypes {
    our $gCT;
    my $dir = shift;
    my $type = $config{$dir}{'type'};

    my $me = "createTargetTypes";

    print "\n=> Running $me with dir=$dir<=\n" if $ll >= 2;

    my %newtts;

    # fetching the existing targettypes
    my $filename = &parseDefaults($dir);

    # We know that type may be several catid's
    my @types = split (",", $config{$dir}{'type'});
    foreach my $type (@types) {
	$type =~ s/^\s*(\w+)?\s*$/$1/;
	$type = "catid='$type'";
    }

    # Todo for new system - try 1
    # - find all netboxes of give type (category)
    # - foreach netbox, find all snmpoids (oidkey)
    # - check if it is

    printf "Creating targetTypes for %s, based on %s .\n", $dir, join (",", @types) if $ll >= 2;

    my $query = "SELECT netboxid,sysname FROM netbox WHERE (" . join ( " OR ", @types ) . ")";
    print "$query\n" if $ll >= 3;
    my $res = $dbh->exec($query);

    # For all the types, make a targetType
    # Use only the oids that are not interface-specific
    while (my($netboxid, $sysname)=$res->fetchrow) {
	print "\nFound netbox $sysname.\n" if $ll >= 2;
	print "---------------------\n" if $ll >= 2;
	
	# Fetch the oids for this netbox
	my $q = "SELECT snmpoidid FROM netboxsnmpoid WHERE netboxid=$netboxid";
	printf "%s\n", $q if $ll >= 3;
	my $fetchoids = $dbh->exec($q);

	# fetches all the oid's that exists in this part of the config-tree
	my $purepath = "/".$dir;
	my $oidinconfig = $gCT->configHash($purepath,'oid');

	# for each oid, check if it should be used in a targettype
	my @newtt;
	while (my $snmpoidid = $fetchoids->fetchrow) {
	    print "Found snmpoidid $snmpoidid " if $ll >= 3;

	    unless ($oidhash{$snmpoidid}) {
		print "- skipping because not in oidhash.\n" if $ll >= 3;
		next;
	    } elsif ($oidhash{$snmpoidid} =~ m/^if/) {
		# here we do a weak test for interface-oids
		print "- skipping because it is an interface oid.\n" if $ll >= 3;
		next;
	    } else {
		print "\n" if $ll >= 3;
	    }

	    # if the oid is not in the config-file we cannot collect data from it	    
	    if ($oidinconfig->{lc($oidhash{$snmpoidid})}) {
		printf "%s should be integrated as a datasource.\n", $oidhash{$snmpoidid} if $ll >= 2;
		push @newtt, $snmpoidid;
	    } else {
		printf "Could not find %s in the config-tree, skipping it.\n", $oidhash{$snmpoidid} if $ll >= 3;
	    }
	}

	next if $#newtt < 0;

	# checking is this targettype already exists in the config-file
	if ($targetoidhash{$sysname}) {
	    print "This targettype already exists, checking if it's equal.\n" if $ll >= 3;
	    if (&compare($targetoidhash{$sysname}, [ @newtt ] )) {
		print "They are equal.\n" if $ll >= 3;
	    } else {
		print "The new targettype does not match with the old, making new.\n" if $ll >= 3;
		$newtts{$sysname} = [@newtt];
		$targetoidhash{$sysname} = [@newtt];
	    }
	} else {
	    print "This targettype does not exist, making new.\n" if $ll >= 3;
	    $newtts{$sysname} = [@newtt];
	    $targetoidhash{$sysname} = [@newtt];
	}

	@newtt = ();

    }

    if (&makeTTs($filename, $dir, %newtts)) {
	print "targettypes made successfully.\n" if $ll >= 2;
    } else {
	print "There was an error when making the targettypes.\n" if $ll >= 2;
    }

    print "\n=> Done running $me <=\n" if $ll >= 2;
    return 1;
    
}

##################################################
# makeTTs
# --------------------
# INPUT: filename, directory of work and a hash
# of the new targettypes to add.
# RETURNS: 0 on error, else nothing.
##################################################
sub makeTTs {
    my ($filename, $dir, %input) = @_;

    my $path = "$dir/$filename";
    my $me = "makeTTs";

    print "\n=> Running $me with filename=$filename, dir=$dir <=\n" if $ll >= 2;

    print "Editing file $path.\n" if $ll >= 3;

    unless (-w $path) {
	print "The file is not writeable, returning.\n" if $ll >= 3;
	print "\n=> Done running $me<=\n" if $ll >= 2;
	return 0;
    }

    # We read the entire defaults file into memory, then rename it for backup.
    open (HANDLE, $path) or die ("Could not open $path for reading: $!\n");
    my @lines = <HANDLE>;
    close HANDLE;

    unless (rename ($path, "$path~")) { 
	print "Could not rename file: $!\n" if $ll >= 2;
    }

    my $delete = 0; # a bool
    my $write = 0; # a bool
    my $tt;


    # Walks through the file, deleting the old tt's that we don't want, and 
    # creating new ones after the special "mark". We currently comment out the
    # new tt because there is no way to automatically set a view, must see 
    # if we at least can start to gather data.
    open (HANDLE, ">$path") or die ("Could not open $path for writing: $!\n ");
    foreach my $line (@lines) {
	if ($write) {
	    # Printing the new targettypes
	    my @keys = keys %input;
	    my $numberofkeys = @keys;
	    if ($numberofkeys > 0) {
		for my $tt (@keys) {
		    print "Adding targettype $tt to file.\n" if $ll >= 3;
		    printf CHANGELOG "Adding targettype %s to %s.\n", $tt, $path;
		    print HANDLE "targetType $tt\n";
		    print HANDLE "\tds\t= \"", join (",", map $oidhash{$_}, @{ $input{$tt} } ), "\"\n";
		    print HANDLE &makeView( @{ $input{$tt} } );
		    print HANDLE "\n\n";
		}
	    } else {
		print "No new targettypes added.\n" if $ll >= 3;
	    }
	    $write = 0;
	    print HANDLE $line;
	} elsif ($line =~ m/^\s*targettype\s*(\w+)/i) {
	    # if this targettype exists in the hash, delete it
	    if ($input{$1}) {
		print "Deleting targettype $1\n" if $ll >= 3;
		printf CHANGELOG "Deleting targettype %s from %s\n", $1, $path;
		$delete = 1;
	    } else {
		print HANDLE $line;
	    }
	} elsif ($delete && $line =~ m/^\s*ds/) {
	    # delete
	    print "Deleting line: $line" if $ll >= 3;
	} elsif ($delete && $line =~ m/^\s*view/) {
	    # delete this line and be happy for now
	    $delete = 0;
	    print "Deleting line: $line" if $ll >= 3;
	} elsif ($line =~ m/\#!\#!\#!/) {
	    $write = 1;
	    print "Found special mark - setting the write-bit.\n" if $ll >= 3;
	    print HANDLE $line;
	} else {
	    print HANDLE $line;
	}

    }
    close HANDLE;

    print "\n=> Done running $me<=\n" if $ll >= 2;
    return 1;

}

##################################################
# makeTargets
# --------------------
# Makes the target-files in the specified directory.
# INPUT: The dir to work in
# RETURNS: nada
##################################################
sub makeTargets {
    my $dir = shift;
    my $file = "targets";
    my $me = "makeTargets";

    print "\n=> Running $me with dir=$dir <=\n" if $ll >= 2;

    print "$config{$dir}{'type'}\n" if $ll >= 3;
    
    # We know that type may be several catid's
    my @types = split (",", $config{$dir}{'type'});
    foreach my $type (@types) {
	$type =~ s/^\s*(\w+)?\s*$/$1/;
	$type = "catid='$type'";
    }

    my $query = "SELECT netboxid,ip,sysname,ro, type.descr as typedescr , room.descr as roomdescr FROM netbox LEFT JOIN type USING (typeid) LEFT JOIN room USING (roomid) WHERE (" . join ( " OR ", @types ) . ") AND up='y' ORDER BY sysname";
    print "$query\n" if $ll >= 3;

    my $res = $dbh->exec($query);
    my $filetext;
    
    my %changes = ();
    my @changes = ();
    while (my ($netboxid,$ip,$sysname,$ro,$typedescr,$roomdescr) = $res->fetchrow) {

	# If we failed to make a targettype for this one, skip it.
	unless ($targetoidhash{$sysname}) {
	    print "Could not find a targettype for $sysname, skipping.\n" if $ll >= 2;
	    next;
	}

	# format:
	# target $sysname
	#     snmp-host = $ip
	#     snmp-community = $ro
	#     target-type = $sysname
	#     short-desc = 
	# We let Cricket do the sorting atm

	# Making description - perhaps we should be more flexible here?
	my $descr;
	if ($roomdescr) {
	    $descr = join (", ", $typedescr,$roomdescr);
	} else {
	    $descr = $typedescr;
	}
	$descr = "\"$descr\"";

	# Storing info that we need later when we are going to 
	# fill the rrd-db.
	$rrdhash{"$cricketconfigdir/$dir"}{$sysname}{'netboxid'} = $netboxid;
	$rrdhash{"$cricketconfigdir/$dir"}{$sysname}{'ds'} = $targetoidhash{$sysname};

	push @changes, $sysname;

	$filetext .= "target \"$sysname\"\n";
	$filetext .= "\tsnmp-host\t=\t$ip\n";
	$filetext .= "\tsnmp-community\t=\t$ro\n";
	$filetext .= "\ttarget-type\t=\t$sysname\n";
	$filetext .= "\tshort-desc\t=\t$descr\n\n";
	print "Adding target \"$sysname\"\n" if $ll >= 2;

    }

    open (TARGETS, ">$dir/$file") or die ("Could not open $dir/$file for writing: $!\n");    
    print TARGETS $filetext;
    close TARGETS;

    # Printing changes
    $changes{"$cricketconfigdir/$dir"} = [@changes];
    &checkChanges(%changes);

    print "\n=> Done running $me <=\n" if $ll >= 2;
    return 1;

}

##################################################
# makeinterfaceTargets
# --------------------
# Makes targets for interfaces. These are standard
# therefore we treat them for themselves. There
# is no need to edit the defaults-file for these
# either.
# INPUT: the dir to work in
# RETURNS: nada, just makes a file
##################################################
sub makeinterfaceTargets {
    my $dir = shift;
    my $file = "targets";
    my $me = "makeinterfaceTargets";
    my %changes = ();

    print "\n=> Running $me with dir=$dir <=\n" if $ll >= 2;

    my @types = split ",",$config{$dir}{'type'};
    my @nameparameters = split (",", $config{$dir}{'name'});
    my $descrsentence = $config{$dir}{'descr'};
    my $joinparam = $config{$dir}{'join'} || "-";
    my $table = $config{$dir}{'table'};
    my $giga = $config{$dir}{'giga'};

    # Stripping whitespace
    foreach my $a (@nameparameters) {
	$a =~ s/^\s*(\w+)?\s*$/$1/;
    }

    foreach my $type (@types) {
	$type =~ s/^\s*(\w+)?\s*$/$1/;
	$type = "catid='$type'";
    }

    # first we kill all the prior config here. 
    # There should not be anything besides a defaults-file and the .nav-file here.
    printf "Deleting all the directories in %s\n", $cricketconfigdir."/".$dir if $ll >= 3;
    `rm -rf $cricketconfigdir/$dir/*/`;

    my $query = "SELECT netboxid,ip,sysname,ro,vendorid FROM netbox LEFT JOIN type USING (typeid) WHERE (". join ( " OR " , @types ) . ") AND up='y' ORDER BY sysname";
    my $res = $dbh->exec($query);

    # For each unit, check if it has any interfaces to gather data from, make
    # a subdir for it and place the targets there.
    while (my($netboxid,$ip,$sysname,$ro,$vendor) = $res->fetchrow) {
	my %ifindexhash = (); # to make sure we don't create a target for the same if twice
	my @changes = ();

	my $filetext = "";
	my $path = "$dir/$sysname";
	my $targetfile = "$path/$file";

	my $q;
	if ($giga) {
	    $q = "SELECT ".$table."id,ifindex,interface,". join (",",@nameparameters) . " FROM $table LEFT JOIN module USING (moduleid) WHERE netboxid=$netboxid AND speed = 1000";
	} else {
	    $q = "SELECT ".$table."id,ifindex,interface,". join (",",@nameparameters) . " FROM $table LEFT JOIN module USING (moduleid) WHERE netboxid=$netboxid AND speed != 1000";
	}
	
	foreach my $parameter (@nameparameters) {
	    $q .= " AND $parameter IS NOT NULL";
	}

	$q .= " ORDER BY ".join (",",@nameparameters);

	my $r = $dbh->exec($q);
	print "$q\n" if $ll >= 3;

	next if $r->ntuples == 0;

	# make a subdirectory for each sysname
	umask 002;
	unless (-e $path) {
	    print "Making dir $path\n" if $ll >= 3;
	    mkdir ($path) or warn ("Could not make directory $path: $!");
	}
	umask 007;

	# create default target
	$filetext .= "target --default--\n";
	$filetext .= "\tsnmp-host\t=\t$ip\n";
	$filetext .= "\tsnmp-community\t=\t$ro\n\n";

	my $numberofports = $r->ntuples;
	my $numtargets = $numberofports+1;
	
	# While there are more interfaces left, fetch them, make a target out of it.
	while (my @params = $r->fetchrow) {
	    my $id = $params[0];
	    my $ifindex = $params[1];
	    my $interface = $params[2];
	    if ($vendor eq 'hp') {
		$ifindex =~ s/^\d0?(.*)/$1/;
	    }

	    # Some interfaces exists more than once in the database, lets skip them
	    next if $ifindexhash{$ifindex};
	    $ifindexhash{$ifindex}++;

	    my $name = "";
	    my $descr = "";
	    my $order = $numberofports--;

	    # In the config-file we specify how to make the target-name.
	    my @tmp;
	    foreach my $param (@nameparameters) {
		my $a = $r->fnumber($param);
		$params[$a] =~ s,/,_,g;
		push @tmp, $params[$a];
	    }
	    $name = join $joinparam, @tmp;

	    # In the config-file we also specify how to make the description.
	    # This is basically a select-sentence, therefore we must filter on
	    # select to avoid mischief.
	    @tmp = ();
	    my $descrq = $descrsentence;
	    if ($descrq =~ /^select/i) {
		$descrq =~ s/\;//;
		$descrq =~ s/\$id/$id/;
		
		print "\tQuerying for description: $descrq\n" if $ll >= 3;
		my $descrres = $dbh->exec($descrq);
		@tmp = $descrres->fetchrow;
	    }

	    my $lengthoftmp = @tmp;
	    if ($lengthoftmp > 0) {
		$descr = join (", ", @tmp);
		$descr = "\"$descr\"";
	    }

	    # Set name = ifindex if no name set and so on
	    $name = $ifindex unless $name;
	    $descr = "\"No description available\"" unless $descr;
	    # create interface-targets
	    # format:
	    # target $name
	    #     interface-index = $ifindex
	    #     short-desc = $descr

	    $rrdhash{"$cricketconfigdir/$dir/$sysname"}{$name}{'netboxid'} = $netboxid;
	    $rrdhash{"$cricketconfigdir/$dir/$sysname"}{$name}{'interface'} = 1;
	    $rrdhash{"$cricketconfigdir/$dir/$sysname"}{$name}{'id'} = $id;
	    $rrdhash{"$cricketconfigdir/$dir/$sysname"}{$name}{'table'} = $table;

	    $filetext .= "target \"$name\"\n";
	    if ($interface =~ m/(.*)\.\d+/) {
		$filetext .= "\ttarget-type\t=\tsub-interface\n";
	    }
	    $filetext .= "\torder\t=\t$order\n";
	    $filetext .= "\tinterface-index\t=\t$ifindex\n";
	    $filetext .= "\tshort-desc\t=\t$descr\n\n";
	    print "Adding target $name to $targetfile\n" if $ll >= 2;

	    push @changes, $name;
	}

	my @targets = @changes;
	@targets = map lc($_), @targets;
	# Adding the all-target
	$filetext .= "target all\n";
	$filetext .= "\torder\t=\t$numtargets\n";
	$filetext .= "\ttargets\t=\t\"".join(";",@targets)."\"\n\n";

	$changes{"$cricketconfigdir/$dir/$sysname"} = [@changes];

	# Write to file.
	open (HANDLE, ">$targetfile") or die ("Could not open $targetfile: $!");
	print HANDLE $filetext;
	close HANDLE;
    }

    &checkChanges(%changes);

    print "\n=> Done running $me <=\n" if $ll >= 2;
    return 1;

}



##################################################
# compare
# --------------------
# Compares two arrays to see if they are equal.
# Written only for my needs, I AM aware that such
# things are made (better), but I don't want to 
# install more mods than necessary.
#
# INPUT: ref to two arrays
# RETURNS: true or false
##################################################
sub compare {
    my ($ref1, $ref2) = @_;

    my @a = sort @{ $ref1 };
    my @b = sort @{ $ref2 };

    my $asize = @a;
    my $bsize = @b;

    if ($asize == $bsize) {
	print "Same size.\n" if $ll >= 3;
    } else {
	print "Arrays are not equal (%s != %s).\n", $asize, $bsize if $ll >= 3;
	return 0;
    }

    for my $i (0 .. $#a) {
	printf "Comparing %s - %s => ", $a[$i], $b[$i] if $ll >= 3;
	if ($a[$i] eq $b[$i]) {
	    print "equal.\n" if $ll >= 3;
	} else {
	    print "not equal.\n" if $ll >= 3;
	    return 0;
	}
    }

    return 1;

}

##################################################
# checkChanges
# --------------------
# Get as input a hash of path and targets from
# makeTargets. Compares that to what we have in
# the database and prints out the changes.
##################################################
sub checkChanges {

    my $me = "checkChanges";

    print "=> Running $me <=\n" if $ll >= 2;
    print "--- CHANGELOG ---\n" if $ll >= 2;
    my %changehash = @_;

    foreach my $dir (keys (%changehash)) {

	print "\t$dir\n" if $ll >= 2;

	my @targets = @{ $changehash{$dir} };
	$dir =~ s/cricket-config/cricket-data/;
	my $q = "SELECT filename FROM rrd_file WHERE path = '$dir' ORDER BY filename";
	my $r = $dbh->exec($q);
	print "\t$q\n" if $ll >= 3;

	my %dbtargets = ();
	while (my ($filename) = $r -> fetchrow) {
	    $dbtargets{$filename}++;
	}

	my @changearr = ();
	foreach my $target (@targets) {
	    $target = lc ($target.".rrd");
	    if ($dbtargets{$target}) {
		print "\t$target exists in the db, not adding to changelog.\n" if $ll >= 3;
	    } else {
		print "\tAdding $target to changelog.\n" if $ll >= 3;
		push @changearr, $target;
	    }
	    delete $dbtargets{$target};
	}
	
	# Printing those who were added.
	my $numadded = @changearr;
	if ($numadded > 0) {
	    printf CHANGELOG "Added %s new targets to %s/targets:\n", $numadded, $dir;
	    foreach my $target (@changearr) {
		print "\t$target\n" if $ll >= 2;
		print CHANGELOG "\t$target\n";
	    }
	}

	# Printing those who were in the database but not in the new config.
	my @inactive = keys %dbtargets;
	my $numinactive = @inactive;
	if ($numinactive > 0) {
	    printf CHANGELOG  "%s inactive in %s:\n", $numinactive, $dir;
	    foreach my $key (@inactive) {
		print CHANGELOG "\t$key\n";
	    }
	}


    }

    print "=> Done running $me <=\n" if  $ll>= 2;
    return 1;

}

##################################################
# fillRRDdatabase
# --------------------
# We have a global hash that functions as a mini-db
# of what files we have made. This sub uses that to
# fill the rrd-db
##################################################
sub fillRRDdatabase {
    our $gCT;

    # This is the hardcoded oids that we collect for interfaces.
    # These are VERY standard and should by no means be altered.
    # I have yet to experience that these do not exist on any units.
    # You may argue that if we want to collect more than these, it
    # is hard to change. That is true. We may read this info from a
    # text-file in the future.
    my @interfacearr = qw(ifInOctets ifOutOctets ifInErrors ifOutErrors ifInUcastPackets ifOutUcastPackets);
    my $interfaceds = "COUNTER";

    print "---------- FILLING THE RRD-DATABASE ----------\n" if $ll >= 2;

    my $me = "fillRRDdatabase";
    print "=> Running $me <=\n" if $ll >= 2;

    # We now have some global hashes - summary follows: 

    # Remember the vars $step and $subsystem that are defined
    # at the top. Also remember to look at the description of the hashes in the
    # beginning of the script.

    # First of all we want to find the path of all the files 
    # we have made configuration for:

    my @allpaths = keys(%rrdhash);

    # Then we go through each and every one of these and fill the database:

    foreach my $path (@allpaths) {

	my $newpath = $path;
	$newpath =~ s/cricket-config/cricket-data/;

	print "--- Creating insert for $path ---\n" if $ll >= 3;

	# For all rrd-files we have in this path, add them to the db.

	my @allfiles = keys ( %{ $rrdhash{$path} });
	foreach my $filename (@allfiles) {

	    my $newfilename = lc($filename.".rrd");
	    print "\tFound $filename\n" if $ll >= 3;
	
	    my $netboxid = $rrdhash{$path}{$filename}{'netboxid'};

	    # Check if it exists from before:
	    my $checkq = "SELECT * FROM rrd_file WHERE path='".$newpath."' AND filename='".$newfilename."'";
	    print "$checkq\n" if $ll >= 3;
	    my $checkr = $dbh->exec($checkq);
	    if ($checkr->ntuples > 0) {
		printf "%s/%s does already exist.\n", $path, $filename if $ll >= 3;
		next;
	    }

	    my $rrdfileq;
	    if ($rrdhash{$path}{$filename}{'interface'}) {
		my $key = $rrdhash{$path}{$filename}{'table'};
		my $value = $rrdhash{$path}{$filename}{'id'};
		$rrdfileq = "INSERT INTO rrd_file (path,filename,step,netboxid,subsystem,key,value) VALUES ('$newpath','$newfilename',$step,$netboxid,'$subsystem','$key',$value)";
	    } else {		
		$rrdfileq = "INSERT INTO rrd_file (path,filename,step,netboxid,subsystem) VALUES ('$newpath','$newfilename',$step,$netboxid,'$subsystem')";
	    }

	    my $r = $dbh->exec($rrdfileq);
	    
	    unless ($r->resultStatus eq PGRES_COMMAND_OK) {
		printf "ERROR DURING INSERT: %s", $dbh->errorMessage if $ll >= 2;
	    }
	    
	    print "\t$rrdfileq\n" if $ll >= 3;

	    # Finding the id of what we just inserted...
	    my $findid = "SELECT rrd_fileid FROM rrd_file WHERE path='$newpath' AND filename='$newfilename'";
	    my $findidres = $dbh->exec($findid);

	    next if $findidres->ntuples == 0;

	    my ($rrd_fileid) = $findidres->fetchrow;


	    # TEMP
	    $path =~ m,$cricketconfigdir(/.*)$,;
	    my $purepath = $1;

	    # IF it's an interface, we have some static things to do
	    if ($rrdhash{$path}{$filename}{'interface'}) {
		print "\t\tINTERFACE:\n" if $ll >= 3;
		for my $i (0 .. $#interfacearr) {
		    # We know that if we are talking about interfaces
		    # the ds-type is automatically COUNTER.

		    # finding the units variable
		    my $units = 0;
		    my $ttRef = $gCT->configHash($purepath, 'graph', lc($interfacearr[$i]));
		    if ($ttRef->{'units'}) {
			$units = $ttRef->{'units'};
		    }

		    # Finding the datasource-type used
		    my $dsRef = $gCT->configHash($purepath, 'datasource', lc($interfacearr[$i]));
		    my $dstype = $dsRef->{'rrd-ds-type'};

		    # if there is some critical error, do this, but this should really never happen
		    $dstype = 'DERIVE' unless $dstype;

		    print "$dstype\n";

		    my $dsq;
		    if ($units) {
			$dsq = "INSERT INTO rrd_datasource (rrd_fileid,name,descr,dstype,units) VALUES ($rrd_fileid,'ds".$i."','$interfacearr[$i]','$dstype','$units')";
		    } else {
			$dsq = "INSERT INTO rrd_datasource (rrd_fileid,name,descr,dstype) VALUES ($rrd_fileid,'ds".$i."','$interfacearr[$i]','$dstype')";
		    }
		    
		    my $r = $dbh->exec($dsq);
		    print "\t\t$dsq\n" if $ll >= 3;

		    unless ($r->resultStatus eq PGRES_COMMAND_OK) {
			printf "ERROR DURING INSERT: %s", $dbh->errorMessage if $ll >= 2;
		    }

		}

	    } else {

		# Gotta love perl and references...
		for my $i (0 .. $#{ $rrdhash{$path}{$filename}{'ds'} } ) {
		    
		    my $datasource = $oidhash{ @{ $rrdhash{$path}{$filename}{'ds'} }[$i] };
		    if ($path =~ /server/) {
			$datasource = @{ $rrdhash{$path}{$filename}{'ds'} }[$i];
			printf "\tPath matches server, using alternate value (%s)\n", $datasource  if $ll >= 3;
		    }

		    # Finding the units-value to give a hint for the graph
		    my $units = 0;
		    my $ttRef = $gCT->configHash($purepath, 'graph', lc($datasource));
		    if ($ttRef->{'units'}) {
			$units = $ttRef->{'units'};
		    }

		    # Finding the datasource-type used
		    my $dsRef = $gCT->configHash($purepath, 'datasource', lc($datasource));
		    my $dstype = $dsRef->{'rrd-ds-type'};

		    my $dsq;
		    if ($units) {
			$dsq = "INSERT INTO rrd_datasource (rrd_fileid,name,descr,dstype,units) VALUES ($rrd_fileid,'ds".$i."','$datasource','$dstype','$units')";
		    } else {
			$dsq = "INSERT INTO rrd_datasource (rrd_fileid,name,descr,dstype) VALUES ($rrd_fileid,'ds".$i."','$datasource','$dstype')";
		    }

		    my $r = $dbh->exec($dsq);
		    print "\t\t$dsq\n" if $ll >= 3;
		    

		    unless ($r->resultStatus eq PGRES_COMMAND_OK) {
			printf "ERROR DURING INSERT: %s", $dbh->errorMessage if $ll >= 2;
		    }
		}
	    }
	}
    }

    print "=> Done running $me <=\n" if $ll >= 2;
    return 1;

}

# Still under developement, lacks information in the typesnmpoid to use the
# standard setup.
sub makeservers {

    my $me = "makeservers";
    print "=> RUNNING $me <=\n";

    my $dir = shift;
    &parseDefaults($dir);

    my $serverdir = "$cricketconfigdir/servers";
    unless (-e $serverdir) {
	mkdir($serverdir, 0775);
    }

    my $query = "SELECT netboxid,sysname,ip,typeid,roomid,ro FROM netbox WHERE catid='SRV' ORDER BY sysname";
    print "$q\n" if $ll >= 3;

    my $getservers = &select($dbh,$query);

    while (my ($id, $sysname,$ip,$type,$roomid,$community) = $getservers->fetchrow) {
	next unless $sysname;
	next unless $ip;
	next unless $community;

	print "Making targets for $id, $sysname\n" if $ll >= 3;

	my $os = 0;
	my $win32 = 'win';
	my $linux = 'linux';
	my $unix = 'unix';

	# Check if os_guess is set, if not try to find os from category. If nothing
	# is found, set os to UNIX
	my $q = "SELECT val FROM netboxinfo WHERE netboxid=$id AND var='os_guess'";
	print "\t$q\n" if $ll >= 3;
	my $r = $dbh->exec($q);
	unless ($r->ntuples > 0) {
	    
	    print "\tNo os_guess found for $id, $sysname\n" if $ll >= 2;

	    $q = "SELECT category FROM netboxcategory WHERE netboxid=$id";
	    print "\t$q\n" if $ll >= 3;
	    $r = $dbh->exec($q);

	    $os = $unix;
	    if ($r->ntuples > 0) {
		while (my ($category) = $r->fetchrow) {
		    if ($category eq 'WIN') {
			$os = $win32;
		    } elsif ($category eq 'LINUX') {
			$os = $linux;
		    }
		}
	    } else {
		printf "\tNo category set for %s, %s\n", $id, $sysname if $ll >= 2;
	    }

	}  else {
	    my ($val) = $r->fetchrow;
	    $os = $val;
	}

	$os = lc $os;
	print "\tOS set to $os\n" if $ll >= 2;


	my $fullpath = "$serverdir/$sysname";
	$rrdhash{$fullpath}{'load'}{'netboxid'} = $id;
	$rrdhash{$fullpath}{'users'}{'netboxid'} = $id;
	$rrdhash{$fullpath}{'memory'}{'netboxid'} = $id;
	$rrdhash{$fullpath}{'cpu'}{'netboxid'} = $id;
	$rrdhash{$fullpath}{'error'}{'netboxid'} = $id;
	$rrdhash{$fullpath}{'processes'}{'netboxid'} = $id;
	
	my $snmpagent = 0;
	if($snmpagent && $snmpagent =~ /^1\.3\.6\.1\.4\.1\.311\./) {
	    $win32 = 1;
	}

	if ($snmpagent && $snmpagent =~ /^1\.3\.6\.1\.4\.1\.8072\.3\.2\.10\./) {
	    $linux = 1;
	}

	my $server = $sysname;
	mkdir ($fullpath,0775);

	my $fil = "$fullpath/$server";
	open (FIL, ">$fil") or die "Could not open $fil for writing: $!\n";
	print FIL "target --default--\n";
	print FIL "\tserver\t\t=\t$sysname\n";
	print FIL "\tsnmp-community\t=\t$community\n";

	# Finding room description
	$query = "SELECT descr FROM room WHERE roomid='$roomid'";
	my $getdesc = &select($dbh,$query);
	if (!(my $desc = $getdesc->fetchrow)) {
	    print "\tNo description for room with id=$roomid\n";
	    print FIL "\tshort-desc\t=\t\"\"\n";
	} else {
	    print FIL "\tshort-desc\t=\t\"$desc\"\n";
	}
	print FIL "\n";


	# USERS
	my $ds;
	if($os eq $win32) {
	    $ds = "userswin";
	} else {
	    $ds = "usersnix";
	}
	$rrdhash{$fullpath}{'users'}{'ds'} = $rtargetoidhash{$ds};
	print FIL "target \"users\"\n";
	print FIL "\ttarget-type\t=\t$ds\n\n";


	# PROCESSES
	print FIL "target \"processes\"\n";
	print FIL "\ttarget-type\t=\tprocesses\n\n";
	$rrdhash{$fullpath}{'processes'}{'ds'} = $rtargetoidhash{'processes'};


	# LOAD
	if($os ne $win32) {
	    print FIL "target \"load\"\n";
	    print FIL "\ttarget-type\t=\tloadnix\n\n";
	    $rrdhash{$fullpath}{'load'}{'ds'} = $rtargetoidhash{'loadnix'};
	}


	# MEMORY
	if($os eq $win32) {
	    $ds = "memwin";
	} elsif($os eq $linux) {
	    $ds = "memlin";
	} else {
	    $ds = "memnix";
	}
	print FIL "target \"memory\"\n";
	print FIL "\ttarget-type\t=\t$ds\n\n";
	$rrdhash{$fullpath}{'memory'}{'ds'} = $rtargetoidhash{$ds};


	# CPU
	if($os eq $win32) {
	    $ds = "cpuwin";
	} else {
	    $ds = "cpunix";
	}
	print FIL "target \"cpu\"\n";
	print FIL "\ttarget-type\t=\t$ds\n\n";
	$rrdhash{$fullpath}{'cpu'}{'ds'} = $rtargetoidhash{$ds};


	# ERROR
	if($os eq $win32) {
	    print FIL "target \"Error\"\n";
	    print FIL "\ttarget-type\t=\terror\n\n";
	    $rrdhash{$fullpath}{'error'}{'ds'} = $rtargetoidhash{'error'};
	}

	close FIL;


	# INTERFACES
	# We make separate directory for interfaces
	$query = "SELECT key FROM netboxinfo WHERE var='interf_type' AND netboxid=$id";
	my $getinterfaces = &select($dbh,$query);

	if ($getinterfaces->ntuples > 0) {

	    mkdir ("$fullpath/interface",0775);
	    $fil = "$fullpath/interface/interfaces";

	    open (FIL, ">$fil") or die "Could not open $fil for writing: $!\n";

	    print FIL "target --default--\n";
	    print FIL "\tserver\t\t=\t$sysname\n";
	    print FIL "\ttarget-type\t=\tinterface\n";
	    print FIL "\tinst\t\t=\tmap(interface-name)\n";
	    print FIL "\n";
	    
	    while (my $interface = $getinterfaces->fetchrow) {
		my $name = $interface;
		$name =~ s/\s/_/g; # We need filesystem-rrd-nicer names without spaces
		$name =~ s,/,_,g;
		my $interface2 = $interface;
		$interface2 =~ s/\\/\\\\/g;
		print FIL "target \"$name\"\n";
		print FIL "\tinterface-name\t=\t\"$interface2\"\n";
		print FIL "\tshort-desc\t=\t\"$interface\"\n";
		print FIL "\n";
		$rrdhash{"$fullpath/interface"}{$name}{'netboxid'}= $id;
		$rrdhash{"$fullpath/interface"}{$name}{'ds'} = $rtargetoidhash{"interface"};
	    }
	    close FIL;
	}


	# DISKS
	# Then all the disks
	$query = "SELECT key,val FROM netboxinfo WHERE var='disk_blocksizeInt' AND netboxid=$id";
	my $getpaths = &select($dbh,$query);

	if ($getpaths->ntuples > 0) {

	    mkdir ("$fullpath/disk",0775);
	    $fil = "$fullpath/disk/disks";

	    open (FIL, ">$fil") or die "Could not open $fil for writing: $!\n";

	    print FIL "target --default--\n";
	    print FIL "\tserver\t\t=\t$sysname\n";
	    print FIL "\ttarget-type\t=\tdisk\n";
	    print FIL "\tinst\t\t=\tmap(mount-point)\n";

	    print FIL "\n";

	    while (my ($key,$val) = $getpaths->fetchrow) {
		my $name = $key;
		if($name eq "/") {
		    $name = "root";    # Special case for /
		} else {
		    $name =~ s,/,_,g;  # /usr/local -> _usr_local
		    $name =~ s/^_//;   # _usr -> usr
		    $name =~ s/:.*//;  # C:\ Label nblablabalb -> C
		}
		$key =~ s/\\/\\\\/g; # Double escape backslashes in configfile  C:\ --> C:\\

		print FIL "target \"$name\"\n";
		# This is for diskIO useage in the future
		#if ($solaris) {
		#       print FIL "\ttarget-type = disksolaris\n"; }
		print FIL "\tmount-point\t=\t\"$key\"\n";
		print FIL "\tshort-desc\t=\t\"$key\"\n";
		print FIL "\tblocksize\t=\t$val\n";
		print FIL "\n";

		$rrdhash{"$fullpath/disk"}{$name}{'netboxid'}= $id;
		$rrdhash{"$fullpath/disk"}{$name}{'ds'} = $rtargetoidhash{"disk"};
	    }
	    close FIL;
	}
    }   
}

# Sorting the d
sub makeView {

    my @oids = @_;

    # Ok, we have a list of oids to put into groups based on the
    # %viewarr. We will return a hash where the groupnames are
    # keys and the members of the group is a reference to an array

    my @strings;

    foreach my $group (keys %viewarr) {
	my @temp = ();
	foreach my $groupmember (@ { $viewarr{ $group } }) {
	    foreach my $oid (@oids) {
		if ($oidhash{$oid} eq $groupmember) {
		    push @temp, $groupmember;
		    printf "Pushing %s on %s\n", $groupmember, $group;
		}
	    }
	}
	if (@temp) {
	    push @strings, "$group:". join (" ", @temp);
	}
    }

    my $returnstring = "\tview\t= \"" . join(", ", @strings) . "\"";
       
    print "$returnstring\n";
    return $returnstring;

}
