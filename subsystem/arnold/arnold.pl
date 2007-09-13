#!/usr/bin/env perl
#
# $Id$
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
use SNMP_util;
$SNMP_Session::suppress_warnings = 2;
use vars qw($opt_x $opt_h $opt_r $opt_t $opt_l $opt_f $opt_i $opt_u $opt_a $opt_c $opt_k $opt_s $opt_m $opt_e $opt_d $opt_z);
use Getopt::Std;
use Digest::MD5;
use NAV;
use NAV::Path;
use NAV::Arnold;

# First of all, parse configfile...it SHOULD be there
# readconfig is in arnold.pm
my %cfg = &readconfig();

# What letters do we have left...
# bgjnopqvwy

my $usage = "$0 [-x action] [-i identityid] [-f filename] [-a ipadresses] [-dhlks] [-m mailfile] [-r reason] [-u user] [-c comment] [-e days]
\t-x enable or disable (required)
\t-i sets the identityid (required if enable is set)
\t-f specify a file with ip-adresses to block (required if disable is set and not -a)
\t-a ip adresses to disable (separate with comma for more than one) required unless -f
\t-l list all reasons for blocking
\t-r specify reason, use -l option to see a list (required if disable set)
\t-u specify user that runs script (otherwise you)
\t-c write a comment
\t-k if set locks an ip so that only internal users may enable it
\t-s if set hides the tuple from non-internal users
\t-t specify time for autoenable (an int representing number of days from disable)
\t-e incremental increase since last time in days blocked, if not set prior, use option as days to set initially
\t-h this helpstring
\t-m send mail, uses \$home/etc/\$mailfile as config. Use \$reason for reason, and \$list for list of blocked ports.
\t-d determined, does not open port even if computer is disabled behind another port
\t-z enable only the one specified, added as we originally open all ports where a matching mac is found
";


# Paths
my $home = $NAV::Path::bindir;
my $etc = $NAV::Path::sysconfdir."/arnold";
my $mailconfigpath = "$etc/mailtemplates";
my $datapath = $NAV::Path::localstatedir."/arnold";

my $logdir = $NAV::Path::localstatedir."/log/arnold";
my $nonblockfile = "$etc/nonblock.conf";
my @nonblockedip;


# First, get options.
getopts('x:hf:lksm:r:i:u:a:c:t:e:dz');


# Open logfile
chomp (my $datetime = `date +%y%m%d-%H%M%S`);
my $logfile = "arnold.log";
umask (0117);
open (LOG, ">>$logdir/$logfile") or die ("Could not open $logdir/$logfile: $!\n");
print LOG "\n\n========== NEW LOGENTRY $datetime ==========\n\n";

# Secondly, connect to the database (only block here in case listing of reasons)
my $dbh_block = &NAV::connection('arnold','arnold');
my $errorMessage = $dbh_block->errorMessage;
if ($errorMessage eq PGRES_CONNECTION_BAD) {
    &reporterror("Could not connect to arnold-database.");
    exit(1);
} else {
    print LOG "Connected successfully to block.\n";
}


# some global vars

# snmpset(community@host:port:timeout:retries:backoff:version, OID, type, value,
# The timeout, retries, and backoff parameters default to whatever
# SNMP_Session.pm uses.  For SNMP_Session.pm version 0.83 they are 2 seconds,
# 5 retries, and a 1.0 backoff factor.  The backoff factor is used as a
# multiplier to increase the timeout after every retry.  With a backoff factor
# of 1.0 the timeout stays the same for every retry.
my $timeout = 2;
my $retries = 3;
my $backoff = 2;


# Treat all options and set variables
if ($opt_h) {
    print $usage;
    exit;
}

if ($opt_l) {
    my %temp = &getreasons(1);
    exit;
}

my $mailconfigfile;
my $sendmail = 0;

if ($opt_m) {
    my $temppath = "$mailconfigpath/$opt_m";
    if (-e $temppath) {
	$mailconfigfile = $temppath;
	$sendmail = 1;
	printf LOG "Using mailfile %s.\n", $temppath;
    } else {
	printf LOG "WARNING: Could not find %s, no mail will be sent.\n", $temppath;
    }
}

my $incremental = 0;
if ($opt_e) {
    $incremental = $opt_e;
    print LOG "Using incremental increase in blockdays (default $incremental).\n";
}

my $filename;
my @iplist;
my $id;
my $action = $opt_x;
my $reason;
my $comment = "";

unless ($opt_x) {
    print "You must specify an action with the -x parameter.\n";
    print $usage;
    exit;
}

$comment = $opt_c if $opt_c;

