#!/usr/bin/perl
####################
#
# $Id$
# This file is part of the NAV project.
# Takes a full backup of the NAV database every
#  * Day        Rotates once every week
#  * Week       Rotates once every 5 weeks
#  * Month      Rotates once a year
#
# Copyright (c) 2002-2003 by NTNU ITEA
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

my ($res, $filnavn);

my $now_string = strftime "%w:%d:%A:%B:%V", localtime;
my ($dayofweek, $dayofmonth, $weekday, $month, $weeknumber) = split(/\:/, $now_string);

my $conf = "$NAV::Path::sysconfdir/pgpasswd.conf";


my %config = &NAV::config($conf);

my $passord = $config{'passord'};
my $brukernavn = $config{'brukernavn'};
my $sti = $config{'sti'};
my $logfil = $config{'logfil'};


# Sjekker om det er den første i måneden
if ($dayofmonth eq '01')
{
	$filnavn = "fullbackup_postgres_01\.$month";
}
# Sjekker om det er første dagen i uka
elsif ($dayofweek eq '0')
{
	$uke = $weeknumber % 5;
	$filnavn = "fullbackup_postgres_uke$uke";
}
# Hvis ikke så er det en vanlig ukedag
else 
{
	$filnavn = "fullbackup_postgres_$weekday";
}

open(LOGFIL,">>$logfil") || die "Kan ikke åpne loggfilen ($logfil): $!";


# Kjøre backup
$now_string = strftime "%a %d %b %Y %T", localtime;
print LOGFIL "$now_string\tBackup: pg_dumpall > $sti$filnavn\n";
$res = `PGPASSWORD=$passord PGUSER=$brukernavn pg_dumpall > $sti$filnavn`;
if ($res ne '') { print LOGFIL "$res\n\n"; }

# Pakker ned filen
$now_string = strftime "%a %d %b %Y %T", localtime;
print LOGFIL "$now_string\tbzip2 $sti$filnavn\n";
$res = `nice bzip2 -f $sti$filnavn`;
if ($res ne '') { print LOGFIL "$res\n\n"; }

#VacuumDB
$now_string = strftime "%a %d %b %Y %T", localtime;
print LOGFIL "$now_string\tVacuumdb ...\n";
$res = `PGPASSWORD=$passord  vacuumdb -U postgres -a -z`;
if ($res ne '') { print LOGFIL "$res"; }

$now_string = strftime "%a %d %b %Y %T", localtime;
print LOGFIL "$now_string\tFerdig.\n\n";

close(LOGFIL);
