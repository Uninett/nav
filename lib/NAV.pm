package NAV;
####################
#
# $Id: NAV.pm,v 1.6 2002/11/25 10:52:09 gartmann Exp $
# This file is part of the NAV project.
# NAV module contains the common methods / subroutines that NAV scripts are
# using. It also does some initial work regarding the NAVlog system.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

require Exporter;
use strict;
use Pg;
use Fcntl qw/:flock/;
#use FileHandle;
use SNMP;
use SNMP_util;
use Socket;

our @ISA = qw(Exporter);
our @EXPORT = qw(log_open log_close skriv log_write db_get get_path db_safe rydd db_select db_execute db_connect db_readconf hash_conf and_ip mask_bits);
our @EXPORT_OK = qw(db_file_to_db fil_hent db_hent_hash db_endring_per_linje db_endring db_sletting db_hent_enkel fil_hent_linje db_delete db_logg_insert db_sett_inn db_insert db_oppdater fil_netaddr db_select_hash db_update db_hent_dobbel snmpsystem snmperrorcorrect verifymib fjern_endelse snmp_type hent_ip hent_dnsname sigwalk siget hent_scalar db_slett db_do_delete get_log make_and_get_sequence_number);
our %EXPORT_TAGS = (
		    collect => [qw(db_file_to_db fil_hent db_hent_hash db_endring_per_linje db_endring db_sletting db_hent_enkel fil_hent_linje db_delete db_logg_insert db_sett_inn db_insert db_oppdater db_select_hash db_update db_hent_dobbel fil_netaddr hent_scalar db_slett db_do_delete)],
		    fil => [qw(fil_netaddr)],
		    snmp => [qw(snmpsystem snmperrorcorrect verifymib fjern_endelse snmp_type hent_ip hent_dnsname sigwalk siget)],
		    log => [qw(get_log make_and_get_sequence_number)],
		    );

our @VERSION = 3.0;

my $NAVDIR = "/usr/local/nav/";
my %conf = &hash_conf($NAVDIR."navme/etc/conf/collect/collect.conf");
my %types = &get_types("navmessage");

my $debug = 1;

sub get_path{
    my $que = $_[0];
    return $conf{$que};
}


