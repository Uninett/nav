#!/usr/bin/perl

# Scriptet henter ut alle bokser med kategori 'SW', og henter ut 
# portspesifikk informasjon fra dem.
#
# Dette hentes og legges i swport:
# ifindex
# status
# speed
# duplex
# trunk (true/false)
# portnavn
# boksbak
#
#
# Dette hentes og legges i swportvlan:
# vlan
# retning
#
# En trunk vil få alle sine aktive vlan listet opp i swportvlan. 
# Retning er default 'x' (ukjent). Kristian har script som avleder
# topologi, de fyller ut retning.

use SNMP_util;
use Pg;
use Socket;
use strict;

require "felles.pl";
##################################

my $db = "manage";
my $conn = db_connect($db);
 
my @felt_swport = ("boksid","modul","port","ifindex","status","speed","duplex","trunk","static","portnavn","boksbak");
my @felt_swportvlan = ("swportid","vlan");
my @felt_swportallowedvlan = ("swportid","hexstring");
my $sql;
my $resultat;
my $table;
my $swid;
my %vlan;
 
my $line;
my $swportid;
my $swportvlanid;

#my %fil;
#my %sw;
my %swport;
my %db_swport;
my %swportid;

my %swportvlan;
my %db_swportvlan;

my %swportallowedvlan;
my %db_swportallowedvlan;
my %sysname2id;
my %sw2id;
my %spv2id;
my %boks;
 
#####################################
# Mib'er

#.iso.org.dod.internet.private.enterprises.cisco.workgroup.stack...
my $Status_catsw   = "1.3.6.1.4.1.9.5.1.4.1.1.6";
my $portName_catsw = "1.3.6.1.4.1.9.5.1.4.1.1.4";
my $Duplex_catsw   = "1.3.6.1.4.1.9.5.1.4.1.1.10";
my $portType_catsw = "1.3.6.1.4.1.9.5.1.4.1.1.5";
my $IfIndex_catsw  = "1.3.6.1.4.1.9.5.1.4.1.1.11";
#stack.vlanGrp.vlanPortTable.vlanPortEntry.vlanPortVlan
my $vlan_catsw     = "1.3.6.1.4.1.9.5.1.9.3.1.3";  
my $trunk_catsw    = "1.3.6.1.4.1.9.5.1.9.3.1.8";
#my $allevlan_catsw = "1.3.6.1.4.1.9.5.1.9.3.1.5";

# For alle -sw
#mib-2.interfaces.ifTable.ifEntry.ifSpeed
my $Speed = "1.3.6.1.2.1.2.2.1.5";

# For C35xx:
my $portName_iossw = "1.3.6.1.4.1.9.2.2.1.1.28";
my $Status_iossw   = "1.3.6.1.2.1.2.2.1.8";
my $IfIndex_iossw  = "1.3.6.1.2.1.2.2.1.2";
my $vlan_iossw     = "1.3.6.1.4.1.9.9.68.1.2.2.1.2";
my $Duplex_iossw   = "1.3.6.1.4.1.9.9.87.1.4.1.1.32.0";
my $trunk_iossw    = "1.3.6.1.4.1.9.9.87.1.4.1.1.6.0";
#my $allevlan_iossw = "1.3.6.1.4.1.9.9.46.1.6.1.1.4";

#-----------------------------------------


#####################################
#henter fra databaser
&hent_db_boks;
&hent_db_swport;

#henter snmp-data og legger dem i hashen swport
foreach my $boksid ("609") { #keys %boks 584 609 2
    &hent_snmpdata($boksid,$boks{$boksid}{typegruppe});
}

print "går videre";
##swid består av boksid og ifindex
#foreach $swid (keys %swport) {
for my $boks (keys %swport) { #swportvlan
    for my $ifindex (keys %{$swport{$boks}}) {
	&sammenlikn_ny(\@{$swport{$boks}{$ifindex}},\@{$db_swport{$boks}{$ifindex}},\@felt_swport, "swport","swportid",$sw2id{$boks}{$ifindex});
    }
}