# We are a bit dependant on the -x option, must check a lot here...
if ($action eq 'disable') {

    if ($opt_f) {
	print LOG "Setting filename = $datapath/$opt_f.\n";
	$filename = "$datapath/$opt_f";

	my $digestfile = "$filename.md5";
	my $sum = "0";
	
	if (-e $digestfile) {
	    # Checking if file has changed from last time, mainly used for cron-jobs.
	    open (DIG, $digestfile) or die ("Could not open $digestfile: $!\n");
	    $sum = <DIG>;
	    close DIG;
	}

        open (FILE, $filename) or die ("Could not open $filename: $!\n");
        binmode(FILE);
        my $sum2 = Digest::MD5->new->addfile(*FILE)->hexdigest;
        close FILE;

        if ($sum eq $sum2) {
            print LOG "File $filename has not changed since last run, exiting.\n";
            exit(0);
        } else {
            open (DIG, ">$digestfile") or die ("Could not open $digestfile: $!\n");
            print DIG $sum2;
            close DIG;
        }

    } elsif ($opt_a) {
	for (split(/,/,$opt_a)) {
	    if (/^\d+\.\d+\.\d+\.\d+$/) {
		print LOG "Pushing $_ on iplist.\n";
		push @iplist, [ $_ ];
	    } else {
		print LOG "$_ is not a valid ip-adress.\n";
	    }
	}
    } else {
	print LOG "You must specify a file or a list with ip-adresses to block.\n";
	exit;
    }

    if ($opt_r) {
	print LOG "Setting reason to $opt_r.\n";
	$reason = $opt_r;
    } else {
	print "You must specify a reason, use the -l parameter to list them.\n";
	exit;
    }
    
} elsif ($action eq 'enable') {

    if ($opt_i) {
	print LOG "Setting identityid to $opt_i.\n";
	$id = $opt_i;
    } else {
	print "You must specify an identityid to unblock.\n";
	exit;
    }

} else {
    printf LOG "No such action %s\n",$opt_x;
    print $usage;
    exit;
}

# Checking user
my $user;
if ($opt_u) {
    $user = $opt_u;
} else {
    chomp ($user = `whoami`);
}

print LOG "User set to $user.\n";


# Setting lock to the correct value
my $lock;
if ($opt_k) {
    $lock = 1;
    print LOG "Lock enabled.\n";
} else {
    $lock = 0;
}

my $secret;
if ($opt_s) {
    $secret = 1;
    print LOG "Hides the tuple.\n";
} else {
    $secret = 0;
}

my $autoenable;
my $autoenablestep;
if ($opt_t) {
    $autoenablestep = $opt_t;
    $autoenable = "now() + '$opt_t days'";
    printf LOG "Setting autoenable to %s.\n",$autoenable;
} else {
    $autoenablestep = "NULL";
    $autoenable = "NULL";
}

# We connect to manage here, because we wanted to check the parameters first.
my $dbh_manage = &NAV::connection('arnold','manage');
$errorMessage = $dbh_manage->errorMessage;
if ($errorMessage eq PGRES_CONNECTION_BAD) {
    &reporterror("Could not connect to manage-database.");
    exit(1);
} else {
    print LOG "Connected successfully to manage.\n";
}

my %reasons;
my %mail;
my @mailconfig;
my %nonblock;
if ($action eq 'disable') {
    unless (@iplist) {
	@iplist = &parsefile($filename);
    }

    # Get reasons for block
    %reasons = &getreasons(0);
    if ($reason) {
	unless ($reasons{$reason}) {
	    printf LOG "No such reason %s, please use the -l option to see list of reasons and try again.\n",$reason;
	    exit;
	}
    }

    # Assign the mail-array, read the mailconfig-file
    if ($sendmail) {
	open (MAILCONFIG, $mailconfigfile) or die ("Could not open $mailconfigfile: $!");
	@mailconfig = <MAILCONFIG>;
	close MAILCONFIG;
    }

    # parse the file with info about what to not block
    %nonblock = &parseconfig($nonblockfile);

}

# SNMP-variables
my $enable = 1;
my $disable = 2;

my %text;
$text{1} = 'enabled';
$text{2} = 'disabled';


########################################
# It goes like this:
# If we are to disable, we take ip as input
# Enabling is only possible with the appropriate identityid,
# as this is used only from the web-page (hopefully)

