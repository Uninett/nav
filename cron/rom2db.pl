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

#--------------ROM-------------
$fil = "/usr/local/NAV/etc/kilde/rom.txt";

print "\n Leser fra fila $fil og legger inn i databasen $db\n"; 

open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
while (<FIL>) {
#leser bare kolonner med "ord:"
    next unless s/^(\w+?)\://; 
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
my @felt = ("id","sted","descr","rom2","rom3","rom4","rom5");
#foreach (@felt) {
#    print;
#}
#select
$sql = "SELECT ".join(",",@felt)." FROM rom ORDER BY id";
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

#oppdaterer databasen eller legger inn romene uten foreldre
#alle romene fra fil
for my $f (keys %fil) {
#eksisterer i databasen?
    if(exists($db{$f})) {
#hvis ja: oppdater
	for my $i (0 .. $#{ $fil{$f} } ) {
	    unless($fil{$f}[$i] eq $db{$f}[$i]) {
#oppdatereringer til null må ha egen spørring
		if ($fil{$f}[$i] eq "" && $db{$f}[$i] ne ""){
		    print "\nOppdaterer $f fra \"$db{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE rom SET $felt[$i+1]=null WHERE $felt[0]=\'$fil{$f}\'";
		    db_execute($sql,$conn);
		} else {
#normal oppdatering
		    print "\nOppdaterer $f fra \"$db{$f}[$i]\" til \"$fil{$f}[$i]\"";
		    $sql = "UPDATE rom SET $felt[$i+1]=\'$fil{$f}[0]\' WHERE $felt[0]=\'$fil{$f}\'";
		    db_execute($sql,$conn);
		}
	    }
	}
    }else{
#setter inn ny (av de som ikke har foreldre)
	print "\nSetter inn $fil{$f}[0] i felt $f";
	for my $i (0 .. $#{ $fil{$f} } ) {
	    $sql = "INSERT INTO rom (".join(",",@felt).") VALUES (\'$f\'";
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









