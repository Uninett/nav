#!/usr/bin/perl -w

use strict;

sub fil_hent_le {
    (my $felt,$_) = @_;
    #tar med linjer som begynner med ord før kolon bestående av 
    #tall,bokstaver,lavstrek,bindestrek,punktum
    if (/^[a-zA-Z0-9_\-\.]+?:/) {
	#sletter ting som er ekstra i stedet for å slå 
	#sammen med seinere feilkolonner.
	(my @linje,undef) = split(/:/,$_,$felt+1); 
	@linje = map rydd($_), @linje; #rydder opp
	return @linje;
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

return 1;
