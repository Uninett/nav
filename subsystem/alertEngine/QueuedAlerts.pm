# QueuedAlerts.pm
#
# Class that contains information about all queued alerts.
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

package NAV::AlertEngine::QueuedAlerts;

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
    $this->{dbh_event}=shift;
    $this->{dbh_user}=shift;
    $this->{log}=NAV::AlertEngine::Log->new();
    bless $this,$class;
    $this->collectInfo();
    return $this;
  }

sub collectInfo()
{
    my $this=shift;

    #get queued alerts
    my $queue=$this->{dbh_user}->selectall_arrayref(q{
        SELECT q.accountid, q.addrid, q.alertid,
            (NOW() - p.lastsentday >= '24 hours' AND CURRENT_TIME >= b.tid) AS day,
            (NOW() - p.lastsentweek >= '7 days' AND EXTRACT(DAY FROM NOW()) >= b.ukedag AND CURRENT_TIME >= b.uketid) AS week,
            (NOW() - q.time >= p.queuelength) AS max,
            DATE_TRUNC('day',AGE(q.time))
        FROM queue q, preference p, brukerprofil b
        WHERE q.accountid = p.accountid and b.accountid = q.accountid  and b.id = p.activeprofile
    });

    $this->{log}->printlog("QueuedAlerts","collectInfo",$Log::debugging, "collecting info about queued alerts");

    my $num=0;
    foreach my $q (@$queue)
      #Collect information about all alerts
      {
#	  print "qa: $q->[0] $q->[1] $q->[2] $q->[3]\n";
	  $this->{qas}{$q->[0]}[$num]->{accountid}=$q->[0];
	  $this->{qas}{$q->[0]}[$num]->{addressid}=$q->[1];
	  $this->{qas}{$q->[0]}[$num]->{alertid}=$num;
	  $this->{qas}{$q->[0]}[$num]->{day}=$q->[3];
	  $this->{qas}{$q->[0]}[$num]->{week}=$q->[4];
	  $this->{qas}{$q->[0]}[$num]->{max}=$q->[5];
	  $this->{acount}[$num]++;
	  $this->addAlert(NAV::AlertEngine::Alert->new($this->{dbh_event},$q->[2]),$num);
	  $num++;
      }
}

sub getUserAlertIDs()
{
    my ($this,$uid)=@_;
    return $this->{qas}{$uid};
}

sub deleteAlert()
{
    my ($this,$alertid,$uid,$addrid)=@_;
    my $a=$this->getAlert($alertid);

    $this->{log}->printlog("QueuedAlerts","deleteAlert",$Log::debugging, "deleting queued alert $alertid");

    #Delete queue
    my $aid=$a->getID();
    $this->{dbh_user}->do("delete from queue where alertid=$aid and accountid=$uid and addrid=$addrid");    

    #Delete alert?
    $this->{acount}[$alertid]--;
    if($this->{acount}[$alertid]==0) {
	#Delete alert
	$a->delete();
    }
}