if ($action eq 'enable') {
    print LOG "Running enable\n";
    # Run the enable-sub on all ports that this computer has disabled

    # z specifies that only this id must be unblocked
    if ($opt_z) {
	if (&enable($id)) {
	    print LOG "Enabling of $id successful.\n";
	} else {
	    print LOG "Enabling if $id NOT successful.\n";
	}
    } else {

	my $getmacs = "SELECT mac FROM identity WHERE identityid=$id";
	my $rgetmacs = $dbh_block->exec($getmacs);
	my ($mac) = $rgetmacs->fetchrow;

	my $getall = "SELECT identityid FROM identity WHERE mac='$mac' AND blocked_status='disabled'";
	my $rgetall = $dbh_block->exec($getall);

	while (my ($id) = $rgetall->fetchrow) {
	    if (&enable($id)) {
		print LOG "Enabling of $id successful.\n";
	    } else {
		print LOG "Enabling if $id NOT successful.\n";
	    }
	}
    }

} elsif ($action eq 'disable') {
    my @disabledlist;
    my @notdisabledlist;

    foreach my $element (@iplist) {

	my $ip = @$element[0];
	my $rest = @$element[1];

	print LOG "\n-- NEW IP --\n";
	# Check if it must be skipped
	next if &skip($ip,0);

	my $netbios = "";
    my $nmbtest = `which nmblookup 2> /dev/null`;
	if ($? == 0) {
		chomp $nmbtest;
		# Running nmblookup on comp	uter
		print LOG "Running nmblookup on $ip...";
		$netbios = `$nmbtest -A $ip -T | grep -v '<GROUP>' | grep -m1 '<00>'`;
		$netbios =~ s/\s+(\S+).*\n.*/$1/;
		print LOG "done\n";
	} else {
		print LOG "Could not find nmblookup.\n";
	}
	unless ($netbios) {$netbios = "N/A";}
	
	# Running host on computer
	print LOG "Running host on $ip...";
	chomp (my $dns = `host $ip`);
	if ($dns =~ m/not\sfound/g) {
	    $dns = "N/A";
	} else {
	    chop $dns;
	    $dns = (split /\s/, $dns)[-1];
	}
	print LOG "done.\n";

	# Trying to disable port
	if (&disable($ip,$netbios,$dns,$rest)) {
	    print LOG "Disabled successfully.\n";
	    push @disabledlist, "$ip, $netbios, $dns";
	} else {
	    print LOG "Disabling of $ip NOT successful.\n";
	    push @notdisabledlist, "$ip, $netbios, $dns";
	}

    }

    if ($sendmail) {
	# Sending mail
	foreach my $address (keys %mail) {
	    
	    my @list;
	    my @hosts = @{ $mail{$address} };
	    my $numberofhosts = 0;
	    foreach my $host (@hosts) {
		$numberofhosts++;
		if (@$host[3]) {
		    push @list, "@$host[0] (NETBIOS: @$host[1], DNS: @$host[2]) @$host[3]";
		} else {
		    push @list, "@$host[0] (NETBIOS: @$host[1], DNS: @$host[2])";
		}
	    }
	    
	    if ($numberofhosts > 0) {
		&send_mail($address,@list);
	    }
	}
    }

    &mailnonblocked();

    # Writing statusinfo when done with all ips
    print LOG "--- SUMMARY ---\n\n";

    if ($#disabledlist >= 0) {
	printf LOG "The following computers were disabled (%s):\n",$#disabledlist + 1;
	for (@disabledlist) {
	    print LOG "$_\n";
	}
    } else {
	print LOG "No computers were disabled.\n";
    }

    if ($#notdisabledlist >= 0) {
	printf LOG "\nThe following computers were NOT disabled (%s), see errorlog for reason:\n",$#notdisabledlist + 1;
	for (@notdisabledlist) {
	    print LOG "$_\n";
	}
    }    
}

my $totalseconds = time - $^T;
my $minutes = int $totalseconds / 60;
my $seconds = $totalseconds - (60 * $minutes);

if ($minutes > 0) {
    printf LOG "\n\nScript executed in %s minutes and %s seconds.\n",$minutes,$seconds;
} else {
    printf LOG "\n\nScript executed in %s seconds.\n", $totalseconds;
}

close LOG;
# From here and down there are only subs (sorted alphabetically)

########################################
# changeportstatus
########################################
sub changeportstatus {

    my ($sysname,$swip,$module,$port,$ifindex,$vendor,$flag,$community) = @_;
    my $ok = 0;
    my $response;

    if ($vendor eq '3com') {
	$response = &set3com($flag,$swip,$ifindex,$community);
    } elsif ($vendor eq 'hp') {
	$response = &setHP($flag,$swip,$module,$ifindex,$community);
    } elsif ($vendor eq 'cisco') {
	$response = &setCisco($flag,$swip,$ifindex,$community);
    } else {
	&reporterror("No such vendor supported: $vendor.");
	return 0;
    }

    if ($response == $flag) {
	printf LOG "Port %s:%s on %s set to %s.\n",$module,$port,$sysname,$text{$flag};
	$ok = 1;
    } else {
	&reporterror("An error occured during changing of portstate - $response.");
    }

    return $ok;

}

