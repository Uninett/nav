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
##################################

my $db = "manage";
my $conn = db_connect($db);
 
my @felt_swport = ("boksid","modul","port","ifindex","status","speed","duplex","trunk","static","portnavn","boksbak");
my @felt_swportvlan = ("swportid","vlan");
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

#&hent_db_swportvlan;

#henter snmp-data og legger dem i hashen swport
foreach my $boksid (keys %boks) { #keys boks

    if ($boks{$boksid}{sysname} eq 'rfb-409-sw')
    {
	&hent_snmpdata($boksid,$boks{$boksid}{typegruppe});
	
    }
}


##swid består av boksid og ifindex
foreach $swid (keys %swport) {
    (my $boksid, my $ifindex) = split /:/,$swid;
    my $swportid = $sw2id{$boksid}{$ifindex};
    &sammenlikn(\%swport,\%db_swport,\@felt_swport,"swport",$swid,$swportid);
}

#henter inn databaser

#my %swportid = ();
&hent_db_swportvlan;

my $boksid;
my $ifindex;

foreach $boksid (keys %swportid)
{
    print "$boksid\n";

}
my $vlanid;

foreach $vlanid (keys %swportvlan)
{
    unless ($db_swportvlan{$vlanid})
    {	
	(my $boksid,my $ifindex, my $vlan) = split(/:/,$vlanid);
	my $temp = $swportid{$boksid}{$ifindex};

	print "$vlanid\t$temp\n";

	$sql = "INSERT INTO swportvlan (swportid,vlan) VALUES ($temp,$vlan)";
	db_execute($sql,$conn);

	print "$sql\n";

    }
    
    delete $swportvlan{$vlanid};
    delete $db_swportvlan{$vlanid};    
}

foreach $vlanid (keys %db_swportvlan) # er i db, men ikke hentet denne runden
{
    (my $boksid,my $ifindex, my $vlan) = split(/:/,$vlanid);

    $sql = "DELETE FROM swportvlan WHERE swportid=$swportid{$boksid}{$ifindex} AND vlan =$vlan";
    db_execute($sql,$conn);

    print "$sql\n";
}


##############################################

##vlanid består av swportid og vlan
#foreach my $vlanid (keys %swportvlan) {
#    (my $swportid, my $vlan) = split /:/,$vlanid;
#    my $swportvlanid = $spv2id{$swportid}{$vlan};
#    &sammenlikn(\%swportvlan,\%db_swportvlan,\@felt_swportvlan,"swportvlan",$vlanid,$swportvlanid);
#}

#################################################
#################################################
#################################################

#se txt2db.pl for mer kommentarer. denne vil inngå i modul seinere
sub sammenlikn {

    my %ny = %{$_[0]};
    my %gammel = %{$_[1]};
    my @felt = @{$_[2]};
    my $tabell = $_[3];
    my $f = $_[4]; #hashens id
    my $nokkel = "id"; #nøkkel
    my $id = $_[5]; #nøkkelens match
    my @line;

    if (defined($id) && $id ne ""){
#-----------------------
#UPDATE
	for my $i (0..$#felt) {
	    unless($ny{$f}[$i] eq $gammel{$f}[$i]) {
#oppdatereringer til null må ha egen spørring
		print "\n\"".$ny{$f}[$i]."\" <> \"".$gammel{$f}[$i]."\"!";
		if ($ny{$f}[$i] eq "" && $gammel{$f}[$i] ne ""){
		  #  print "\nOppdaterer $f felt $felt[$i] fra \"$gammel{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE $tabell SET $felt[$i]=null WHERE $nokkel=\'$id\'";
		    db_execute($sql,$conn);
		    print $sql;
		} else {
#normal oppdatering
		  #  print "\nOppdaterer $f felt $felt[$i] fra \"$gammel{$f}[$i]\" til \"$ny{$f}[$i]\"";
		    $sql = "UPDATE $tabell SET $felt[$i]=\'$ny{$f}[$i]\' WHERE $nokkel=\'$id\'";
		    print $sql;
		    db_execute($sql,$conn);
		}
	    }
	}

    } else {
	
#-----------------------
#INSERT
	print "\nSetter inn $ny{$f}[0]";
	my @val;
	my @key;
	foreach my $i (0..$#felt) {
	    if (defined($ny{$f}[$i]) && $ny{$f}[$i] ne ""){
		push(@val, "\'".$ny{$f}[$i]."\'");
		push(@key, $felt[$i]);
	    }
	}
	
	$sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	print $sql;
	db_execute($sql,$conn);
    }    
#OBS: KAN IKKE SLETTE FRA DATABASEN (pga fillesing)
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
    my $swid;
    my @temp;
    my @temp2;
    my $line;
    my $line2;
    my $vlans;
    my %hash;
    my %if;
    my %mp2if;
    my $temp;
    my $mp;
    my %vlan;

    my %tempvlan = ();

#mp og temp bør sees på som midlertidige variabler, selv om mp noen ganger faktisk er modul.port.

    @temp = &snmpwalk($ro."\@".$ip,$IfIndex_catsw);
    unless ($temp[0]) {
	return(0);
    }

    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);
	$mp2if{$mp} = $temp; 
	$if{$temp}{mp} = $mp;
	$if{$temp}{ifindex} = $temp;
