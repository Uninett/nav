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
# Contains common subroutines for all NAV perl scripts.
#
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#          Morten Vold <morten.vold@itea.ntnu.no>
#
package NAV;

require Exporter;
use strict;
use Pg;
use NAV::Path;

our @ISA = qw(Exporter);
our @EXPORT = qw(config connection execute select);
our @EXPORT_OK = qw(config connection execute select);

#
# Parse a config file with VAR=VALUE assignments, ignoring
# leading/trailing whitespace and comments.  Return the result as a
# hash.
#
sub config {
    my $conffile = shift or return undef;

    open(my $FD, $conffile) || die "Could not open $conffile: $!\n";
    my %hash = map { /\s*(.+?)\s*=\s*(.*?)\s*(\#.*)?$/ && $1 => $2 } 
    grep { !/^(\s*\#|\s+)$/ && /.+=.*/ } <$FD>;
    close($FD);

    return %hash;
}

#
# Return an open database connection, using db.conf as the
# configuration source.  First parameter is the name of the script (to
# look for in db.conf), second parameter is the idname of the database
# to connect to (if omitted, 'manage' is used).
#
sub connection {
    my $myself = shift;
    my $mydb = shift || 'manage';

    my %hash = &config("$NAV::Path::sysconfdir/db.conf");
			
    my $db_user = $hash{'script_'.$myself} || $hash{'script_default'};
    unless ($db_user) {
	die "No database configuration for $myself or default in db.conf";
    }
    my $db_passwd = $hash{'userpw_'.$db_user};
    unless($db_passwd){
	die "No password found for user $db_user in db.conf";
    }
    my $db_db = $hash{'db_'.$mydb} || $hash{'db_nav'};
    my $db_host = $hash{'dbhost'};
    my $db_port = $hash{'dbport'};
						    
    my $conn = Pg::connectdb("host=$db_host port=$db_port dbname=$db_db user=$db_user password=$db_passwd");
    die $conn->errorMessage unless &PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
}

#
# Execute an SQL statement and return the status code from the
# backend.
#
sub execute {
    my $sql = $_[1];
    my $conn = $_[0];
    if($sql =~ /^\s*(select)/i){
	my $resultat = $conn->exec($sql);
	return $resultat;
    } else {

	my $resultat = $conn->exec($sql);
	unless ($resultat->resultStatus eq (&PGRES_COMMAND_OK||&PGRES_TUPLES_OK)){
	    die($conn->errorMessage);
	}
	return 1;
    }
}

#
# Execute an SQL SELECT-statement and return the result set.
#
sub select {
    my $sql = $_[1];
    my $conn = $_[0];
    my $resultat = $conn->exec($sql);
    return $resultat;
}
