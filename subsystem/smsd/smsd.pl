#!/usr/bin/perl
####################
#
# $Id$
# This file is part of the NAV project.
# This is the NAV SMS daemon, responsible for dispatching sms messages
# from the database to users' phones, through the use of
# MyGnokii2/Gammu
#
# Copyright (c) 2001-2003 by NTNU, ITEA nettgruppen
# Authors: Knut-Helge Vindheim <knut-helge.vindheim@itea.ntnu.no>
#          Gro-Anita Vindheim <gro-anita.vindheim@itea.ntnu.no>
#          Morten Vold <mortenv@tihlde.org>
#
####################

# Dette er en sms-demon som henter sms meldinger i fra
# databasen på bigbud og sender dem ved hjelp av 
# mobiltelefon koblet til com-porten.
#
# Hvis det ligger flere sms i ut køen som skal til 
# samme person, sendes det kun en sms + antall meldinger
# som ikke sendes.
#
# Både meldinger som blir sendt og meldinger som ikke sendes
# skrives til logg. 
#
# Det skrives til logg og sendes mail vist vist det oppstår 
# feil under sendigen av sms'en

# Innparametere som kan brukes er
# -c  / setter alle meldingen i utkøen til ignored
# -d xx / setter tiden mellom hver gang demone sjekker databasen, default er 30 sek
# -t xxxxxxxx / sender en testmelding til telefonnummeret

use POSIX qw(strftime);
use strict;
use vars qw($opt_c $opt_d $opt_t $opt_h);
use Getopt::Std;
use English;
use Pg;

my $NAVROOT='/usr/local/nav';
my $vei = "/usr/local/nav/navme/lib";
require "$vei/NAV.pm";
import NAV;

my $DISPATCHER = '/usr/local/bin/gammu';
my $FREEZELIMIT = 30;
my $pidfil = "$NAVROOT/local/var/run/smsd.pl.pid";
my $conffil= "$NAVROOT/local/etc/conf/smsd.conf";
my $navconf= "$NAVROOT/local/etc/conf/nav.conf";

switchuser(); # Sørg for at vi kjører som brukeren navcron

getopt('dt'); 

my %conf = &hash_conf($conffil);
my $logfil = $conf{logfil} || '/usr/local/nav/local/log/smsd.log';
my %navconf = &hash_conf($navconf);
my $MAILDRIFT = $navconf{ADMIN_MAIL};


my $temp;
my $smssyk = 0;

my ($tlf, $tekst, @respons, $respons_, $v, $nr1);
my ($dbh, $ko, $ko2, $maxidsok, $smsid);
my $dato = strftime "Tid: %H:%M:%S", localtime;
my $forsinkelse = 30;


# Viser hjelp
if ($opt_h) {
    print "\nsmsd [-[hc] [-d sec] [-t tlf]\n -h Viser denne hjelpen\n -c Setter alle meldingen i utkøen til ignored\n -d setter sleep i sekunder\n -t sender en testmelding til <tlf>\n\n";
    exit(0);   
}

# Kjører en lokal test på systemet
if ($opt_t) {
    $respons_ = &send_sms($opt_t, "Dette er en test fra smsd paa " . `hostname`);
    print "$respons_\n";
    exit(0);    
}

justme();				# sjekker om smsd kjøres fra før.

# Lager bare en connection mot databasen, som er konstant.
my %dbconf = &db_readconf();
my $dbname = $dbconf{db_trapdetect};
my $dbuser = $dbconf{script_smsd};
my $userpw = $dbconf{'userpw_' . $dbuser};
my $conn = &db_connect($dbname, $dbuser, $userpw);

# Sletter utkøen i databasen
if ($opt_c) {
    
    my $sql = "UPDATE smsutko SET sendt=\'I\', tidsendt=NOW() WHERE sendt=\'N\'";
    
    my $ok = &db_execute($conn,$sql);
}


# Sjekker om en ønsker en annen forsinkelse
if ($opt_d) {
    $forsinkelse = $opt_d;
}


# Henter ut antall sms vi har sendt.


my $sql = "SELECT max(smsid) FROM smsutko";

&sjekk_conn;
$maxidsok = &db_select($conn,$sql);

