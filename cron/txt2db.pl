#!/usr/bin/perl -w

use Pg;
use strict;

#-------------ALLE-------------
my $db = "manage";
my $conn = db_connect($db);
my ($fil,$tabell,@felt);
#--------------ANV-------------
$fil = "/usr/local/nav/etc/anv.txt";
$tabell = "anv";
@felt = ("id","descr");
&db_endring($fil,$tabell,\@felt);
#--------------STED------------
$fil = "/usr/local/nav/etc/sted.txt";
$tabell = "sted";
@felt = ("sted","descr");
&db_endring($fil,$tabell,\@felt);
#--------------ROM-------------
$fil = "/usr/local/nav/etc/rom.txt";
$tabell = "rom";
@felt = ("id","sted","descr","rom2","rom3","rom4","rom5");
&db_endring($fil,$tabell,\@felt);
#--------------ORG-------------
$fil = "/usr/local/nav/etc/org.txt";
$tabell = "org";
@felt = ("id","forelder","descr","org2","org3","org4");
&db_endring($fil,$tabell,\@felt);
@felt = ("id","forelder","descr","org2","org3","org4");
&db_endring($fil,$tabell,\@felt);
#--------------FELLES_KODE-----
sub db_endring {
    my @gen = (); my $sql = ""; my $resultat = ""; my %ny = (); my %gammel = ();

    open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
    foreach (<FIL>) {
	if (/^[a-zA-Z0-9_\-]+?:/) {#bindestrek i itea-stud
	    (@_,undef) = split(/:/,$_,scalar(@felt)+1); #sletter ting som er ekstra i stedet for å slå sammen med seinere feilkolonner.
	    @gen = map rydd($_), @_; #rydder opp
	    $ny{$gen[0]} = [ @gen ];
	}
	close FIL;
    }

    $sql = "SELECT ".join(",", @felt )." FROM $tabell ORDER BY $felt[0]";
    $resultat = db_select($sql,$conn);
    while(@_ = $resultat->fetchrow) {
	@_ = map rydd($_), @_;
	$gammel{$_[0]} = [ @_ ];
    }
    for my $f (keys %ny) {


#eksisterer i databasen?
    if($gammel{$f}[0]) {
#-----------------------
#UPDATE
	for my $i (0..$#felt ) {
	    if(defined( $gammel{$f}[$i] ) && defined( $ny{$f}[$i] )){
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
	    } elsif (defined($ny{$f}[$i])) {
		push(@val, "NULL");
		push(@key, $felt[$i]);
	    }
	}
	if(scalar(@key)){
	    print scalar(@key);
	    
	    $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	    print $sql;
	    db_execute($sql,$conn);
	}
    }
}
=cut
#eksisterer i databasen?
	if($db{$f}[0]) {
#-----------------------
#UPDATE
	    for my $i (0..$#{ $fil{$f} } ) {
		#print $felt[$i];
		unless($fil{$f}[$i] eq $db{$f}[$i]) {
#oppdatereringer til null må ha egen spørring
		    if ($fil{$f}[$i] eq "" && $db{$f}[$i] ne ""){
			print "\nOppdaterer $f felt $felt[$i] fra \"$db{$f}[$i]\" til \"NULL\"";
			$sql = "UPDATE $tabell SET $felt[$i]=null WHERE $felt[0]=\'$f\'";
			db_execute($sql,$conn);
			print $sql;
		    } else {
#normal oppdatering
			print "\nOppdaterer $f felt $felt[$i] fra \"$db{$f}[$i]\" til \"$fil{$f}[$i]\"";
			$sql = "UPDATE $tabell SET $felt[$i]=\'$fil{$f}[$i]\' WHERE $felt[0]=\'$f\'";
			print $sql;
			db_execute($sql,$conn);
		    }
		}
	    }
	}else{
#-----------------------
#INSERT
	    print "\nSetter inn $fil{$f}[0]";
	    my @val = (); my @key = ();
	    foreach my $i (0..$#felt) {
		if (defined($fil{$f}[$i])){
		    push(@val, "\'".$fil{$f}[$i]."\'");
		    push(@key, $felt[$i]);
		}
	    }
	    print scalar(@key);
	    if(scalar(@key)){
		print scalar(@key);
		$sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
		print $sql;
		db_execute($sql,$conn);
	    }
	}
	
    }
=cut
#-----------------------------------
#DELETE
    for my $f (keys %gammel) {
	unless(exists($ny{$f})) {
	    print "sletter ".$f;
	    $sql = "DELETE FROM $tabell WHERE $felt[0]=\'$f\'";
	    print $sql;
	    db_execute($sql,$conn);
	}
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
    print "DATABASEFEIL: $sql\n".$conn->errorMessage
	unless ($resultat->resultStatus eq PGRES_COMMAND_OK);
    return $resultat;
}


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