########################################
# disable
########################################
sub disable {

    my ($ip,$netbios,$dns,$rest) = @_;
    my ($email,$orgid);

    $comment = $rest if $rest;

    # Finding email address
    #my $q = "SELECT orgid,org2 FROM org LEFT JOIN prefiks USING (orgid) WHERE netaddr >> inet '$ip'";
    my $q = "SELECT orgid,opt1 FROM org LEFT JOIN prefixreport USING (orgid) WHERE netaddr >> inet '$ip'";
    my $r = $dbh_manage->exec($q);

    if ($r->ntuples > 0) {
        ($orgid,$email) = $r->fetchrow;
        print LOG "Found email $email\n";
    } else {
        print LOG "Could not find email for $ip ($dns,$netbios)\n";
        $email = 0;
	$orgid = 0;
    }

    # Find information about which switchport the box lies behind, mac-adress and so on.
    # The variable names should explain the meaning.
    my $query = "SELECT netbox.ip, netbox.rw, netbox.catid, cam.sysname, REPLACE(mac::text, ':', '') AS mac, type.vendorid, type.typename, swport.swportid, swport.ifindex, module.module, swport.port FROM arp LEFT JOIN cam USING (mac) LEFT JOIN netbox ON (cam.netboxid = netbox.netboxid) LEFT JOIN type USING (typeid) LEFT JOIN module ON (module.netboxid=netbox.netboxid) LEFT JOIN swport ON (module.moduleid=swport.moduleid) WHERE arp.ip='$ip' AND arp.end_time='infinity' AND cam.end_time = 'infinity' AND swport.ifindex=cam.ifindex AND swport.ifindex IS NOT NULL";
    my $res = $dbh_manage->exec($query);

    #print "$query\n";

    my ($swip, $community, $kat, $sysname, $mac, $vendorid, $typename, $swportid, $ifindex, $module, $port);

    # If we find only one match, we're happy and go on with the disabling of the port
    # and updating of database.
    if ($res->ntuples == 1) {
	($swip, $community, $kat, $sysname, $mac, $vendorid, $typename, $swportid, $ifindex, $module, $port) = $res->fetchrow;

	# Setting allowedok to 1 if we find match of netboxtype in config-file.
	my $allowedok = 0;
	foreach my $confkat (split(/,/,$cfg{'allowtypes'})) {
	    if ($kat eq $confkat) {
		$allowedok = 1;
	    }
	}

	unless ($allowedok) {
	    &reporterror($ip,$netbios,$dns,"$kat is not an allowed equipmenttype for blocking - skipping block.");
	    return 0;
	}

	if (&skip($vendorid,$typename)) {
	    &reporterror($ip,$netbios,$dns,"$vendorid-$typename is not supported.");
	    return 0;
	}

	if (&skipid($ip,$swportid,$mac)) {
	    &reporterror($ip,$netbios,$dns,"This port is already blocked.");
	    return 0;
	}

	unless ($community) {
	    &reporterror($ip,$netbios,$dns,"No snmp write-community found on $sysname.");
	    return 0;
	}

	# Check if there are other computers behind this port
	# Disabled due to long execution time
	my $multiple = 1;
# 	$q = "SELECT mac FROM cam WHERE sysname='$sysname' AND module='$module' AND port=$port AND end_time='infinity'";
# 	$r = $dbh_manage->exec($q);
# 	if ($r->ntuples > 1) {
# 	    $multiple = $r->ntuples;
# 	    printf LOG "There are %s computers behind this port, people may become unhappy...\n",$multiple;
# 	} else {
# 	    $multiple = 1;
# 	}

	# Disable the port
	if (&changeportstatus($sysname,$swip,$module,$port,$ifindex,$vendorid,$disable,$community)) {
	    print LOG "Seemed to work.\n";
	} else {
	    &reporterror($ip,$netbios,$dns,"Disabling of port didn't work as expected, something wrong with the SNMP-query.");
	    return 0;
	}

	# Put it into / update database
	unless (&updatedb($swportid,$sysname,$vendorid,$community,$swip,$mac,$ifindex,$module,$port,$disable,$ip,$dns,$netbios,$multiple,$email,$orgid)) {
	    &reporterror($ip,$netbios,$dns,"Something went wrong when updating the database.");
	    return 0;
	}

	unless ($opt_d) {
	    # if there is another tuple in the database that has the same mac-address as key, AND is
	    # disabled AND is not the same tuple, enable that port.
	    $q = "SELECT identityid,swportid,mac FROM identity WHERE mac='$mac' AND blocked_status='disabled' AND swportid!=$swportid";
	    $r = $dbh_block->exec($q);

	    while (my ($identityid,$swportid,$mac) = $r->fetchrow) {
		printf LOG "Oops, another tuple found (ID: %s, swid: %s, mac: %s), enabling it.\n",$identityid,$swportid,$mac;
		&enable($identityid);
	    }
	}

	# Add it to the mail-hash
	if ($email) {
            push @{ $mail{$email} }, [$ip, $netbios, $dns, $rest];
            print LOG "Pushing $ip ($netbios, $dns) on $email.\n";
        } else {
            print LOG "Can't find email for $ip ($netbios, $dns)\n";
        }

	print "$ip (connected to $sysname $module:$port) disabled successfully.\n";

    # If more than one hit, we get confused and return 0
    } elsif ($res->ntuples > 1) {
	my @swportids;
	while (	($swip, $community, $kat, $sysname, $mac, $vendorid, $typename, $swportid, $ifindex, $module, $port) = $res->fetchrow) {
	    push @swportids, $swportid;
	}
	
	my $text = "Query returned ".$res->ntuples." ifindexes - ".join (",", @swportids);
	&reporterror($ip,$netbios,$dns,$text);
	return 0;

    # If nothing else matters, we get even more confused and return 0
    } else {
	&reporterror($ip,$netbios,$dns,"Could not find (a unique) port for blocking, the computer is either shut-down or has recently moved to another port.");
	return 0;
    }

    return 1;
    
}

