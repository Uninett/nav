package NAV::Arnold;

our @ISA = qw(Exporter);
our @EXPORT = qw(&readconfig);

use NAV::Path;

sub readconfig {
    my $config = "$NAV::Path::sysconfdir/arnold/arnold.conf";
    my %cfg;

    open (CFG, $config) or die ("Could not open $config, exiting: $!");
    while (<CFG>) {
	next if /^\#/;
	next unless /^\S+/;
	
	chomp;
	$_ =~ /(\S+)\s*=\s*(.+)/;
	$cfg{$1} = $2;
	
    }
    close CFG;
    
    return %cfg;
}

1;
