#!/usr/bin/env perl

use strict;
require '/usr/local/nav/navme/subsystem/lib-perl/nav.pm';
import nav;

# få tak i en connection / databasehandler
my $conn = connection("ragen");

# gjør en spørring og motta et resultat
my $res = execute($conn,"select netboxid from netbox");

#lagre i hash
#my %resultat_hash;
#while(@_ = $res->fetchrow) {
#    $resultat_hash{$_[0]} = [ @_ ];
#}

#lagre i array
my @resultat_array;
while(@_ = $res->fetchrow) {
    push(@resultat_array,@_);
}

# test-print
#for my $a (@resultat_array) {
#    print $a;
#}
