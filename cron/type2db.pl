#!/usr/bin/perl -w

use Pg;
use strict;

my $db = "manage";
my $conn = db_connect($db);
my $fil;

my @felt;
my $sql;
my $resultat;

my %fil;
my %db;

my $cols = 4;
#--------------TYPE-------------

$fil = "/usr/local/NAV/etc/kilde/type.txt";
print "\n Leser fra fila $fil og legger inn i databasen $db\n"; 

open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
foreach (<FIL>) {
    if (/^(\w+?):/) {
	@_ = split(/:/,$_,$cols);

	for my $val (0..$cols-1) {
	    $_[$val] = fjern($_[$val]);
	    $_[$val] = sjekk($_[$val]);
	}
	
	$fil{$1} = [ @_[0..$cols-1] ];
    }
    close FIL;
}

@felt = ("type","typegruppe","sysObjectID","descr");

$sql = "SELECT ".join(",", @felt )." FROM type ORDER BY $felt[0]";
$resultat = db_select($sql,$conn);
while(@_ = $resultat->fetchrow) {
    foreach my $f (@_) {
	$f = fjern($f);
	$f = sjekk($f);
    }
    $db{$_[0]} = [ @_[0..$cols-1] ];
#    print @_;
}
foreach my $f (keys(%fil)) {
    if(exists($db{$f})){
	for my $i (0..$cols-1 ) {
#bruker lowercase for å få dem like
	    unless($fil{$f}[$i] eq $db{$f}[$i]) {
		#update kommer her
		if ($fil{$f}[$i] eq "" && $db{$f}[$i] ne ""){
		    print "\nOppdaterer $f felt $felt[$i] fra \"$db{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE type SET $felt[$i]=null WHERE $felt[0]=\'$f\'";
		    print $sql;
		    db_execute($sql,$conn);

		} else {
#normal oppdatering
		    print "\nOppdaterer $f felt $felt[$i] fra \"$db{$f}[$i]\" til \"$fil{$f}[$i]\"";
		    $sql = "UPDATE type SET $felt[$i]=\'$fil{$f}[$i]\' WHERE $felt[0]=\'$f\'";
		    print $sql;
		    db_execute($sql,$conn);
		}
	    }
	}
    } else {
	#insert kommer her
	print "\nSetter inn $fil{$f}[1]";
	my @val;
	foreach my $i (0..$cols-1) {
	    if (defined($fil{$f}[$i])){
		push(@val, "\'".$fil{$f}[$i]."\'");
	    }
	}
	
	$sql = "INSERT INTO type (".join(",",@felt ).") VALUES (".join(",",@val).")";
	print $sql;
	db_execute($sql,$conn);
    }
}
#-----------------------------
#DELETE
for my $f (keys %db) {
    unless(exists($fil{$f})) {
	print "sletter ".$f;
	$sql = "DELETE FROM type WHERE $felt[0]=\'$f\'";
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

sub sjekk{
    if (!defined $_[0]) {
	return "";
    } else {
	return $_[0];
    }
}





