package Log;

use vars qw{%log};

if(-f "$ENV{'NAV_PREFIX'}/etc/conf/alertengine.cfg") {
    require "$ENV{'NAV_PREFIX'}/etc/conf/alertengine.cfg";
} else {
    require "alertengine.cfg";
}

use strict 'vars';

use vars qw{$cfg};

sub new
#Constructor
{
    my $class=shift;
    my $this={};

    bless $this,$class;

    $this->{cfg}=$cfg;
    return $this;
}

sub printlog()
{
    my ($this,$class,$func,$level,$msg)=@_;
    my $time=localtime;

    my $log=$this->{cfg}->{log};

    if(!defined $level) {
	$this->printlog("Log","printlog",$Log::error,"Level not defined: $class $func $msg");
	return;
    }

    if($log=~/$level/) {
        print "$time alertEngine $class-$level-$func: $msg\n";
    }
}

$Log::emergency=0;
$Log::alert=1;
$Log::critical=2;
$Log::error=3;
$Log::warning=4;
$Log::notification=5;
$Log::informational=6;
$Log::debugging=7;

1;
