#!/usr/bin/perl -w

use Pg;
use strict;

my $debug;

sub db_hent {
    my ($db,$sql) = @_;
    return &db_select($db,$sql);
}
sub db_hent_hash {
    my ($db,$sql) = @_;
    my $res = &db_select($db,$sql);
    my %resultat;
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat{$_[0]} = [ @_ ];
    }
    return %resultat;
}
sub db_hent_array {
    my ($db,$sql) = @_;
    my $res = &db_select($db,$sql);
    my @resultat;
    my $i;
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat[$i] = [ @_ ];
	$i++;
    }
    return @resultat;
}
sub db_hent_hash_konkatiner {
    my ($db,$sql) = @_;
    my $res = &db_select($db,$sql);
    my %resultat;
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat{"$_[1]\/$_[2]"} = [ @_ ];
    }
    return %resultat;
}

sub db_hent_enkel {
## Henter ut hash indeksert på første ledd i sql-setning. 
## Nøkkelen er første ledd
## Verdien er andre ledd
    my ($db,$sql) = @_;
    my %resultat = ();
    my $res =  &db_select($db,$sql);
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat{$_[0]} = $_[1] ;
    }
    return %resultat;
}
sub db_hent_dobbel {
    my ($db,$sql) = @_;
    my %resultat = ();
    my $res =  &db_select($db,$sql);
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat{$_[0]}{$_[1]} = $_[2] ;
    }
    return %resultat;
}

sub db_select_hash {
    my $db = $_[0];
    my $tabell = $_[1];
    my @felt = @{$_[2]};
    my $en = $_[3];
    my $to = $_[4];
    my $tre = $_[5];

    my %resultat;
    my $sql = "SELECT ".join(",", @felt)." FROM $tabell";
    my $res =  &db_select($db,$sql);

    if(defined($tre)){
	while(@_ = $res->fetchrow) {
	    @_ = map rydd($_), @_;
	    $resultat{$_[$en]}{$_[$to]}{$_[$tre]} = [ @_ ] ;
	}
    } elsif (defined($to)) {
	while(@_ = $res->fetchrow) {
	    @_ = map rydd($_), @_;
	    $resultat{$_[$en]}{$_[$to]} = [ @_ ] ;
	}
    } elsif (defined($en)){
	while(@_ = $res->fetchrow) {
	    @_ = map rydd($_), @_;
	    $resultat{$_[$en]} = [ @_ ] ;
	}
    }
    return %resultat;
}

sub db_sql_hash {
    my $db = $_[0];
    my $sql = $_[1];
#    my @felt = @{$_[2]};
    my $en = $_[2];
    my $to = $_[3];
    my $tre = $_[4];
    print $sql;
    my $felt = $sql =~ /SELECT(.*)FROM/is;
    print $felt;
    my @felt = split /\, */,$felt;

    my %resultat;
    print $sql = "SELECT ".join(",", @felt)." FROM ";
    my $res =  &db_select($db,$sql);

    if(defined($tre)){
	while(@_ = $res->fetchrow) {
	    @_ = map rydd($_), @_;
	    $resultat{$_[$en]}{$_[$to]}{$_[$tre]} = [ @_ ] ;
	}
    } elsif (defined($to)) {
	while(@_ = $res->fetchrow) {
	    @_ = map rydd($_), @_;
	    $resultat{$_[$en]}{$_[$to]} = [ @_ ] ;
	}
    } elsif (defined($en)){
	while(@_ = $res->fetchrow) {
	    @_ = map rydd($_), @_;
	    $resultat{$_[$en]} = [ @_ ] ;
	}
    }
    return %resultat;
}




