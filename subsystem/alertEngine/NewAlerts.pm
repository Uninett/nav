# NewAlerts.pm
#
# Class that contains information about all new alerts.
#
# Arne Øslebø, UNINETT, 2002
#

package NewAlerts;

require AlertsBase;

use strict;
use Exporter;
use vars qw(@ISA);
@ISA=qw(AlertsBase);

sub new
#Constructor
  {
    my $class=shift;
    my $this={};
    $this->{dbh}=shift;

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
	$this->addAlert(Alert->new($this->{dbh},$id->[0]),$num);
	$this->{lastid}=$id->[0];
	$num++;
      }
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
