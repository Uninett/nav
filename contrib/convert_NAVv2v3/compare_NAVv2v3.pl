#!/usr/local/perl

####################################### 
# compare_NAVv2v3.pl: 
#
# syntax: compare_NAVv2v3.pl <v3_dbuser> <v3_dbpwd> <path to v2_nettel.txt> <path to v2_server.txt>
#
# * read v2 nettel.txt and server.txt.
# * compare with content of table netbox in NAVv3 database
#    - if ip in v2 not in v3: print line to insert into editDB
#    - if ip in v2 and v3, but different roomid or catagory: print "EDIT <info>"
#    - if name in server.txt doesn't respond with ip address using gethostbyaddr: print "WARNING: <info>"
#
# Author: grohi@itea.ntnu.no, 21/5-04
#

use Pg;
use Socket;

($dbuser,$dbuserpw,$v2nettel,$v2server)=@ARGV; 

$db = "manage";

# Read nettel.txt v2
open (V2,"< $v2nettel");
while (<V2>) {
    unless (/^#/) {
	    @line = split(/:/);
	    chomp($line[$#line]);
	    $v2{$line[1]}{room} = $line[0];
	    $line[3]='EDGE' if $line[3] eq 'KANT';
	    $line[3]='OTHER' if $line[3] eq 'NAS';
	    $v2{$line[1]}{cat} = $line[3];
	    $v2{$line[1]}{v3line} = "$line[0]:$line[1]:$line[2]:$line[3]:$line[5]::$line[6]::$line[4]";
	}
}
close(V2);

# Read server.txt v2
open (V2,"< $v2server");
while (<V2>) {
    unless (/^#/) {
            @line = split(/:/);
            chomp($line[$#line]);
	    if (defined $line[1]) {
		if(my $ip = gethostbyname($line[1])){
		    $ipa = inet_ntoa($ip);
		    $v2{$ipa}{room} = $line[0];
		    $v2{$ipa}{cat}  = $line[3];
		    $v2{$ipa}{v3line} = "$line[0]:$ipa:$line[2]:$line[3]:$line[5]:$line[1]::$line[6]:$line[4]";
		   print "$line[1]\t$ipa\n"; 
		} else {
		    print "WARNING: host($line[1]) not responding. \n";
		}
	    }
	    
	}
}
    close(V2);
    


# Read table netbox v3

$conn = db_connect($db, $dbuser, $dbuserpw);

$sql = "select ip,roomid,catid from netbox";

$resultat = db_select($sql,$conn);

while (my @line = $resultat->fetchrow) {
    print "$line[0]\n";
    $v3{$line[0]}{room} = $line[1];
    $v3{$line[0]}{cat}  = $line[2];
}



# Compare v2 og v3

print "Missing in NAVv3 database:\n";

foreach $ip (keys %v2) {
    if (exists $v3{$ip}) {
	unless ($v2{$ip}{room} eq $v3{$ip}{room}) {
	    print "EDIT: $ip room v2:$v2{$ip}{room} v3:$v3{$ip}{room}\n";
	}
	unless ($v2{$ip}{cat} eq $v3{$ip}{cat}) {
            print "EDIT: $ip cat v2:$v2{$ip}{cat} v3:$v3{$ip}{cat}\n";
        }
    }
    else
    {
	print "$v2{$ip}{v3line}\n";
    }
}

##################################################################
sub db_connect {
    my($db, $user, $pass) = @_;
    my $conn = Pg::connectdb("dbname=$db user=$user password=$pass");
    die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
}
sub db_select {
    my $sql = $_[0];
    my $conn = $_[1];
    my $resultat = $conn->exec($sql);
    print "DATABASEFEIL: $sql\n".$conn->errorMessage
        unless ($resultat->resultStatus eq PGRES_TUPLES_OK);
    return $resultat;
}
###############################################################