# Leser inn en config-fil i en hash. Config-filen må være av type
# "navn=verdi". Denne kan brukes til å lese nav.conf, db.conf og andre
# filer etter samme lest.
sub hash_conf
{
    my $conffile = shift or return undef;

    open(my $FD, $conffile) || die "Could not open $conffile: $!\n";
    my %hash = map { /\s*(.+?)\s*=\s*(.*?)\s*(\#.*)?$/ && $1 => $2 } 
    grep { !/^(\s*\#|\s+)$/ && /.+=.*/ } <$FD>;
    close($FD);

    return %hash;
}

sub db_readconf {
    return &hash_conf($NAVDIR.'local/etc/conf/db.conf');
}

sub db_get {
    my $myself = $_[0];

    my %hash = &db_readconf();
			
    my $db_user = $hash{'script_'.$myself};
    my $db_passwd = $hash{'userpw_'.$db_user};
    unless($db_passwd){
	die "Database password information not supplied in database configuration file\n";
    }
    my $db_db = $hash{'db_'.$db_user};
    my $db_host = $hash{'dbhost'};
    my $db_port = $hash{'dbport'};
						    
    my $conn = Pg::connectdb("host=$db_host port=$db_port dbname=$db_db user=$db_user password=$db_passwd");
    die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
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
sub get_types {
    my $system = $_[0];
    my $connection = db_get("navlogadmin");
    my @fields = ("facility","mnemonic","priorityid","defaultmessage");
    my %temp_types = &db_select_hash($connection,"type join system on (system.id=type.systemid) where name=\'$system\'",\@fields,0,1);

    my %types;
    foreach my $t (keys %temp_types){
	foreach my $tt (keys %{$temp_types{$t}}){
	    $types{$temp_types{$t}{$tt}[0]."-".$temp_types{$t}{$tt}[1]} = [$temp_types{$t}{$tt}[0]."-".($temp_types{$t}{$tt}[2]-1)."-".$temp_types{$t}{$tt}[1],
									   $temp_types{$t}{$tt}[3]
									   ];
	}
    }
    return %types;
}

sub log_open {
    my $file = $_[0] || '/usr/local/nav/local/log/syslog/navmessage.log';
    ### åpner loggfil for appending, lager ny hvis den ikke eksisterer.
    #sysopen fungerer ikke som jeg vil
    #sysopen(COLLECTLOG, $file, 'O_WRONLY' | 'O_APPEND'|'O_CREAT');
    my $make;

    print "åpner log \n" if $debug;

    unless(-e $file){
	$make = 1;
    }
    open(COLLECTLOG,'>>',$file);
    print "skal teste om jeg er root\n" if $debug;
    if($< == "0"){
	print "jeg er visst root\n" if $debug;
### hvis fila blir opprettet nå (av root) blir nav eier.	
	`chgrp nav $file;chmod 775 $file`;
    }
    print "skal nå prøve å låse fila\n" if $debug;
    flock(COLLECTLOG, LOCK_EX) or die "klarte ikke å låse fila: $!";
    print "har fått log\n" if $debug;
}

sub log_close {
    $|=1;
    flock(COLLECTLOG, LOCK_UN);
    close(COLLECTLOG);
}

sub log_write {

    my ($identificator,@parameters) = @_;
    my %parameter = ();

    my $filename = $0;

    for my $parameter (@parameters) {
#	print "\n$parameter";
	my ($key,$value) = split /\=/,$parameter,2;
#	print " $key = $value - ";
	$parameter{$key} = $value;

    }

    my $newidentificator = $types{$identificator}[1];
    my $message = $types{$identificator}[2];

#    print $message."\n";

    $message =~ s/\$(\w+)/$parameter{$1}/g;

#    print $message."\n";


    $filename =~ /^.*?\/?(\w+\.\w+)$/;
    $filename = $1;

    my $text = $filename." %$newidentificator: $message\n";

    &printlog($text);

    return 1;

}
sub skriv { # alias for log_write

    my ($identificator,@parameters) = @_;
    my %parameter = ();

    my $filename = $0;

    for my $parameter (@parameters) {
#	print "\n$parameter";
	my ($key,$value) = split /\=/,$parameter,2;
#	print " $key = $value - ";
	$parameter{$key} = $value;

    }

    my $newidentificator = $types{$identificator}[1];
    my $message = $types{$identificator}[2];

#    print $message."\n";

    $message =~ s/\$(\w+)/$parameter{$1}/g;

#    print $message."\n";


    $filename =~ /^.*?\/?(\w+\.\w+)$/;
    $filename = $1;

    my $text = $filename." %$newidentificator: $message\n";

    &printlog($text);

    return 1;

}

sub printlog{
    my $time = scalar localtime;
    my $text = $_[0];
    $text =~ s/\'//g;

    if (fileno(COLLECTLOG)){
	#hvis filehandle finnes, skriv til fil og stdout
	print COLLECTLOG $time." ".$text;
	print $time." ".$text;
    } else {
	#skriv bare til stdout
	print $time." ".$text;
    }
    return 1;
}

sub file_netaddr{
    my $netaddr = $_[0];
    my $mask = $_[1];
    if($netaddr){
	unless($mask == 32){
	    $netaddr .= "/".$mask;
	}
	return $netaddr;
    }
}
sub fil_netaddr{
    my $netaddr = $_[0];
    my $mask = $_[1];
    if($netaddr && $mask){
	$netaddr .= "/".$mask;
    }
    return $netaddr;
}

sub db_do{
    my %parameter = @_;
    print "er i db_do\n" if $debug;

    unless(
	   exists($parameter{connection}) && 
	   exists($parameter{table}) && 
	   exists($parameter{fields}) &&
	   exists($parameter{old}) &&
	   exists($parameter{new}) &&
	   exists($parameter{index}) 
	   ){

	die("Parametrene er ikke fullstendig utfylt\n");
	
    } else {

	my $db = $parameter{connection};
	my $tabell = $parameter{table};
	my @felt = @{$parameter{fields}};
	my @index = @{$parameter{index}};
	my @sequence = @{$parameter{sequence}};
	my %ny = %{$parameter{new}};
	my %gammel = %{$parameter{old}};
	my $delete = $parameter{delete}||0;
	my $insert = $parameter{insert}||1;
	my $update = $parameter{update}||1;

	$delete = 0 if $delete eq "no";
	
    my $niv = scalar(@index);

	if($niv == 3){ 
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
	    for my $k1 ( keys %ny ) {
		for my $k2 (keys %{$ny{$k1}}) {
		    for my $k3 (keys %{$ny{$k1}{$k2}}) {
			my $where = &lag_where(\@felt,\@index,[$k1,$k2,$k3]);
			if(exists $gammel{$k1}{$k2}{$k3}) {
			    for my $i (0..$#felt ) {
				
				&db_do_update(connection =>$db,table =>$tabell,field=>$felt[$i],old=>$gammel{$k1}{$k2}{$k3}[$i],new=>$ny{$k1}{$k2}{$k3}[$i],where => $where,update =>$update);
			    }
			} else {
			    
			    &db_do_insert($db,$tabell,\@felt,\@{$ny{$k1}{$k2}{$k3}},$insert);
			}
		    }
		}
	    }
	} elsif ($niv == 2){
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
	    for my $k1 ( keys %ny ) {
		for my $k2 (keys %{$ny{$k1}}) {
		    my $where = &lag_where(\@felt,\@index,[$k1,$k2]);
		    if(exists $gammel{$k1}{$k2}) {
			for my $i (0..$#felt ) {
			    &db_do_update(connection => $db,table => $tabell,field => $felt[$i],old => $gammel{$k1}{$k2}[$i],new => $ny{$k1}{$k2}[$i],where => $where,update => $update);
			}
		    } else {
			&db_do_insert($db,$tabell,\@felt,\@{$ny{$k1}{$k2}},$insert);
		    }
		}
	    }
	} elsif ($niv == 1){
	    if($delete){
		for my $k1 ( keys %gammel ) {
		    unless($ny{$k1}[1]) {
			my $where = &lag_where(\@felt,\@index,[$k1]);
			if($gammel{$k1}[1]){
			    &db_do_delete($db,$tabell,$where,$delete);
			}
		    }
		}
	    } 
	    for my $k1 ( keys %ny ) {
		my $where = &lag_where(\@felt,\@index,[$k1]);
		if(exists $gammel{$k1}) {
		    for my $i (0..$#felt ) {
			&db_do_update(connection => $db,table => $tabell,field => $felt[$i],old => $gammel{$k1}[$i],new => $ny{$k1}[$i],where => $where,update => $update);
		    }
		} else {
		    &db_do_insert($db,$tabell,\@felt,\@{$ny{$k1}},$insert);
		}
	    }
	}
	print "done\n" if $debug;
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
#	print $verdier[$i]."\n";
	if (defined($verdier[$i]) && $verdier[$i] ne ''){
	    push(@val, "\'".$verdier[$i]."\'");
	    push(@key, $felt[$i]);
	}
    }
    if(scalar(@key)){ #key eksisterer
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
#	print $sql."\n" if $debug;
	if($insert eq "nolog"){
	    &db_execute($db,$sql);
	} else {
	    &skriv("DATABASE-INSERT", "table=$tabell", "tuple=".join(" ",@val)) if &db_execute($db,$sql);
#	    print $db->errorMessage;

	}
    }
}
sub db_do_update {
    my %parameter = @_;
    
    unless(
	   exists($parameter{old}) && 
	   exists($parameter{new}) && 
	   exists($parameter{connection}) &&
	   exists($parameter{table}) &&
	   exists($parameter{field}) && 
	   exists($parameter{where}) 
	   ) {

	die("Parametrene er ikke fullstendig utfylt\n");
	
    } else {
	my $db = $parameter{connection};
	my $tabell = $parameter{table};
	my $felt = $parameter{field};
	my $fra = $parameter{old};
	my $til = $parameter{new};
	my $hvor = $parameter{where};

	my $update;
	if(exists($parameter{update})){
	    $update = $parameter{update};
	}
	
    } else {
	my $db = $parameter{connection};
	my $tabell = $parameter{table};
	my $felt = $parameter{field};
	my $fra = $parameter{old};
	my $til = $parameter{new};
	my $hvor = $parameter{where};

	my $update;
	if(exists($parameter{update})){
	    $update = $parameter{update};
	}
	$til = &rydd($til);
	unless($til eq $fra) {
	    if (!$til && $fra){
		my $sql = "UPDATE $tabell SET $felt=null WHERE $hvor";
		&skriv("DATABASE-UPDATE", "from=$fra","to=null","where=$hvor","table=$tabell", "field=$felt") if &db_execute($db,$sql);
		
	    } elsif ($til) {
		my $sql = "UPDATE $tabell SET $felt=\'$til\' WHERE $hvor";

		if($update eq "swport" && $felt eq "trunk"){
		    my $swportid = &hent_scalar($db,"SELECT swportid from swport WHERE $hvor");
		    &db_do_delete($db,"swportvlan","swportid=$swportid");
		} 
		&skriv("DATABASE-UPDATE", "from=$fra","to=$til","where=$hvor","table=$tabell","field=$felt") if &db_execute($db,$sql);
	    }
	}
    }
}
sub db_do_delete {
    my ($db,$tabell,$hvor,$special) = @_[0..2];
    if($special eq "swport"){
	&db_do_delete($db,"swport",$hvor." and swportbak is not null");
    }
    my $sql = "DELETE FROM $tabell WHERE $hvor";
    &skriv("DATABASE-DELETE", "table=$tabell","where=$hvor");
    &db_execute($db,$sql);
    
#    print $sql;
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
	
	die("Parametrene er ikke fullstendig utfylt\n");

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

	&db_do(connection => $connection,table => $table,fields=> \@fields,index => \@index,sequence => \@sequence,new => \%new,old =>  \%old,delete => $parameter{delete},insert => $parameter{insert},update => $parameter{update});


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
#		print "setter ".$fields[$j]." i felt $i\n";
	    }

	}

	unless(defined($newindex[$i])){
#	    print "satt lik 0 : $i";
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

sub lag_where{
    my @felt = @{$_[0]};
    my @keys = @{$_[1]};
    my @vals = @{$_[2]};

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
    return $where;
}

sub db_file_to_db {
    my %parameter = @_;

    print "er i file_to_db\n" if $debug;

    my $db = $parameter{connection};
    my $file = $parameter{file};
    my $table = $parameter{table};
    my @fields = @{$parameter{databasefields}};
    my @fieldindex = ();
    my @fieldsequence;

    if($parameter{filefields}){
	@fieldsequence = @{$parameter{filefields}};
    } else {
	@fieldsequence = @{$parameter{databasefields}};
    }

    unless(exists($parameter{index})){
	@fieldindex = ("0");
    } else {
	@fieldindex = @{&make_sequence(\@{$parameter{index}},\@fields)};
	
    }

    my $localfile = get_path("path_local").$file;
    my $navmefile = get_path("path_navme").$file;

    my %file = ();
    my %database;

    %file = %{&file_get_hash(file=>$navmefile,fields=>\@fields,sequence=>\@fieldsequence,index=>\@fieldindex,oldfile=>\%file)} if -r $navmefile;
    %file = %{&file_get_hash(file=>$localfile,fields=>\@fields,sequence=>\@fieldsequence,index=>\@fieldindex,oldfile=>\%file)} if -r $localfile;

    %database = %{&db_get_hash(connection=>$db,fields => \@fields,index=>\@fieldindex,query=>"SELECT ".join(",", @fields )." FROM ".$table)};

### sammenlikn data i hasher, legg inn, erstatt og slett
    &db_do(connection=>$db,table=>$table,fields=>\@fields,index=>\@fieldindex,sequence=>\@fieldsequence,new=>\%file,old=>\%database,delete=>1);

}
sub db_get_hash {
    my %parameter = @_;

    my $conn = $parameter{connection};
    my @index = @{$parameter{index}};
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
    my $complexity = scalar(@index);

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
    my @index = @{$parameter{index}};
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
		$result{$newline[$index[0]]}{$newline[$index[1]]}{$newline[$index[2]]} = [@newline];
	    } elsif ($complexity==2){
		$result{$newline[$index[0]]}{$newline[$index[1]]} = [@newline];
#		print $line[$index[0]].$line[$index[1]]." = ".$newline[0].$newline[1]."\n";
	    } elsif ($complexity==1){
		$result{$newline[$index[0]]} = [@newline];
#		print $line[$index[0]]." = ".$newline[0].$newline[1]."\n";
	    }
	}
    }
    close FILE;
    return \%result;
}

sub file_get_line {
    my $l = $_[0];
    #tar med linjer som begynner med ord før kolon bestående av 
    #tall,bokstaver,lavstrek,bindestrek,punktum
    if ($l =~ /^([\p{IsAlnum}_\-\.]+):?/) {
	if($1){
	#sletter ting som er ekstra i stedet for å slå 
	#sammen med seinere feilkolonner.
	(my @line) = split(/:/,$l); 
#	for(@line){print};
#	@line = map rydd($_), @line; #rydder opp
	return @line;
    }
    } else {
	return 0;
    }
}    
sub fil_hent_linje {
    (my $felt,$_) = @_;
    #tar med linjer som begynner med ord før kolon bestående av 
    #tall,bokstaver,lavstrek,bindestrek,punktum
    if (/^[\p{IsAlnum}_\-\.]+?:/) {
	#sletter ting som er ekstra i stedet for å slå 
	#sammen med seinere feilkolonner.
	(my @linje,undef) = split(/:/,$_,$felt+1); 
	@linje = map rydd($_), @linje; #rydder opp
	return @linje;
#    } else {
#	return 0;
    }
}  

sub fil_hent {
    my ($fil,$felt) = @_;
    my %resultat = ();
    my @linje = ();
    open (FIL, "<$fil") || die ("KUNNE IKKE ÅPNE FILA: $fil");
    foreach (<FIL>) {
	if(@linje = &fil_hent_linje($felt,$_)){
	    $resultat{$linje[0]} = [ @linje ]; #legger inn i hash
	}
    }
    close FIL;
    return %resultat;
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
	if($sql =~ /^UPDATE (\w+) SET (\w+)=(.*) WHERE/i){
	    
	    &skriv("TEXT-TOOLONG", "table=$1","field=$2","value=$3","length=$lengde");
	} elsif($sql =~ /^INSERT INTO (\w+) \((.+?)\) VALUES \((.+?)\)/i){
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
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	&skriv("DATABASE-INSERT","tuple=".join(" ",@val),"table=$tabell") if &db_execute($db,$sql);

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
#	print $verdier[$i]."\n";
	if (defined($verdier[$i]) && $verdier[$i] ne ''){
	    push(@val, "\'".$verdier[$i]."\'");
	    push(@key, $felt[$i]);
	}
    }
    if(scalar(@key)){
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	&db_execute($db,$sql);
    }
}
sub db_update {
    my ($db,$tabell,$felt,$fra,$til,$hvor) = @_;
    $til = &rydd($til);
    unless($til eq $fra) {
	if (!$til && $fra){
	    my $sql = "UPDATE $tabell SET $felt=null WHERE $hvor";
	    &skriv("DATABASE-UPDATE", "from=$fra","to=null","where=$hvor","table=$tabell", "field=$felt") if &db_execute($db,$sql);

	} elsif ($til) {
	    my $sql = "UPDATE $tabell SET $felt=\'$til\' WHERE $hvor";
	    &skriv("DATABASE-UPDATE", "from=$fra","to=$til","where=$hvor","table=$tabell","field=$felt") if &db_execute($db,$sql);
	}
    }
}

sub db_oppdater {
    my ($db,$tabell,$felt,$fra,$til,$hvor_nokkel,$hvor_passer) = @_;

    my $sql = "UPDATE $tabell SET $felt=$til WHERE $hvor_nokkel=\'$hvor_passer\'";
    &skriv("DATABASE-UPDATE", "from=$fra","to=$til","where=$hvor_nokkel = $hvor_passer","table=$tabell","field=$felt") if &db_execute($db,$sql);

}
sub db_delete {
    my ($db,$tabell,$hvor) = @_;
#    my $nql = "\n\nSLETTER FRA TABELL |$tabell| HVOR |$hvor|";
    my $sql = "DELETE FROM $tabell WHERE $hvor";
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

    }
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
sub db_logg_insert {
    my $db = $_[0];
    my $tabell = $_[1];
    my @felt = @{$_[2]};
    my @verdier = @{$_[3]};

    my @val;
    my @key;
    foreach my $i (0..$#felt) {
#	print $verdier[$i]."\n";
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
	my $sql = "INSERT INTO $tabell (".join(",",@key ).") VALUES (".join(",",@val).")";
	&skriv("DATABASE-INSERT", "table=$tabell", "tuple=".join(" ",@val)) if &db_execute($db,$sql);
    }
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
###############################################
### SNMP
###############################################


sub snmpsystem{
    my ($host,$community,$endelser) = @_;

    # kan ikke gjøre noe før vi har community
    if ($community){
	# henter dnsname og fjerner domain suffix
	my $dns = &hent_dnsname($host);
	$dns = &fjern_endelse($dns,$endelser);

	# oppretter et snmpobjekt, og henter type og sysname derfra.
	my $sess = new SNMP::Session(DestHost => $host, Community => $community, Version => 1, Timeout => 1000000, Retries => 1);
	my $vars = new SNMP::VarList(['1.3.6.1.2.1.1.5.0'], ['1.3.6.1.2.1.1.2.0']);
	my ($sys, $type) = $sess->get($vars);   

	# hvis sysname ok:
	if($sys){
	    $sys = &fjern_endelse($sys,$endelser);
	    # rapporterer at vi henter data fra "sysname"
	    &skriv("DEVICE-COLLECT","ip=$sys");
	    
	    # rapporter feilmelding hvis dns og sysname er forskjellige
	    unless($dns eq $sys) {
		&skriv("DNS-NAMECHAOS", "ip=$host", "sysname=$sys", "dns=$dns");
	    }
	} else {
	    # skriver ut feilmelding hvis ikke svar, etc.
	    my $error = $sess->{ErrorStr};

	    # rapporterer at vi henter data fra "ip"
	    &skriv("DEVICE-COLLECT","ip=$host");

	    # hvis feilmelding, rapporter riktig type feilmelding,
	    # hvis ikke: rapporter at vi her bruker dns, siden vi ikke
	    # fikk noe sysname
	    if($error){
		&snmperrorcorrect($host,$error);
	    } else {
		&skriv("SNMP-DNSNAME", "ip=$host", "dns=$dns");
	    }

	    #dns brukes som sysname hvis sysname ikke fins.
	    $sys = $dns;
	}
	# fjerner punktum fra starten av OID
	$type =~ s/^\.//; 
	return ($sys,$type);
    }
}

sub snmperrorcorrect {
    my $error = $_[1];
    my $ip = $_[0];

    if($error =~ /^Timeout/){
	
	&skriv("SNMP-TIMEOUT","ip=$ip");

    } else {

	&skriv("SNMP-ERROR", "ip=$ip", "message=$error");
    }
}

sub verifymib{
    if($_[0]){
	return 1;
    } else {
	return 0;
    }
}

sub fjern_endelse{
    
    # tar inn sysname
    my $sysname = $_[0];

    # splitter de forskjellige endelsene, der skilletegn er , eller :
    my @endelser =  split(/:|,/,$_[1]);

    #for hver endelse
    for my $endelse (@endelser) {
	
	# fjern endelse fra name
	$sysname =~ s/\.?$endelse//i;
    }
    return $sysname;
}


# depricated
sub snmp_type{
    my ($ip,$ro,$mib) = @_;
    my $resultat = 0;
    if ($ro) {
        ($resultat) = &snmpget("$ro\@$ip:161:1:2:4",$mib);
    }
    return $resultat;
}

sub hent_ip{
    if (defined $_[0]){
	if(my $ip = gethostbyname($_[0])){
	    return inet_ntoa($ip);
	} else {
	    return 0;
	}
    } else {
	return "";
    }   
}
sub hent_dnsname{
    if (defined $_[0]){
	my $dns;
	if($dns =&inet_aton($_[0])){
	    $dns = gethostbyaddr($dns,AF_INET);
	    return $dns;
	} else {
	    return 0;
	}
    } else {
	return 0;
    }   
}
sub sigwalk{
    my $session = $_[0];
    my $mib = $_[1];
    my $vb = new SNMP::Varbind([$mib]);
    my @min = ();
    $min[0] = $mib;
    my $teller = 0;
    my @resultat = ();
    while ($min[0] =~ /^$mib/) {

	if(exists $min[1]){
	    $min[0] =~ /$mib\.(\S+)/;
	    my $temp;
	    if($1){
		$temp = $1.".".$min[1];
	    } else {
		$temp = $min[1];
	    }
	    $resultat[$teller] = [$temp,$min[2]];
	    $teller++;
	}
	$session->fgetnext($vb);
	@min = @{$vb};
    }
    return @resultat;
}
sub siget {
    my $session = $_[0];
    my $mib = $_[1];
    return $session->get($mib);
}

###############################################
### IP
###############################################
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
    if    (/255.255.128.0/)   { return 17; }
    elsif (/255.255.192.0/)   { return 18; }
    elsif (/255.255.224.0/)   { return 19; }
    elsif (/255.255.240.0/)   { return 20; }
    elsif (/255.255.248.0/)   { return 21; }
    elsif (/255.255.252.0/)   { return 22; }
    elsif (/255.255.254.0/)   { return 23; }
    elsif (/255.255.255.0/)   { return 24; }
    elsif (/255.255.255.128/) { return 25; }
    elsif (/255.255.255.192/) { return 26; }
    elsif (/255.255.255.224/) { return 27; }
    elsif (/255.255.255.240/) { return 28; }
    elsif (/255.255.255.248/) { return 29; }
    elsif (/255.255.255.252/) { return 30; }
    elsif (/255.255.255.254/) { return 31; }
    elsif (/255.255.255.255/) { return 32; }
    else
    {
        return 0;
    }
}   
###############################################
### LOG
###############################################
sub get_log {
    my $fil = $_[0];
    my $delete = $_[1]||0;
    ### åpner en fil for oppdatering, trenger ikke eksistere fra før.
    open(SYSLOG, "+<$fil") or die "error: $!";
    flock(SYSLOG, LOCK_EX) or die "klarte ikke å låse fila: $!";
    @_ = <SYSLOG>;
    truncate(SYSLOG,0) if $delete; #slett gammel fil
    flock(SYSLOG, LOCK_UN);
    close SYSLOG;
    return @_;
}
sub make_and_get_sequence_number {
    my $connection = $_[0];
    my $table = $_[1];
    my $field = $_[2];

    my $seq_name = $table."_".$field."_seq";
    my $sequence_number = &hent_scalar($connection, "select nextval(\'$seq_name\')");
    return $sequence_number;
}

1;