########################################
# enable
########################################
sub enable {

    my ($id) = @_;

    # 1. Check if it exists in the database, else skip
    my $query = "SELECT swportid,swsysname,swvendor,community,swip,swmodule,swport,swifindex,blocked_status,ip,mac,dns,netbios FROM identity WHERE identityid=$id";
    my $res = $dbh_block->exec($query);

    my $nummatches = $res->ntuples;
    if ($nummatches < 1) {
	print LOG "No tuple in the database with id=$id.\n";
	return 0;
    }

    # 2. If the last event indicated that it is disabled, enable the port and update the database.
    my ($swportid,$sysname,$vendor,$community,$swip,$module,$port,$ifindex,$status,$ip,$mac,$dns,$netbios) = $res->fetchrow;


    # 2.1 Enable the port(s)
    if (&changeportstatus($sysname,$swip,$module,$port,$ifindex,$vendor,$enable,$community)) {
	print LOG "Seemed to work.\n";
	print "$ip (connected to $sysname $module:$port) enabled successfully.\n";
    } else {
	print LOG "Didn't work as expected.\n";
	return 0;
    }

    # 2.2 Update database.
    if (&updatedb($swportid,$sysname,$vendor,$community,$swip,$mac,$ifindex,$module,$port,$enable,0,0,0)) {
	return 1;
    } else {
	&reporterror($ip,$netbios,$dns,"Something went wrong when updating the database.");
	return 0;
    }

}


############################################################
# getreasons
# ----------
# gets all reasons from the database and returns a hash
# with the values.
############################################################
sub getreasons {
    my $bool = shift;
    my %hash;

    my $q = "SELECT * FROM blocked_reason";
    my $r = $dbh_block->exec($q);

    print "Reasons for blocking currently in the database:\n" if $bool;
    while (my ($id,$text) = $r->fetchrow) {
	printf "%s: %s\n", $id,$text if $bool;
	$hash{$id} = $text;
    }

    return %hash;

}

############################################################
# getstep
# -------
# Used to make incremental steps to the autoenablestep
# so that the punishment is harder the more you are
# blocked. We are some sadistic people.
############################################################
sub getstep {
    my ($reason, $id, $inc) = @_;
    my $newstep;
    my $oldstep;

    my $q = "SELECT autoenablestep FROM event WHERE identityid = $id AND blocked_reasonid = $reason AND autoenablestep IS NOT NULL ORDER BY eventtime DESC";
    my $r = $dbh_block->exec($q);

    print LOG "$q\n";

    if ($r->ntuples > 0) {
	($oldstep) = $r->fetchrow;
	$newstep = $oldstep * 2;
    } else {
	$newstep = $inc;
    }

    return $newstep;

}


############################################################
# matchip
# -------
# input - an ip and an iprange checks if the ip is in the 
# iprange returns 1 if yes, otherwise 0
############################################################
sub matchip {

    my ($ip,$iprange) = @_;

    my ($quad,$bits) = split /\//, $iprange;
    $bits = 32 - ($bits || 32);

    my $ipnum = unpack("N", pack("C4", split(/\./, $ip))) >> $bits;
    my $rangenum = unpack("N", pack("C4", split(/\./, $quad))) >> $bits;

    if ($ipnum == $rangenum) {
	return 1;
    } else {
	return 0;
    }

}

