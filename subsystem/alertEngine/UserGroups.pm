# UserGroups.pm
#
# Class that contains information about all available user groups
#
# Arne Øslebø, UNINETT, 2002
#

package UserGroups;

use strict;

sub new
#Constructor
  {
    my $this={};
    shift;
    $this->{dbh}=shift;
    bless $this;

    $this->collectInfo();
    return $this;
  }

sub collectInfo()
#Collects all relevant information
#Returns true if successful.
  {
    my $self=shift;

    my $ugs=$self->{dbh}->selectall_arrayref("select id from brukergruppe");

    if($DBI::errstr)
      {
	print "ERROR: could not get list of user groups\n";
	return 0;
      }

    foreach my $ug (@$ugs)
      {
	my $egs=$self->{dbh}->selectall_arrayref("select ug.id from utstyrgruppe ug,rettighet r,brukergruppe bg where bg.id=r.brukergruppeid and r.utstyrgruppeid=ug.id and bg.id=$ug->[0]") || print "ERROR: could not get list of equipment groups";
	
	if($DBI::errstr)
	  {
	    print "ERROR: could not get list of equipment groups\n";
	    return 0;
	  }
	
	my $list;

	foreach my $eg (@$egs)
	  {
	    push @$list,$eg->[0];
	  }
	
	$self->{info}[$ug->[0]]->{permissions}=$list;
      }
    return 1;
  }

sub getEquipmentGroups()
  {
    my ($self,$userGroup)=@_;
    return $self->{info}[$userGroup]->{permissions};
  }

1;
