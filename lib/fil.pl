#!/usr/bin/perl
#
# $Id: fil.pl,v 1.11 2002/08/05 14:16:37 gartmann Exp $
#

#Lagt inn av KH & JM 18.06.02
#require "/usr/local/nav/navme/lib/database.pl";

#use strict;
sub log_open {
    open(COLLECTLOG,'>>','/usr/local/nav/local/log/syslog/navmessage.log');
}

sub log_close {
    close(COLLECTLOG);
}

sub fil_hent_linje {
    (my $felt,$_) = @_;
    #tar med linjer som begynner med ord før kolon bestående av 
    #tall,bokstaver,lavstrek,bindestrek,punktum
    if (/^[a-zA-Z0-9_\-\.]+?:/) {
	#sletter ting som er ekstra i stedet for å slå 
	#sammen med seinere feilkolonner.
	(my @linje,undef) = split(/:/,$_,$felt+1); 
	@linje = map rydd($_), @linje; #rydder opp
	return @linje;
#    } else {
#	return 0;
    }
}    
sub file_get_line {
    my $l = $_[0];
    #tar med linjer som begynner med ord før kolon bestående av 
    #tall,bokstaver,lavstrek,bindestrek,punktum
    if ($l =~ /^([a-zA-Z0-9_\-\.]+):?/) {
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
sub fil_hent_hash {
    my $fil = $_[0];
    my $felt = $_[1];
    my %resultat = %{$_[2]};
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

sub fil_netaddr{
    my $netaddr = $_[0];
    my $mask = $_[1];
    unless($mask == 32){
	$netaddr .= "/".$mask;
    }
    return $netaddr;
}


my %types = &get_types("collect");

sub get_types {
    my $class = $_[0];
    my %hash = &db_readconf();
    my $script = 'fil';
    my $user = $hash{'script_' . $script};
    my $userpw = $hash{'userpw_' . $user};

    my $syslogconnection = &db_connect($hash{db_syslog}, $user, $userpw);
    my %types = &db_hent_hash($syslogconnection,"select id,type,message from messagetemplate where class=\'$class\'");

    return %types;
}


sub device_endring {
#helt lik
    my $db = $_[0];
    my %ny = %{$_[1]};
    my %gammel = %{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];
    for my $feltnull (keys %ny) {
	&device_endring_per_linje($db,\@{$ny{$feltnull}},\@{$gammel{$feltnull}},\@felt,$tabell,$feltnull);
    }
}

sub device_endring_per_linje {
    my $db = $_[0];
    my @ny = @{$_[1]};
    my @gammel = @{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];
    my $id = $_[5];
    my $niv = $_[6]||0;
    
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
### legger til deviceid til bokslinja.
	my $seq = &finn_og_bruk_deviceid();
	push(@felt, "deviceid");
	push(@ny, $seq);
	&db_logg_insert($db,$tabell,\@felt,\@ny);
    }
}
sub skriv {

    my ($identificator,@parameters) = @_;
    my %parameter = ();

    my $filename = $0;

    for my $parameter (@parameters) {
#	print "\n$parameter";
	my ($key,$value) = split /\=/,$parameter,2;
#	print " $key = $value - ";
	$parameter{$key} = $value;

    }

    my $newidentificator = $types{$identificator}[1]||"";
    my $message = $types{$identificator}[2]||"";

#    print $message."\n";

    $message =~ s/\$(\w+)/$parameter{$1}/g;

#    print $message."\n";


    $filename =~ /^.*?\/?(\w+\.\w+)$/;
    $filename = $1;

    my $text = $filename." %$newidentificator %$message\n";

=cut
    print DBERR $tekst if $handle =~ /DBERR/;
    print DBOUT $tekst if $handle =~ /DBOUT/;
    print SNERR $tekst if $handle =~ /SNERR/;
    print SNOUT $tekst if $handle =~ /SNOUT/;
    print GWERR $tekst if $handle =~ /GWERR/;
    print GWOUT $tekst if $handle =~ /GWOUT/;
    print SWERR $tekst if $handle =~ /SWERR/;
    print SWOUT $tekst if $handle =~ /SWOUT/;

    print $tekst unless fileno($handle);
=cut

 #   &printlog($text);
    my $time = scalar localtime;
    if(my $i = $_[0]){
#	print COLLECTLOG $time." ".'%'.$i;
    }
    return 1;

}

sub printlog{
    my $time = scalar localtime;
    if(my $i = $_[0]||0){
	print COLLECTLOG $time." ".'%'.$i;
    }
    return 1;
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

sub read_navconf 
{
    return hash_conf('/usr/local/nav/local/etc/conf/nav.conf');
}

return 1;