if ($maxidsok->ntuples)
{
    while (my @smsid = $maxidsok->fetchrow)
    {
	$smsid=$smsid[0];
    }
}
else
{
    $smsid=0;
}

my $sql = "SELECT tlf,smsutko.id,melding FROM smsutko,bruker WHERE bruker.id = smsutko.brukerid AND sendt=\'N\'";

chdir('/');
# Disconnect from terminal, STD(OUT|ERR|IN)
close(STDOUT);
close(STDERR);
close(STDIN);
# background ourself and go away only if we get this far..
my $pid = fork();
if ($pid) {
    # Skriver pid til fil
    open (PIDFIL, ">$pidfil");
    print PIDFIL $pid;
    close (PIDFIL);
    exit(0);
}

$0 = 'smsd.pl: NAV SMS daemon ready...';

# Kjører en uendelig løkke her
while ($v=2) {
    &sjekk_ko;
    sleep $forsinkelse;
}


sub sjekk_ko {
    my (%hash_ko_, @line);
    
    &sjekk_conn;
    my $ko_N = &db_select($conn,$sql);
    
    if ($ko_N->ntuples) {
	while ( @line = $ko_N->fetchrow) {
	    $hash_ko_{$line[0]}{$line[1]} = $line[2];
	}
    }
    
    if (%hash_ko_) {
	&sorter_sms(%hash_ko_);
    }
}




sub sorter_sms {
    my (%hash_ko, %hash_ko2_, $user, $id, @line, $id_);
    my ($nr1_user, $meld_nr) = 1;
    my ($text_, $tlf_, @sendt_id, @ignored_id, $ant_ignored);

    my ($ga,$ok);
    
    (%hash_ko) = @_;
    open(LOGFIL,">>$logfil");
    
    # Bruk 'sort keys' vist en vist en ønsker at lavest mobil-nummer skal komme først 
    foreach $user (sort keys %hash_ko) {

	@sendt_id = ();
	@ignored_id = ();


	# Clear hash for ny bruker
	%hash_ko2_ = (); 

	# Henter på nytt alle meldingen til denne personen

	$ko = "SELECT smsutko.id,melding FROM smsutko,bruker WHERE bruker.id=smsutko.brukerid AND sendt=\'N\' AND tlf=\'$user\'"; 

	&sjekk_conn;
	$ok = &db_select($conn,$ko);

	# Hvis der var noe flere meldinger legges de i en hash
	if ($ok->ntuples) {
	    while ( @line = $ok->fetchrow) {
		$hash_ko2_{$line[0]} = $line[1];
	    }
	}


	$meld_nr = 1;
	$ant_ignored = 0;
	$text_ = "";

	foreach $id (keys %hash_ko2_) {

	    # Meldinger som sendes til personen
	    if ((length($text_) + length($hash_ko2_{$id})) < 136) {
		if ($meld_nr eq '1') {
		    $text_ = $hash_ko2_{$id};
		}
		elsif ($meld_nr eq '2') {
		    $text_ = "1:".$text_."\\;  2:".$hash_ko2_{$id};
		}
		else {
		    $text_ = $text_."\\; $meld_nr:".$hash_ko2_{$id};
		}

		$tlf_ = $user;
		push @sendt_id, $id; 

		$meld_nr++;
	    }

	    # Meldinger som ignoreres, en teller dem opp
	    else {
		push @ignored_id, $id;
		$ant_ignored++;
	    }

	}

	# Hvis der er flere en 1 melding til persone
	if ($ant_ignored > 0) {
	    $respons_ = &send_sms($tlf_, $text_." +$ant_ignored se web.");
	}

	# Hvis der kun er en melding til personen
	else {
	    $respons_ = &send_sms($tlf_, $text_);
	}


	# Sjekker om sendingen var vellykket
	if ($respons_ == 0) {

	    if ($smssyk) {
		$smssyk = 0;

		# Skriv logg
		$dato = strftime "%d\.%m\.%Y %H:%M:%S", localtime;
		print LOGFIL "\nsmsd_up: $dato\tExit-code: $respons_\n";

		sendmail($MAILDRIFT, 'Re: Feil på smsd',
			 "\nsmsd_ok: $dato\tExit-code: $respons_\n");
	    }

	    $dato = strftime "%d\.%m\.%Y %H:%M:%S", localtime;

	    # Teller antall velykkede sendte meldinger
	    $smsid++;

	    # Setter meldingen lik sendt i databasen
	    $nr1 = $#sendt_id - 1;
	    while (@sendt_id) {
		$id_ = pop @sendt_id;

		$ko2 = "UPDATE smsutko SET sendt=\'Y\',smsid=\'$smsid\',tidsendt=NOW() WHERE id=\'$id_\'";

		&sjekk_conn;
		$ga = &db_execute($conn,$ko2);

		# Skriv til logg
		if ($nr1 == $#sendt_id) {
		    print LOGFIL "Sendt: $dato\t$user\t$hash_ko2_{$id_}\n";
		}
		else {
		    print LOGFIL "  Sendt: $dato\t$user\t$hash_ko2_{$id_}\n";
		}

		unless ($ga) {
		    print LOGFIL "Database error: $dato\tUnable to mark message as sent, terminating!\n";
		    sendmail($MAILDRIFT, 'Feil på smsd',
			     "\nDatabase error: $dato\tUnable to mark message as sent, terminating!\n");
		    exit(1);
		}

	    }

	    # Setter meldingen lik ignored i databasen
	    while (@ignored_id) {
		$id_ = pop @ignored_id;

		$ko2 = "UPDATE smsutko SET sendt=\'I\',smsid=\'$smsid\',tidsendt=NOW() WHERE id=\'$id_\'";
		&sjekk_conn;
		$ga = &db_execute($conn,$ko2);

		# Skriv til logg
		print LOGFIL "  Ignored: $dato\t$user\t$hash_ko2_{$id_}\n";
	    }

	}
	else {

	    unless ($smssyk) {

		$smssyk = 1;

		# Skriv logg
		$dato = strftime "%d\.%m\.%Y %H:%M:%S", localtime;
		print LOGFIL "\nError: $dato\tExit-code: $respons_\n";

		sendmail($MAILDRIFT, 'Feil på smsd',
			 "\nError: $dato\tExit-code: $respons_\n");

		# Resetter gnokii programmet
		# $respons_ = `killall gammu`;
		# Ble tidligere brukt til å drepe gnokii dersom flere
		# utgaver av programmet kjørte samtidig og slåss om
		# com-porten.

	    }		

	    sleep 60;
	}


    }
    
    close(LOGFIL);
    
    # Sjekker om det har kommet noen nye meldinger i mens en har holdt på å sende.
    &sjekk_ko;
}



