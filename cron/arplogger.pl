#!/usr/bin/perl
## Name:	arplogger.pl
## $Id: arplogger.pl,v 1.10 2002/07/12 06:45:23 mortenv Exp $
## Author:	Stig Venaas   <venaas@itea.ntnu.no>
## Uses some code from test/arp by Simon Leinen. test/arp is distributed
## with the Perl SNMP library by Simon Leinen <simon@switch.ch> that
## we are using.
##
## Modified by grohi@itea.ntnu.no, Aug/Sept/Oct 2001
######################################################################

# * asks the database for data (which gw's to get arp from++)
# * asks each gw for it's 
# * checks with existing records in the database manage, the arp table
#   - inserts new records unless already inserted
#   - terminates old records where the ip<->mac comb. was not found 
#   - leaves the rest unchanged

require 5.002;
use strict;

use SNMP_Session "0.57"; 

use BER;
use Pg;

my @arguments;
my $filename;
my $dbh;
my $hostname;
my $community;
my $hostid;
my $session;
my %arptable;
my %arptable_new;
my $cursor;
my $stat;
my %prefiksdb;
my %prefiks2boks;
my %gwport;
my %arpid;
my %sysName;

my $avsluttes;
my $oppdat;
my $nye;

my $tot_avs=0;
my $tot_oppdat=0;
my $tot_nye=0;

my $sti = '/usr/local/nav/log/arp/';

my %OIDS = (
	    'ipNetToMediaPhysAddress' => [1,3,6,1,2,1,4,22,1,2],
	    'ipNetToMediaType' => [1,3,6,1,2,1,4,22,1,4],
	    );


# Hente aktuelle rutere fra databasen.

my %dbconf = &db_readconf();
my $db = $dbconf{db_nav};
my $dbuser = $dbconf{script_arplogger};
my $dbuserpw = $dbconf{'userpw_' . $dbuser};
my $conn = db_connect($db, $dbuser, $dbuserpw);


my $sql = "SELECT boksid,ip,ro,sysName FROM boks WHERE kat=\'GW\'";

my $resultat = db_select($sql,$conn);

while(my @line = $resultat->fetchrow) 
{
    push(@arguments,$line[0],$line[1],$line[2]);
    $sysName{$line[0]} = $line[3];
}


#$sql = "SELECT prefiksid,nettadr FROM prefiks"; 

$sql = "SELECT boksid,prefiksid,nettadr FROM gwport JOIN prefiks USING (prefiksid) WHERE gwportid=rootgwid"; 

$resultat = db_select($sql,$conn);

while (my @line = $resultat->fetchrow) 
{
    $prefiksdb{$line[2]} = $line[1];

    $prefiks2boks{$line[1]} = $line[0];

}

$sql = "SELECT boksid,ifindex,prefiksid FROM gwport";
$resultat = db_select($sql,$conn);

while (my @line = $resultat->fetchrow) 
{
    $gwport{$line[0]}{$line[1]}{$line[2]}++;
}

$sql= "SELECT arpid,boksid,ip,mac FROM arp WHERE til='infinity'"; 

$resultat = db_select($sql,$conn);

while (my @line = $resultat->fetchrow) 
{
    $arpid{$line[1]}{$line[2]}{$line[3]} = $line[0];
    $arptable{$line[1]}{$line[2]} = $line[3];
}

# Main program

while (@arguments) 
{
    $avsluttes =0;
    $oppdat = 0;
    $nye = 0;

    $hostid    = shift @arguments;  
    $hostname  = shift @arguments;
    $community = shift @arguments;

#    print "Henter fra $hostname\n";

    print "Couldn't open SNMP session to $hostname\n" && next
	unless ($session = SNMP_Session->open ($hostname, $community, 161));
 
   %arptable_new = ();

    $session->map_table ([$OIDS{'ipNetToMediaPhysAddress'}],
			 \&process_arp_entry);
    $session->close ();

    # Avslutter records som ikke ble funnet på ruter denne runden.

    my $ip = '';
    foreach $ip (keys %{$arptable{$hostid}}) 
    { 
#	print "$ip\n";

	my $sql = "UPDATE arp SET til=NOW() WHERE arpid = \'$arpid{$hostid}{$ip}{$arptable{$hostid}{$ip}}\'"; 

	$avsluttes++;
	db_execute($sql,$conn);
	
    }
    
#    print "$hostname\tnye:$nye\toppdaterte:$oppdat\tAvsluttet:$avsluttes\n";


    $tot_nye += $nye;
    $tot_oppdat += $oppdat;
    $tot_avs += $avsluttes;

}


