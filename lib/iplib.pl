#!/usr/bin/perl -w

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


return 1;
