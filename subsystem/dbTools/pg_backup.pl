#!/usr/bin/env perl
#
# Copyright 2002-2004 Norwegian University of Science and Technology
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
# $Id$
#
# Takes a full backup of the NAV database every
#  * Day        Rotates once every week
#  * Week       Rotates once every 5 weeks
#  * Month      Rotates once a year
#
# Needs to have the username/password of a PostgreSQL superuser to do
# a full database dump.  To avoid having a world-readable config file
# containing this password, you could set the setuid bit of this
# script (when owned by root), and make the config file owned by root
# and having mode 0600 (the script should be taint-proof to allow this
# behaviour).
#
# Authors: Knut-Helge Vindheim <knutvi@itea.ntnu.no>
#          Morten Vold <morten.vold@itea.ntnu.no>
#
####################
use POSIX qw(strftime isatty);
use NAV;
use NAV::Path;
use warnings;
use strict;

sub log {
    my $logline = shift;
    my @loglines = split(/\n/, $logline);
    for $logline (@loglines) {
	my $now_string = strftime "%a %d %b %Y %T", localtime;
	print LOGFILE "$now_string $logline\n";
    }
}

# De-taint:
$ENV{'PATH'} = '/bin:/usr/bin:/usr/local/bin';
delete @ENV{'IFS', 'CDPATH', 'ENV', 'BASH_ENV'};

my ($res, $filename);

# Remember, month and day names produced here depend on which locale
# settings the running user has!
my $now_string = strftime "%w:%d:%A:%B:%V", localtime;
my ($dayofweek, $dayofmonth, $weekday, $month, $weeknumber) = split(/\:/, $now_string);

my $conf = "$NAV::Path::sysconfdir/pg_backup.conf";


my %config = &NAV::config($conf);

my $password = $config{'password'};
my $username = $config{'username'} || 'postgres';
my $path = $config{'path'} || "$NAV::Path::localstatedir/pg_backup";;
my $logfile = $config{'logfile'} || "$NAV::Path::localstatedir/log/pg_backup.log";
my $doVacuum = $config{'vacuum'} || 'no';
$doVacuum = ($doVacuum =~ /\b(yes|true|on)\b/i);

if ($password eq '') {
    die("$0: No database password supplied in config file ($conf)\n");
}

# Check whether today is the first of the month
if ($dayofmonth eq '01')
{
	$filename = "fullbackup_postgres_01\.$month";
}
# Check whether it is the first day of the week
elsif ($dayofweek eq '0')
{
	my $week = $weeknumber % 5;
	$filename = "fullbackup_postgres_week$week";
}
# If not, it is a regular weekday
else 
{
	$filename = "fullbackup_postgres_$weekday";
}

open(LOGFILE,">>$logfile") || die "$0: Unable to open log for writing ($logfile): $!\n";


# Dump all the databases
if (isatty(1)) { print "$0: Dumping databases\n" }
&log("Backup: pg_dumpall > $path/$filename");
$res = `PGPASSWORD=$password PGUSER=$username pg_dumpall > $path/$filename`;
if ($res ne '') { &log($res); }

# Compress the dump file
if (isatty(1)) { print "$0: Compressing dump file\n" }
&log("bzip2 $path/$filename");
$res = `nice bzip2 -f $path/$filename`;
if ($res ne '') { &log($res); }

# Vacuum databases
if ($doVacuum) {
    if (isatty(1)) { print "$0: Vacuuming databases\n" }
    &log("Vacuuming databases");
    $res = `PGPASSWORD=$password  vacuumdb -U postgres -a -z 2>&1 1>/dev/null`;
    if ($res ne '') { &log($res); }
}

&log("Done");

close(LOGFILE);