sub db_hent_dobbel_hash_konkatiner {
    my ($db,$sql) = @_;
    my %resultat = ();
    my $res =  &db_select($db,$sql);
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat{$_[1]}{$_[2]."/".$_[3]} = @_ ;
    }
    return %resultat;
}
sub db_hent_scalar {
    my ($db,$sql) = @_;
    my $resultat;
    my $res =  &db_select($db,$sql);
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat = $_[1] ;
    }
    return $resultat;
}
sub db_sett_inn {
    my ($db,$tabell,$felt,$verdier) = @_;
    my @felt = split/:/,$felt;
    my @verdier = split/:/,$verdier;
    my @val;
    my @key;
    foreach my $i (0..$#felt) {
	if (defined($verdier[$i]) && $verdier[$i] ne ''){
	    #normal
	    push(@val, "\'".$verdier[$i]."\'");
	    push(@key, $felt[$i]);
#	} elsif (defined($verdier[$i])) {
	    #null
#	    push(@val, "NULL");
#	    push(@key, $felt[$i]);
	}
    }
    if(scalar(@key)){ #key eksisterer
	&skriv("DBOUT","\n\nSetter inn *".join(" ",@val)."* i *$tabell*");
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	print $sql if $debug;
	&skriv("DBERR", &db_execute($db,$sql));
    }
}
sub db_insert {
    my $db = $_[0];
    my $tabell = $_[1];
    my @felt = @{$_[2]};
    my @verdier = @{$_[3]};

    my @val;
    my @key;
    foreach my $i (0..$#felt) {
	if (defined($verdier[$i]) && $verdier[$i] ne ''){
	    #normal
	    push(@val, "\'".$verdier[$i]."\'");
	    push(@key, $felt[$i]);
#	} elsif (defined($verdier[$i])) {
	    #null
#	    push(@val, "NULL");
#	    push(@key, $felt[$i]);
	}
    }
    if(scalar(@key)){ #key eksisterer
	my $nql = "\n\nSETTER INN I |$tabell| FELT |".join(" ",@key)."| VERDIER |".join(" ",@val)."|";
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	&skriv("DBOUT", $nql);
	&skriv("DBERR", &db_execute($db,$sql));
    }
}
sub db_update {
    my ($db,$tabell,$felt,$fra,$til,$hvor) = @_;
    if(defined( $fra ) && defined( $til )){
    unless($til eq $fra) {
#	print "***IKKE LIKE\n";
	if (!$til && $fra){
	    my $sql = "UPDATE $tabell SET $felt=null WHERE $hvor";
	    my $nql = "\n\nOPPDATERER |$tabell| FELT |$felt| FRA |$fra| TIL |null| hvor |$hvor|";
	    &skriv("DBOUT", $nql);
	    &skriv("DBERR", &db_execute($db,$sql));
	} elsif ($til) {
	    my $sql = "UPDATE $tabell SET $felt=\'$til\' WHERE $hvor";
	    my $nql = "\n\nOPPDATERER |$tabell| FELT |$felt| FRA |$fra| TIL |$til| hvor |$hvor|";
	    &skriv("DBOUT", $nql);
	    &skriv("DBERR", &db_execute($db,$sql));
	    print $sql if $debug;
#	} else {
#	    print "tomme: $til & $fra\n";
	}
    }
    }
}

sub db_oppdater {
    my ($db,$tabell,$felt,$fra,$til,$hvor_nokkel,$hvor_passer) = @_;

    &skriv("DBOUT", "\n\nOppdaterer *$tabell* felt *$felt* fra *$fra* til *$til* hvor *$hvor_nokkel* er *$hvor_passer*");
    my $sql = "UPDATE $tabell SET $felt=$til WHERE $hvor_nokkel=\'$hvor_passer\'";
    &skriv("DBERR", &db_execute($db,$sql));
    print $sql if $debug;
}
sub db_oppdater_idant_to {
    my ($db,$tabell,$felt,$fra,$til,$hvor_nokkel1,$hvor_nokkel2,$hvor_passer1,$hvor_passer2) = @_;

    &skriv("DBOUT", "\n\nOppdaterer *$tabell* felt *$felt* fra *$fra* til *$til* hvor *$hvor_nokkel1* er *$hvor_passer1* og *$hvor_nokkel2* er *$hvor_passer2*");
    my $sql = "UPDATE $tabell SET $felt=$til WHERE $hvor_nokkel1=\'$hvor_passer1\' AND $hvor_nokkel2=\'$hvor_passer2\'";
    &skriv("DBERR", &db_execute($db,$sql));
#    print $sql,"\n";
}

