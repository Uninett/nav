#!/usr/bin/env perl
#
# $Id$
#
# This script runs as a cron-job and enables all blocked ports where
# the time for autoenabling has been surpassed.
# 
# Copyright 2003-2005 Norwegian University of Science and Technology
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
# Authors: John Magne Bredal <john.m.bredal@ntnu.no>
#

use strict;
use Pg;
use NAV;
use NAV::Path;
use NAV::Arnold;

my %cfg = readconfig();
my $home = $NAV::Path::bindir;

my $logdir = $NAV::Path::localstatedir."/log/arnold";
chomp (my $datetime = `date +%y%m%d-%H%M%S`);
my $logfile = "autoenable.log";


# Connect to the arnold database
my $dbh_block = &NAV::connection('arnold','arnold');


# Get all blocked ports where autoenable is < now
my $query = "SELECT identityid FROM identity WHERE autoenable < now() AND blocked_status ='disabled'";
my $res = $dbh_block->exec($query);

my $results = $res->ntuples;


# If we have any results, enable them.
if ($results > 0) {
    umask (0117);
    open (LOG, ">>$logdir/$logfile") or die ("Could not open $logdir/$logfile: $!\n");
    print LOG "\n\n========== NEW LOGENTRY $datetime ==========\n\n";

    while (my ($id) = $res->fetchrow) {
	enable($id);
    }

    close LOG;
} 


# This sub takes as input the database id of a blocked port and enables it using arnold.
sub enable {

    my $id = shift;

    my $comment = "Enablet automatisk fordi tid for autoenable passert.";
    
    print LOG "Enabler $id.\n";
    `$home/arnold.pl -x enable -i $id -u cron -c "$comment"`;

}