############################################################
# parseconfig
# -----------
# parses the configfiles and puts the config in
# appropriate hashes.
############################################################
sub parseconfig {

    my $filename = shift;
    my $dotypes = 0;
    my $doips = 0;
    my %hash;
    
    open (FILE, $filename) or die "Could not open $filename: $!";
    while (<FILE>) {
	next if /^\#/;
	chomp $_;
	if (/^;netboxtypes/) {
	    $doips = 0;
	    $dotypes = 1;
	    next;
	} elsif (/^;ip-ranges/) {
	    $dotypes = 0;
	    $doips = 1;
	    next;
	}

	if ($dotypes && /^\w+/) {
	    my $var = $_;
	    my ($vendor,$type) = map { s/\s*(\S+)\s*/$1/; $_ } split (/,/, $var);
	    $hash{$vendor}{$type} = 1;
	    print LOG "Adding $vendor, $type to typehash.\n";
	    next;
	}
	
	if ($doips && /^\d+\.\d+\.\d+\.\d+$/) {
	    $hash{'ip'}{$_} = 1;
	    print LOG "Adding $_ to iplist.\n";
	} elsif ($doips && /^\d+\.\d+\.\d+\.\d+\/\d+/) {
	    $hash{'range'}{$_} = 1;
	    print LOG "Adding $_ to iprangelist.\n";
	} elsif ($doips && /^\d+\.\d+\.\d+\.\d+-\d+/) {
	    $hash{'iplist'}{$_} = 1;
	    print LOG "Adding $_ to iplist.\n";
	}

    }
    close FILE;

    return %hash;

}

########################################
# parsefile
########################################
sub parsefile {
    my $filename = shift;
    my @list;

    open (FILE, $filename) or die ("Could not open $filename: $!\n");
    while (<FILE>) {
	chomp $_;
	next if /^\#/;
	if (/^(\d+\.\d+\.\d+\.\d+)\s*(.*)/) {
	    print LOG "Pushing >$1< >$2<\n";
	    push @list, [ $1, $2 ];
	} else {
	    print LOG "$_ is not a valid ip-adress - skipping.\n";
	    next;
	}
    }
    close FILE;

    return @list;
}

########################################
# reporterror
########################################
sub reporterror {
    my $numargs = @_;
    if ($numargs == 1) {
	my $text = shift;
	print STDERR "ERROR $text\n";
	print LOG "ERROR $text\n";
    } else {
	my ($ip,$netbios,$dns,$text) = @_;

	print STDERR "ERROR ($ip, $netbios, $dns): $text\n";
	print LOG "ERROR ($ip, $netbios, $dns): $text\n";
    }
	
}


########################################
# send_mail
########################################
sub send_mail {
    
    my ($email, @complist) = @_;
    my $text;

    my @temptext = @mailconfig;
    my $from = $cfg{'fromaddress'};
    chomp (my $subject = shift @temptext);
    $subject =~ s/\$reason/$reasons{$reason}/g;

    my $complist = join "\n", @complist;

    foreach my $line (@temptext) {
	$line =~ s/\$list/$complist/g;
	$line =~ s/\$comment/$comment/g;
	$text .= $line;
    }

    print LOG "--- NEW MAIL ---\nSending mail to $email with subject $subject:\n$text\n";

    open (SENDMAIL, "|$cfg{'mailprogram'}") or die ("Could not fork for email. $!\n");

    print SENDMAIL "From: $from\n";
    print SENDMAIL "To: $email\n";
    print SENDMAIL "Subject: $subject\n\n";
    print SENDMAIL "$text\n";

    close SENDMAIL;
    
    
}


########################################
# set3com
########################################
sub set3com {
    # 3com

    my ($flag,$ip,$ifindex,$community) = @_;
    my $mibstring = "interfaces.ifTable.ifEntry.ifAdminStatus";
    
    my ($response) = &snmpset ("$community\@$ip:161:$timeout:$retries:$backoff", "$mibstring\.$ifindex",'integer', $flag);
    print LOG "$community\@$ip:161:$timeout:$retries:$backoff, $mibstring\.$ifindex,'integer', $flag\n";
 
    #my $response = $flag;

    $response = -1 unless $response;
    return $response;

}

########################################
# setHP
########################################
sub setHP {

    my ($flag,$ip,$modul,$ifindex,$community) = @_;
    my $mibstring = "interfaces.ifTable.ifEntry.ifAdminStatus";
    
    # Fix for wrong ifindex in database. HP has lokal ifindexes even when stacked, but
    # NAV doesn't support that. So NAV pads the ifindexes to make them unique.
    # We get the two last characters and pray it's the ifindex. 
    $ifindex =~ s/.*(..)$/$1/;
    
    # Make it a number (because 101 -> 01 which is not usable as an ifindex)
    $ifindex += 0;
    
    my $response;

    if ($modul) {
	($response) = &snmpset ("$community\@sw$modul\@$ip:161:$timeout:$retries:$backoff", "$mibstring.$ifindex", 'integer', $flag);
	print LOG "$community\@sw$modul\@$ip:161:$timeout:$retries:$backoff, $mibstring\.$ifindex,'integer', $flag\n";
    } else {
	($response) = &snmpset ("$community\@$ip:161:$timeout:$retries:$backoff", "$mibstring.$ifindex", 'integer', $flag);
	print LOG "$community\@$ip:161:$timeout:$retries:$backoff, $mibstring\.$ifindex,'integer', $flag\n";
    }
 
    #$response = $flag;
    $response = -1 unless $response;
    return $response;
}


