#!/usr/bin/perl

#use strict;
sub log_open {
    open(COLLECTLOG,'>>','/usr/local/nav/local/log/collect/navllog.log');
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

sub fil_prefiks {
    my ($fil,$felt) = @_;
    my %resultat;
#    my @linje = ();
    open (FIL, "<$fil") || die ("KUNNE IKKE ÅPNE FILA: $fil");
    foreach (<FIL>) {
	if(my @linje = &fil_hent_linje($felt,$_)){
	    $resultat{$linje[0]}{$linje[1]} = [ undef,$linje[0],$linje[1],undef,undef,$linje[2],$linje[3],undef,undef,undef,$linje[4] ]; #legger inn i hash
	}
    }
    close FIL;
    return %resultat;
}

my %types = &get_types("collect");

sub get_types {
    my $class = $_[0];
    my $syslogconnection = &db_connect("syslog","syslogadmin","urg20ola");
    my %types = &db_hent_hash($syslogconnection,"select id,type,message from messagetemplate where class=\'$class\'");

    return %types;
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

    my $newidentificator = $types{$identificator}[1];
    my $message = $types{$identificator}[2];

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

    &printlog($text);

    return 1;

}

sub printlog{
    my $time = scalar localtime;
    print COLLECTLOG $time." ".'%'.$_[0];
    return 1;
}

return 1;

