#!/usr/bin/perl
####################
#
# $Id: gwporter.pl,v 1.15 2002/12/19 10:12:37 gartmann Exp $
# This file is part of the NAV project.
# gwporter uses the SNMP-protocol to aquire information about the routers and
# their interfaces. Information about the subnets (prefices) are also aquired.
# The information is used to update the database.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;
require '/usr/local/nav/navme/lib/NAV.pm';
import NAV qw(:DEFAULT :collect :fil :snmp);

my $localkilde = get_path("path_localkilde");

my $debug = 0;

# tar inn en parameter som er en ip-adresse på formen bokser.pl ip=123.456.789.0
my $one_and_only = shift;

if($one_and_only){ #har sann verdi
    if($one_and_only =~ /^(\d+\.\d+\.\d+\.\d+)$/i){
	$one_and_only = $1;
    } else {
	die("Invalid ip-address: $one_and_only\n");
	$one_and_only = "no";
    }
}
print $one_and_only."\n" if $debug;

&log_open;

my $ip2IfIndex     = ".1.3.6.1.2.1.4.20.1.2"; 
my $ip2NetMask     = ".1.3.6.1.2.1.4.20.1.3"; 
my $ip2ospf        = ".1.3.6.1.2.1.14.8.1.4";
my $ifType         = ".1.3.6.1.2.1.2.2.1.3";
my $if2AdminStatus = ".1.3.6.1.2.1.2.2.1.7";
my $if2Descr       = ".1.3.6.1.2.1.2.2.1.2";
my $if2Speed       = ".1.3.6.1.2.1.2.2.1.5";
my $ifInOctet      = ".1.3.6.1.2.1.2.2.1.10";
my $ifAlias        = ".1.3.6.1.2.1.31.1.1.1.18";
my $hsrp_status    = ".1.3.6.1.4.1.9.9.106.1.2.1.1.15";
my $hsrp_rootgw    = ".1.3.6.1.4.1.9.9.106.1.2.1.1.11";

my $db = &db_get("gwporter");

## active_ip_cnt tatt ut
my @felt_prefix =("netaddr","vlan","max_ip_cnt","nettype","orgid","usageid","netident","to_gw","descr");
my @felt_gwport = ("netboxid","ifindex","gwip","interface","masterindex","speed","ospf");

my (%lan, %stam, %link, %vlan, %hsrp, %undefined_prefices);

#vlaninfo blir innlest fra vlan.txt
&fil_vlan;

#data fra org- og usage- tabellene
my %db_usage = &db_select_hash($db,"usage",["usageid"],0);
my %db_org = &db_select_hash($db,"org",["orgid"],0);

### prefixtabellen
my %prefix = &fil_prefix($localkilde."prefiks.txt",4);
my %db_prefix = &db_select_hash($db,"prefix",\@felt_prefix,0);

### bokser det skal samles inn gwportinfo for
my %bokser;

if($one_and_only){
    %bokser = &db_hent_hash($db,"SELECT netboxid,ip,sysname,up,ro FROM netbox WHERE (catid=\'GW\' OR catid=\'GSW\') AND ip='$one_and_only'");
} else {
    %bokser = &db_hent_hash($db,"SELECT netboxid,ip,sysname,up,ro FROM netbox WHERE (catid=\'GW\' OR catid=\'GSW\')");
}
my %boks2prefix;
# my %prefix; definert i fillesinga fra prefiks.txt

### gwportinnsamling
my (%gwport,%db_gwport);

if($one_and_only){
### Gammel informasjon hentes fra databasen.
    %db_gwport = &db_select_hash($db,"gwport join netbox using (netboxid) WHERE up='y' AND ip='$one_and_only'",\@felt_gwport,0,1,2);
} else {
    %db_gwport = &db_select_hash($db,"gwport join netbox using (netboxid) WHERE up='y'",\@felt_gwport,0,1,2);
}

my %gwip_cnt;
my %netbox_cnt;

### Henter SNMP-info fra ruterne.
foreach my $netboxid (keys %bokser) { #$_ = netboxid keys %boks
    if($bokser{$netboxid}[3] =~ /n|f/i) {
	&skriv("DEVICE-WATCH","ip=".$bokser{$netboxid}[2]);
    } else {
	if ( &hent_snmpdata($bokser{$netboxid}[1],$bokser{$netboxid}[4],$netboxid) eq '0' ) {
	    &skriv("DEVICE-BOXDOWN","ip=".$bokser{$netboxid}[2]);
	}
    }
}

