#!/usr/bin/perl

use File::Copy;
use SNMP_util;
use Net::hostent;
use Socket;
#use Mail::Sendmail;
use Pg;

my $eier = 'grohi@itea.ntnu.no';

my @felt = ("boksid","software","mem","flashmem");
#################################

# Setter error out til '/dev/null'
#open(STDERR, ">/dev/null");
my @chassisType = (1,  # Fikser slik at unknown = 1 osv
		"unknown","multibus","agsplus","igs","c2000","c3000","c4000","c7000","cs500","c7010",
		"c2500","c4500","c2102","c2202","c2501","c2502","c2503","c2504","c2505","c2506",
		"c2507","c2508","c2509","c2510","c2511","c2512","c2513","c2514","c2515","c3101",
		"c3102","c3103","c3104","c3202","c3204","accessProRC","accessProEc","c1000","c1003","c1004",
		"c2516","c7507","c7513","c7506","c7505","c1005","c4700","c2517","c2518","c2519",
		"c2520","c2521","c2522","c2523","c2524","c2525","c4700S","c7206","c3640","as5200",
		"c1601","c1602","c1603","c1604","c7204","c3620","udef","wsx3011","c3810","udef",
		,"udef","c1503","as5300","as2509RJ","as2511RJ","udef","c2501FRAD-FX","c2501LANFRAD-FX",
		"c2502LANFRAD-FX","udef","c1605","udef","udef","udef","udef","cr7256");

&snmpmapOID("sysName","1.3.6.1.2.1.1.5.0");
&snmpmapOID("sysLocation","1.3.6.1.2.1.1.6.0");

&snmpmapOID("sysDescr","1.3.6.1.2.1.1.1.0");

my $ip2NetMask = ".1.3.6.1.2.1.4.20.1.3"; 

#cisco.workgroup.stack.chassisGrp.chassisModel
&snmpmapOID("chassisModel","1.3.6.1.4.1.9.5.1.2.16.0");
&snmpmapOID("chassisType","1.3.6.1.4.1.9.3.6.1.0");
&snmpmapOID("sysObjectID","1.3.6.1.2.1.1.2.0");

&snmpmapOID("processorRam","1.3.6.1.4.1.9.3.6.6.0");
&snmpmapOID("flashSize","1.3.6.1.4.1.9.2.10.1.0");  

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

#sysName
    (my $sn) = &snmpget("$ro\@$ip","sysName");
   
    return 0 if (!$sn);
#    print ":".$sn.":".$boks{$id}{sysName}.":";
    unless ($boks{$id}{sysName} =~ /$sn/){
	$boks{$id}{sysName}= $sn;
	&oppdater_en("boks","sysName",$sn,"id",$id);
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
	&oppdater_en("boks","prefiksid",$prefiksid,"id",$id);
    }

#software

    (my $software) = &snmpget("$ro\@$ip","sysDescr");
    $software =~ s/(.|\n)*Version(.+)\,(.|\n)*/$2/g; 
    $software = rydd($software);

#Memory
    my $mem = (&snmpget("$ro\@$ip","processorRam"))[0]/1e6 . "Mb";
    if ($mem)
    {
	$mem =~ s/(\d+\.\d{2})(\d+)/$1/g;   #Konverterer til to desimaler 
    }
    else
    {
	$mem = 'udef';
    }
#FlashMem
    my $flashmem = (&snmpget("$ro\@$ip","flashSize"))[0]/1e6;
    if ($flashmem)
    {
        $flashmem =~ s/(\d+\.\d{2})(\d+)/$1/g;  #Konverterer til to desimaler
        $flashmem .= "Mb";
    }
    else
    {
	$flashmem ="udef";
    }                         

    $boksinfo{$id} = [ $id, $software, $mem, $flashmem ];
    print $boksinfo{$id}[0];
    
    return 1;

}

###########################################
sub hent_db
{
    $sql = "SELECT id,ip,type,sysName,prefiksid,watch,ro FROM boks WHERE kat=\'GW\'";

    $resultat = db_select($sql,$conn);
    while (@line = $resultat->fetchrow)
    {
	@line = map rydd($_), @line;
	
	$boks{$line[0]}{ip}      = $line[1];
	$boks{$line[0]}{type}      = $line[2];
	$boks{$line[0]}{sysName} = $line[3];
	$boks{$line[0]}{prefiksid} = $line[4];
        $boks{$line[0]}{watch}   = $line[5];
        $boks{$line[0]}{ro}      = $line[6];
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
    my $ro = $_[2];
    my @temp = ("tull","-");
    my $svmib = "";
    my $ro = $_[2];

#    if ($db_boksinfo{$id}{type} eq 'C1900')
#    {
#	$ret = '-';
#    }
#    else
#    {
	if ($db_boksinfo{$id}[4] =~ /PS40|SW1100|SW3300/) {
	    $svmib = '.1.3.6.1.4.1.43.10.27.1.1.1.12';
	    @temp = &snmpwalk("$ro\@$ip","$svmib");
	} elsif ($db_boksinfo{$id}[4] =~ /PS10|Off8/) {  
	    $svmib = '.1.3.6.1.4.1.43.10.3.1.1.4.1';
	    @temp = &snmpwalk("$ro\@$ip","$svmib");
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

    $sql = "SELECT distinct id FROM prefiks WHERE nettadr=\'$_[0]\' and maske=\'$_[1]\'";
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
    my $conn = Pg::connectdb("dbname=$db");
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