sub send_sms {

    my ($tlf, $text) = @_;

    $dato = strftime " %d\/%m %H:%M", localtime; 
    $text = $text.$dato;

    # We need to fork off another process to open the pipe to the
    # dispatcher.  This is becase the alarm setup won't work when
    # spawning a new process through the system (or open) call.  If
    # the spawned process hangs, the close() call blocks our process
    # forever, and the alarm is never sent/received.  The idea is to
    # fork off another smsd.pl and wait for that to exit instead. If
    # this process times out, wekill the entire process group
    # (something along those lines).  A message is mailed to the
    # admin, and safe_smsd will start the daemon again on its next
    # run.
    my $forkpid = fork();
    if ($forkpid == 0) {
	# I am the child process...
	$0 = 'SMSD Dispatcher Process';
	open(my $PIPE, "| $DISPATCHER nothing --sendsms TEXT $tlf 1>/dev/null 2>/dev/null")
	    or die "Unable to run $DISPATCHER ($!, $?)";
	print $PIPE $text;
	close($PIPE);

	# Exit this forked subprocess, using the exit value of the sms
	# dispatcher.
	exit($?);
    } else {
	# I am the parent process
	my $err_code = 0;

	# Alarm setup that will wait no longer than $FREEZELIMIT
	# seconds for our forked process to exit,
	eval {
	    local $SIG{ALRM} = sub { die "alarm\n" };
	    alarm($FREEZELIMIT);
	    # Blocking wait for child processes.
	    if (wait() >= 0) {
		$err_code = $? >> 8;
	    } else {
		$err_code = 6969;
	    }
	    alarm(0);
	};

	if ($@) {
	    print STDERR "Dispatcher froze";

	    # Log the event
	    my $date = strftime "%d\.%m\.%Y %H:%M:%S", localtime;
	    print LOGFIL "\nError: $date\t$DISPATCHER froze, killing process (including sms daemon)\n";
	    close(LOGFIL);

	    sendmail($MAILDRIFT, 'Feil på smsd',
		     "\nError: $date\t$DISPATCHER froze, killing process (including sms daemon)\n");

	    # Send a KILL signal to pid 0.  This is the only efficient
	    # way I found to kill all processes created by this
	    # process and its children. The SMS Daemon itself will
	    # also be killed, but safe_smsd should revive it on its
	    # next run.
	    unless (kill('KILL', 0)) {
		$date = strftime "%d\.%m\.%Y %H:%M:%S", localtime;
		sendmail($MAILDRIFT, 'Feil på smsd', 
			 "\nError: $date\tWas UNABLE to signal my dispatcher subprocess!\n");
		print STDERR " - Failed to kill it\n";
		# Never thought of this happening...
		exit(6969);
	    }
	} else {
	    # For some reason, we need to explicitly reset the
	    # database connection here after doing a wait() system
	    # call.  It seems the connection to the database is lost,
	    # and the sjekk_conn() subroutine seems to not do any
	    # good when this particular situation arises.
	    $conn->reset;
	    return $err_code;
	}
    }
}