foreach my $netaddr (keys %prefix){
    my $i = $gwip_cnt{$netaddr};
    my $b = $netbox_cnt{$netaddr};
    my $hsrp = $hsrp{$netaddr};
   
    print "\nAutomatisk nettypeavleder for $netaddr ($prefix{$netaddr}[6]) sier:\n$i gwporter til $prefix{$netaddr}[6], fordelt på \n$b bokser,\n" if $debug;
    print "hsrpverdi er $hsrp\n" if $hsrp && $debug;
    print "betyr at vi har en boks av nettype:\n" if $debug;

    my $type = 0;

    if($prefix{$netaddr}[3] eq "ukjent"){
	if(exists $undefined_prefices{$netaddr}){
	    my ($vlan,$writevlan);
	    if($vlan = $undefined_prefices{$netaddr}[0]){
		$writevlan = ",".$undefined_prefices{$netaddr}[0];
	    }
	    my $nettype = $undefined_prefices{$netaddr}[1];
	    my $org = $undefined_prefices{$netaddr}[2];
	    my $usage = $undefined_prefices{$netaddr}[3];
	    my $nettident = "$org,$usage";
	    my $kommentar = $undefined_prefices{$netaddr}[4];

	    $org =~ s/^(\w*?)\d*$/$1/;
	    unless(exists $db_org{$org}){
		$org = "";
	    }

	    $usage =~ s/^(\w*?)\d*$/$1/;
	    unless(exists $db_usage{$usage}){
		$usage = "";
	    }

	    $vlan = "" unless $vlan;
	    $prefix{$netaddr}[1] = $vlan;
	    $prefix{$netaddr}[3] = $nettype;
	    $prefix{$netaddr}[4] = $org;
	    $prefix{$netaddr}[5] = $usage;
	    $prefix{$netaddr}[6] = $nettident;
	    $prefix{$netaddr}[7] = $kommentar;
	    
	}
    }

### Automatisk tnettypeavledning, treffer bare inn hvis type=ukjent
    if($prefix{$netaddr}[3] ne "ukjent"){
### ikke helt ideell:    if($prefix{$netaddr}[3] eq "tildelt" || $prefix{$netaddr}[3] eq "statisk" || $prefix{$netaddr}[3] eq "adresserom" || $prefix{$netaddr}[3] eq "elink") {
	$type = $prefix{$netaddr}[3];
    } elsif($hsrp){
	$type = "lan";
    } elsif ($i==1){
	if($prefix{$netaddr}[3] eq "loopback"){
	    $type = "loopback";
	} else {
	    $type = "lan";
	}
    } elsif($i==2){
	# ikke hsrp
	if($b == 2){
	    $type = "link";
	} else {
	    $type = "lan";
	}
    } else {
	if($b > 2){
	    $type = "stam";
	} else {
	    $type = "lan";
	}
    }
    print "$type\n" if $debug;
    print "FEIL i følge kildefilene, som vil ha det til at dette er et\n".$prefix{$netaddr}[3]."\n" if $type ne $prefix{$netaddr}[3] && $debug;

    $prefix{$netaddr}[3] = $type;

}

### oppdaterer databasen for prefix (uten sletting).
&db_safe(connection => $db,table => "prefix",fields => \@felt_prefix, new => \%prefix,old => \%db_prefix, delete => 0);

#nå som alle prefixene er samlet inn, vil det være på sin plass å sette dem inn i boks.

my %netaddr2prefixid = &db_hent_enkel($db,"SELECT netaddr,prefixid FROM prefix");
#for my $net (sort keys %netaddr2prefixid) {
#    print "|".$net."|".$netaddr2prefixid{$net}."|\n";
#}


if($one_and_only){
&db_safe(connection => $db,table => "gwport",fields => \@felt_gwport,index => ["netboxid","ifindex","gwip"], new => \%gwport,old => \%db_gwport, delete => 0);
} else {
&db_safe(connection => $db,table => "gwport",fields => \@felt_gwport,index => ["netboxid","ifindex","gwip"], new => \%gwport,old => \%db_gwport, delete => 1);
}

