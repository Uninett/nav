#!/usr/bin/env perl
#
# alertengine.pm
#
#    This just daemonizes the alertEngine functionality.  Responsible
# for starting and stopping alertEngine.
#
# Copyright 2002, 2003 UNINETT AS
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
# Authors: Andreas Aakre Solberg, UNINETT
#          Arne Øslebø, UNINETT
#

package AlertEngine;

use warnings;
use strict;
use diagnostics;
use POSIX qw(setsid);
use IO::Handle;

use Engine;

#BEGIN {require "alertengine.cfg";}

####################################################
## Engine 
####################################################


sub runEngine() {

	my $e = Engine->new($Log::cfg);
	$e->run();

}

####################################################
## Engine management
####################################################

sub launch() {
    my $logfile=shift;
    my $pidfile=shift;

	if (-f $pidfile) {
	    open pid_file, '< '.$pidfile ||
		die "Cannot open pidfile";
	    my ($pid, $tid) = split / /, <pid_file>;
	    close(pid_file);
	    open ps_file, "ps -e | grep $pid | wc -l|";
	    my $count=<ps_file>;
	    close(ps_file);
	    if($count==0) {
		unlink($pidfile) ||
		    die "Could not delete pidfile\n";
	    } else {
		print "It seems like alertengine is already running.\n";
		exit(0);
	    }
	}

	print "Starting alertengine...\n";
	
	chdir '/' ||
		die "Can't chdir to /: $!";
	umask 0;
	
	open STDIN, '/dev/null' ||
		die "Can't read /dev/null: $!";
		
	open STDOUT, '>> '.$logfile || 
		die "Can't write to /dev/null: $!";
	
	open STDERR, '>> '.$logfile || 
		die "Can't write to /dev/null: $!";

    select(STDOUT);
    
	my $pid = 0;
	if ($pid = fork()) {
	    print "PID: $pidfile\n";
		open pid_file, '> '.$pidfile || die "Could not open pid file $pidfile";
		print pid_file $pid . " " . time();
		close(pid_file);
		exit(0);
	}
	if ($pid < 0) { die "Can't fork: $!"; }
	
	setsid || 
		die "Can't start a new session: $!";


	&runEngine();
}

sub datediff() {
	my $diff = shift;
	
	my $secs = $diff % 60;
	$diff = ($diff - $secs) / 60;
	
	my $mins = $diff % 60;
	$diff = ($diff - $mins) / 60;	

	my $hrs = $diff % 60;
	$diff = ($diff - $hrs) / 60;
	
	my $days = $diff;
	
	my $ds = "";
	
	if ($days > 0) {
		$ds = $days . " days and " . $hrs . " hours";
	} elsif ($hrs > 0) {
		$ds = $hrs . " hours and " . $mins . " minutes";
	} else {
		$ds = $mins . " minutes and " . $secs . " seconds";
	}
	return $ds;
}

sub stop() {
    my $pidfile=shift;
	if (-f $pidfile) {
		open pid_file, '< '.$pidfile ||
			die "Cannot open pidfile";
		my ($pid, $tid) = split / /, <pid_file>;
		close(pid_file);
		open ps_file, "ps -e | grep $pid | wc -l|";
		my $count=<ps_file>;
		close(ps_file);
		if($count==0) {
		    print "Alertengine is not running.\n";
		    unlink($pidfile) ||
			die "Could not delete pidfile\n";
		    return(0);
		}
		my $dif = time() - $tid;
		unlink($pidfile) ||
			die "Could not delete pidfile\n";
		print "Trying to stop alertengine. It has been running for " . &datediff($dif) . ".\n";
		print "Please wait for it to gracefully flush queue to database etc...\n";
		my $status = kill 15 => $pid;
		if ($status > 0) {
			print "Alertengine is successfully shut down.\n";
		} else {
			print "Sorry, could not shut down alertengine.\n";
		}
		
	} else {
		print "Alertengine is not running.\n";
	}

}


sub status() {
    my $pidfile=shift;
    if (-f $pidfile) {
	open pid_file, '< '.$pidfile ||
	    die "Cannot open pidfile";
	my ($pid, $tid) = split / /, <pid_file>;
	close(pid_file);
	open ps_file, "ps -e | grep $pid | wc -l|";
	my $count=<ps_file>;
	close(ps_file);
	if($count>0) {	   
	    print "Alertengine is running with process id $pid.\n";
	    my $dif = time() - $tid;
	    print "It has been running for " . &datediff($dif) . ".\n";
	} else {
	    print "Alertengine is not running.\n";
	    unlink($pidfile) ||
		die "Could not delete pidfile\n";
	}
    }     
    else {
	print "Alertengine is not running.\n";
    }
    
}


####################################################
## Main
####################################################

$_ = shift @ARGV || 'start';
my $pidfile=$Log::cfg->{pidfile};

SWITCH : {
    /^start$/ && do { &launch($Log::cfg->{logfile},$pidfile); last; };
    /^restart$/ && do { &stop($pidfile); &launch($Log::cfg->{logfile},$pidfile); last; };
    /^stop$/ && do { &stop($pidfile); last; };
    /^status$/ && do { &status($pidfile); last; };    
    print <<END
Usage: alertengine.pl [option]

[option] :
	start	- launch alertengine if not already running
	stop	- stops alertengine if running
	restart	- stops alertenige if running, and then launch it
	status	- tells if alertengine is running or not

END
}


