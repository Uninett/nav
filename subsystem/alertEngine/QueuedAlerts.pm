# QueuedAlerts.pm
#
# Class that contains information about all queued alerts.
#
# Arne Øslebø, UNINETT, 2002
#

package QueuedAlerts;

require AlertsBase;

use strict;
use Exporter;
use Log;

use vars qw(@ISA);
@ISA=qw(AlertsBase);

sub new
#Constructor
  {
    my $class=shift;
    my $this={};
    $this->{dbh_event}=shift;
    $this->{dbh_user}=shift;
    $this->{log}=Log->new();
    bless $this,$class;
    $this->collectInfo();
    return $this;
  }

sub collectInfo()
{
    my $this=shift;

    #get queued alerts
    my $queue=$this->{dbh_user}->selectall_arrayref("select q.accountid,q.addrid,q.alertid,(now()-p.lastsentday>='24 hours' and now()>=b.tid) as day, (now()-p.lastsentweek>='7 days' and extract(day from now())>=b.ukedag and now()>=b.uketid) as week, now()-q.time>=p.queuelength as max, date_trunc('day',age(q.time)) from queue q, preference p,brukerprofil b where q.accountid=p.accountid and b.accountid=q.accountid  and b.id=p.activeprofile");

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
	  $this->addAlert(Alert->new($this->{dbh_event},$q->[2]),$num);
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
