#!/usr/bin/perl -w
#
# $Id: database.pl,v 1.12 2002/08/05 14:16:37 gartmann Exp $
#

use Pg;
use strict;
require "/usr/local/nav/navme/lib/fil.pl";



my $debug=1;
my $navdir = "/usr/local/nav/";

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
sub db_insert {
    my $db = $_[0];
    my $tabell = $_[1];
    my @felt = @{$_[2]};
    my @verdier = @{$_[3]};

    @verdier = map rydd($_), @verdier;

    my @val;
    my @key;
    foreach my $i (0..$#felt) {
#	print $verdier[$i]."\n";
	if (defined($verdier[$i]) && $verdier[$i] ne ''){
	    push(@val, "\'".$verdier[$i]."\'");
	    push(@key, $felt[$i]);
	}
    }
    if(scalar(@key)){
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	&db_execute($db,$sql);
	print $db->errorMessage;
    }
}
sub db_do_insert {
    my $db = $_[0];
    my $tabell = $_[1];
    my @felt = @{$_[2]};
    my @verdier = @{$_[3]};
    my $insert = $_[4];

    if($insert eq "device"){
	my $seq = &finn_og_bruk_deviceid($db);
	push(@felt, "deviceid");
	push(@verdier, $seq);
    }

    @verdier = map rydd($_), @verdier;

    my @val;
    my @key;
    foreach my $i (0..$#felt) {
	print $verdier[$i]."\n";
	if (defined($verdier[$i]) && $verdier[$i] ne ''){
	    push(@val, "\'".$verdier[$i]."\'");
	    push(@key, $felt[$i]);
	}
    }
    if(scalar(@key)){ #key eksisterer
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	print $sql if $debug;
	if($insert eq "nolog"){
	    &db_execute($db,$sql);
	} else {
	    &skriv("DATABASE-INSERT", "table=$tabell", "tuple=".join(" ",@val)) if &db_execute($db,$sql);
	    print $db->errorMessage;

	}
    }
}
sub db_logg_insert {
    my $db = $_[0];
    my $tabell = $_[1];
    my @felt = @{$_[2]};
    my @verdier = @{$_[3]};

    @verdier = map rydd($_), @verdier;
    

    my @val;
    my @key;
    foreach my $i (0..$#felt) {
	print $verdier[$i]."\n";
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
#	my $nql = "\n\nSETTER INN I |$tabell| FELT |".join(" ",@key)."| VERDIER |".join(" ",@val)."|";
	print my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	&skriv("DATABASE-INSERT", "table=$tabell", "tuple=".join(" ",@val)) if &db_execute($db,$sql);
print $db->errorMessage;
    }
}
sub db_update {
    my ($db,$tabell,$felt,$fra,$til,$hvor) = @_;
    if(defined( $fra ) && defined( $til )){
    unless($til eq $fra) {
#	print "***IKKE LIKE\n";
	if (!$til && $fra){
	    my $sql = "UPDATE $tabell SET $felt=null WHERE $hvor";
#	    my $nql = "\n\nOPPDATERER |$tabell| FELT |$felt| FRA |$fra| TIL |null| hvor |$hvor|";
	    &skriv("DATABASE-UPDATE", "from=$fra","to=null","where=$hvor","table=$tabell", "field=$felt") if &db_execute($db,$sql);

	} elsif ($til) {
	    my $sql = "UPDATE $tabell SET $felt=\'$til\' WHERE $hvor";
#	    my $nql = "\n\nOPPDATERER |$tabell| FELT |$felt| FRA |$fra| TIL |$til| hvor |$hvor|";
	    &skriv("DATABASE-UPDATE", "from=$fra","to=$til","where=$hvor","table=$tabell","field=$felt") if &db_execute($db,$sql);
	    print $sql if $debug;
	    print $db->errorMessage;
#	} else {
#	    print "tomme: $til & $fra\n";
	}
    }
    }
}
sub db_do_update {
    my ($db,$tabell,$felt,$fra,$til,$hvor,$update) = @_;

    if(defined( $fra ) && defined( $til )){
	unless($til eq $fra) {
	    
	    if (!$til && $fra){
		my $sql = "UPDATE $tabell SET $felt=null WHERE $hvor";
		&skriv("DATABASE-UPDATE", "from=$fra","to=null","where=$hvor","table=$tabell", "field=$felt") if &db_execute($db,$sql);
		
	    } elsif ($til) {
		my $sql = "UPDATE $tabell SET $felt=\'$til\' WHERE $hvor";
		&skriv("DATABASE-UPDATE", "from=$fra","to=$til","where=$hvor","table=$tabell","field=$felt") if &db_execute($db,$sql);
		print $sql if $debug;
		print $db->errorMessage;
	    }
	}
    }
}
    