sub db_delete {
    my ($db,$tabell,$hvor) = @_;
    my $nql = "\n\nSLETTER FRA TABELL |$tabell| HVOR |$hvor|";
    my $sql = "DELETE FROM $tabell WHERE $hvor";
    &skriv("DBOUT", $nql);
    &skriv("DBERR", &db_execute($db,$sql));
#    print $sql;
}    
sub db_slett {
    my ($db,$tabell,$hvor_nokkel,$hvor_passer) = @_;
    if($hvor_passer){
	&skriv("DBOUT", "\n\nSletter fra *$tabell* hvor $hvor_nokkel = $hvor_passer");
	my $sql = "DELETE FROM $tabell WHERE $hvor_nokkel=\'$hvor_passer\'";
	&skriv("DBERR", &db_execute($db,$sql));
	print $sql if $debug;
    }
}    
sub db_slett_idant_to {
    my ($db,$tabell,$hvor_nokkel1,$hvor_nokkel2,$hvor_passer1,$hvor_passer2) = @_;


    &skriv("DBOUT", "\n\nSletter fra *$tabell* hvor $hvor_nokkel1 = $hvor_passer1");
    my $sql = "DELETE FROM $tabell WHERE $hvor_nokkel1=\'$hvor_passer1\' AND $hvor_nokkel2=\'$hvor_passer2\'";
    &skriv("DBERR", &db_execute($db,$sql));
    print $sql if $debug;
}    

sub db_sletting{
    my $db = $_[0];
    my %ny = %{$_[1]};
    my %gammel = %{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];
#-----------------------------------
#DELETE
    #hvis den ikke ligger i fila
    for my $f (keys %gammel) {
	unless(exists($ny{$f})) {
	    &db_slett($db,$tabell,$felt[0],$f);
	}
    }
}

sub db_manipulate {
    my $db = $_[0];
    my $slett = $_[1];
    my $tabell = $_[2];
    my @felt = @{$_[3]};
    my @ny = @{$_[4]};
    my @gammel = @{$_[5]};
    my $en = $_[6];
    my $to = $_[7];
    my $tre = $_[8];

    my @where;

    if($en) {
	$where[0] = "$felt[1] = \'$en\' ";
    }
    if($to) {
	$where[1] = "$felt[2] = \'$to\' ";
    }
    if($tre) {
	$where[2] = "$felt[3] = \'$tre\' ";
    }

    my $where = " ".join("AND ",@where);

#	print "til: $ny[3] & fra: $gammel[3] $where\n";


    if($gammel[1]) {
	for my $i (0..$#felt ) {
#	    print "-$i|$gammel[$i]|$ny[$i]|";
#	    if(defined( $gammel[$i] ) && defined( $ny[$i] )){
#	    print "FELT til: $ny[$i] & fra: $gammel[$i] $where\n";
		&db_update($db,$tabell,$felt[$i],$gammel[$i],$ny[$i],$where);

#	    }
	}
#	print "\n";
    } else {
	&db_insert($db,$tabell,\@felt,\@ny);
    }

    if($slett == 1){
	unless($ny[1]) {
	    &db_delete($db,$tabell,$where);
	}
    }
}

#for fil og db-sammenlikning
sub db_endring_med_sletting {
    my ($db,$fil,$tabell,$felt) = @_;
    my @felt = split(/:/,$felt);
    my %ny = &fil_hent($fil,scalar(@felt));
    #leser fra database
    my %gammel = &db_hent_hash($db,"SELECT ".join(",", @felt )." FROM $tabell ORDER BY $felt[0]");
    &db_endring($db,\%ny,\%gammel,\@felt,$tabell);
    &db_sletting($db,\%ny,\%gammel,\@felt,$tabell);
}
#for fil og db-sammenlikning
sub db_endring_uten_sletting {
    my ($db,$fil,$tabell,$felt) = @_;
    my @felt = split(/:/,$felt);
    my %ny = &fil_hent($fil,scalar(@felt));
    #leser fra database
    my %gammel = &db_hent_hash($db,"SELECT ".join(",", @felt )." FROM $tabell ORDER BY $felt[0]");

    &db_endring($db,\%ny,\%gammel,\@felt,$tabell);
}

sub db_endring {

    my $db = $_[0];
    my %ny = %{$_[1]};
    my %gammel = %{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];
    for my $feltnull (keys %ny) {
	&db_endring_per_linje($db,\@{$ny{$feltnull}},\@{$gammel{$feltnull}},\@felt,$tabell,$feltnull);
    }
}