#henter inn databaser

my %swportid = ();
&hent_db_swport;

for my $boks (keys %swportvlan) {
    print "$boks   $swportvlan{$boks}.\n";
}
&hent_db_swportvlan;
&hent_db_swportallowedvlan;
print "hei";
print @{$swportvlan{2}{3}}[0..3];
print $sw2id{2}{3};
print "hopp";
for my $boks (keys %swportvlan) {
    for my $ifindex (keys %{$swportvlan{$boks}}) {
	if ($swportvlan{$boks}{$ifindex}[0]){
	    print @{$swportvlan{$boks}{$ifindex}}[0..1],"\n";
	    print $sw2id{$boks}{$ifindex},"\n";
	    @{$swportvlan{$boks}{$ifindex}} = ($sw2id{$boks}{$ifindex},$swportvlan{$boks}{$ifindex}[0]);
	    print @{$swportvlan{$boks}{$ifindex}}[0..1],"-----------------\n";
	    &sammenlikn_ny(\@{$swportvlan{$boks}{$ifindex}},\@{$db_swportvlan{$boks}{$ifindex}},\@felt_swportvlan, "swportvlan", "swportid",$sw2id{$boks}{$ifindex});
	}
    }
}

for my $boks (keys %swportallowedvlan) {
    for my $ifindex (keys %{$swportvlan{$boks}}) {
	if ($swportallowedvlan{$boks}{$ifindex}[0]){
	    print @{$swportvlan{$boks}{$ifindex}}[0..1],"\n";
	    print $sw2id{$boks}{$ifindex},"\n";
	    @{$swportallowedvlan{$boks}{$ifindex}} = ($sw2id{$boks}{$ifindex},$swportallowedvlan{$boks}{$ifindex}[0]);
	    &sammenlikn_ny(\@{$swportallowedvlan{$boks}{$ifindex}},\@{$db_swportallowedvlan{$boks}{$ifindex}},\@felt_swportallowedvlan, "swportallowedvlan", "swportid",$sw2id{$boks}{$ifindex});
	}
    }
}
#################################################

sub sammenlikn_ny {
    my @ny = @{$_[0]};
    my @gammel = @{$_[1]};
    my @felt = @{$_[2]};
    my $tabell = $_[3];
    my $nokkel = $_[4];
    my $treff = $_[5];

    print $gammel[0],"\n\n\n";
    if($gammel[0]) {
#    if ($treff) {
	for my $i  (0..$#felt) {
	    unless ( $ny[$i] eq $gammel[$i]) {
		if ( $ny[$i] eq "" && $gammel[$i] ) {
		    $sql = "UPDATE $tabell SET $felt[$i] = null WHERE $nokkel = \'$treff\'";
		    &db_execute($sql,$conn);
		    print $sql;
		} else {
		    print "Oppdaterer *$tabell* felt *$felt[$i]* fra *$gammel[$i]* til *$ny[$i]*\n";
		    $sql = "UPDATE $tabell SET $felt[$i] = \'$ny[$i]\' WHERE $nokkel = \'$treff\'";
		    print $sql;
		    &db_execute($sql,$conn);
		}
	    }
	}
    } else {
	
#-----------------------
#INSERT
	print "\nSetter inn $ny[0]";
	my @val;
	my @key;
	foreach my $i (0..$#felt) {
	    if (defined($ny[$i]) && $ny[$i] ne ""){
		push(@val, "\'".$ny[$i]."\'");
		push(@key, $felt[$i]);
	    }
	}
	
	$sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	print $sql;
	db_execute($sql,$conn);
    }   
}

