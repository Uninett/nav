# AlertsBase.pm
#
# Base class that contains information about alerts.
#
# Copyright 2002 UNINETT AS
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

package AlertsBase;

use strict;

sub new
#Constructor
  {
    my $class = shift;
    my $this={};
    bless $this,$class;
    $this->{num}=0;
    return $this;
  }

sub addAlert()
#Adds an alert
  {
    my ($this,$alert,$alertid)=@_;
    $this->{alerts}[$alertid]=$alert;
    $this->{num}++;
  }

sub getAlert()
#Returns a specific alert
  {
    my ($this,$alert)=@_;

    return $this->{alerts}[$alert];
  }

sub getAlertNum()
#Returns number of new alerts
  {
    my $this=shift;
    return $this->{num};
  }



1;