# Oppdaterer prefixfeltet i boks.
&oppdater_prefix($db,"netbox","ip","prefixid");

#prefixid i gwport oppdateres her
&oppdater_prefix($db,"gwport","gwip","prefixid");



### trenger å sette rootgwid per prefix til laveste gwip på det prefixet.
my %prefixid2rootgwid = &db_hent_enkel($db,"SELECT prefixid,rootgwid FROM prefix");
my %gwip2gwportid = &db_hent_enkel($db,"SELECT gwip,gwportid FROM gwport");
my %prefixid2gwip =  &db_hent_enkel($db,"select prefixid,min(host(gwip)) from gwport join prefix using (prefixid) where netaddr < gwip group by prefixid");
my %prefixid2prefixid =  &db_hent_dobbel($db,"select prefixid,host(gwip),prefixid from gwport join prefix using (prefixid) where netaddr < gwip");

# Oppdaterer rootgwid

foreach my $prefixid (keys %prefixid2prefixid) {

    my $gammel = $prefixid2rootgwid{$prefixid};
    my $ny;

    foreach my $gwip (keys %{$prefixid2prefixid{$prefixid}}){

	if($hsrp{$gwip}){
	    $ny = $gwip2gwportid{$gwip};
	} 
    }


    unless($ny){
	
	$ny = $gwip2gwportid{$prefixid2gwip{$prefixid}};
	
    }
    unless ($ny eq $gammel) {
#	print $gammel." > ".$ny."\n";
	&db_update($db,"prefix","rootgwid",$gammel,$ny,"prefixid=$prefixid");
    }    
}

## Setter active_ip_cnt. Dette skjer til slutt. Det er dumt, det kunne vært
## gjort underveis.
my %active_ip_cnt = &db_hent_enkel($db,"select prefixid,count(distinct mac) from arp where date_part('days',cast(NOW()-start_time as INTERVAL)) <7 or end_time ='infinity' group by prefixid");
my %db_active_ip_cnt = &db_hent_enkel($db,"select prefixid,active_ip_cnt from prefix");
foreach my $prefixid (keys %db_active_ip_cnt) {
    my $gammel = $db_active_ip_cnt{$prefixid};
    my $ny;
    unless($ny = $active_ip_cnt{$prefixid}){
	$ny = '';
    }
    unless ($ny eq $gammel) {
	&db_update($db,"prefix","active_ip_cnt",$gammel,$ny,"prefixid=$prefixid");
    }
}
&slett_prefix($db);

&log_close;


