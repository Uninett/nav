#!/usr/bin/perl

###########################################################################
# Et cron-script som sjekker vert n-min om smsd framdeles kjører. 
# Skulle smsd ha stoppet startes den og det sendes en mail til ansvarlige.
# Skulle noen stoppe smsd og fjerne pid filen fungerer ikke testen.
#
# knutvi@itea.ntnu.no
###########################################################################

use strict;
use POSIX qw(strftime);
require '/usr/local/nav/navme/lib/fil.pl';

my %navconf = &read_navconf();
my $MAILDRIFT = $navconf{ADMIN_MAIL} || 'postmaster@localhost';
my $pidfil = '/usr/local/nav/local/var/run/smsd.pl.pid';
my $dato = strftime "%d\.%m\.%Y %H:%M:%S", localtime; 
my ($pid, $res); 

# Mangler pid filen sjekkes det ikke at smsd kjører. 
if (open PIDFIL, "<$pidfil") {
  	$pid = <PIDFIL>;
	close($pid);

	unless (kill(0, $pid)) { 

	    $res = `/usr/local/nav/navme/etc/init.d/smsd restart` || die $!;
	    # Send mail
	    open(MAIL, "|mail -s 'Restartet smsd' $MAILDRIFT");
	    print MAIL "$dato\tstartet smsd på nytt\n";
	    print MAIL "$res\n";
	    close(MAIL);
	}

} 
