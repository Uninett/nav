#!/usr/bin/perl -w

#postgresql
use Pg;
#hostname
use Socket;

#snmp
use SNMP_util;

use strict;

#require "/usr/local/NAV/lib/Innhenting.pm";

my $db = "manage";
my $conn = db_connect($db);

#blir angitt i begynnelsen av hver del
my $fil;

#databaseting
my @felt;
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

#midlertidig array av bestemt, generelt format
my @gen;

#kommenter ut =cut i hent_type for å hente ut typer
#tar så lang tid, så det er ikke like gøy hver gang


#-----------------------
#FILLESING: server.txt
$fil = "/usr/local/nav/etc/server.txt";
open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
foreach my $l (<FIL>) {
#leser bare kolonner med "ord:"

    next unless $l =~ /^(\w+?\:)(\S+?)\:/; 
    (@_,undef) = split /:/, $l,$les+1;

    @_ = map rydd($_), @_;

    $ip = hent_ip($2);
    $type = hent_type($ip,$_[5]);
    @gen = ($ip,$type,@_[0..5],undef);

#fjerner "whitespace"-tegn
    @gen = map rydd($_), @gen;

#lagrer array i hash
    $fil{$gen[0]} = [ @gen ];
}
close FIL;

#------------------------------
#FILLESING: nettel.txt
$fil = "/usr/local/nav/etc/nettel.txt";
open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
while (<FIL>) {
#leser bare kolonner med "ord:"
    next unless /^\w+?\:\S+?\:/; 
#splitter resten av linja
    (@_,undef) = split /:/, $_,$les+2;
#rydder før bruk av ip og ro
    @_ = map rydd($_), @_;
#setter opp gen
    $ip = $_[1];
    $type = hent_type($ip,$_[5]);
    @gen = ($ip,$type,$_[0],undef,@_[2..6]);
#rydder i gen
    @gen = map rydd($_), @gen;

#lagrer array i hashen fil
    $fil{$gen[0]} = [ @gen ];

}
close FIL;

#----------------------------------
#DATABASELESING
#felter som skal leses ut av databasen
@felt = ("ip","type","romid","sysname","drifter","kat","kat2","ro","rw");

#select 
$sql = "SELECT ".join(",", @felt )." FROM boks ORDER BY $felt[0]";
$resultat = db_select($sql,$conn);
while(@_ = $resultat->fetchrow) {
#fjerner whitespace"-tegn og andre ekle ting
    @_ = map rydd($_), @_;

#lagrer array i hashen db
    $db{$_[0]} = [ @_ ];
}

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
	foreach my $i (0..@felt-1) {
	    if (defined($fil{$f}[$i])){
		push(@val, "\'".$fil{$f}[$i]."\'");
	    } else {
#		push(@val, "\'\'");
	    }
	}
	
	$sql = "INSERT INTO boks (".join(",",@felt ).") VALUES (".join(",",@val).")";
	print $sql;
	db_execute($sql,$conn);
    }
    
}
#-----------------------------------
#DELETE
for my $f (keys %db) {
    unless(exists($fil{$f})) {
	print "sletter ".$f;
	$sql = "DELETE FROM boks WHERE $felt[0]=\'$f\'";
	db_execute($sql,$conn);
    }
}

sub hent_ip{
    $_ = gethostbyname($_[0]);
    return inet_ntoa($_);
}
sub hent_type{
    my $ip = $_[0];
    my $ro = $_[1];
    my $resultat;
    if (defined($ro) && $ro ne "") {
	my @res = snmpwalk("$ro\@$ip:161:1:2:4","system");
	(undef,my $oid) = split /:/, $res[1];
	print "oid: ".$oid."\n";
	my $conn = db_connect($db);
	my $sql = "SELECT type FROM type WHERE sysobjectid=\'$oid\'";
	$resultat = db_select($sql,$conn);
	$resultat = $resultat->fetchrow;
	print "OK:\t$ro\@$ip = $resultat \n";
	
    }
    return $resultat;
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


