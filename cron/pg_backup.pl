#!/usr/bin/perl

##############################################################
# Et script som tar full backup av databasen hver
#  * Dag	Roterer pr uke
#  * Uke	Roterer pr 5 uke
#  * Måned	Roterer pr år
#
##############################################################

use POSIX qw(strftime);

my ($res, $filnavn);

my $now_string = strftime "%w %e %A %B %V", localtime;
my ($dayofweek, $dayofmonth, $weekday, $month, $weeknumber) = split(/\s/, $now_string);

my $conf = '/usr/local/nav/local/etc/conf/pgpasswd.conf';


open(CONF,$conf);
while (<CONF>)
{
	unless (/^\#|^\s+/)
	{
		($key,$string) = split(/=/);
		chomp($string);  # Fjerne linjeskift
		$config{$key}=$string;
	}
}
close(CONF);

my $passord = $config{'passord'};
my $brukernavn = $config{'brukernavn'};
my $sti = $config{'sti'};
my $logfil = $config{'logfil'};


# Sjekker om det er den første i måneden
if ($dayofmonth eq '1')
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

open(LOGFIL,">>$logfil");


# Kjøre backup
$now_string = strftime "%a %e %b %Y %T", localtime;
print LOGFIL "$now_string\tBackup: pg_dumpall > $sti$filnavn\n";
$res = `PGPASSWORD=$passord PGUSER=$brukernavn pg_dumpall > $sti$filnavn`;
if ($res ne '') { print LOGFIL "$res\n\n"; }

# Pakker ned filen
$now_string = strftime "%a %e %b %Y %T", localtime;
print LOGFIL "$now_string\tbzip2 $sti$filnavn\n";
$res = `nice bzip2 -f $sti$filnavn`;
if ($res ne '') { print LOGFIL "$res\n\n"; }

#VacuumDB
$now_string = strftime "%a %e %b %Y %T", localtime;
print LOGFIL "$now_string\tVacuumdb ...\n";
$res = `PGPASSWORD=$passord  vacuumdb -U postgres -a -z`;
if ($res ne '') { print LOGFIL "$res"; }

$now_string = strftime "%a %e %b %Y %T", localtime;
print LOGFIL "$now_string\tFerdig.\n\n";

close(LOGFIL);
