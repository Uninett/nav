#!/usr/bin/perl
#
# Parse a config file with VAR=VALUE assignments, ignoring
# leading/trailing whitespace and comments.
#

my $filename = shift || die "Missing filename on command line\n";

open(IN, $filename) || die "Could not open $filename: $!\n";
my %hash = map { /\s*(.+?)\s*=\s*(.*?)\s*(\#.*)?$/ && $1 => $2 } 
grep { !/^(\s*\#|\s+$)/ && /.+=.*/ } <IN>;
close(IN);

foreach (keys %hash) {
    print "$_=$hash{$_}\n";
}