#print "TOTALT\t$tot_nye\t$tot_oppdat\t$tot_avs\n";

1;

##
sub process_arp_entry ($$$) {
    
    my ($index, $mac, $type) = @_;
    
    ## the index of this table has the form IFINDEX.IPADDRESS, where
    ## IPADDRESS is a "dotted quad" of four integers.  We simply split
    ## at the first dot to get the interface index and the IP address in
    ## readable notation:
    ##
    
    my ($ifIndex, $ip) = split(/\./, $index, 2);
    
    my $prefiksid = getprefiks($ip);
    
    
    
#    if (exists $gwport{$hostid}{$ifIndex}{$prefiksid})
#    {
#      print "Legges inn: $ip\n";

	$arptable_new{$ip} = hex_string($mac);
	
	if (defined( $arptable{$hostid}{$ip} )) {

#	    print "gml: $ip fra *$arptable{$hostid}{$ip}* til *$arptable_new{$ip}*\n";

	    if ($arptable{$hostid}{$ip} ne $arptable_new{$ip}) {
	      
#		print "IKKE like\n";

	      # Avslutte gammel record. 
	      my $sql1 = "UPDATE arp SET til=NOW() WHERE arpid = \'$arpid{$hostid}{$ip}{$arptable{$hostid}{$ip}}\'"; 
#               print "AVSLUTT: $sql1\n";                 
	      db_execute($sql1,$conn);
	      
	      # Legge inn ny record.
	      if ($prefiks2boks{$prefiksid} == $hostid)
	      {
		  my $sql2 = "INSERT INTO arp (boksid,prefiksid,ip,ip_inet,mac,kilde,fra) VALUES (\'$hostid\',\'$prefiksid\',\'$ip\',\'$ip\',\'$arptable_new{$ip}\',\'$sysName{$hostid}\',NOW())";
#               print "$sql2\n";
		  db_execute($sql2,$conn);
	      }
	      $oppdat++;
	      
	  }
	  delete $arptable{$hostid}{$ip};
      } 
      else # ikke i %arptable fra før: legg inn.
      {
#	  print "LIKE\n";

	  # Legge inn ny record.
	  if ($prefiks2boks{$prefiksid} == $hostid)
	  {
	      my $sql2 = "INSERT INTO arp (boksid,prefiksid,ip,ip_inet,mac,kilde,fra) VALUES (\'$hostid\',\'$prefiksid\',\'$ip\',\'$ip\',\'$arptable_new{$ip}\',\'$sysName{$hostid}\',NOW())";
#           print "NY: $sql2\n";
	      db_execute($sql2,$conn);
	      $nye++;
	  }
      }
#  }
}

##############################################

sub getprefiks
{
    # Tar inn ip, splitter opp og and'er med diverse
    # nettmasker. Målet er å finne en match med en allerede innhentet
    # prefiksid (hash over alle), som så returneres.

    my $ip = $_[0];
    
    my @masker = ("255.255.255.255","255.255.255.254","255.255.255.252","255.255.255.248","255.255.255.240","255.255.255.224","255.255.255.192","255.255.255.128","255.255.255.0","255.255.254.0","255.255.252.0");

    my $netadr;
    my $maske;

    foreach $maske (@masker)
    {
	$netadr = and_ip($ip,$maske);
	
	return $prefiksdb{$netadr} if (defined $prefiksdb{$netadr});
    }

#    print "Fant ikke prefiksid for $ip\n";
    return 0;
}

###############################################

sub and_ip
{
    my @a =split(/\./,$_[0]);
    my @b =split(/\./,$_[1]);
    
    for (0..$#a) {
        $a[$_] = int($a[$_]) & int($b[$_]);
    }
    
    return join(".",@a);
}

###############################################

sub db_readconf {
    my $dbconf = '/usr/local/nav/local/etc/conf/db.conf';

    open(IN, $dbconf) || die "Could not open $dbconf: $!\n";
    my %hash = map { /\s*(.+?)\s*=\s*(.*?)\s*(\#.*)?$/ && $1 => $2 } 
    grep { !/^(\s*\#|\s+)$/ && /.+=.*/ } <IN>;
    close(IN);

    return %hash;
}

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
sub db_execute {
    my $sql = $_[0];
    my $conn = $_[1];
    my $resultat = $conn->exec($sql);
    print "DATABASEFEIL: $sql\n".$conn->errorMessage
        unless ($resultat->resultStatus eq PGRES_COMMAND_OK);
    return $resultat;
}
