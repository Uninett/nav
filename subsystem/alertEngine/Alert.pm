# Alert.pm
#
# Class that contains all relevant information about a specific alert.
#
# Arne Øslebø, UNINETT, 2002
#

package Alert;

use strict;

sub new
#Constructor
  {
    my $this={};
    my $class=shift;
    $this->{dbh}=shift;
    $this->{id}=shift;
    bless $this,$class;
    $this->collectInfo();
    return $this;
  }

sub collectInfo()
#Collects all relevant information
#Returns true if successful.
  {
    my $this=shift;

    my $sth = $this->{dbh}->prepare("select source,deviceid,netboxid,subid,time,eventtypeid,state,value,severity,alertqid from alertq where alertqid=$this->{id}");
    $sth->execute;

    my $info=$sth->fetchrow_arrayref();

    if($DBI::errstr)
      {
	print "ERROR: could not get list of equipment groups\n";
	return 0;
      }

    $this->{source}=$info->[0];
    $this->{deviceid}=$info->[1];
    $this->{netboxid}=$info->[2];
    $this->{subid}=$info->[3];
    $this->{time}=$info->[4];
    $this->{eventtypeid}=$info->[5];
    $this->{state}=$info->[6];
    $this->{value}=$info->[7];
    $this->{severity}=$info->[8];
    $this->{id}=$info->[9];
    $this->{queued}=0;
    return 1;
  }

sub collectNetbox()
  {
    my $this=shift;
    if(defined $this->{netboxid})
      {
	
	my $sth=$this->{dbh}->prepare("select ip,sysname,typeid from netbox where netboxid=$this->{netboxid}");
	$sth->execute;
	
	my $info=$sth->fetchrow_arrayref();
	
	
	if($DBI::errstr)
	  {
	    print "ERROR: could not get information about alert\n";
	    return 0;
	  }
	
	$this->{equipment}->{ip}=$info->[0];
	$this->{equipment}->{name}=$info->[1];
      }
    else
      {
	$this->{equipment}->{ip}=0;
	$this->{equipment}->{name}="";
      }
  }

sub getIP()
#returns IP adress of equipment
{
    my $this=shift;
    if(!defined $this->{equipment}->{ip})
    {
	$this->collectNetbox();
    }
    
    return $this->{equipment}->{ip};
}

sub getSource()
#returns source of the alert
{
    my $this=shift;
    return $this->{source};
}

sub getSeverity()
#returns alert severity
{
    my $this=shift;
    return $this->{severity};
}

sub getName()
#returns IP adress of equipment
{
    my $this=shift;
    if(!defined $this->{equipment}->{name})
    {
	$this->collectNetbox();
    }
    
    return $this->{equipment}->{name};
}

sub getEmailSubject()
#returns email subject of alert
{
    my ($this,$lang)=@_;

    if(!defined $this->{alertvar})
    {
	$this->collectVar();
    }
    my $str=$this->{alertvar}{email}{$lang};

    if(!defined $str)
    {
	print "Error: no email alert defined\n";
	return "";
    }
    $str=~/Subject: (.*)/;
    return $1;
}

sub getSMSMsg()
{
    my ($this,$lang)=@_;
    if(!defined $this->{alertvar})
    {
	$this->collectVar();
    }
    return $this->{alertvar}{sms}{$lang};
}

sub getEmailBody()
{
    my ($this,$lang)=@_;

    if(!defined $this->{alertvar})
    {
	$this->collectVar();
    }
    my $str=$this->{alertvar}{email}{$lang};

    if(!defined $str)
    {
	print "Error: no email alert defined\n";
	return "";
    }
    $str=~s/^.*\n//;
    return $str;
}

sub collectVar()
{
    my $this=shift;

    my $vars=$this->{dbh}->selectall_arrayref("select msgtype,language,msg from alertqvar where alertqid=$this->{id}") || print "ERROR: could not get alertqvar list";

    foreach my $var (@$vars)
    {
	$this->{alertvar}{$var->[0]}{$var->[1]}=$var->[2];
    }    
}

sub getEventtype()
{
    my $this=shift;
    return $this->{eventtypeid};
}

sub getID()
#returns ID of alert
{
    my $this=shift;
    return $this->{id};
}

sub queued()
{
    my $this=shift;
    $this->{queued}=1;
}

sub delete()
#deletes alert from db
{
    my $this=shift;
    if(!$this->{queued})
    {
	print "delete alertqid=$this->{id}\n";
#	return;
	$this->{dbh}->do("delete from alertq where alertqid=$this->{id}");    
    }
}

1;
