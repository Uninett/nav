# UserGroups.pm
#
# Class that contains information about all available user groups
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

package NAV::AlertEngine::UserGroups;

use strict;
use NAV::AlertEngine::Log;

sub new
#Constructor
  {
    my $this={};
    shift;
    $this->{dbh}=shift;

    $this->{log}=NAV::AlertEngine::Log->new();
    bless $this;

    $this->collectInfo();
    return $this;
  }

sub collectInfo()
#Collects all relevant information
#Returns true if successful.
  {
    my $this=shift;

    my $ugs=$this->{dbh}->selectall_arrayref("select id from accountgroup");

    if($DBI::errstr)
      {
	  $this->{log}->printlog("UserGroups","collectInfo",$Log::error,"could not get list of account groups");
	return 0;
      }

    foreach my $ug (@$ugs)
      {
	my $egs=$this->{dbh}->selectall_arrayref("select ug.id from utstyrgruppe ug,rettighet r,accountgroup bg where bg.id=r.accountgroupid and r.utstyrgruppeid=ug.id and bg.id=$ug->[0]") || $this->{log}->printlog("UserGroups","collectInfo",$Log::error,"could not get list of equipment groups");
	
	if($DBI::errstr)
	  {
	      $this->{log}->printlog("UserGroups","collectInfo",$Log::error,"could not get list of equipment groups");
	    return 0;
	  }
	
	my $list;

	foreach my $eg (@$egs)
	  {
	    push @$list,$eg->[0];
	  }
	
	$this->{info}[$ug->[0]]->{permissions}=$list;
      }
    return 1;
  }

sub getEquipmentGroups()
  {
    my ($this,$userGroup)=@_;
    return $this->{info}[$userGroup]->{permissions};
  }

1;
