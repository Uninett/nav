#!/usr/bin/perl -w

#postgresql
use Pg;

use strict;


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

#midlertidig array av bestemt, generelt format
my @gen;

#antall kolonner i fil som skal tas med:
my $les = 6;

#-----------------------
#FILLESING: prefiks.txt
$fil = "/usr/local/nav/etc/prefiks.txt";
open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
foreach my $l (<FIL>) {
#leser bare kolonner med "ord:"

    next unless $l =~ /^\S+?\:/; 
    @_ = split /:/, $l,$les;
    @_ = map rydd($_), @_;

    @gen = (@_[0..3],$_[5]);

#lagrer array i hash
    $fil{$gen[0]} = [ @gen ];
}
close FIL;

#----------------------------------
#DATABASELESING
#felter som skal leses ut av databasen
@felt = ("nettadr","maske","nettype","org","komm");

#select 
$sql = "SELECT ".join(",", @felt )." FROM prefiks ORDER BY $felt[0]";
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
	for my $i (0..@felt-1 ) {
	    #print $felt[$i];
	    unless($fil{$f}[$i] eq $db{$f}[$i]) {
#oppdatereringer til null må ha egen spørring
		if ($fil{$f}[$i] eq "" && $db{$f}[$i] ne ""){
		    print "\nOppdaterer $f felt $felt[$i] fra \"$db{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE prefiks SET $felt[$i]=null WHERE $felt[0]=\'$f\'";
		    db_execute($sql,$conn);
		    print $sql;
		} else {
#normal oppdatering
		    print "\nOppdaterer $f felt $felt[$i] fra \"$db{$f}[$i]\" til \"$fil{$f}[$i]\"";
		    $sql = "UPDATE prefiks SET $felt[$i]=\'$fil{$f}[$i]\' WHERE $felt[0]=\'$f\'";
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
	    }
	}
	
	$sql = "INSERT INTO prefiks (".join(",",@felt ).") VALUES (".join(",",@val).")";
	print $sql;
	db_execute($sql,$conn);
    }
    
}
#-----------------------------------
#DELETE
for my $f (keys %db) {
    unless(exists($fil{$f})) {
	print "sletter ".$f;
	$sql = "DELETE FROM prefiks WHERE $felt[0]=\'$f\'";
	db_execute($sql,$conn);
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
