#!/usr/bin/perl -w

#postgresql
use Pg;
#hostname
use Socket;

# TESTING :)
#snmp
use SNMP_util;

use strict;

#require "/usr/local/NAV/lib/Innhenting.pm";

my $db = "manage";
my $conn = db_connect($db);

#blir angitt i begynnelsen av hver del
my $fil;

#databaseting
#my @felt;
my $sql;
my $resultat;

#hasher som blir brukt til sammenlikning
#arrayer fra filene
my %fil;
#arrayer fra databasen
my %db;

#antall kolonner i fil som skal tas med:
my $les = 6;

#blir hentet fra dns-navn for servere
my $ip;
#blir hentet via snmp
my $type;

my $mib_sysname = ".1.3.6.1.2.1.1.5.0";
#midlertidig array av bestemt, generelt format
my @gen;

my (%server,%db_server,%nettel,%db_nettel,%alle,%db_alle,@felt_nettel,@felt_server);
#kommenter ut =cut i hent_type for å hente ut typer
#tar så lang tid, så det er ikke like gøy hver gang

#sysname-endelser
$fil = "/usr/local/nav/etc/conf/endelser.txt";
open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
my @endelser;
while (<FIL>) {
#leser bare kolonner med "ord:"

    next unless /^\./; 
    my $endelse = rydd($_);
    @endelser=(@endelser,$endelse);
}
close FIL;

#-----------------------
#FILLESING: server.txt
$fil = "/usr/local/nav/etc/server.txt";
open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
while (<FIL>) {
#leser bare kolonner med "ord:"

    next unless /^\w+?\:\S+?\:/; 
    (@_,undef) = split /:/, $_,$les+1;

    @_ = map rydd($_), @_;

    if($ip = hent_ip($_[1])) {
	@_ = ($ip,@_[0..5]);
	@_ = map rydd($_), @_;

	my $sysname = &fjern_endelse($_[2],join(":",@endelser));

#lagrer array i hash
	$server{$_[0]} = [ @_[0..1],$sysname,@_[3..6] ];
	map print($_), @{$server{$_[0]}};
	print "\n";
	$alle{$_[0]} = 1;
    }
}
close FIL;

#----------------------------------
#DATABASELESING
#felter som skal leses ut av databasen
@felt_server = ("ip","romid","sysname","orgid","kat","kat2","ro");

#select 
$sql = "SELECT ".join(",", @felt_server )." FROM boks";
$resultat = db_select($sql,$conn);
while(@_ = $resultat->fetchrow) {
#fjerner whitespace"-tegn og andre ekle ting
    @_ = map rydd($_), @_;

#lagrer array i hashen db
    $db_server{$_[0]} = [ @_ ];
    $db_alle{$_[0]} = 1;
}

for my $it (keys %server) {
#    print "$it\n";
    &sammenlikn(\%server,\%db_server,\@felt_server,"boks",$it);
}

#------------------------------
#FILLESING: nettel.txt
$fil = "/usr/local/nav/etc/nettel.txt";
open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
while (<FIL>) {
#leser bare kolonner med "ord:"


    next unless /^[a-zA-Z0-9_\-]+?:/;
#    next unless /^\w+?\:\S+?\:/; 

#splitter resten av linja
    (@_,undef) = split /:/, $_,$les+2;

    @_ = map rydd($_), @_;

#setter opp gen
    $ip = $_[1];
    my $ro = $_[5];
    $type = hent_type($ip,$ro);

    my $sysname = hent_sysname($ip,$ro,join(":",@endelser));

    if($type) {
	@_ = ($ip,$type,$_[0],$sysname,$_[2],@_[3..6]);
	@_ = map rydd($_), @_;

#lagrer array i hashen fil
	$nettel{$_[0]} = [ @_ ];
	map print($_), @{$nettel{$_[0]}};
	print "\n";
	$alle{$_[0]} = 1;
    }
}
close FIL;

#----------------------------------
#DATABASELESING
#felter som skal leses ut av databasen
@felt_nettel = ("ip","typeid","romid","sysname","orgid","kat","kat2","ro","rw");

