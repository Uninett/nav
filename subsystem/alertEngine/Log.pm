# Log.pm
#
# Copyright 2003 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Authors: Arne Øslebø, UNINETT
#
package Log;
use NAV::Path;
use vars qw{%log};

if(-f "$NAV::Path::sysconfdir/alertengine.cfg") {
    require "$NAV::Path::sysconfdir/alertengine.cfg";
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
