#!/usr/bin/perl
## Name:	arpdblogger
## $Id: arplogger.pl,v 1.5 2001/09/21 15:44:45 gartmann Exp $
## Author:	Stig Venaas   <venaas@itea.ntnu.no>
## Uses some code from test/arp by Simon Leinen. test/arp is distributed
## with the Perl SNMP library by Simon Leinen <simon@switch.ch> that
## we are using.
## Description:	Print changes in arp caches from previous run
######################################################################
## Usage: arp hostname [community]
##        arp {argument} [argument] ...
##        
##        argument:
##        { -f file } | { hostname community }
##
##        The lines in file must have the following format:
##        [ hostname [community] ]
##
## Extracts each HOSTNAME's network to media address table using SNMP
##
##

require 5.002;
use strict;

use SNMP_Session "0.57"; 

#use SNMP_util;

use BER;
use Pg;

# ipNetToMediaPhysAddress
#my $ip2mac = '.1.3.6.1.2.1.4.22.1.2';

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
my %gwport;


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

my $db = "manage";
my $conn = db_connect($db);


my $sql = "SELECT boksid,ip,ro FROM boks WHERE kat=\'GW\'";

#print "$sql\n";

my $resultat = db_select($sql,$conn);

while(my @line = $resultat->fetchrow) 
{
    push(@arguments,$line[0],$line[1],$line[2]);
}


$sql = "SELECT prefiksid,nettadr FROM prefiks"; 

$resultat = db_select($sql,$conn);

while (my @line = $resultat->fetchrow) 
{
    $prefiksdb{$line[1]} = $line[0];
}

$sql = "SELECT boksid,ifindex,prefiksid FROM gwport";
$resultat = db_select($sql,$conn);

while (my @line = $resultat->fetchrow) 
{
    $gwport{$line[0]}{$line[1]}{$line[2]}++;
}




#exit();


# Main program

while (@arguments) 
{
    $avsluttes =0;
    $oppdat = 0;
    $nye = 0;

    $hostid    = shift @arguments;  
    $hostname  = shift @arguments;
    $community = shift @arguments;

    my $filnavn = $sti."arpdb_".$hostname;

    print "Couldn't open SNMP session to $hostname\n" && next
	unless ($session = SNMP_Session->open ($hostname, $community, 161));
    dbmopen (%arptable, "$filnavn", 0644)
	|| print "Couldn't open $filnavn\n" && next;
    %arptable_new = ();

    $session->map_table ([$OIDS{'ipNetToMediaPhysAddress'}],
			 \&process_arp_entry);
    $session->close ();

    # Avslutter records som ikke ble funnet på ruter denne runden.

    my $ip = '';
    foreach $ip (keys %arptable) 
    { 

	my $sql = "UPDATE arp SET til=NOW() WHERE ip =\'$ip\' AND mac=\'$arptable{$ip}\' AND boksid=\'$hostid\' AND til IS NULL";
	$avsluttes++;
	db_execute($sql,$conn);
	
    }
    
    %arptable=%arptable_new;
    dbmclose (%arptable);

#    print "$hostname\tnye:$nye\toppdaterte:$oppdat\tAvsluttet:$avsluttes\n";


    $tot_nye += $nye;
    $tot_oppdat += $oppdat;
    $tot_avs += $avsluttes;

}


#print "TOTALT\t$tot_nye\t$tot_oppdat\t$tot_avs\n";

#$dbh->disconnect;
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


#  print "$hostname\t$ip\t$prefiksid\t";

#  if ($prefiksid == 0)
#  {
#      print "Finner ikke prefiks for $ip\n";
      
  unless (exists $gwport{$hostid}{$ifIndex}{$prefiksid})
  {
      print "Feil prefiks: $ip\t$prefiksid\t$hostname.\n";
#      print "Feil\n";
  }
  else  # prefiksid funnet og er ok, skal legges inn
  {
#      print "Legges inn\n";
      $arptable_new{$ip} = hex_string($mac);
      
      if (defined( $arptable{$ip} )) {
	  if ($arptable{$ip} ne $arptable_new{$ip}) {
	      
	      # Avslutte gammel record. 
	      my $sql1 = "UPDATE arp SET til=NOW() WHERE ip =\'$ip\' AND mac=\'$arptable{$ip}\' AND boksid=\'$hostid\' AND til IS NULL"; 
#               print "$sql1\n";                 
	      db_execute($sql1,$conn);
	      
	      # Legge inn ny record.
	      my $sql2 = "INSERT INTO arp (boksid,prefiksid,ip,mac,fra) VALUES (\'$hostid\',\'$prefiksid\',\'$ip\',\'$arptable_new{$ip}\',NOW())";
#               print "$sql2\n";
	      db_execute($sql2,$conn);
	      
	      $oppdat++;
	      
	  }
	  delete $arptable{$ip};
      } 
      else # ikke i %arptable fra før: legg inn.
      {
	  # Legge inn ny record.
	  my $sql2 = "INSERT INTO arp (boksid,prefiksid,ip,mac,fra) VALUES (\'$hostid\',\'$prefiksid\',\'$ip\',\'$arptable_new{$ip}\',NOW())";
#           print "$sql2\n";
	  db_execute($sql2,$conn);
	  
	  $nye++;
      }
  }
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


sub db_connect {
    my $db = $_[0];
    my $conn = Pg::connectdb("dbname=$db user=navall password=uka97urgf");
    die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
}
sub db_select {
    my $sql = $_[0];
    my $conn = $_[1];
    my $resultat = $conn->exec($sql);
    die "DATABASEFEIL: $sql\n".$conn->errorMessage
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
