# UserGroups.pm
#
# Class that contains information about all available user groups
#
# Arne Øslebø, UNINETT, 2002
#

package UserGroups;

use strict;
use Log;

sub new
#Constructor
  {
    my $this={};
    shift;
    $this->{dbh}=shift;

    $this->{log}=Log->new();
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
