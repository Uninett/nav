#!/usr/bin/perl
####################
#
# $Id$
# This file is part of the NAV project.
# This script runs from cron to check that the SMS Daemon is up and
# running.  If the daemon is gone, while the pidfile remains, it
# is restarted, and a mail is sent to the NAV administrator.
#
# Copyright (c) 2001-2003 by NTNU, ITEA
# Authors: Knut-Helge Vindheim <knut-helge.vindheim@itea.ntnu.no>
#
####################
use strict;
use POSIX qw(strftime);
use NAV;
use NAV::Path;

my %navconf = &NAV::config("$NAV::Path::sysconfdir/nav.conf");
my $MAILDRIFT = $navconf{ADMIN_MAIL} || 'postmaster@localhost';
my $pidfil = "$NAV::Path::vardir/run/smsd.pl.pid";
my $dato = strftime "%d\.%m\.%Y %H:%M:%S", localtime; 
my ($pid, $res); 

# Mangler pid filen sjekkes det ikke at smsd kjører. 
if (open PIDFIL, "<$pidfil") {
  	$pid = <PIDFIL>;
	close($pid);

	unless (kill(0, $pid)) { 

	    $res = `$NAV::Path::initdir/smsd restart` || die $!;
	    # Send mail
	    open(MAIL, "|mail -s 'Restartet smsd' $MAILDRIFT");
	    print MAIL "$dato\tstartet smsd på nytt\n";
	    print MAIL "$res\n";
	    close(MAIL);
	}

} 
