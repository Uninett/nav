#!/usr/bin/perl -w

use Pg;
use strict;

#-------------ALLE-------------
my $db = "manage";
my $conn = db_connect($db);
my ($fil,$tabell,@felt);

#--------------ANV-------------
$tabell = "anv";
$fil = "/usr/local/NAV/etc/kilde/anv.txt";
@felt = ("id","descr");
&db_endring($fil,$tabell,\@felt);
#--------------ANV_SLUTT-------


sub db_endring {
    my @gen = (); my $sql = ""; my $resultat = ""; my %fil = (); my %db = ();

    open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
    foreach (<FIL>) {
	if (/^\S+?:/) {
	    (@_,undef) = split(/:/,$_,scalar(@felt)+1); #sletter ting som er ekstra i stedet for å slå sammen med seinere feilkolonner.
	    @gen = map rydd($_), @_; #rydder opp
	    $fil{$gen[0]} = [ @gen ];
	}
	close FIL;
    }

    $sql = "SELECT ".join(",", @felt )." FROM $tabell ORDER BY $felt[0]";
    $resultat = db_select($sql,$conn);
    while(@_ = $resultat->fetchrow) {
	@_ = map rydd($_), @_;
	$db{$_[0]} = [ @_ ];
    }
    for my $f (keys %fil) {
#eksisterer i databasen?
	if(exists($db{$f})) {
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
	    my @val;
	    foreach my $i (0..@felt-1) {
		if (defined($fil{$f}[$i])){
		    push(@val, "\'".$fil{$f}[$i]."\'");
		} else {
		    push(@val, "\'\'");
		}
	    }
	    
	    $sql = "INSERT INTO $tabell (".join(",",@felt ).") VALUES (".join(",",@val).")";
	    print $sql;
	    db_execute($sql,$conn);
	}
	
    }

#-----------------------------------
#DELETE
    for my $f (keys %db) {
	unless(exists($fil{$f})) {
	    print "sletter ".$f;
	    $sql = "DELETE FROM $tabell WHERE $felt[0]=\'$f\'";
	    print $sql;
	    db_execute($sql,$conn);
	}
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




