#!/usr/bin/perl -w

use Pg;
use strict;

my $db = "manage";
my $conn = db_connect($db);
my $fil;

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

my $sql = "SELECT sted,descr FROM sted ORDER BY sted";
my $resultat = db_select($sql,$conn);
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

#-------------ROM------------
=cut
$fil = "/usr/local/NAV/etc/kilde/rom.txt";

open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
foreach (<FIL>) {
    if (/^\w+?:/) {
	(my $id, my $sted, my $descr) = split(/:/,$_);
	chomp($sted);
	chomp($descr);
	$fil{$sted} = $descr;
    }
    close FIL;
}

my $sql = "SELECT sted,descr FROM sted ORDER BY sted";
my $resultat = db_select($sql,$conn);
while(my @linje = $resultat->fetchrow) {
    $linje[0] = fjern($linje[0]);
    $linje[1] = fjern($linje[1]);
    $db{$linje[0]} = $linje[1];
}

foreach my $f (keys(%fil)) {
    if(exists($db{$f})){
	#update kommer her
	print "\nOppdaterer $f til $fil{$f}";
	$sql = "UPDATE sted SET descr=\'$fil{$f}\' WHERE sted=\'$f\'";
    } else {
	#insert kommer her
	print "\nSetter inn $fil{$f} i felt $f";
	$sql = "INSERT INTO sted (sted,descr) VALUES (\'$f\',\'$fil{$f}\')";
    }
    db_execute($sql,$conn);
}


#--------------ANV-------------
$fil = "/usr/local/NAV/etc/kilde/anv.txt";
open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
foreach (<FIL>) {
    if (/^\w+?:/) {
	(my $id, my $anv) = split(/:/,$_);
	$id = fjern($id);
	$anv = fjern($anv);
	$fil{$id} = $anv;
    }
    close FIL;
}

$sql = "SELECT id,anv FROM anv ORDER BY id";
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
=cut

#--------------ORG-------------
$fil = "/usr/local/NAV/etc/kilde/org.txt";
%db = ();
%fil = ();
print "er i ".$fil;

#$sql = "INSERT INTO org (id,forelder,descr,org2,org3,org4) VALUES ('tekno','NULL','Teknostallen','nettstotte\@itea.ntnu.no')";
#db_execute($sql,$conn);

open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
while (<FIL>) {
    next unless s/^(\w+?)\://;
    @_ = split /:/;
    foreach my $val (@_) {
	$val = fjern($val);
#	$val = NULL if $val eq "";
    }
    $fil{$1} = [ @_ ];
#    print $fil{$1}, $1;
}
close FIL;

#for my $id (keys %fil) {
#    print $id;
#    for my $i (0 .. $#{ $fil{$id} } ) {
#	print " $i = $fil{$id}[$i]";
#    }
#}

my @felt = ("id","forelder","descr","org2","org3","org4");
foreach (@felt) {
    print;
}
$sql = "SELECT ".join(",",@felt)." FROM org ORDER BY id";
$resultat = db_select($sql,$conn);
while(@_ = $resultat->fetchrow) {
    foreach my $f (@_) {
	$f = fjern($f);
    }
    $db{$_[0]} = [$_[1],$_[2],$_[3],$_[4],$_[5]];
}

#for my $id (keys %db) {
#    print $id;
#    for my $i (0 .. $#{ $db{$id} } ) {
#	print " $i = $db{$id}[$i]";
#    }
#}

for my $f (keys %fil) {
    if(exists($db{$f})) {
	for my $i (0 .. $#{ $fil{$f} } ) {
	    unless($fil{$f}[$i] eq $db{$f}[$i]) {
		#oppdater
		if ($fil{$f}[0] eq ""){
		    print "\nOppdaterer $db{$f} fra \"$db{$f}[$i]\" til \"NULL\"";
		    $sql = "UPDATE org SET $felt[$i+1]=null WHERE $felt[0]=\'$fil{$f}\'";
		} else {
		    print "\nOppdaterer $db{$f} fra \"$db{$f}[$i]\" til \"$fil{$f}[$i]\"";
		    $sql = "UPDATE org SET $felt[$i+1]=\'$fil{$f}[0]\' WHERE $felt[0]=\'$fil{$f}\'";
		}
		db_execute($sql,$conn);
	    }
	}
    }else{
	#setter inn ny
	print "\nSetter inn $fil{$f}[0] i felt $f";
	if($fil{$f}[0] eq "") {
	    $sql = "INSERT INTO org (".join(",",$felt[0],@felt[2..5]).") VALUES (\'$f\'";
	    for my $i (0 .. $#{ $fil{$f} } ) {
		unless ($i eq "1") {
		    $sql .= ",\'$fil{$f}[$i]\'";
		}
	    }
	    $sql .= ")";
	    db_execute($sql,$conn);
	}
    }
}
#leser fra databasen på nytt
$sql = "SELECT ".join(",",@felt)." FROM org ORDER BY id";
$resultat = db_select($sql,$conn);
while(@_ = $resultat->fetchrow) {
    foreach my $f (@_) {
	$f = fjern($f);
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









