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
# $Id: $
# Retrieves arp tables from network equipment and stores them in the
# database.
#
# Uses some code from test/arp by Simon Leinen. test/arp is
# distributed with the Perl SNMP library by Simon Leinen
# <simon@switch.ch> that we are using.
#
# Authors: Stig Venaas <venaas@itea.ntnu.no>
#          Gro-Anita Vindheim <grohi@itea.ntnu.no>
#
####################

# * asks the database for data (which gw's to get arp from++)
# * asks each gw for it's 
# * checks with existing records in the database manage, the arp table
#   - inserts new records unless already inserted
#   - terminates old records where the ip<->mac comb. was not found 
#   - leave the rest unchanged

require 5.002;
use strict;

use SNMP_Session "0.57"; 

use BER;
use Pg;
use NAV;
use NAV::Path;

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

my %OIDS = (
	    'ipNetToMediaPhysAddress' => [1,3,6,1,2,1,4,22,1,2],
	    'ipNetToMediaType' => [1,3,6,1,2,1,4,22,1,4],
	    );


# Hente aktuelle rutere fra databasen.

my $conn = NAV::connection("arplogger", "manage");

my $sql = "SELECT netboxid,ip,ro,sysname FROM netbox WHERE catid IN ('GW', 'GSW') AND up='y'";

my $resultat = NAV::select($conn, $sql);

while(my @line = $resultat->fetchrow) 
{
    push(@arguments,$line[0],$line[1],$line[2]);
    $sysName{$line[0]} = $line[3];
}


$sql = "select netboxid,prefixid,host(netaddr) from gwportprefix join gwport using (gwportid) join module using (moduleid) join prefix using (prefixid)";

$resultat = NAV::select($conn, $sql);

while (my @line = $resultat->fetchrow) 
{
    $prefiksdb{$line[2]} = $line[1];
    $prefiks2boks{$line[1]} = $line[0];
}

$sql= "SELECT arpid,netboxid,ip,REPLACE(mac::text, ':', '') AS mac FROM arp WHERE end_time='infinity'"; 

$resultat = NAV::select($conn, $sql);

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
	my $sql = "UPDATE arp SET end_time=NOW() WHERE arpid = \'$arpid{$hostid}{$ip}{$arptable{$hostid}{$ip}}\'"; 

	$avsluttes++;
	NAV::execute($conn, $sql);
	
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
            
    $arptable_new{$ip} = hex_string($mac);
    
    if (defined( $arptable{$hostid}{$ip} )) {
	
	if ($arptable{$hostid}{$ip} ne $arptable_new{$ip}) {
	    
# IP er koblet mot en annen macadresse, => vil avslutte gammel
# og legge til ny record.

	    # Avslutte gammel record. 
	    my $sql1 = "UPDATE arp SET end_time=NOW() WHERE arpid = \'$arpid{$hostid}{$ip}{$arptable{$hostid}{$ip}}\'"; 
	    NAV::execute($conn, $sql1);
	    
	    # Legge inn ny record.
	    if ($prefiks2boks{$prefiksid} == $hostid)
	    {
		my $sql2 = "INSERT INTO arp (netboxid,prefixid,ip,mac,sysname,start_time) VALUES (\'$hostid\',\'$prefiksid\',\'$ip\',\'$arptable_new{$ip}\',\'$sysName{$hostid}\',NOW())";
		NAV::execute($conn, $sql2);
	    }
	    $oppdat++;	    
	}
	
# Sletter "behandlede" IP-adresser fra tabellen. De som blir igjen var aktive forrige runde, men er ikke aktive naa.
# De skal derfor slettes. (senere i scriptet).

	delete $arptable{$hostid}{$ip};
	
    } 
    else # ikke i %arptable fra før: nye innslag: legg inn!
    {
	# Legge inn ny record.
	if ($prefiks2boks{$prefiksid} == $hostid)
	{
	    my $sql2 = "INSERT INTO arp (netboxid,prefixid,ip,mac,sysname,start_time) VALUES (\'$hostid\',\'$prefiksid\',\'$ip\',\'$arptable_new{$ip}\',\'$sysName{$hostid}\',NOW())";
	    NAV::execute($conn, $sql2);

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

