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

#-------------STED--------------
$fil = "/usr/local/NAV/etc/kilde/sted.txt";

open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
foreach (<FIL>) {
    if (/^\w+?:/) {
	(my $sted, my $descr) = split(/:/,$_);
	$sted = fjern($sted);
	$descr = fjern($descr);
	$fil{$sted} = $descr;
    }
    close FIL;
}

$sql = "SELECT sted,descr FROM sted ORDER BY sted";
$resultat = db_select($sql,$conn);
while(my @linje = $resultat->fetchrow) {
    $linje[0] = fjern($linje[0]);
    $linje[1] = fjern($linje[1]);
    $db{$linje[0]} = $linje[1];
}

foreach my $f (keys(%fil)) {
    if(exists($db{$f})){
	unless($db{$f} eq $fil{$f}) {
	    #update kommer her
	    print "\nOppdaterer $f fra \"$db{$f}\" til \"$fil{$f}\"";
	    $sql = "UPDATE sted SET descr=\'$fil{$f}\' WHERE sted=\'$f\'";
	    db_execute($sql,$conn);
	}
    } else {
	#insert kommer her
	print "\nSetter inn $fil{$f} i felt $f";
	$sql = "INSERT INTO sted (sted,descr) VALUES (\'$f\',\'$fil{$f}\')";
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