#	print "IFINDEX".$mp.":".$temp.":".$if{$temp}{ifindex}."\n";
#	$ii2mp{$temp} = $mp;
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
	
#	$ii2mp{$temp} = $mp;
    }
    @temp = &snmpwalk($ro."\@".$ip,$portType_catsw);
    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);
	$if{$mp2if{$mp}}{porttype} = $temp; 
#	print "PORTTYPE".$mp2if{$mp}.":".$temp."\n";
	
#	$ii2mp{$temp} = $mp;
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
	
#	$ii2mp{$temp} = $mp;
    }
    @temp = &snmpwalk($ro."\@".$ip,$Speed);
    foreach $line (@temp)    {
	(my $if,$temp) = split(/:/,$line);
	$temp = ($temp/1e6);
	$temp =~ s/^(.{0,10}).*/$1/; #tar med de 10 første tegn fra speed

	$if{$if}{speed} = $temp; 
#	print "SPEED".$if.":".$temp."\n";
	
#	$ii2mp{$temp} = $mp;
    }

    @temp = &snmpwalk($ro."\@".$ip,$vlan_catsw);
    foreach $line (@temp) {
	($mp,$temp) = split(/:/,$line);
	$if{$mp2if{$mp}}{vlan} = $temp;
	
#	print "VLAN $mp\t$mp2if{$mp}\t$temp\t$if{$mp2if{$mp}}{vlan}\n";

	$vlanid = "$id:$mp2if{$mp}:$if{$mp2if{$mp}}{vlan}"; 
	$swportvlan{$vlanid}++;

	$tempvlan{$temp}++;

    }
    
    @temp = &snmpwalk($ro."\@".$ip,$trunk_catsw);
    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);

	$if{$mp2if{$mp}}{trunk} = $temp % 2; 

	if ($if{$mp2if{$mp}}{trunk} == 1)
	{
	    $if{$mp2if{$mp}}{trunk} = 't';
	}
	else {
	    $if{$mp2if{$mp}}{trunk} = 'f';
	}

#	print "TRUNK $mp\t$mp2if{$mp}\t$temp\t$if{$mp2if{$mp}}{trunk}\n";

	if ($if{$mp2if{$mp}}{trunk} eq 't')
	{
	    foreach $temp (keys %tempvlan)
	    {
#		print "$mp\t$temp\n";
		$vlanid = "$id:$mp2if{$mp}:$temp";
		$swportvlan{$vlanid}++;
	    }
	    
	}
#	else # ikke trunk
#	{
#	    $vlanid = "$id:$mp2if{$mp}:$if{$mp2if{$mp}}{vlan}"; 
#	    $swportvlan{$vlanid}++;
#	}

#	$ii2mp{$temp} = $mp;
    }


    @temp = &snmpwalk($ro."\@".$ip,$portName_catsw);
    foreach $line (@temp)
    {
	($mp,$temp) = split(/:/,$line,2);
	$if{$mp2if{$mp}}{portnavn} = $temp; 
#	print "NAME".$mp2if{$mp}.":".$temp."\n";

## Dropper å skrive til boksbak
#	if ($temp =~ /^n|h|o|link|srv/i)
#	{
#	    (undef,my $sysName) = split(/:/,$temp);
#	    $if{$mp2if{$mp}}{boksbak} = $sysname2id{$sysName};
#	    print $if{$mp2if{$mp}}{boksbak};
#	}
    }

    foreach my $interface (keys %if) 
    {
	(my $modul, my $port) = split /\./,$if{$interface}{mp};
	if(defined($if{$interface}{ifindex}))
	{
	    $swid = join(":",($id,$if{$interface}{ifindex}));
	    $swport{$swid} = [ $id, 
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
#	    $vlan{$swid} = [ $if{$interface}{vlan} ];
	}
    }
    return 1;
}

#########################################


sub hent_iossw {
    my $ip = $_[0];
    my $ro = $_[1];
    my $id = $_[2];
    my $swid;
    my @temp;
    my $line;
    my %hash;
    my %if;
    my %mp2if;
    my $temp;
    my $mp;
    my %vlan;
    my %tempvlan = ();

    @temp = &snmpwalk($ro."\@".$ip,$IfIndex_iossw);
    unless ($temp[0]) {
	return(0);
    }

    foreach $line (@temp)    {
	($temp,$mp) = split(/:/,$line);
	$mp =~ s/FastEthernet/Fa/i;
	$mp =~ s/GigabitEthernet/Gi/i;
	($if{$temp}{modul}, $if{$temp}{port}) = split /\//,$mp;
	$mp2if{$mp} = $temp; 
	$if{$temp}{ifindex} = $temp;
#	print "IFINDEX".$mp.":".$temp.":".$if{$temp}{ifindex}."\n";
#	$ii2mp{$temp} = $mp;
    }
     
    @temp = &snmpwalk($ro."\@".$ip,$Duplex_iossw);
    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);

	# Oversetter fra tall til beskrivelse
	if ($temp == 1)
	{
	    $if{$mp}{duplex} = 'full'; 
	}
	else
	{
	    $if{$mp}{duplex} = 'half'; 
	}