########################################
# setCisco
########################################
sub setCisco {

    my ($flag,$ip,$ifindex,$community) = @_;
    my $mibstring = "interfaces.ifTable.ifEntry.ifAdminStatus";
    
    my $response;

    my ($response) = &snmpset ("$community\@$ip:161:$timeout:$retries:$backoff", "$mibstring\.$ifindex",'integer', $flag);
    print LOG "$community\@$ip:161:$timeout:$retries:$backoff, $mibstring\.$ifindex,'integer', $flag\n";
 
    #$response = $flag;
    $response = -1 unless $response;
    return $response;

}


########################################
# skip
########################################
sub skip {

    my ($element1,$element2) = @_;

    # If $element2 is set, we assume that this is a type
    # otherwise it's an ip adress/range

    # Checking types
    if ($element2) {
	if ($nonblock{$element1}{$element2}) {
	    print LOG "Skipping type $element1, $element2.\n";
	    return 1;
	} else {
	    return 0;
	}
    }

    # Checking ip-adresses
    
    # 1 - ranges
    foreach my $iprange (keys (%{$nonblock{'range'}})) {
	if (&matchip($element1, $iprange)) {
	    print LOG "$element1 is in a nonblockrange, skipping.\n";
	    &reporterror("$element1 is in a nonblockrange, skipping.");
	    push @nonblockedip, $element1;
	    return 1;
	}
    }
    
    # 2 - specific ip adressess
    if ($nonblock{'ip'}{$element1}) {
	print LOG "$element1 is in nonblocklist, skipping.\n";
	&reporterror("$element1 is in nonblocklist, skipping.");
	push @nonblockedip, $element1;
	return 1;
    }

    # 3 - ip list
    foreach my $iplist (keys (%{$nonblock{'iplist'}})) {
	$iplist =~ /(\d+\.\d+\.\d+)\.(\d+)-(\d+)$/;
	my $body = $1;
	my $first = $2;
	my $last = $3;
	
	$element1 =~ /(\d+\.\d+\.\d+)\.(\d+)/;
	
	if ($body eq $1) {
	    if ($2 >= $first and $2 <= $last) {
		print LOG "$element1 is in a nonblocklist ($iplist), skipping.\n";
		&reporterror ("$element1 is in a nonblocklist ($iplist), skipping.\n");
		return 1;
	    }
	}
    }
    
    return 0;

}

############################################################
# skipid
# ------
# sub to check if this swport,mac combo is blocked already
############################################################
sub skipid {
    my ($ip, $swportid, $mac) = @_;

    # Lets first check if this ip is blocked already.
    my $q = "SELECT * FROM identity WHERE swportid=$swportid AND blocked_status='disabled'";
    my $r = $dbh_block->exec($q);

    if ($r->ntuples > 0) {
	print LOG "$ip is already blocked, skipping.\n";
	return 1;
    }


}