#select 
$sql = "SELECT ".join(",", @felt_nettel )." FROM boks";
$resultat = db_select($sql,$conn);
while(@_ = $resultat->fetchrow) {
#fjerner whitespace"-tegn og andre ekle ting
    @_ = map rydd($_), @_;

#lagrer array i hashen db
    $db_nettel{$_[0]} = [ @_ ];
    $db_alle{$_[0]} = 1;
}
for my $it (keys %nettel) {
    &sammenlikn(\%nettel,\%db_nettel,\@felt_nettel,"boks",$it);
}

=cut
#----------------------------------------
#ENDRINGER

for my $f (keys %fil) {
#eksisterer i databasen?
    if(exists($db{$f})) {
#-----------------------
#UPDATE
	for my $i (0..$#felt ) {
	    #print $felt[$i];
	    unless($fil{$f}[$i] eq $db{$f}[$i]) {
#oppdatereringer til null må ha egen spørring
		if ($fil{$f}[$i] eq "" && $db{$f}[$i] ne ""){
		    print "\nOppdaterer $f felt $felt[$i] fra \"$db{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE boks SET $felt[$i]=null WHERE $felt[0]=\'$f\'";
		    db_execute($sql,$conn);
		    print $sql;
		} else {
#normal oppdatering
		    print "\nOppdaterer $f felt $felt[$i] fra \"$db{$f}[$i]\" til \"$fil{$f}[$i]\"";
		    $sql = "UPDATE boks SET $felt[$i]=\'$fil{$f}[$i]\' WHERE $felt[0]=\'$f\'";
		    print $sql;
		    db_execute($sql,$conn);
		}
	    }
	}
    }else{
#-----------------------
#INSERT
	print "\nSetter inn $fil{$f}[0]";
	my @val;
	my @key;
	foreach my $i (0..$#felt) {
	    if (defined($fil{$f}[$i]) && $fil{$f}[$i] ne ""){
		push(@val, "\'".$fil{$f}[$i]."\'");
		push(@key, $felt[$i]);
	    }
	}
	
	$sql = "INSERT INTO boks (".join(",",@key ).") VALUES (".join(",",@val).")";
	print $sql;
	db_execute($sql,$conn);
    }
    
}
=cut
#-----------------------------------
#DELETE
for my $f (keys %db_alle) {
    unless(exists($alle{$f})) {
	print "sletter ".$f;
	print $sql = "DELETE FROM boks WHERE ip =\'$f\'";
	db_execute($sql,$conn);
    }
}

sub sammenlikn {

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

sub hent_ip{
    if (defined $_[0]){
	if(my $ip = gethostbyname($_[0])){
	    return inet_ntoa($ip);
	} else {
	    return 0;
	}
    } else {
	return "";
    }   
}
sub hent_type{
    my $ip = $_[0];
    my $ro = $_[1];
    my $resultat;

#    print "$ip\t$ro";

    if (defined($ro) && $ro ne "") {
	my @res = snmpwalk("$ro\@$ip:161:1:2:4","system");
	(undef,my $oid) = split /:/, $res[1];
#	print "oid: ".$oid."\n";
	my $conn = db_connect($db);
	my $sql = "SELECT typeid FROM type WHERE sysobjectid=\'$oid\'";
	$resultat = db_select($sql,$conn);
	$resultat = $resultat->fetchrow;
#	print "OK:\t$ro\@$ip = $resultat \n";
	
    }
    return $resultat;
}

sub hent_sysname{
    my $ip = $_[0];
    my $ro = $_[1];
    my $endelser = $_[2];
    my $resultat = "";
    if ($ro) {
	($resultat) = &snmpget("$ro\@$ip:161:1:2:4",$mib_sysname);
	$resultat = &fjern_endelse($resultat,$endelser);
    }
    return $resultat;
}
sub fjern_endelse{
    my $sysname = $_[0];
    my @endelser =  split(/:/,$_[1]);
    for my $endelse (@endelser) {
	if ($sysname =~ /$endelse/){
#		print "fjerner endelse\n\n\n";
	    $sysname =~ s/$endelse//i;
	}
    }
    return $sysname;
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
    print "DATABASEFEIL: $sql\n".$conn->errorMessage
	unless ($resultat->resultStatus eq PGRES_COMMAND_OK);
    return $resultat;
}
#utvidet chomp som også tar tab. og andre \s
#returnerer tom streng hvis ikke definert
sub rydd {    if (defined $_[0]) {
	$_ = $_[0];
	s/\s*$//;
	s/^\s*//;
    return $_;
    } else {
	return "";
    }
}


return 1;