##################################

sub sjekk_conn
{
    my $status = $conn->status;

    unless ($status == PGRES_CONNECTION_OK)
    {
	my $errorMessage = $conn->errorMessage;
	my $resolve = "$status Reset";
	$conn->reset;
	$status = $conn->status;
	$resolve = "$status Unable to reset!" unless ($status == PGRES_CONNECTION_OK);

	my $dato_ = strftime "%d\.%m\.%Y %H:%M:%S", localtime; 
	sendmail($MAILDRIFT, 'smsd database connection problem',
		 "\nStatus: $dato_\t$conn\t $resolve\n\nError was:\n$errorMessage");

    }
}
##################################

sub justme {
	my $pid;

	if (open PIDFIL, "<$pidfil") {
        $pid = <PIDFIL>;
	if ($pid =~ /([0-9]+)/) {
	    $pid = $1;
	    kill(0, $pid) and die "\n$0 already running (pid $pid), bailing out\n\n";
	} else {
	    die "\nPidfile was corrupt, cannot detect whether we are already running, bailing out\n";
	}
        close PIDFIL;
    }
}

##################################

# Finn alle de ekstra gruppene en navngitt bruker er medlem av.
sub usergroups
{
    my $uname = shift;
    my @gids;

    while (my($name, $passwd, $gid, $members) = getgrent()) {
	push(@gids, $gid) if ($members =~ /\b$uname\b/);
    }

    return "@gids";
}

# Dersom vi kjører som noen andre enn navcron-brukeren, prøver vi å
# tvinge oss selv til å kjøre som denne. Dette vil kun fungere dersom
# root er den som kjører scriptet.
sub switchuser
{
    if (getpwnam('navcron')) {
	my ($name,$passwd,$uid,$gid,
	    $quota,$comment,$gcos,$dir,$shell,$expire) = getpwnam('navcron');
	if ($UID != $uid) {
	    my $gids = usergroups('navcron');
	    $GID = "$gid $gids";
	    $UID = $uid;
	    $EGID = "$gid $gids";
	    $EUID = $uid;

	    #print "DEBUG: UID=$UID,GID=$GID,EUID=$EUID,EGID=$EGID\n";

	    $UID == $uid or die "Kan ikke skifte til bruker navcron!";
	}
    } else {
	# Dersom navcron ikke eksisterer på systemet:
	print STDERR "Advarsel! Kjører med root-privilegier!\n";
    }
}

sub sendmail ($$$)
{
    my($address, $subject, $body) = @_;

    open(MAIL, "|mail -s '$subject' $address");
    print MAIL $body;
    close(MAIL);
}

exit(0);