###################################################
# henter snmpdata avhengig av boksens typegruppe
sub hent_snmpdata
{
#    print "hei";
    my $id = $_[0];
    my $typegruppe = $_[1];

    print "$boks{$id}{sysname}\t";

# Sjekker på typegruppe.
    
    if ($typegruppe eq 'cat-sw')
    {
	print "Henter normalt fra ".$typegruppe."\n";
	unless (&hent_catsw($boks{$id}{ip},$boks{$id}{ro},$id)) {
	    print "FEIL: ".$boks{$id}{ip}.$boks{$id}{ro}.$id."\n";
	}
    }
    elsif ($typegruppe eq 'ios-sw')
    {
	print $typegruppe." er ios-sw\n";
	unless (&hent_iossw($boks{$id}{ip},$boks{$id}{ro},$id)) {
	    print "FEIL: ".$boks{$id}{ip}.$boks{$id}{ro}.$id."\n";
	}
    }
    else
    {
	print $typegruppe." ukjent typegruppe\n";  
    }
}


######################################
sub hent_catsw 
{
    my $ip = $_[0];
    my $ro = $_[1];
    my $id = $_[2];
    my @temp;
    my $line;
    my %if;
    my %mp2if;
    my $temp;
    my $mp;

#mp og temp bør sees på som midlertidige variabler, selv om mp noen ganger faktisk er modul.port.

    @temp = &snmpwalk($ro."\@".$ip,$IfIndex_catsw);
    unless ($temp[0]) {
	return(0);
    }

    foreach $line (@temp)    {
	($mp,my $ifi) = split(/:/,$line);
	$mp2if{$mp} = $ifi; 
	$if{$ifi}{mp} = $mp;
	$if{$ifi}{ifindex} = $ifi;
#	print "IFINDEX".$mp.":".$temp.":".$if{$temp}{ifindex}."\n";
    }
    
    @temp = &snmpwalk($ro."\@".$ip,$Duplex_catsw);
    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);

# Oversetter fra tall til beskrivelse
	if ($temp == 1)
	{
	    $if{$mp2if{$mp}}{duplex} = 'half'; 
	}
	else
	{
	    $if{$mp2if{$mp}}{duplex} = 'full'; 
	}
#	print "DUPLEX".$mp.":".$temp.":".$mp2if{$mp}."\n";
    }
    @temp = &snmpwalk($ro."\@".$ip,$portType_catsw);
    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);
	$if{$mp2if{$mp}}{porttype} = $temp; 
#	print "PORTTYPE".$mp2if{$mp}.":".$temp."\n";
    }
    @temp = &snmpwalk($ro."\@".$ip,$Status_catsw);
    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);
# Oversetter fra tall til up/down
	if ($temp == 2)
	{
	    $if{$mp2if{$mp}}{status} = 'up';
	}
	else
	{
	    $if{$mp2if{$mp}}{status} = 'down'; 
	}
