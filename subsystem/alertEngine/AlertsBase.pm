# AlertsBase.pm
#
# Base class that contains information about alerts.
#
# Arne Øslebø, UNINETT, 2002
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