sub db_endring_per_linje {
    my $db = $_[0];
    my @ny = @{$_[1]};
    my @gammel = @{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];
    my $id = $_[5];
    
    #eksisterer i databasen?
    if($gammel[0]) {
#-----------------------
#UPDATE
	for my $i (0..$#felt ) {
	    if(defined( $gammel[$i] ) && defined( $ny[$i] )){
#		print "NY: $ny[$i] GAMMEL: $gammel[$i]\n";
		unless($ny[$i] eq $gammel[$i]) {
		    #oppdatereringer til null må ha egen spørring
		    if ($ny[$i] eq "" && $gammel[$i] ne ""){
			&db_oppdater($db,$tabell,$felt[$i],$gammel[$i],"null",$felt[0],$id);
		    } else {
			
			&db_oppdater($db,$tabell,$felt[$i],"\'$gammel[$i]\'","\'$ny[$i]\'",$felt[0],$id);
		    }
		}
	    }
	}
    }else{
#-----------------------
#INSERT
	&db_sett_inn($db,$tabell,join(":",@felt),join(":",@ny));
	
    }
}
sub db_alt_per_linje_idant_to {
    my $db = $_[0];
    my @ny = @{$_[1]};
    my @gammel = @{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];
    my $nokkel1 = $_[5];
    my $nokkel2 = $_[6];
    my $id1 = $_[7];
    my $id2 = $_[8];
    
    #eksisterer i databasen?
    if($gammel[0]) {
#-----------------------
#UPDATE
	for my $i (0..$#felt ) {
	    if(defined( $gammel[$i] ) && defined( $ny[$i] )){
		unless($ny[$i] eq $gammel[$i]) {
		    #oppdatereringer til null må ha egen spørring
		    if ($ny[$i] eq "" && $gammel[$i] ne ""){
			&db_oppdater_idant_to($db,$tabell,$felt[$i],$gammel[$i],"null",$nokkel1,$nokkel2,$id1,$id2);
		    } else {
			
			&db_oppdate_idant_to($db,$tabell,$felt[$i],"\'$gammel[$i]\'","\'$ny[$i]\'",$nokkel1,$nokkel2,$id1,$id2);
		    }
		}
	    }
	}
    }else{
#-----------------------
#INSERT
	&db_sett_inn($db,$tabell,join(":",@felt),join(":",@ny));
	
    }
#-----------------------
#DELETE
    unless($ny[0]) {
	&db_slett_idant_to($db,$tabell,$nokkel1,$nokkel2,$id1,$id2);
    }
}