#	print "STATUS".$mp.":".$temp."\n";
    }
    @temp = &snmpwalk($ro."\@".$ip,$Speed);
    foreach $line (@temp)    {
	(my $if,$temp) = split(/:/,$line);
	$temp = ($temp/1e6);
	$temp =~ s/^(.{0,10}).*/$1/; #tar med de 10 første tegn fra speed
	$if{$if}{speed} = $temp; 
#	print "SPEED".$if.":".$temp."\n";
    }

    @temp = &snmpwalk($ro."\@".$ip,$trunk_catsw);
    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);
	if ($temp == 1)
	{
	    $if{$mp2if{$mp}}{trunk} = 't';
	    my ($vlanhex) = &snmpget($ro."\@".$ip,"1.3.6.1.4.1.9.5.1.9.3.1.5.$mp");
	    $vlanhex = unpack "H*", $vlanhex;
	    $if{$mp2if{$mp}}{vlanhex} = $vlanhex;
	} else {
	    $if{$mp2if{$mp}}{trunk} = 'f';
	    my ($temp2) = &snmpget($ro."\@".$ip,$vlan_catsw.".".$mp);
	    $if{$mp2if{$mp}}{vlan} = $temp2;
	}
	print "TRUNK $mp\t$mp2if{$mp}\t$temp\t$if{$mp2if{$mp}}{trunk}\n";
    }
    
    @temp = &snmpwalk($ro."\@".$ip,$portName_catsw);
    foreach $line (@temp)
    {
	($mp,$temp) = split(/:/,$line,2);
	$if{$mp2if{$mp}}{portnavn} = $temp; 
#	print "NAME".$mp2if{$mp}.":".$temp."\n";
    }

    foreach my $interface (keys %if) 
    {
	(my $modul, my $port) = split /\./,$if{$interface}{mp};
	if(defined($if{$interface}{ifindex}))
	{
	    my $boksid = $id;
	    my $ifindex = $if{$interface}{ifindex};

#	    $swid = join(":",($id,$if{$interface}{ifindex}));
	    $swport{$boksid}{$ifindex} = [ $id, 
					   $modul, 
					   $port, 
					   $if{$interface}{ifindex}, 
					   $if{$interface}{status},
					   $if{$interface}{speed},
					   $if{$interface}{duplex},
					   $if{$interface}{trunk},
					   $if{$interface}{static},
					   $if{$interface}{portnavn},
					   $if{$interface}{boksbak} ];
	    $swportvlan{$boksid}{$ifindex} = [ $if{$interface}{vlan} ];
	    $swportallowedvlan{$boksid}{$ifindex} = [ $if{$interface}{vlanhex} ];
	}
    }
    return 1;
}

#########################################


sub hent_iossw {
    my $ip = $_[0];
    my $ro = $_[1];
    my $id = $_[2];
    my @temp;
    my $line;
    my %if;
    my %mp2if;
    my $temp;
    my $mp;

    @temp = &snmpwalk($ro."\@".$ip,$IfIndex_iossw);
    unless ($temp[0]) {
	return(0);
    }

    foreach $line (@temp)    {
	($temp,$mp) = split(/:/,$line);
	$mp =~ s/FastEthernet/Fa/i;
	$mp =~ s/GigabitEthernet/Gi/i;
	($if{$temp}{modul}, $if{$temp}{port}) = split /\//,$mp;
	print $if{$temp}{modul},"\.",$if{$temp}{port};
	$if{$temp}{ifindex} = $temp;
#	print "IFINDEX".$mp.":".$temp.":".$if{$temp}{ifindex}."\n";
#	$ii2mp{$temp} = $mp;
    }
    
    @temp = &snmpwalk($ro."\@".$ip,$Duplex_iossw);
    foreach $line (@temp)    {
	(my $port,$temp) = split(/:/,$line);
	my $ifi = $port+1;
	# Oversetter fra tall til beskrivelse
	if ($temp == 1)
	{
	    $if{$ifi}{duplex} = 'full'; 
	}
	else
	{
	    $if{$ifi}{duplex} = 'half'; 
	}

#	print "DUPLEX\t$ifi\t$temp\t$if{$ifi}{duplex}\n";
	
#	$ii2mp{$temp} = $mp;
    }

#HAR IKKE RIKTIG MIB FOR PORTTYPE
#    @temp = &snmpwalk($ro."\@".$ip,$portType_iossw);
#    foreach $line (@temp)    {
#	($mp,$temp) = split(/:/,$line);
#	$if{$mp2if{$mp}}{porttype} = $temp; 
#	print "PORTTYPE".$mp2if{$mp}.":".$temp."\n";
    
#	$ii2mp{$temp} = $mp;
#    }

    @temp = &snmpwalk($ro."\@".$ip,$Status_iossw);
    foreach $line (@temp)    {
	(my $ifi,$temp) = split(/:/,$line);

# Oversetter fra tall til up/down.
	if ($temp == 1)
	{
	    $if{$ifi}{status} = 'up';
	}
	else
	{
	    $if{$ifi}{status} = 'down';
	}

#	print "STATUS".$mp.":".$temp."\n";
	
    }
    @temp = &snmpwalk($ro."\@".$ip,$Speed);
    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);
	$temp = ($temp/1e6);
	$temp =~ s/^(.{0,10}).*/$1/; #tar med de 10 første tegn fra speed

	$if{$mp}{speed} = $temp; 
