#!/usr/bin/perl

use File::Copy;
use SNMP_util;
use Net::hostent;
use Socket;
#use Mail::Sendmail;
use Pg;

my $eier = 'grohi@itea.ntnu.no';

my @felt = ("boksid","sysCon","software","supVersion");
#################################

# Setter error out til '/dev/null'
#open(STDERR, ">/dev/null");

my %modulType = (1,"other",2,"empty",3,"wsc1000",4,"wsc1001",5,"wsc1100",11,"wsc1200",
		 12,"wsc1400",13,"wsx1441",14,"wsx1450",16,"wsx1483",17,"wsx1454",18,"wsx1455",
		 19,"wsx1431",20,"wsx1465",21,"wsx1436",22,"wsx1434",23,"wsx5009",24,"wsx5013",
		 25,"wsx5011",26,"wsx5010",27,"wsx5113",28,"wsx5101",29,"wsx5103",30,"wsx5104",
		 31,"wsx5105",32,"wsx5155",33,"wsx5154",34,"wsx5153",35,"wsx5111",36,"wsx5213",
		 37,"wsx5020",38,"wsx5006",39,"wsx5005",40,"wsx5509",41,"wsx5506",42,"wsx5505",
		 43,"wsx5156",44,"wsx5157",45,"wsx5158",46,"wsx5030",47,"wsx5114",48,"wsx5223",
		 49,"wsx5224",50,"wsx5012",52,"wsx5302",53,"wsx5213a",55,"wsx5201",56,"wsx5203",
		 57,"wsx5530",66,"wsx5166",67,"wsx5031");


&snmpmapOID("sysName","1.3.6.1.2.1.1.5.0");
&snmpmapOID("sysLocation","1.3.6.1.2.1.1.6.0");

#cisco.workgroup.stack.chassisGrp.chassisModel
&snmpmapOID("chassisModel","1.3.6.1.4.1.9.5.1.2.16.0");

#cisco.ciscoMgmt.ciscoFlashMIB.ciscoFlashMIBObjects.ciscoFlashDevice.ciscoFlashDeviceTable.ciscoFlashDeviceEntry.ciscoFlashDeviceSize
&snmpmapOID("ciscoFlashDeviceSize","1.3.6.1.4.1.9.9.10.1.1.2.1.2");

#cisco.ciscoMgmt.ciscoFlashMIB.ciscoFlashMIBObjects.ciscoFlashDevice.ciscoFlashDevicesSupported
&snmpmapOID("ciscoFlashDevicesSupported","1.3.6.1.4.1.9.9.10.1.1.1.0");

# enterprises.cisco.ciscoMgmt.ciscoFlashMIB.ciscoFlashMIBObjects.ciscoFlashDevice.ciscoFlashPartitions.ciscoFlashPartitionTable.ciscoFlashPartitionEntry.ciscoFlashPartitionSize
&snmpmapOID("ciscoFlashPartitionSize","1.3.6.1.4.1.9.9.10.1.1.4.1.1.4");

#cisco.ciscoMgmt.ciscoMemoryPoolMIB.ciscoMemoryPoolObjects.ciscoMemoryPoolTable.ciscoMemoryPoolEntry.ciscoMemoryPoolUsed
&snmpmapOID("ciscoMemoryPoolUsed","1.3.6.1.4.1.9.9.48.1.1.1.5");

#cisco.ciscoMgmt.ciscoMemoryPoolMIB.ciscoMemoryPoolObjects.ciscoMemoryPoolTable.ciscoMemoryPoolEntry.ciscoMemoryPoolFree
&snmpmapOID("ciscoMemoryPoolFree","1.3.6.1.4.1.9.9.48.1.1.1.6");

my $ip2NetMask = ".1.3.6.1.2.1.4.20.1.3"; 


# Kjente typer:
#brukes ikke
# my $kjentetyper = 'PS40|SW1100|SW3300|PS10|Off8|C1900';

my $database = "manage";
my $conn = db_connect($database);
my $sql;
my $resultat;
my @line;

#########################################

# Setter error out til '/dev/null'
#open(STDERR, ">/dev/null");

# Dette forhindrer at det som vanligvis skrives til terminal, blir sendt i 
# mail. Gjelder f.eks passord osv.

##########################################

my %db = ();

&hent_db;
#my $linje = 0;

#%logg=();

# kan gjøre "sort by_ip"

foreach my $id (keys %boks)
{
#    print "$ip\n";
#    if ($boks{$id}{watch} eq 'f') 
	# Er pingbar, så hvis den ikke svarer er det noe galt med community
#    {
	unless (&hent_data($id,$boks{$id}{ip},$boks{$id}{ro})){	
	    print "$boks{$id}{ro}\@$boks{$id}{ip} er ikke på watch, men svarer ikke på snmp.\n";
	}
 #   }    
 #   else
 #   {
#	print "$id2ip{$id} er på watch, hopper over denne.\n";
#    }
}