sub hent_snmpdata {
    my $ip = $_[0];
    my $ro = $_[1];
    my $netboxid = $_[2];

    my %interface = ();
    my %gatewayip = ();
    my %id;
    my %boks;
    print "henter snmpdata for $ip\n\n\n" if $debug;

    my $sess = new SNMP::Session(DestHost => $ip, Community => $ro, Version => 1, UseNumeric=>1, UseLongNames=>1);
    &skriv("DEVICE-COLLECT","ip=$ip");

    my @ifindex = &sigwalk($sess,$ip2IfIndex);
    return(0) unless $ifindex[0];
    foreach my $line (@ifindex) {
        (my $gwip,my $if) = @{$line};
#	print "\n$netboxid:$if:$gwip:",
#	print "...";
	$interface{$if}{gwip} = $gwip;
	$gatewayip{$gwip}{ifindex} = $if;
	print $gwip."\n" if $debug;
    }
    my @alias = &sigwalk($sess,$ifAlias);
    foreach my $line (@alias) {
        (my $if,my $nettnavn) = @{$line};
#	print "nettnavn $nettnavn\n\n";
	$interface{$if}{nettnavn} = $nettnavn;
    }    
    my @inoctet = &sigwalk($sess,$ifInOctet);
    foreach my $line (@inoctet) {                                             
	(my $if,my $octet) = @{$line}; 
	$interface{$if}{octet} = $octet;
#	print "$ip-$if - ".$octet."\n";
#	$gatewayip{0.0.0.0}{ifindex} = $if;
    }    
    my @descr = &sigwalk($sess,$if2Descr);
    my %description;
    my %master;
    my %have_children;
    foreach my $line (@descr) {
        (my $if,my $interf) = @{$line};
	$interface{$if}{interf} = $interf;

	# splitter interface, slik at subinterface er det som kommer 
	# etter et eventuelt punktum
	my ($masterinterf,$subinterf) = $interf =~ /^(\w+\/\w+)?(?:\.(\d+))?/;
	# oppretter masterinterface dersom både subinterface eksisterer
	# og ifInOctet == 0.
	if($subinterf && $interface{$if}{octet}==0){
	    $interface{$if}{master} = $description{$masterinterf};
	    $have_children{$masterinterf} = 1;
	} else {
	    $description{$masterinterf} = $if;
	    $master{$if} = 1;
	}
    } 
    my @netmask = &sigwalk($sess,$ip2NetMask);
    foreach my $line (@netmask)
    {
        (my $gwip,my $netmask) = @{$line};
	my $netaddr = &and_ip($gwip,$netmask);
#	print "\n$gwip & $netmask = ".$gatewayip{$gwip}{netaddr};
	$gatewayip{$gwip}{maske} = my $maske = &mask_bits($netmask);
	$gatewayip{$gwip}{netaddr} = &fil_netaddr($netaddr,$maske);
#	print "\n";
#	print $gwip;
#	print "\n";
#	print $gatewayip{$gwip}{prefixid};
    }
#over: prefix& under: gwport
    my @speed = &sigwalk($sess,$if2Speed);
    foreach my $line (@speed) {
        (my $if,my $speed) = @{$line};
	$speed = ($speed/1e6);
	$speed =~ s/^(.{0,10}).*/$1/; #tar med de 10 første tegn fra speed
	$interface{$if}{speed} = $speed;
    }
    my @adminstatus = &sigwalk($sess,$if2AdminStatus);
    foreach my $line (@adminstatus) {                                             
	(my $if,my $status) = @{$line}; 
	$interface{$if}{status} = $status;
    }
    my @type = &sigwalk($sess,$ifType);
    foreach my $line (@type) {                                             
	(my $if,my $type) = @{$line}; 
	$interface{$if}{type} = $type;
    }
    my @ospf = &sigwalk($sess,$ip2ospf);
    foreach my $line (@ospf) {
        (my $utv_ip,my $ospf) = @{$line};
        if ($utv_ip =~ /\.0\.0$/){
            my (@ip) = split(/\./,$utv_ip);
            my $gwip = "$ip[0].$ip[1].$ip[2].$ip[3]";
            if ($gatewayip{$gwip}{ifindex}){
		$gatewayip{$gwip}{ospf} = $ospf;
#	    print "OSPF $gwip\t$ospf\n";
	    }
        }
    }  
# hsrpgw-triksing
    my @hsrp = &sigwalk($sess,$hsrp_status);
    my %hsrp_temp;
    foreach my $line (@hsrp) {
	(my $if,my $hsrpstatus) = @{$line};
	if($hsrpstatus == 6) {
	    if(my ($rootgwip) = &siget($sess,$hsrp_rootgw.".".$if)){
		($if,undef) = split /\./,$if,2;
#		print "\n$if:$rootgwip:hsrp:",
		$hsrp_temp{$if} = 1;
		#lager gwportrecords for hsrp-adressene.
		$gatewayip{$rootgwip}{ifindex} = $if;
	    }
	}
    }
    foreach my $h (keys %hsrp_temp){
	my $gwip = $interface{$h}{gwip};
	my $netaddr = $gatewayip{$gwip}{netaddr};
	$hsrp{$netaddr} = $hsrp_temp{$h};
    }


    my %allerede_telt;

    ### Lager gwport for ifindexer som ikke ligger i adresseromhash (%gatewayip)

    foreach my $if ( keys %interface ) {
#	print $interface{$if}{status};
	my $interf =$interface{$if}{interf};

	my $netaddr = $gatewayip{$interface{$if}{gwip}}{netaddr};
	
	if($interface{$if}{status} == 1 && $have_children{$interface{$if}{interf}}) {

	    $gwport{$netboxid}{$if}{""} = [ $netboxid,
					    $if,
					    undef,
					    $interface{$if}{interf},
					    $interface{$if}{master},
					    $interface{$if}{speed},
					    undef];
	    unless($allerede_telt{$netaddr}){
		$allerede_telt{$netaddr} = 1;
		$netbox_cnt{$netaddr}++;
	    }

	}
    }

### Lager gwport for ifindexer som ligger i adresseromhash (%gatewayip)
    foreach my $gwip ( keys %gatewayip ) {
#	print "$gwip\n";
	my $if = $gatewayip{$gwip}{ifindex};
	my $interf = $interface{$if}{interf};
#	print $interface{$if}{status};
	if($interface{$if}{status} == 1 && $interf !~ /^EOBC|^Vlan0$/) {

#	if($interface{$if}{status} == 1 && $interface{$if}{type} != 23) {
	    my $ospf = $gatewayip{$gwip}{ospf};
#	print "m|".$interface{$if}{master}."|\n";
	    $gwport{$netboxid}{$if}{$gwip} = [ $netboxid,
					     $if,
					     $gwip,
					     $interf,
					     $interface{$if}{master},
					     $interface{$if}{speed},
					     $ospf];
	    my $netaddr = $gatewayip{$gwip}{netaddr};
	    unless($allerede_telt{$netaddr}){
		$allerede_telt{$netaddr} = 1;
		$netbox_cnt{$netaddr}++;
	    }
	    
	    ### teller opp antall gwip per prefix.
	    $gwip_cnt{$gatewayip{$gwip}{netaddr}}++;

	}
    }


    foreach my $gwip (keys %gatewayip)
    {

	my $if = $gatewayip{$gwip}{ifindex};

	if($interface{$if}{status} == 1 && $gatewayip{$gwip}{netaddr}) {

	my $netaddr = $gatewayip{$gwip}{netaddr};
	my $maxhosts = &max_ant_hosts($gatewayip{$gwip}{maske});
#	my $active_ip_cnt= &ant_maskiner($interface{$if}{gwip},
#						  $netmask)
#						  $maxhosts);

	my $interf = $interface{$if}{interf};
	$_ = &rydd($interface{$if}{nettnavn});
	s/\s+//g;
	
	if(/^(?:lan|stam)/i) {
		my %lanstam = %{&tolk_lanstam($_,$netboxid,$interf)};
		$prefix{$netaddr} = [ $netaddr,
				       $lanstam{'vlan'},  $maxhosts, 
				       $lanstam{'nettype'},$lanstam{'org'},$lanstam{'usage'},
				       $lanstam{'nettident'}, $lanstam{'kommentar'}];

	    } elsif (/^link/i) {

		my %link = %{&tolk_link($_,$netboxid,$interf)};
		$prefix{$netaddr} = [ $netaddr,
				       $link{'vlan'},  $maxhosts,
				       $link{'nettype'}, undef, undef,
				       $link{'nettident'}, $link{'kommentar'}];

	    } elsif (/^elink/i) {

		my %elink = %{&tolk_elink($_,$netboxid,$interf)};
		$prefix{$netaddr} = [$netaddr, 
				      $elink{'vlan'},  $maxhosts,
				      $elink{'nettype'}, $elink{'org'}, undef,
				      $elink{'nettident'}, $elink{'kommentar'}];

	    } elsif ($interf =~ /loopback/i) {
#	    print "har funnet loopback";
		my $nettype = "loopback";
		my $vlan = &riktig_vlan(0,$interf,$ip,$if);
		$prefix{$netaddr} = [ $netaddr,
				       $vlan,  $maxhosts,
				       $nettype, undef, undef,
				       undef, undef ];
	    } else {
#	    print "har funnet ukjent ".$interface{$if}{nettnavn}."\n";

		my $nettype = "ukjent";
		my $vlan = &riktig_vlan(0,$interf,$ip,$if);
		if($prefix{$netaddr}[8]){
		    &skriv("DEBUG-NOOVRWRT", "prefix=".$prefix{$netaddr}[8]);
		} else {
		    

		    $interface{$if}{nettnavn} =~ /^(.{0,50})/;
		    my $nettident = $1;
		    $prefix{$netaddr} = [ $netaddr,
					   $vlan,  $maxhosts,
					   $nettype, undef, undef,
					   $nettident, undef ];
		}
	    }
	}
    }
}
sub fil_vlan{
    open VLAN, "<$localkilde/vlan.txt";
    foreach (<VLAN>){ #finner vlan og putter i nettypehasher

	if(/^(\d+)\:((lan|stam|e?link)\,(\S+?)\,(\S+?))(?:\,(\S+?))?(?:\:(\S+?)\/(\d+))??\s*(?:\#.*)??$/) {
#	    print "$1:$2:$3:$4:$5:$6:$7:$8\n";
	    $lan{$4}{$5} = $1;
	    if($7 && $8){
		$undefined_prefices{&fil_netaddr($7,$8)} = [$1,$3,$4,$5,$6];
	    }
	}
    }
}
sub finn_vlan{
    my $vlan;
    my ($boks,undef) = split /\./,$bokser{$_[1]}[2],2;
    $_ = $_[0];
    
### på formen:   lan,org,usage,komm,vlan
    
    if(/^(?:lan|stam)\d*\,(\S+?)\,(\S+?)(?:\,.*\,(\d+)|\,.*)$/i){
	
	unless($vlan = $3){
	    $vlan = $lan{$1}{$2};
	}
	
    }elsif(/^e?link\,(\S+?)(?:\,.*\,(\d+)|\,.*)$/i) {
	unless($vlan = $3){
	    if (defined($boks)){
		$vlan = $lan{$1}{$boks} || $lan{$boks}{$1};
	    }
	}
    }
    return ($vlan,$boks,$1);
}

sub hent_prefixid {
    my ($netaddr,$maske) = @_;
    return $netaddr2prefixid{&fil_netaddr($netaddr,$maske)};
}
sub max_ant_hosts
{
    return 0 unless(defined($_[0]));
    return 0 if($_[0] == 0);
    return(($_ = 2**(32-$_[0])-2)>0 ? $_ : 0);
} 
sub ant_maskiner {
    my $prefixid = $_[0];
    return $active_ip_cnt{$prefixid};
}

sub finn_prefixid {
    # Tar inn ip, splitter opp og and'er med diverse
    # nettmasker. Målet er å finne en match med en allerede innhentet
    # prefixid (hash over alle), som så returneres.
    #print "\nPrøver å finne prefix for ";
    my $ip = $_[0];
    #print $ip."\n";
    my @masker = ("255.255.255.255","255.255.255.254","255.255.255.252","255.255.255.248","255.255.255.240","255.255.255.224","255.255.255.192","255.255.255.128","255.255.255.0","255.255.254.0","255.255.252.0","255.255.248.0","255.255.240.0","255.255.255.224","255.255.255.192","255.255.255.128","255.255.255.0","255.255.254.0","255.255.252.0");
    foreach my $maske (@masker) {
	my $netaddr = &and_ip($ip,$maske);
	#print $netaddr;
	my $mask = &mask_bits($maske);
	$netaddr = &fil_netaddr($netaddr,$mask);
	#print " $ip & $mask = $netaddr\n";
	return $netaddr2prefixid{$netaddr} if (defined $netaddr2prefixid{$netaddr});
    }
    #print "Fant ikke prefixid for $ip\n";
    return 0;
}

sub oppdater_prefix{
    my ($db,$tabell,$felt_fast,$felt_endres) = @_;
    my %iper = &db_hent_enkel($db,"SELECT $felt_fast,$felt_endres FROM $tabell");
    foreach my $ip (keys %iper) {
	#print $ip."\n";
	my $prefixid = &finn_prefixid($ip);
	my $where = "$felt_fast=\'$ip\'";
	&db_update($db,$tabell,$felt_endres,$iper{$ip},$prefixid,$where);
    }
}

sub slett_prefix{
    my $db = $_[0];

    if ($debug) {
	my $sql = "select netaddr, nettype, vlan, active_ip_cnt, orgid, usageid, descr from prefix left outer join gwport using(prefixid) where gwport.prefixid is null and nettype <> 'tildelt' and nettype <> 'statisk' and nettype <> 'adresserom'";
	
	my $res = &db_select($db,$sql);
	
	while(@_ = $res->fetchrow) {
	    print @_;
	    print "\n";
	}
    }

    &db_delete($db,"prefix","prefixid in (select prefix.prefixid from prefix left outer join gwport using(prefixid) where gwport.prefixid is null and nettype <> 'tildelt' and nettype <> 'statisk' and nettype <> 'adresserom')");
    return 1;
}
sub fil_prefix {
    my ($fil,$felt) = @_;
    my %resultat;
    my %orgs;
    my $res = &db_select($db,"select orgid from org");
    while($_ = $res->fetchrow) {
	$orgs{$_} = 1;
    }
    
    open (FIL, "<$fil") || die ("KUNNE IKKE ÅPNE FILA: $fil");
    foreach (<FIL>) {
	if(my @linje = &fil_hent_linje($felt,$_)){
	    
	    if(my $netaddr = &fil_netaddr($linje[0],$linje[1])){
		unless($orgs{$linje[3]}){
		    $linje[3]= "";
		}

	    $resultat{$netaddr} = [$netaddr,undef,undef,$linje[2],$linje[3],undef,$linje[4],$linje[5] ]; #legger inn i hash
	    }
	}
    }
    close FIL;
    return %resultat;
}
sub riktig_vlan{

    my $vlan = $_[0];
    my $interf = $_[1];
    my $ip = $_[2];
    my $if = $_[3];
    
    if($interf =~ /^Vlan(\d+)/){
	if(defined($vlan)&&$vlan!=$1){
	    &skriv("VLAN-MISMATCH","ip=$ip","interface=$if","box=$1","text=$vlan");
	}
	$vlan = $1;
    }
    return $vlan;
}

sub tolk_lanstam{
    $_ = $_[0];
    
    my %lanstam;
    my ($boks,undef) = split /\./,$bokser{$_[1]}[2],2;

    my $interf = $_[2];
    my $ip = $_[3];
    my $if = $_[4];

    /^(lan|stam)\d*\,(\S+?)\,(\S+?)(?:\,(.*)\,(\d+)|\,(.*))?$/i;

    my $vlan;
    unless($vlan = $5){
	$vlan = $lan{$1}{$2};
    }
    $lanstam{'kommentar'} = $4 || $6 || "";
    $lanstam{'nettype'} = &rydd($1);
    $lanstam{'vlan'} = &riktig_vlan($vlan,$interf,$ip,$if);
    my $org = &rydd($2);
    my $usage = &rydd($3);

    $lanstam{'nettident'} = "$org,$usage";

    $org =~ s/^(\w*?)\d*$/$1/;
    if(exists $db_org{$org}){
	$lanstam{'org'} = $org;
    } else {
	$lanstam{'org'} = "";
    }

    $usage =~ s/^(\w*?)\d*$/$1/;
    if(exists $db_usage{$usage}){
	$lanstam{'usage'} = $usage;
    } else {
	$lanstam{'usage'} = "";
    }

    return \%lanstam;
}

sub tolk_link{
    $_ = $_[0];
    my %link;

    my ($boks,undef) = split /\./,$bokser{$_[1]}[2],2;
    my $interf = $_[2];
    my $ip = $_[3];
    my $if = $_[4];

    /^(link)\,(\S+?)(?:\,(.*)\,(\d+)|\,(.*))?$/i;

    $link{'nettype'} = $1;
    my $tilruter = $2;
    $link{'kommentar'} = $3 || $5 || "";
    my $vlan;
    unless($vlan = $4){
	if (defined($boks)){
	    $vlan = $lan{$tilruter}{$boks} || $lan{$boks}{$tilruter};
	}
    }
    $link{'vlan'} =  &riktig_vlan($vlan,$interf,$ip,$if);
    $link{'nettident'} = "$boks,$tilruter";
    return \%link;
}
sub tolk_elink{
    $_ = $_[0];
    my %elink;

    my ($boks,undef) = split /\./,$bokser{$_[1]}[2],2;
    my $interf = $_[2];
    my $ip = $_[3];
    my $if = $_[4];

    # elink, tilruter, tilorg, kommentar(opt), vlan (opt)
    /^(elink)\,(\S+?),(\S+?)(?:\,(.*)\,(\d+)|\,(.*))?$/i;
    $elink{'nettype'} = $1;
    my $tilruter = $2;

    my $org = $3;
    $elink{'kommentar'} = $4 || $6 || "";

    my $vlan;
    unless($vlan = $5){
	if (defined($boks)){
	    $vlan = $lan{$tilruter}{$boks} || $lan{$boks}{$tilruter};
	}
    }
    $org =~ s/^(\w*?)\d*$/$1/;
    if(exists $db_org{$org}){
	$elink{'org'} = $org;
    } else {
	$elink{'org'} = "";
    }

    $elink{'vlan'} = &riktig_vlan($vlan,$interf,$ip,$if);
    $elink{'nettident'} = "$boks,$tilruter";
    return \%elink;
}