#	print "SPEED".$mp.":".$temp."\n";
	
#	$ii2mp{$temp} = $mp;
    }

    @temp = &snmpwalk($ro."\@".$ip,$trunk_iossw);
    foreach $line (@temp)    {
	(my $port,$temp) = split(/:/,$line);
	my $ifi = $port+1;

	if ($temp == 0) {
	    $if{$ifi}{trunk} = 't';
	    my ($vlanhex) = &snmpget($ro."\@".$ip,"1.3.6.1.4.1.9.9.46.1.6.1.1.4.$ifi");
	    print $vlanhex = unpack "H*", $vlanhex;
	    $if{$ifi}{vlanhex} = $vlanhex;
	} else {
	    $if{$ifi}{trunk} = 'f';  
	    my ($temp2) = &snmpget($ro."\@".$ip,$vlan_iossw.".".$ifi);
	    $if{$ifi}{vlan} = $temp2;
	}

    }


    @temp = &snmpwalk($ro."\@".$ip,$portName_iossw);
    foreach $line (@temp)
    {
	(my $ifi, $temp) = split(/:/,$line,2);
	$if{$ifi}{portnavn} = $temp; 
#	print "NAME".$mp.":".$temp."\n";

    }

    foreach my $interface (keys %if) {
	unless ($if{$interface}{modul} =~ /Null0|Vlan1|Tunnel0/i) {
	(my $modul, my $port) = split /\./,$if{$interface}{mp};
	    if(defined($if{$interface}{ifindex})){
#		$swid = join(":",($id,$if{$interface}{ifindex}));
		my $boksid = $id;
		my $ifindex = $if{$interface}{ifindex};
		$swport{$boksid}{$ifindex} = [ $id, 
					       $if{$interface}{modul}, 
					       $if{$interface}{port}, 
					       $if{$interface}{ifindex}, 
					       $if{$interface}{status},
					       $if{$interface}{speed},
					       $if{$interface}{duplex},
					       $if{$interface}{trunk},
					       $if{$interface}{static},
					       $if{$interface}{portnavn},
					       $if{$interface}{boksbak} ];
		$swportvlan{$boksid}{$ifindex} = [ $if{$interface}{vlan} ];
		$swportallowedvlan{$boksid}{$ifindex} = [ $if{$interface}{vlanhex} ];
		
#		print "$swid: $interface\t$if{$interface}{trunk}\t$swport{$swid}[1]\t$swport{$swid}[2]\t$swport{$swid}[7]\n";

#	    $vlan{$swid} = [ $if{$interface}{vlan} ];

	    }
	}
    }
    return 1;
}


