#! /usr/bin/perl -w
#
# alertengine.pm
#
#    Dette er bare daemon innpakninga. Den starter og stopper alertengine.
#
# (author) Andreas Aakre Solberg, Aug 2002

package AlertEngine;

use strict;
use diagnostics;
use POSIX qw(setsid);

use Engine;

BEGIN {require "alertengine.cfg";}


####################################################
## Engine 
####################################################


sub runEngine() {

	my $e = Engine->new($cfg);
	$e->run();

}

####################################################
## Engine management
####################################################

sub launch() {

	if (-f '/tmp/alertengine.pid') {
		print "It seems like alertengine is already running.\n";
		exit(0);
	}

	print "Starting alertengine...\n";
	
	chdir '/' ||
		die "Can't chdir to /: $!";
	umask 0;
	
	open STDIN, '/dev/null' ||
		die "Can't read /dev/null: $!";
		
	open STDOUT, '>>/tmp/alertengine.debug' || 
		die "Can't write to /dev/null: $!";
	
	open STDERR, '>>/tmp/alertengine.debug' || 
		die "Can't write to /dev/null: $!";

	my $pid = 0;
	if ($pid = fork()) {
		open pid_file, '>/tmp/alertengine.pid';
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

	if (-f '/tmp/alertengine.pid') {
		open pid_file, '</tmp/alertengine.pid' ||
			die "Cannot open pidfile";
		my ($pid, $tid) = split / /, <pid_file>;
		close(pid_file);
		my $dif = time() - $tid;
		unlink('/tmp/alertengine.pid') ||
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
	if (-f '/tmp/alertengine.pid') {
		open pid_file, '</tmp/alertengine.pid' ||
			die "Cannot open pidfile";
		my ($pid, $tid) = split / /, <pid_file>;
		close(pid_file);
		print "Alertengine is running with process id $pid.\n";
		my $dif = time() - $tid;
		print "It has been running for " . &datediff($dif) . ".\n";
	} else {
		print "Alertengine is not running.\n";
	}

}


####################################################
## Main
####################################################

$_ = shift @ARGV || 'start';

SWITCH : {
    /^start$/ && do { &launch(); last; };
    /^restart$/ && do { &stop(); &launch(); last; };
    /^stop$/ && do { &stop(); last; };
    /^status$/ && do { &status(); last; };    
    print <<END
Usage: alertengine.pl [option]

[option] :
	start	- launch alertengine if not already running
	stop	- stops alertengine if running
	restart	- stops alertenige if running, and then launch it
	status	- tells if alertengine is running or not

END
}


