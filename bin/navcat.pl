#!/usr/bin/perl

my $fil = shift;
open(FIL, "<$fil");
my @fil = <FIL>;
close FIL;
my @ny;

my @len;
my $pos;
foreach (@fil) {
    if(/^\w+?:/) {
	@_ = split(/:/,$_);
	for (my $i=0; $i < @_; $i++) {
	    $_[$i] = fjern ($_[$i]);
	    if(defined($_[$i])) { #alltid
		$_[$i] =~ /.+/g;
#		print $_[$i];
		if (!defined($len[$i])){
		    $len[$i] = pos($_[$i])-1;
		}
		elsif ($len[$i] < pos($_[$i])-1) {
		    $len[$i] = pos($_[$i])-1;
		}
#		print " " x $pos;
	    }   
	}

	@ny = (@ny, join(":",@_));
    }
}
foreach (@ny) {
    if(/^\w+?:/) {
	@_ = split(/:/,$_);
	for (my $i=0; $i < @_; $i++) {
#	    @_[$i] = fjern(@_[$i]);
	    if($_[$i] =~ /.+/g) { #alltid
		print $_[$i];
		$pos = $len[$i]-pos($_[$i])+2;
		print " " x $pos;
	    }   
	}
	print "\n";

#	@ny = (@ny, join(":",@_));
    }
}
sub fjern { #utvidet chomp som også tar tab. og andre \s
    if (defined $_[0]) {
	$_ = $_[0];
	s/\s*$//;
	s/^\s*//;
    return $_;
    }
}


