# NewAlerts.pm
#
# Class that contains information about all new alerts.
#
# Copyright 2002, 2003 UNINETT AS
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

package NAV::AlertEngine::NewAlerts;

use NAV::AlertEngine::AlertsBase;

use strict;
use Exporter;
use NAV::AlertEngine::Log;

use vars qw(@ISA);
@ISA=qw(NAV::AlertEngine::AlertsBase);

sub new
#Constructor
  {
    my $class=shift;
    my $this={};
    $this->{dbh}=shift;
    $this->{log}=NAV::AlertEngine::Log->new();
    bless $this,$class;
    $this->collectInfo();
    return $this;
  }

sub collectInfo()
#Collects information about all new alerts
#Returns true if successful.
  {
    my $this=shift;

    #Get ID of last processed alert.
    if(!defined $this->{lastid})
      {
	my $tmp=$this->{dbh}->selectall_arrayref("select lastalertqid from alertengine");
	$this->{lastid}=@$tmp[0]->[0];
      }

    #get new alerts
    my $ids=$this->{dbh}->selectall_arrayref("select alertqid from alertq where alertqid>$this->{lastid} order by alertqid");

    my $num=0;
    foreach my $id (@$ids)
      #Collect information about all alerts
      {
	$this->addAlert(NAV::AlertEngine::Alert->new($this->{dbh},$id->[0]),$num);
	$this->{lastid}=$id->[0];
	$num++;
      }

    $this->{log}->printlog("NewAlerts","collectInfo",$Log::debugging, "found $num new alerts");
  }

sub finished()
#Finished with all alerts. Updates index for processed alerts. 
#Returns last alert id that was processed.
  {
    my $this=shift;

    $this->{dbh}->do("update alertengine set lastalertqid=$this->{lastid}");
    return $this->{lastid};
  }

1;
