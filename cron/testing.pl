#!/usr/bin/perl

and_ip("129.112.1.1","255.255.1.0");

sub and_ip {
    my @a =split(/\./,$_[0]);
    my @b =split(/\./,$_[1]);

    for (0..$#a) {
#	print $_."\n";
        print $a[$_] = int($a[$_]) & int($b[$_]);
    }

    return join(".",@a);
}
    