sub db_alt{
    my $db = $_[0];
    my $niv = $_[1]; #nivå av hashing
    my $slett = $_[2];
    my $tabell = $_[3];
    my @felt = @{$_[4]};
    my %ny = %{$_[5]};
    my %gammel = %{$_[6]};
    if($niv == 3){ 
	for my $key1 ( keys %ny ) {
	    for my $key2 (keys %{$ny{$key1}}) {
		for my $key3 (keys %{$ny{$key1}{$key2}}) {
#		my @nyrad = @{$ny{$key1}{$key2}{$key3}};
#		my @gammelrad = @{$gammel{$key1}{$key2}{$key3}};
		    my $where = &lag_where(\@felt,$key1,$key2,$key3);
		    if($gammel{$key1}{$key2}{$key3}[1]) {
			for my $i (0..$#felt ) {
			    &db_update($db,$tabell,$felt[$i],$gammel{$key1}{$key2}{$key3}[$i],$ny{$key1}{$key2}{$key3}[$i],$where);
			}
		    } else {
			&db_insert($db,$tabell,\@felt,\@{$ny{$key1}{$key2}{$key3}});
		    }
		}
	    }
	}
	for my $key1 ( keys %gammel ) {
	    for my $key2 (keys %{$gammel{$key1}}) {
		for my $key3 (keys %{$gammel{$key1}{$key2}}) {
		    if($slett == 1){
#		    my @nyrad = @{$ny{$key1}{$key2}{$key3}};
#		    my @gammelrad = @{$gammel{$key1}{$key2}{$key3}};
			unless($ny{$key1}{$key2}{$key3}[1]) {
			    my $where = &lag_where(\@felt,$key1,$key2,$key3);
			    &db_delete($db,$tabell,$where);
			}
		    }
		}
	    }
	}
    } elsif ($niv == 2){
	for my $key1 ( keys %ny ) {
	    for my $key2 (keys %{$ny{$key1}}) {
		my $where = &lag_where(\@felt,$key1,$key2);
		if($gammel{$key1}{$key2}[1]) {
		    for my $i (0..$#felt ) {
			&db_update($db,$tabell,$felt[$i],$gammel{$key1}{$key2}[$i],$ny{$key1}{$key2}[$i],$where);
		    }
		} else {
		    &db_insert($db,$tabell,\@felt,\@{$ny{$key1}{$key2}});
		}
	    }
	}	
	for my $key1 ( keys %gammel ) {
	    for my $key2 (keys %{$gammel{$key1}}) {
		if($slett == 1){
		    unless($ny{$key1}{$key2}[1]) {
			my $where = &lag_where(\@felt,$key1,$key2);
			if($gammel{$key1}{$key2}[1]){
			    &db_delete($db,$tabell,$where);
			}
		    }
		}
	    }
	}
    }
}
sub lag_where{
    my @felt = @{$_[0]};
    my $key1 = $_[1];
    my $key2 = $_[2];
    my $key3 = $_[3];

    my @where;
    if (defined($key1)){
	if($key1 eq ''){
	    $where[0] = "$felt[1] is null ";
	} else {
	    $where[0] = "$felt[1] = \'$key1\' ";
	}
    }
    if (defined($key2)){
	if($key2 eq ''){
	    $where[1] = "$felt[2] is null ";
	} else {
	    $where[1] = "$felt[2] = \'$key2\' ";
	}
    }
    if (defined($key3)){
	if($key3 eq ''){
	    $where[2] = "$felt[3] is null ";
	} else {
	    $where[2] = "$felt[3] = \'$key3\' ";
	}
    }
    my $where = " ".join("AND ",@where);
    return $where;
}

sub db_alt_per_linje {
    my $db = $_[0];
    my @ny = @{$_[1]};
    my @gammel = @{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];
    my $id = $_[5];
    
    #eksisterer i databasen?
    if($gammel[0]) {
#-----------------------
#UPDATE
	for my $i (0..$#felt ) {
	    if(defined( $gammel[$i] ) && defined( $ny[$i] )){
		unless($ny[$i] eq $gammel[$i]) {
		    #oppdatereringer til null må ha egen spørring
		    if ($ny[$i] eq "" && $gammel[$i] ne ""){
			&db_oppdater($db,$tabell,$felt[$i],$gammel[$i],"null",$felt[0],$id);
		    } else {
			
			&db_oppdater($db,$tabell,$felt[$i],"\'$gammel[$i]\'","\'$ny[$i]\'",$felt[0],$id);
		    }
		}
	    }
	}
    }else{
#-----------------------
#INSERT
	&db_sett_inn($db,$tabell,join(":",@felt),join(":",@ny));
	
    }
#-----------------------
#DELETE
    unless($ny[0]) {
	&db_slett($db,$tabell,$felt[0],$id);
    }
}



sub rydd {    
    if (defined $_[0]) {
	$_ = $_[0];
	s/\'/\\\'/;
	s/\\/\\\\/;
	s/\s*$//;
	s/^\s*//;
    return $_;
    } else {
	return "";
    }
}
sub db_connect {
    my ($db,$user,$password) = @_;
    my $conn = Pg::connectdb("dbname=$db user=$user password=$password");
    die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
}
sub db_select {
    my $sql = $_[1];
    my $conn = $_[0];
    my $resultat = $conn->exec($sql);
    die "KLARTE IKKE Å SPØRRE: \n$sql\n".$conn->errorMessage
	unless ($resultat->resultStatus eq PGRES_TUPLES_OK);
    return $resultat;
}
sub db_execute {
    my $sql = $_[1];
    my $conn = $_[0];
    my $resultat = $conn->exec($sql);
    unless ($resultat->resultStatus eq PGRES_COMMAND_OK){
	&skriv("DBERR", "\nDATABASEFEIL: \n$sql".$conn->errorMessage);
    }
    return $resultat->oidStatus;
}

return 1;
