#!/usr/bin/env perl
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
# $Id$
# This script runs from cron to check that the SMS Daemon is up and
# running.  If the daemon is gone, while the pidfile remains, it
# is restarted, and a mail is sent to the NAV administrator.
#
# Authors: Knut-Helge Vindheim <knut-helge.vindheim@itea.ntnu.no>
#
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