########################################
# updatedb
# --------
# 
########################################
sub updatedb {
    my ($swportid,$sysname,$vendor,$community,$swip,$mac,$ifindex,$module,$port,$action,$ip,$dns,$netbios,$multiple,$email,$orgid) = @_;

    my $q = "SELECT identityid FROM identity WHERE mac='$mac' AND swportid=$swportid";
    my $r = $dbh_block->exec($q);

    my $identityid;

    # DISABLE
    if ($action == $disable) {

	my $determined;
	if ($opt_d) {
	    $determined = 'y';
	} else {
	    $determined = 'n';
	}


	if ($r->ntuples > 0) {
	    ($identityid) = $r->fetchrow;

	    $q = "UPDATE identity SET blocked_reasonid=$reason, blocked_status='$text{$action}', swsysname='$sysname', swvendor='$vendor', community='$community', swip='$swip', swmodule='$module', swport=$port, swifindex=$ifindex, ip='$ip', dns='$dns', netbios='$netbios', lastchanged=now(), mail='$email', autoenable=$autoenable, determined='$determined' WHERE identityid=$identityid";
	    printf LOG "Executing %s\n",$q;
	    $r = $dbh_block->exec($q);

	    return 0 unless &checkquery($r);

	} else {
	    $q = "INSERT INTO identity (blocked_reasonid, blocked_status, mac, swportid, swsysname, swvendor, community, swip, swmodule, swport, swifindex, ip, dns, netbios, starttime, lastchanged, multiple, mail,userlock,secret,autoenable,orgid,determined) VALUES ($reason, '$text{$action}', '$mac', $swportid, '$sysname', '$vendor', '$community', '$swip', '$module', $port, $ifindex, '$ip', '$dns', '$netbios', now(), now(), $multiple, '$email','$lock','$secret',$autoenable,'$orgid','$determined')";
	    printf LOG "Executing %s\n",$q;
	    $r = $dbh_block->exec($q);

	    $q = "SELECT identityid FROM identity WHERE mac='$mac' AND swportid=$swportid";
	    printf LOG "Executing %s\n",$q;
	    $r = $dbh_block->exec($q);

	    return 0 unless &checkquery($r);

	    ($identityid) = $r->fetchrow;

	}

	if ($incremental) {
	    # Get days of last block from this identityid with this reason
	    $autoenablestep = &getstep($reason, $identityid, $incremental);
	    $autoenable = "now() + '$autoenablestep days'";

	    $q = "UPDATE identity SET autoenable=$autoenable WHERE identityid=$identityid";
	    $r = $dbh_block->exec($q);
	}

	$q = "INSERT INTO event (identityid, event_comment, blocked_status, blocked_reasonid, eventtime, username, autoenablestep) VALUES ($identityid, '$comment', '$text{$action}', $reason, now(), '$user', $autoenablestep)";
	printf LOG "Executing %s\n",$q;
	$r = $dbh_block->exec($q);

	return 0 unless &checkquery($r);
	
	# ENABLE
    } elsif ($action == $enable) {
	if ($r->ntuples > 0) {
	    ($identityid) = $r->fetchrow;
	    $q = "UPDATE identity SET blocked_status='$text{$action}', swsysname='$sysname', swvendor='$vendor', community='$community', swip='$swip', swmodule='$module', swport=$port, swifindex=$ifindex, lastchanged=now(), autoenable=NULL WHERE identityid=$identityid";
	    printf LOG "Executing %s\n",$q;
	    $r = $dbh_block->exec($q);

	    return 0 unless &checkquery($r);

	} else {
	    print LOG "No prior tuple in the database, this shouldn't happen...\n";
	    return 0;
	}
	
	$q = "INSERT INTO event (identityid, event_comment, blocked_status, eventtime, username) VALUES ($identityid, '$comment', '$text{$action}', now(), '$user')";
	printf LOG "Executing %s\n",$q;
	$r = $dbh_block->exec($q);

	return 0 unless &checkquery($r);

    }
    

}

sub checkquery {
    my $res = shift;
    my $status = $res->resultStatus;
    my $error = $dbh_block->errorMessage;

    if ($status eq PGRES_COMMAND_OK) {
	print LOG "Query ok\n";
	return 1;
    } elsif ($status eq PGRES_EMPTY_QUERY) {
	print LOG "Empty query\n";
	return 1;
    } elsif ($status eq PGRES_TUPLES_OK) {
	print LOG "Tuples ok\n";
	return 1;
    } elsif ($status eq PGRES_COPY_OUT) {
	print LOG "Copy out\n";
	return 1;
    } elsif ($status eq PGRES_COPY_IN) {
	print LOG "Copy in\n";
	return 1;
    } elsif ($status eq PGRES_BAD_RESPONSE) {
	print LOG "Bad response: $error\n";
	return 0;
    } elsif ($status eq PGRES_NONFATAL_ERROR) {
	print LOG "Nonfatal error: $error\n";
	return 0;
    } elsif ($status eq PGRES_FATAL_ERROR) {
	print LOG "Fatal error: $error\n";
	return 0;
    } else {
	print LOG "Undefined status from database.\n";
	return 0;
    }

}

sub mailnonblocked {

    unless ($#nonblockedip >= 0) { return; }

    # Send mail for computers not blocked

    unless ($cfg{'nonblockmail'}) { return; }

    my $email = $cfg{'nonblockmail'};
    my $from = $cfg{'fromaddress'};
    my $subject = "Maskiner ikke blokkert av Arnold.";
    my $text = "The following ip-addresses where not blocked because they are in the nonblock-list:\n\n";
    $text .= join "\n", @nonblockedip;
    $text .= "\n\nThe reason for block was $reasons{$reason}\n";
    $text .= "The user running the block was $user\n";
    $text .= "The log of this incident is in $logdir/$logfile\n";
    $text .= "\n---\nArnold\n";
    
    print LOG "--- NEW MAIL ---\nSending mail to $email with subject $subject:\n$text\n";

    open (SENDMAIL, "|$cfg{'mailprogram'}") or die ("Could not fork for email. $!\n");
    
    print SENDMAIL "From: $from\n";
    print SENDMAIL "To: $email\n";
    print SENDMAIL "Subject: $subject\n\n";
    print SENDMAIL "$text\n";
    
    close SENDMAIL;

}