foreach my $f (keys %boksinfo) {
    &sjekk(\%boksinfo, \%db_boksinfo, \@felt, "boksinfo", $f);
}   

#$tid = localtime(time);

#$LOGG = '>>/local/nettinfo/log/NTNUlog';
#open(LOGG,$LOGG);
#foreach $line (keys %logg)
#{
#   print LOGG "$logg{$line}\n";
#}

exit(0);

###########################################
sub sjekk {
    my %ny = %{$_[0]};
    my %gammel = %{$_[1]};
    my @felt = @{$_[2]};
    my $tabell = $_[3];
    my $f = $_[4];


#eksisterer i databasen?
    if($gammel{$f}[0]) {
#-----------------------
#UPDATE
	for my $i (0..$#felt ) {
	    unless($ny{$f}[$i] eq $gammel{$f}[$i]) {
#oppdatereringer til null må ha egen spørring
		if ($ny{$f}[$i] eq "" && $gammel{$f}[$i] ne ""){
		    print "\nOppdaterer $f felt $felt[$i] fra \"$gammel{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE $tabell SET $felt[$i]=null WHERE $felt[0]=\'$f\'";
		    db_execute($sql,$conn);
		    print $sql;
		} else {
#normal oppdatering
		    print "\nOppdaterer $f felt $felt[$i] fra \"$gammel{$f}[$i]\" til \"$ny{$f}[$i]\"";
		    $sql = "UPDATE $tabell SET $felt[$i]=\'$ny{$f}[$i]\' WHERE $felt[0]=\'$f\'";
		    print $sql;
		    db_execute($sql,$conn);
		}
	    }
	}
    }else{
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
}

#################################
sub hent_data
{
    my $id = $_[0];
    my $ip = $_[1];
    my $ro = $_[2];

    (my $sc) = &snmpget("$ro\@$ip","system.sysContact");
    return 0 unless $sc;
    (undef,my $so) = split /:/,&snmpwalk("$ro\@$ip",".1.3.6.1.4.1.9.5.1.3.1.1.20");    
#    $nettel{$id}{software}    =~ s/.+\://g;

    (undef,my $sv) = split /:/,&snmpwalk("$ro\@$ip",".1.3.6.1.4.1.9.5.1.3.1.1.2"); 
#sysName
    (my $sn) = &snmpget("$ro\@$ip","sysName");

# Sysname avsluttes ved 1. punktum.
    my $dummy;
    ($sn,$dummy) = split(/\./,$sn);

#    print "$ip\t$sn\n";
   
    return 0 if (!$sn);
   
    unless ($boks{$id}{sysName} eq $sn){
	$boks{$id}{sysName}= $sn;
	&oppdater_en("boks","sysName",$sn,$felt[0],$id);
    }


#prefiksid
    my $prefiksid;
    @lines = &snmpwalk("$ro\@$ip",$ip2NetMask);
    foreach $line (@lines)
    {
        ($gwip,$netmask) = split(/:/,$line);
	my $nettadr = &and_ip($gwip,$netmask);
	my $maske = &mask_bits($netmask);
	$prefiksid = &hent_prefiksid($nettadr, $maske);

    }
    unless ($boks{$id}{prefiksid} =~ /$prefiksid/){
	$boks{$id}{prefiksid}= $prefiksid;
	&oppdater_en("boks","prefiksid",$prefiksid,$felt[0],$id);
    }
  
#    $sup_version =~ s/\d+://g;
    $sv = $modulType{$sv};

    $boksinfo{$id} = [ $id,$sc,$so,$sv ];       
    print $boksinfo{$id}[0];

    return 1;



}



###########################################
sub hent_db
{
    $sql = "SELECT boksid,ip,sysName,prefiksid,watch,ro FROM boks WHERE kat=\'SW\'";
    $resultat = db_select($sql,$conn);
    while (@line = $resultat->fetchrow)
    {
	@line = map rydd($_), @line;
	
	$boks{$line[0]}{ip}      = $line[1];
	$boks{$line[0]}{sysName} = $line[2];
	$boks{$line[0]}{prefiksid} = $line[3];
        $boks{$line[0]}{watch}   = $line[4];
        $boks{$line[0]}{ro}      = $line[5];
    }	    

    my $sql = "SELECT ".join(",",@felt)." FROM boksinfo";
    $resultat = db_select($sql,$conn);

    while (@line=$resultat->fetchrow)
    {
	@line = map rydd($_), @line;

	$db_boksinfo{$line[0]} = [ @line ];

    }
}

####################
sub sjekk_type
{
    # Gir bare resultat for 3com-utstyr (og ikke Off8).
    $id = $_[0];
    $ip = $id2ip{$id};

    $no_res1 = '-';
    $no_res2 = 'x';

    return $no_res1 if ($db{$id}{type} eq 'C1900');
    return $no_res1 if ($db{$id}{type} eq 'Off8');

    $typemib = '.1.3.6.1.4.1.43.10.27.1.1.1.5.1';
    @svar = &snmpget("$db{$id}{ro}\@$ip","$typemib");
    if ($svar[0])
    {
	return $svar[0];
    }
    else
    {
	return $no_res2;
    }
}  # end sjekk_type

####################

sub ip2dns
{
    if ($h1 = gethost($_[0]))
    {
	$dnsname = $h1->name;
    }
    else
    {
	$dnsname = '-';
    }
    return $dnsname;
} # end sub ip2dns

#############################################
	
sub dns2ip
{
    if ($h2 = gethost($nettel{$_[0]}{sysName}.'.ntnu.no'))
    {
	$dnsip = inet_ntoa($h2->addr);
    }
    else
    {
	$dnsip = '-';
    }
    return $dnsip;

}   # end sub dns2ip

#############################################

sub finn_sv    # $sv  = software-versjon 
{
    my $id = $_[0];
    my $ip = $_[1]; #$id2ip{$id};
    my @temp = ("tull","-");
    my $svmib = "";

#    if ($db_boksinfo{$id}{type} eq 'C1900')
#    {
#	$ret = '-';
#    }
#    else
#    {
	if ($db_boksinfo{$id}{type} =~ /PS40|SW1100|SW3300/) {
	    $svmib = '.1.3.6.1.4.1.43.10.27.1.1.1.12';
	    @temp = &snmpwalk("$db_boksinfo{$id}{ro}\@$ip","$svmib");
	} elsif ($db_boksinfo{$id}{type} =~ /PS10|Off8/) {  
	    $svmib = '.1.3.6.1.4.1.43.10.3.1.1.4.1';
	    @temp = &snmpwalk("$db_boksinfo{$id}{ro}\@$ip","$svmib");
	}
    (undef,my $ret) = split(/\:/,$temp[0]);
    return $ret;
#    }
}   # end sub finn_ais_og_sv


########################################################

sub by_ip
# sorterer paa ip "i samarbeid med" sort-funksjonen
# typisk kall: sort by_ip <...>
{
    ($aa,$ab,$ac,$ad)=split(/\./,$a);
    ($ba,$bb,$bc,$bd)=split(/\./,$b);    

    if ($ac < $bc){
	return -1;}
    elsif ($ac == $bc)
    {
	if ($ad < $bd)
	{return -1;}
	elsif ($ad == $bd)
	{return 0;}
	elsif ($ad > $bd)
	{return 1;}
    }
    if ($ac > $bc) {
	return 1;}
    
} # end sub by_ip

sub and_ip {
    my @a =split(/\./,$_[0]);
    my @b =split(/\./,$_[1]);

    for (0..$#a) {
	$a[$_] = int($a[$_]) & int($b[$_]);
    }
    
    return join(".",@a);
}
sub mask_bits {
    $_ = $_[0];
    if    (/255.255.254.0/)   { return 23; }
    elsif (/255.255.255.0/)   { return 24; }
    elsif (/255.255.255.128/) { return 25; }
    elsif (/255.255.255.192/) { return 26; }
    elsif (/255.255.255.224/) { return 27; }
    elsif (/255.255.255.240/) { return 28; }
    elsif (/255.255.255.248/) { return 29; }
    elsif (/255.255.255.252/) { return 30; }
    elsif (/255.255.255.255/) { return 32; }
    else
    {
        return 0;
    }
}  
sub hent_prefiksid {
    my $id = "";

    $sql = "SELECT distinct prefiksid FROM prefiks WHERE nettadr=\'$_[0]\' and maske=\'$_[1]\'";
    $resultat = db_select($sql,$conn);

    while (@line=$resultat->fetchrow)
    {
	@line = map rydd($_), @line;
	$id = $line[0];
    }
    return $id;
} 
sub oppdater_en
{
    my $tabell = $_[0];
    my $key = $_[1];
    my $val = $_[2];
    my $nokkel =$_[3];
    my $verdi = $_[4];
    
    if($val){
	my $sql = "UPDATE $tabell SET $key=\'$val\' WHERE $nokkel=\'$verdi\'";
	print $sql;
	&db_execute($sql,$conn);
    }
}

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
    die "DATABASEFEIL: $sql\n".$conn->errorMessage
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