sub db_oppdater {
    my ($db,$tabell,$felt,$fra,$til,$hvor_nokkel,$hvor_passer) = @_;

    my $sql = "UPDATE $tabell SET $felt=$til WHERE $hvor_nokkel=\'$hvor_passer\'";
    &skriv("DATABASE-UPDATE", "from=$fra","to=$til","where=$hvor_nokkel = $hvor_passer","table=$tabell","field=$felt") if &db_execute($db,$sql);

    print $sql if $debug;
}
sub db_sett_inn {
    my ($db,$tabell,$felt,$verdier) = @_;
    my @felt = split/:/,$felt;
    my @verdier = split/:/,$verdier;
    my @val;
    my @key;

    @verdier = map rydd($_), @verdier;

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
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	print $sql if $debug;
	&skriv("DATABASE-INSERT","tuple=".join(" ",@val),"table=$tabell") if &db_execute($db,$sql);
	print $db->errorMessage;

    }
}
sub db_delete {
    my ($db,$tabell,$hvor) = @_;
#    my $nql = "\n\nSLETTER FRA TABELL |$tabell| HVOR |$hvor|";
    print my $sql = "DELETE FROM $tabell WHERE $hvor";
    &skriv("DATABASE-DELETE", "table=$tabell","where=$hvor");
  &db_execute($db,$sql);

#    print $sql;
}    
sub db_do_delete {
    my ($db,$tabell,$hvor) = @_;
#    my $nql = "\n\nSLETTER FRA TABELL |$tabell| HVOR |$hvor|";
    print my $sql = "DELETE FROM $tabell WHERE $hvor";
    &skriv("DATABASE-DELETE", "table=$tabell","where=$hvor");
  &db_execute($db,$sql);

#    print $sql;
}  
sub db_slett {
    my ($db,$tabell,$hvor_nokkel,$hvor_passer) = @_;
    if($hvor_passer){
	my $sql = "DELETE FROM $tabell WHERE $hvor_nokkel=\'$hvor_passer\'";
	&skriv("DATABASE-DELETE", "table=$tabell","where=$hvor_nokkel = $hvor_passer");
	&db_execute($db,$sql);

	print $sql if $debug;
    }
}    
#ikke i bruk

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
sub db_file_to_db {
    my %parameter = @_;

    my $db = $parameter{connection};
    my $file = $parameter{file};
    my $table = $parameter{table};
    my @fields = @{$parameter{databasefields}};
    my @fieldindex = @{$parameter{index}};
    my @fieldsequence;

    if($parameter{filefields}){
	@fieldsequence = @{$parameter{filefields}};
    } else {
	@fieldsequence = @{$parameter{databasefields}};
    }
    
    my $localfile = $navdir."local/".$file;
    my $navmefile = $navdir."navme/".$file;

    my %file = ();
    my %database;

    %file = %{&file_get_hash(file=>$navmefile,fields=>\@fields,sequence=>\@fieldsequence,index=>\@fieldindex,oldfile=>\%file)} if -r $navmefile;
    %file = %{&file_get_hash(file=>$localfile,fields=>\@fields,sequence=>\@fieldsequence,index=>\@fieldindex,oldfile=>\%file)} if -r $localfile;

    %database = %{&db_get_hash(connection=>$db,fields => \@fields,index=>\@fieldindex,query=>"SELECT ".join(",", @fields )." FROM ".$table)};

### sammenlikn data i hasher, legg inn, erstatt og slett
    &db_safe(connection=>$db,table=>$table,oldfields=>\@fields,index=>\@fieldindex,newfields=>\@fieldsequence,new=>\%file,old=>\%database,delete=>0);

    print "\n\n\n";
}
sub db_get_hash {
    my %parameter = @_;

    my $conn = $parameter{connection};
    my @oldindex = @{$parameter{index}};
    my $sql = $parameter{query};
    my %result = ();
    my @line = ();
    my @fields;

   if (exists($parameter{oldfields})){

	@fields = @{$parameter{oldfields}};

    } else {
	
	@fields = @{$parameter{fields}};
    }


### hvor mange nivåer indexeringshashen skal være på
    my $complexity = scalar(@oldindex);

    my @index = @{&make_sequence(\@oldindex,\@fields)};
	    

#    }
### get data into hash and sequence	 
    my $res = &db_select($conn,$sql);
    while(@line = $res->fetchrow()) {
       
	if($complexity==3){
	    $result{$line[$index[0]]}{$line[$index[1]]}{$line[$index[2]]} = [@line];
	} elsif ($complexity==2){
	    $result{$line[$index[0]]}{$line[$index[1]]} = [@line];
	} elsif ($complexity==1){
	    $result{$line[$index[0]]} = [@line];
	}
    }
    return \%result;
   
}
sub file_get_hash {
    my %parameter = @_;

    my $file = $parameter{file};
    my @oldindex = @{$parameter{index}};
    my %result = %{$parameter{oldfile}};
    my @line = ();
    my @newline = ();
    my $serial = 0;

    my @sequence;
    my @fields;

    if (exists($parameter{fields})){

	@fields = @{$parameter{fields}};
	@sequence = @{&make_sequence(\@{$parameter{fields}},\@{$parameter{sequence}})};

    } else {
	
	@fields = @{$parameter{fields}};
	@sequence = @{&count_sequence(scalar(@fields))};
	
    }

    my @index = @{&make_sequence(\@oldindex,\@fields)};

    my $complexity = scalar(@index);
    my $rest = scalar(@sequence);

    open (FILE, "<$file") || die ("KUNNE IKKE ÅPNE FILA: $file");
    foreach my $f(<FILE>) {
	@line = &file_get_line($f);
	@line = map rydd($_), @line;
	if($line[0]){
	    @newline = ();
	    for my $s (@sequence){
		my $new = $line[$s]||"";
		push(@newline,$new);
	    }
	    if($complexity==3){
		$result{$line[$index[0]]}{$line[$index[1]]}{$line[$index[2]]} = [@newline];
	    } elsif ($complexity==2){
		$result{$line[$index[0]]}{$line[$index[1]]} = [@newline];
	    } elsif ($complexity==1){
		$result{$line[$index[0]]} = [@newline];
		print $line[$index[0]]." = ".$newline[0].$newline[1]."\n";
	    }
	}
    }
    close FILE;
    return \%result;
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

sub db_do{
    my $db = $_[0];
    my $tabell = $_[1];
    my @felt = @{$_[2]};
    my @index = @{$_[3]};
    my @sequence = @{$_[4]};
    my %ny = %{$_[5]};
    my %gammel = %{$_[6]};
    my $delete = $_[7]||0;
    my $insert = $_[8]||1;
    my $update = $_[9]||1;

    if($delete eq "no"){

	$delete = 0;
    }

    my $niv = scalar(@index);

    if($niv == 3){ 
	for my $k1 ( keys %ny ) {
	    for my $k2 (keys %{$ny{$k1}}) {
		for my $k3 (keys %{$ny{$k1}{$k2}}) {
		    my $where = &lag_where(\@felt,\@index,[$k1,$k2,$k3]);
		    if(exists $gammel{$k1}{$k2}{$k3}) {
			print $k1." ".$k2." ".$k3." ER\n";;
			for my $i (0..$#felt ) {
				    
			    &db_do_update($db,$tabell,$felt[$i],$gammel{$k1}{$k2}{$k3}[$i],$ny{$k1}{$k2}{$k3}[$i],$where,$update);
			}
		    } else {

			    &db_do_insert($db,$tabell,\@felt,\@{$ny{$k1}{$k2}{$k3}},$insert);
			    print $k1." ".$k2." ".$k3." NY\n";;
		    }
		}
	    }
	}
	if($delete){
	    for my $k1 ( keys %gammel ) {
		for my $k2 (keys %{$gammel{$k1}}) {
		    for my $k3 (keys %{$gammel{$k1}{$k2}}) {
			unless($ny{$k1}{$k2}{$k3}[1]) {
			    my $where = &lag_where(\@felt,\@index,[$k1,$k2,$k3]);
			    &db_do_delete($db,$tabell,$where,$delete);
			}
		    }
		}
	    }
	}
    } elsif ($niv == 2){
	for my $k1 ( keys %ny ) {
	    for my $k2 (keys %{$ny{$k1}}) {
		my $where = &lag_where(\@felt,\@index,[$k1,$k2]);
		if(exists $gammel{$k1}{$k2}) {
		    for my $i (0..$#felt ) {
			&db_do_update($db,$tabell,$felt[$i],$gammel{$k1}{$k2}[$i],$ny{$k1}{$k2}[$i],$where,$update);
		    }
		} else {
		    &db_do_insert($db,$tabell,\@felt,\@{$ny{$k1}{$k2}},$insert);
		}
	    }
	}	
	if($delete){
	    for my $k1 ( keys %gammel ) {
		for my $k2 (keys %{$gammel{$k1}}) {
		    unless($ny{$k1}{$k2}[1]) {
			my $where = &lag_where(\@felt,\@index,[$k1,$k2]);
			if($gammel{$k1}{$k2}[1]){
			    &db_do_delete($db,$tabell,$where,$delete);
			}
		    }
		}
	    }
	}
    } elsif ($niv == 1){
	for my $k1 ( keys %ny ) {
	    print $k1;
	    my $where = &lag_where(\@felt,\@index,[$k1]);
	    if(exists $gammel{$k1}) {
		print $k1." ER\n";
		for my $i (0..$#felt ) {
		    &db_do_update($db,$tabell,$felt[$i],$gammel{$k1}[$i],$ny{$k1}[$i],$where,$update);
		}
	    } else {
		&db_do_insert($db,$tabell,\@felt,\@{$ny{$k1}},$insert);
		print $k1." NY\n";;
	    }
	}
    	
	if($delete){
	    for my $k1 ( keys %gammel ) {
		unless($ny{$k1}[1]) {
		    print $k1." DØ\n";
		    my $where = &lag_where(\@felt,\@index,[$k1]);
		    if($gammel{$k1}[1]){
			&db_do_delete($db,$tabell,$where,$delete);
		    }
		}
	    }
	}
	
    }
}
sub lag_where{
    my @felt = @{$_[0]};
    my @keys = @{$_[1]};
    my @vals = @{$_[2]};

    for my $i (@keys){
	print $i."iii\n";
    }

    my @where;
    if (defined($vals[0])){
	if($vals[0] eq ''){
	    $where[0] = $felt[$keys[0]]." is null ";
	} else {
	    $where[0] = $felt[$keys[0]]." = \'".$vals[0]."\' ";
	}
    }
    if (defined($vals[1])){
	if($vals[1] eq ''){
	    $where[1] = $felt[$keys[1]]." is null ";
	} else {
	    $where[1] = $felt[$keys[1]]." = \'".$vals[1]."\' ";
	}
    }
    if (defined($vals[2])){
	if($vals[2] eq ''){
	    $where[2] = $felt[$keys[2]]." is null ";
	} else {
	    $where[2] = $felt[$keys[2]]." = \'".$vals[2]."\' ";
	}
    }
    my $where = " ".join("AND ",@where);
    print "\n".$where."\n";
    return $where;
}
sub hent_scalar {
    my ($db,$sql) = @_;
    my $resultat;
    my $res =  &db_select($db,$sql);
    while(@_ = $res->fetchrow) {
	@_ = map rydd($_), @_;
	$resultat = $_[0] ;
    }
    return $resultat;
}

sub finn_og_bruk_deviceid {
    my $db = $_[0];
    my $sql = "select nextval(\'device_deviceid_seq\')";
    my $seq = &hent_scalar($db,$sql);
    &db_logg_insert($db, "device", ["deviceid"],[$seq]);
    return $seq;
}
sub db_safe {
    my %parameter = @_;

    unless(
	   exists($parameter{old}) && 
	   exists($parameter{new}) && 
	   (exists($parameter{oldfields}) || exists($parameter{fields})) && 
	   exists($parameter{table}) &&
	   exists($parameter{connection})
	   ){
	
	die("Parametrene er ikke fullstendig utfylt");

    } else {

	### Her begynner det

	my %old = %{$parameter{old}};
	my %new = %{$parameter{new}};
	my $table = $parameter{table};
	my $connection = $parameter{connection};
	my @sequence;
	my @index;
	my @fields;
	

	### To mulige veier videre:
	### 1: hvis bare fields er satt, ikke tenk på rekkefølger
	### 2: hvis oldfields er satt, stokk om på rekkefølgen etter newfields

	if (exists($parameter{oldfields})){

	    @fields = @{$parameter{oldfields}};
	    @sequence = @{&make_sequence(\@{$parameter{oldfields}},\@{$parameter{newfields}})};

	} else {
	    
	    @fields = @{$parameter{fields}};
	    @sequence = @{&count_sequence(scalar(@fields))};
   
	}

	unless (exists($parameter{index})){

	    @index = ("0");

	} else {

	    @index = @{&make_sequence(\@{$parameter{index}},\@fields)};
	    
	}

	&db_do($connection,$table,\@fields,\@index,\@sequence,\%new,\%old,$parameter{delete},$parameter{insert},$parameter{update});


    }
}

sub make_sequence {

    my @index = @{$_[0]};
    my @fields = @{$_[1]};
    my @newindex;

    for my $i (0..$#index){

	for my $j (0..$#fields){

	    if ($index[$i] eq $fields[$j]){
		
		$newindex[$i] = $j;

	    }

	}

	unless(defined($newindex[$i])){

	    $newindex[$i] = 0;
	}
    }

    return \@newindex;
}

sub count_sequence {
    
    my $number = $_[0]-1;

    my @sequence;

    for (0..$number){
	$sequence[$_] = $_;
    }

    return \@sequence;
}

sub error_correct{
    my $conn = $_[0];
    my $sql = $_[1];
    my $errmsg = $_[2];
    chomp($errmsg);
    if($errmsg =~ /ERROR:  Cannot insert a duplicate key into unique index (\w+?)_/){
	if($sql =~ s/UPDATE/DELETE FROM/){
	    $sql =~ s/SET .* (WHERE)/$1/;
	    &skriv("DATABASE-ALREADY", "sql=$sql", "message=".$errmsg);
	    &db_execute($conn,$sql);
	} else {
	    &skriv("DATABASE-ALREADY", "sql=$sql", "message=".$errmsg);
	}
    } elsif ($errmsg =~ /ERROR:  value too long for type character varying\((\d+)\)/){
	my $lengde = $1;
	if($sql =~ /^UPDATE (\w+) SET (\w+)=(.*) WHERE/){
	    
	    &skriv("TEXT-TOOLONG", "table=$1","field=$2","value=$3","length=$lengde");
	    
	} else {
	      &skriv("TEXT-TOOLONG", "table=\"$sql\"","field=","value=$errmsg","length=$lengde");
	}

    } elsif ($errmsg =~ /ERROR:  ExecAppend: Fail to add null value in not null attribute (\w+)/){
	&skriv("DATABASE-NOTNULL", "sql=$sql","value=$1");
	
    } elsif ($errmsg =~ /ERROR:  \<unnamed\> referential integrity violation - key referenced from (\w+) not found in (\w+)/){
	
	my $child = $1;
	my $parent = $2;

	my $field;

	if($sql =~ /UPDATE \w+ SET (\w+)\=(.*) WHERE/){
	
	    $field = "(".$1."=".$2.")";
	}
	&skriv("DATABASE-REFERENCE", "sql=$sql","child=$child", "field=$field","parent=$parent");
	
    } else {
	&skriv("DATABASE-ERROR", "sql=$sql", "message=".$errmsg);
    }
}

sub rydd {    
    if (defined $_[0]) {
	$_ = $_[0];
	s/\\/\\\\/;
	s/\'/\\\'/;
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

sub db_readconf {
    return &hash_conf('/usr/local/nav/local/etc/conf/db.conf');
}

sub db_get {
    my $myself = $_[0];

    my %hash = &db_readconf();
			
    my $db_user = $hash{'script_'.$myself};
    my $db_passwd = $hash{'userpw_'.$db_user};
    my $db_db = $hash{'db_'.$db_user};
    my $db_host = $hash{'dbhost'};
    my $db_port = $hash{'dbport'};
						    
    my $conn = Pg::connectdb("host=$db_host port=$db_port dbname=$db_db user=$db_user password=$db_passwd");
    die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
}
sub db_select {
    my $sql = $_[1];
    my $conn = $_[0];
    my $resultat = $conn->exec($sql);
    unless ($resultat->resultStatus eq PGRES_TUPLES_OK){
	&skriv("DATABASE-ERROR", "sql=$sql", "message=".$conn->errorMessage);
    }
    return $resultat;
}
sub db_execute {
    my $sql = $_[1];
    my $conn = $_[0];
    my $resultat = $conn->exec($sql);
    unless ($resultat->resultStatus eq PGRES_COMMAND_OK){
	&error_correct($conn,$sql,$conn->errorMessage);
	return 0;
#	&skriv("DATABASE-ERROR", "sql=$sql", "message=".$conn->errorMessage);
    }
    return 1;
}

#return 1;