#	print "DUPLEX".$mp.":".$temp.":".$mp."\n";
	
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
	($mp,$temp) = split(/:/,$line);

# Oversetter fra tall til up/down.
	if ($temp == 1)
	{
	    $if{$mp}{status} = 'up';
	}
	else
	{
	    $if{$mp}{status} = 'down';
	}

#	print "STATUS".$mp.":".$temp."\n";
	
#	$ii2mp{$temp} = $mp;
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

    @temp = &snmpwalk($ro."\@".$ip,$vlan_iossw);
    foreach $line (@temp) {
	($mp,$temp) = split(/:/,$line);
	$if{$mp2if{$mp}}{vlan} = $temp;
	
#	print "VLAN $mp\t$mp2if{$mp}\t$temp\t$if{$mp2if{$mp}}{vlan}\n";

	my $temp2 = $mp+1;
	
	$vlanid = "$id:$temp2:$if{$mp2if{$mp}}{vlan}"; 
	$swportvlan{$vlanid}++;

	$tempvlan{$temp}++;
	
    }
    
    @temp = &snmpwalk($ro."\@".$ip,$trunk_iossw);
    foreach $line (@temp)    {
	($mp,$temp) = split(/:/,$line);

	# $temp=0 betyr trunk, ikke ellers.

	if ($temp == 0) {
	    $if{$mp}{trunk} = 't';
	}
	else {
	    $if{$mp}{trunk} = 'f';  
	}

	if ($if{$mp}{trunk} eq 't')
	{
	    foreach $temp (keys %tempvlan)
	    {
#		print "$mp\t$temp\n";
		my $temp2=$mp+1;
		$vlanid = "$id:$temp2:$temp";
		$swportvlan{$vlanid}++;
	    }	    
	}
#	else
#	{
#	    $vlanid = "$id:$mp:$if{$mp2if{$mp}}{vlan}"; 
#	    $swportvlan{$vlanid}++;
#	}

#	print "TRUNK $mp : $temp : $if{$mp}{trunk}\n";
	
#	$ii2mp{$temp} = $mp;
    }


    @temp = &snmpwalk($ro."\@".$ip,$portName_iossw);
    foreach $line (@temp)
    {
	($mp,$temp) = split(/:/,$line,2);
	$if{$mp}{portnavn} = $temp; 
#	print "NAME".$mp.":".$temp."\n";

    }

    foreach my $interface (keys %if) {
	unless ($if{$interface}{modul} =~ /Null0|Vlan1|Tunnel0/i) {
#	(my $modul, my $port) = split /\./,$if{$interface}{mp};
	    if(defined($if{$interface}{ifindex})){
		$swid = join(":",($id,$if{$interface}{ifindex}));
		$swport{$swid} = [ $id, 
				   $if{$interface}{modul}, 
				   $if{$interface}{port}, 
				   $if{$interface}{ifindex}, 
				   $if{$interface}{status},
				   $if{$interface}{speed},
				   $if{$interface}{duplex},
	   # Trunk har ikke data for vlan1, begynner derfor aa telle fra 1 paa fa0/1 :(	   
				   $if{$interface-1}{trunk},
				   $if{$interface}{static},
				   $if{$interface}{portnavn},
				   $if{$interface}{boksbak} ];

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
    $sql = "SELECT id,ip,sysname,typegruppe,watch,ro FROM boks,type WHERE type.type=boks.type and kat=\'SW\' ORDER BY id";
    
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
sub hent_db_swport
{
    %db_swport = ();
    $sql = "SELECT id,".join(",", @felt_swport)." FROM swport ORDER BY id";
    
    $resultat = db_select($sql,$conn);
    while(@_ = $resultat->fetchrow) 
    {
	@_ = map rydd($_), @_;

	#lager entydig nøkkel og legger inn i hashen db_swport
	my $id = join(":",$_[1],$_[4]);
	$sw2id{$_[1]}{$_[4]} = $_[0];
	$db_swport{$id} = [ @_[1..@felt_swport] ];
    }    
}
##########################

sub hent_db_swportvlan
{

    my %temp1 = ();

    my $sql1 = "SELECT id,boksid,ifindex FROM swport";

    my $sql2 = "SELECT swportid,vlan FROM swportvlan";
    
    my $resultat1 = db_select($sql1,$conn);
    while(@_ = $resultat1->fetchrow) 
    {
	@_ = map rydd($_), @_;

	$swportid{$_[1]}{$_[2]} = $_[0];

	$temp1{$_[0]} = "$_[1]:$_[2]"; 

    }
	
    my $resultat2 = db_select($sql2,$conn);
    while(@_ = $resultat2->fetchrow) 
    {
	@_ = map rydd($_), @_;

	#lager entydig nøkkel og legger inn i hashen db_swport
	my $id = join(":",$temp1{$_[0]},$_[1]);
	
	$db_swportvlan{$id}++;
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