#####################################
sub hent_db_boks
{
    %boks = ();
    $sql = "SELECT boksid,ip,sysname,typegruppe,watch,ro FROM boks,type WHERE type.typeid=boks.typeid and kat=\'SW\' ORDER BY boksid";
    
    $resultat = db_select($sql,$conn);
    while(@_ = $resultat->fetchrow) 
    {
	@_ = map rydd($_), @_;
	
	$boks{$_[0]}{ip}      = $_[1];
	$boks{$_[0]}{sysname} = $_[2];
        $boks{$_[0]}{typegruppe} = $_[3];
        $boks{$_[0]}{watch}   = $_[4];
        $boks{$_[0]}{ro}      = $_[5];

	$sysname2id{$_[2]} = $_[0];

#	$sw{$_[0]} = [ @_ ];
#	    print "@_\n";

    }
    
}
##########################
sub hent_snmpdata_ett_vlan 
{
    my $swportid = $_[0];
    my $ip = $_[1];
    my $ro = $_[2];
    my $typegruppe = $_[3];
    my @temp = ();

    if ($typegruppe eq "cat-sw") 
    {
	(@temp) = &snmpwalk($ro."\@".$ip,$vlan_catsw);
    } elsif ($typegruppe eq "ios-sw")
    {
	(@temp) = &snmpwalk($ro."\@".$ip,$vlan_iossw);
    } else {
	return 0;
    }
    
    foreach $line (@temp)    {
	(undef,my $temp) = split(/:/,$line);
	my $vlanid = join (":", $swportid, $temp);
	#legger inn i hashen swportvlan
	$swportvlan{$vlanid} = [ $swportid, $temp ]; 
	print "VLAN".$vlanid.":".$temp."\n";
	
#       $ii2mp{$temp} = $mp;
	return 1;
    }
    
    
}
sub hent_snmpdata_vlan 
{
    my $modport = join (".", ($swport{$_[0]}[1],$swport{$_[0]}[2]) );
    my $swportid = $_[1];
    my $ip = $_[2];
    my $ro = $_[3];
    my $typegruppe = $_[4];
    my $vlanhex;

    if ($typegruppe eq "cat-sw") {
        ($vlanhex) = &snmpget($ro."\@".$ip,"1.3.6.1.4.1.9.5.1.9.3.1.5.$modport");
    } elsif ($typegruppe eq "ios-sw") {
        ($vlanhex) = &snmpget($ro."\@".$ip,"1.3.6.1.4.1.9.9.46.1.6.1.1.4.$modport");
    } else {
        return 0;
    }
#pakker ut hexstrengen og legger den i hash klar for database
    print $vlanhex."\n";
    print $vlanhex = unpack "H*", $vlanhex;
    $swportallowedvlan{$swportid} = [ $swportid, $vlanhex ];
    return 1;
}


sub hent_db_swport
{
    %db_swport = ();
    $sql = "SELECT swportid,".join(",", @felt_swport)." FROM swport ORDER BY swportid";
    
    $resultat = db_select($sql,$conn);
    while(@_ = $resultat->fetchrow) 
    {
	@_ = map rydd($_), @_;

	#lager entydig nøkkel og legger inn i hashen db_swport
	my $id = join(":",$_[1],$_[4]);
	$sw2id{$_[1]}{$_[4]} = $_[0];
	$db_swport{$_[1]}{$_[4]} = [ @_[1..@felt_swport] ];
    }    
}

##########################

sub hent_db_swportvlan
{

    my $sql = "SELECT boksid,ifindex,".join(",",@felt_swportvlan)." FROM swport natural join swportvlan";
    
    my $resultat = db_select($sql,$conn);
    while(@_ = $resultat->fetchrow) 
    {
	@_ = map rydd($_), @_;
	$db_swportvlan{$_[0]}{$_[1]} = [ @_[2..$#_] ];
	print $db_swportvlan{$_[0]}{$_[1]}[0..1],"\n";
    }    
}


sub hent_db_swportallowedvlan
{
    my $sql = "SELECT  boksid,ifindex,".join(",",@felt_swportallowedvlan)." FROM swport natural join swportallowedvlan";
    
    my $resultat = db_select($sql,$conn);
    while(@_ = $resultat->fetchrow) 
    {
	@_ = map rydd($_), @_;
	$db_swportallowedvlan{$_[0]}{$_[1]} = [ @_[2..$#_] ];
	print $db_swportallowedvlan{$_[0]}{$_[1]}[0..4],"\n";

    }    
}

########################################################

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

sub rydd {    
    if (defined $_[0]) {
	$_ = $_[0];
	s/\s*$//;
	s/^\s*//;
	return $_;
    } else {
	return "";
    }
}




