#!/usr/bin/perl -w

use Pg;
use strict;

my $db = "manage";
my $conn = db_connect($db);
my $fil;
my $sql;
my $resultat;

my %fil;
my %db;

#--------------ORG-------------
$fil = "/usr/local/NAV/etc/kilde/org.txt";

print "\n Leser fra fila $fil og legger inn i databasen $db\n"; 

open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
while (<FIL>) {
#leser bare kolonner med "ord:"
    next unless s/^(\S+?)\://; 
#splitter resten av linja
    @_ = split /:/;
#fjerner "whitespace"-tegn
    foreach my $val (@_) {
	$val = fjern($val);
    }
#lagrer array i hash
    $fil{$1} = [ @_ ];
}
close FIL;

#felter som skal leses ut av databasen
my @felt = ("id","forelder","descr","org2","org3","org4");
#foreach (@felt) {
#    print;
#}
#select
$sql = "SELECT ".join(",",@felt)." FROM org ORDER BY id";
$resultat = db_select($sql,$conn);
while(@_ = $resultat->fetchrow) {
#fjerner whitespace"-tegn
    foreach my $f (@_) {
	$f = fjern($f);
	unless(defined($f)) {
	    $f = "";
	}
    }
#lagrer array i hash
    $db{$_[0]} = [$_[1],$_[2],$_[3],$_[4],$_[5]];
}

#oppdaterer databasen eller legger inn orgene uten foreldre
#alle orgene fra fil
for my $f (keys %fil) {
#eksisterer i databasen?
    if(exists($db{$f})) {
#hvis ja: oppdater
	for my $i (0 .. $#{ $fil{$f} } ) {
	    unless($fil{$f}[$i] eq $db{$f}[$i]) {
#oppdatereringer til null må ha egen spørring
		if ($fil{$f}[$i] eq "" && $db{$f}[$i] ne ""){
		    print "\nOppdaterer $f fra \"$db{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE org SET $felt[$i+1]=null WHERE $felt[0]=\'$fil{$f}\'";
		    db_execute($sql,$conn);
		} else {
#normal oppdatering
		    print "\nOppdaterer $f fra \"$db{$f}[$i]\" til \"$fil{$f}[$i]\"";
		    $sql = "UPDATE org SET $felt[$i+1]=\'$fil{$f}[0]\' WHERE $felt[0]=\'$fil{$f}\'";
		    db_execute($sql,$conn);
		}
	    }
	}
    }else{
#setter inn ny (av de som ikke har foreldre)
	print "\nSetter inn $fil{$f}[0] i felt $f";
	if($fil{$f}[0] eq "") {
	    $sql = "INSERT INTO org (".join(",",$felt[0],@felt[2..5]).") VALUES (\'$f\'";
	    for my $i (0 .. $#{ $fil{$f} } ) {
#kolonne "forelder" tas ikke med	   
		unless ($i eq "0") {
		    $sql .= ",\'$fil{$f}[$i]\'";
		}
	    }
	    $sql .= ")";
	    db_execute($sql,$conn);
	}
    }
}
#tømmer hasharrayen db for å lese inn databasen på nytt
%db = ();
print "2";

#leser fra databasen på nytt
$sql = "SELECT ".join(",",@felt)." FROM org ORDER BY id";
$resultat = db_select($sql,$conn);
while(@_ = $resultat->fetchrow) {
    foreach my $f (@_) {
	$f = fjern($f);
	unless(defined($f)) {
	    $f = "";
	}
    }
    $db{$_[0]} = [$_[1],$_[2],$_[3],$_[4],$_[5]];
}
#setter inn de som hadde foreldre
for my $f (keys %fil) {
    unless(exists($db{$f})) {
	for my $i (0 .. $#{ $fil{$f} } ) {
	    $sql = "INSERT INTO org (".join(",",@felt).") VALUES (\'$f\'";
	    for my $i (0 .. $#{ $fil{$f} } ) {
		$sql .= ",\'$fil{$f}[$i]\'";
	    }
	    $sql .= ")";
	}
	db_execute($sql,$conn);
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
sub fjern { #utvidet chomp som også tar tab. og andre \s
    if (defined $_[0]) {
	$_ = $_[0];
	s/\s*$//;
	s/^\s*//;
    return $_;
    }
}









