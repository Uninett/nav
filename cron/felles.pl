#!/usr/bin/perl -w

use Pg;
use strict;
sub and_ip {
    my @a =split(/\./,$_[0]);
    my @b =split(/\./,$_[1]);

    for (0..$#a) {
	$a[$_] = int($a[$_]) & int($b[$_]);
    }
    
    return join(".",@a);
}
sub mask_bits {
    $_ = $_[0];
    if    (/255.255.254.0/)   { return 23; }
    elsif (/255.255.255.0/)   { return 24; }
    elsif (/255.255.255.128/) { return 25; }
    elsif (/255.255.255.192/) { return 26; }
    elsif (/255.255.255.224/) { return 27; }
    elsif (/255.255.255.240/) { return 28; }
    elsif (/255.255.255.248/) { return 29; }
    elsif (/255.255.255.252/) { return 30; }
    elsif (/255.255.255.255/) { return 32; }
    else
    {
        return 0;
    }
}   


sub fil_hent {
    my ($fil,$felt) = @_;
    my %resultat = ();
    my @linje = ();
    open (FIL, "<$fil") || die ("KUNNE IKKE ÅPNE FILA: $fil");
    foreach (<FIL>) {
	#tar med linjer som begynner med ord før kolon bestående av 
	#tall,bokstaver,lavstrek,bindestrek
	if (/^[a-zA-Z0-9_\-]+?:/) {
	    #sletter ting som er ekstra i stedet for å slå 
	    #sammen med seinere feilkolonner.
	    (@linje,undef) = split(/:/,$_,$felt+1); 
	    @linje = map rydd($_), @linje; #rydder opp
	    $resultat{$linje[0]} = [ @linje ]; #legger inn i hash
	}
	close FIL;
    }
    return %resultat;
}

sub db_hent {
    my ($db,$sql) = @_;
    my %resultat = ();
#    my $sql = "SELECT $felt FROM $tabell $restsetning";
    my $res =  &db_select($sql,$db);
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat{$_[0]} = [ @_ ];
    }
    return %resultat;
}
sub db_hent_en {
    my ($db,$sql) = @_;
    my %resultat = ();
    my $res =  &db_select($sql,$db);
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat{$_[0]} =  $_[1] ;
    }
    return %resultat;
}

sub db_sett_inn {
    my ($db,$tabell,$felt,$verdier) = @_;
    my @felt = split/:/,$felt;
    my @verdier = split/:/,$verdier;
    my @val;
    my @key;
    foreach my $i (0..$#felt) {
	if ($verdier[$i]){
	    #normal
	    push(@val, "\'".$verdier[$i]."\'");
	    push(@key, $felt[$i]);
	} elsif (defined($verdier[$i])) {
	    #null
	    push(@val, "NULL");
	    push(@key, $felt[$i]);
	}
    }
    if(scalar(@key)){ #key eksisterer
	print "Setter inn *".join(" ",@val)."* i *$tabell*\n";
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	print $sql,"\n";
	db_execute($sql,$db);
    }
}

sub oppdater {
    my ($db,$tabell,$felt,$fra,$til,$hvor_nokkel,$hvor_passer) = @_;

    print "Oppdaterer *$tabell* felt *$felt* fra *$fra* til *$til*\n";
    my $sql = "UPDATE $tabell SET $felt=$til WHERE $hvor_nokkel=\'$hvor_passer\'";
    db_execute($sql,$db);
    print $sql,"\n";
}

sub slett {
    my ($db,$tabell,$hvor_nokkel,$hvor_passer) = @_;


    print "Sletter fra *$tabell* hvor $hvor_nokkel = $hvor_passer";
    my $sql = "DELETE FROM $tabell WHERE $hvor_nokkel=\'$hvor_passer\'";
    db_execute($sql,$db);
    print $sql;
}    
sub rydd {    
    if (defined $_[0]) {
	$_ = $_[0];
	s/\s*$//;
	s/^\s*//;
    return $_;
    } else {
	return "";
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
    die "KLARTE IKKE Å SPØRRE: \n$sql\n".$conn->errorMessage
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


return 1;
