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
# This file is part of the NAV project.
# Takes a full backup of the NAV database every
#  * Day        Rotates once every week
#  * Week       Rotates once every 5 weeks
#  * Month      Rotates once a year
#
# Authors: Knut-Helge Vindheim <knutvi@itea.ntnu.no>
#          Morten Vold <morten.vold@itea.ntnu.no>
#
####################
use POSIX qw(strftime);
use NAV;
use NAV::Path;

# De-taint:
$ENV{'PATH'} = '/bin:/usr/bin:/usr/local/bin';
delete @ENV{'IFS', 'CDPATH', 'ENV', 'BASH_ENV'};

my ($res, $filename);

my $now_string = strftime "%w:%d:%A:%B:%V", localtime;
my ($dayofweek, $dayofmonth, $weekday, $month, $weeknumber) = split(/\:/, $now_string);

my $conf = "$NAV::Path::sysconfdir/pgpasswd.conf";


my %config = &NAV::config($conf);

my $password = $config{'password'};
my $username = $config{'username'} || 'postgres';
my $path = $config{'path'} || '.';
my $logfile = $config{'logfile'} || "$NAV::Path::localstatedir/log/pg_backup.log";


# Check whether today is the first of the month
if ($dayofmonth eq '01')
{
	$filename = "fullbackup_postgres_01\.$month";
}
# Check whether it is the first day of the week
elsif ($dayofweek eq '0')
{
	$week = $weeknumber % 5;
	$filename = "fullbackup_postgres_week$week";
}
# If not, it is a regular weekday
else 
{
	$filename = "fullbackup_postgres_$weekday";
}

open(LOGFILE,">>$logfile") || die "Unable to open log for writing ($logfile): $!";


# Dump all the databases
$now_string = strftime "%a %d %b %Y %T", localtime;
print LOGFILE "$now_string\tBackup: pg_dumpall > $path/$filename\n";
$res = `PGPASSWORD=$password PGUSER=$username pg_dumpall > $path/$filename`;
if ($res ne '') { print LOGFILE "$res\n\n"; }

# Compress the dump file
$now_string = strftime "%a %d %b %Y %T", localtime;
print LOGFILE "$now_string\tbzip2 $path/$filename\n";
$res = `nice bzip2 -f $path/$filename`;
if ($res ne '') { print LOGFILE "$res\n\n"; }

# Vacuum databases
$now_string = strftime "%a %d %b %Y %T", localtime;
print LOGFILE "$now_string\tVacuumdb ...\n";
$res = `PGPASSWORD=$password  vacuumdb -U postgres -a -z`;
if ($res ne '') { print LOGFILE "$res"; }

$now_string = strftime "%a %d %b %Y %T", localtime;
print LOGFILE "$now_string\tDone.\n\n";

close(LOGFILE);
