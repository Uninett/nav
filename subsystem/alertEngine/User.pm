# User.pm
#
# Class that contains all relevant information about a specific user.
#
# Arne Øslebø, UNINETT, 2002
#

package User;

use strict;

sub new
#Constructor
  {
    my $class=shift;
    my $this={};

    $this->{id}=shift;
    $this->{dbh}=shift;
#    $this->{dbh_alert}=shift;
    my $cfg=shift;
    $this->{email_from}=$cfg->{email_from};
    $this->{sendmail}=$cfg->{sendmail};
    bless $this,$class;
    $this->collectInfo();
    return $this;
  }

sub collectInfo()
#Collects all relevant information
#Returns true if successful.
  {
    my $this=shift;
    my $sth=$this->{dbh}->prepare("select aktivprofil,sms from bruker where id=$this->{id}");
    $sth->execute();

    my $info=$sth->fetchrow_arrayref();

    if($DBI::errstr)
      {
	print "ERROR: could not get information about user\n";
	return 0;
      }

    $this->{activeProfile}=$info->[0];
    $this->{sms}=$info->[1];

    return 1;
  }

sub collectAddresses()
  {
    my $this=shift;

    #Collect information about addresses
    my $addrs=$this->{dbh}->selectall_arrayref("select adresse,type,id from alarmadresse where brukerid=$this->{id}");

    if($DBI::errstr)
      {
	print "ERROR: could not get information about addresses\n";
	return 0;
      }

    foreach my $addr (@$addrs)
      {
	$this->{addrs}[$addr->[2]]->{address}=$addr->[0];
	$this->{addrs}[$addr->[2]]->{type}=$addr->[1];
      }
    return 1;
  }

sub collectTimePeriod()
  {
    my $this=shift;
    #Collect information about timeperiod

    my $tps=$this->{dbh}->selectall_arrayref("select id,helg,starttid from tidsperiode where brukerprofilid=$this->{activeProfile} and starttid<now() order by starttid desc");
    my $tp=$tps->[0];
    if($DBI::errstr)
      {
	print "ERROR: could not get information about time periods\n";
	return 0;
      }

    $this->{timePeriod}->{weekend}=$tp->[1];
    $this->{timePeriod}->{starttime}=$tp->[2];
    my $aEs=$this->{dbh}->selectall_arrayref("select alarmadresseid,utstyrgruppeid,vent from varsle where tidsperiodeid=$tp->[0]");

    if($DBI::errstr)
      {
	print "ERROR: could not get information about addresses\n";
	return 0;
      }

    my $c2=0;
    foreach my $aE (@$aEs)
      {
	$this->{timePeriod}->{aE}[$c2]->{address}=$aE->[0];
	$this->{timePeriod}->{aE}[$c2]->{eGID}=$aE->[1];
	$this->{timePeriod}->{aE}[$c2]->{queue}=$aE->[2];
	$c2++;
      }
    return 1;
  }

sub collectUserGroups()
  {
    my $this=shift;
    #Collect list of user groups that the user is member of

    my $ugs=$this->{dbh}->selectall_arrayref("select gruppeid from brukertilgruppe where brukerid=$this->{id}");

    if($DBI::errstr)
      {
	print "ERROR: could not get information about time periods\n";
	return 0;
      }

    my $list;
    foreach my $ug (@$ugs)
      {
	push @$list,$ug->[0];
      }
    $this->{usergroups}=$list;
    return 1;
  }

sub collectEquipmentGroups()
  {
    my $this=shift;
    #Collect list of equipment groups the user is allowed to access
    my $egs=$this->{dbh}->selectall_arrayref("select utstyrgruppeid from brukerrettighet where brukerid=$this->{id}");

    if($DBI::errstr)
      {
	print "ERROR: could not get information about time periods\n";
	return 0;
      }

    my $list;
    foreach my $eg (@$egs)
      {
	push @$list,$eg->[0];
      }
    $this->{equipmentgroups}=$list;
    return 1;
  }

sub checkAlertQueue()
#Check alert queue to see if alerts should be sent out
  {
    my $this=shift;

    #check active profile
#    my $ae=$this->checkActiveProfile($alertsnum);
#    if(defined $ae)
#      {		
#	if(!$ae->{queue})
#	  {
#	    #Send alert
#	    $this->sendAlert($alertsnum,$ae->{address});
#	  }
#      }
  }

sub checkNewAlerts()
#Checks the new alerts and sends or queues them
{
    my $this=shift;
    ($this->{nA},$this->{uG},$this->{eG})=@_;
    my $alertsnum=$this->{nA}->getAlertNum();
    
    for(my $c=0;$c<$alertsnum;$c++)
    {
	#check permissions
	
	if($this->checkRights($c))
	  {
	    #check active profile
	    my @aes=$this->checkActiveProfile($c);
	    foreach my $ae (@aes)
	    {
		if($ae->{queue})
		{
		    #Queue alert
		    $this->queueAlert($this->{nA}->getAlert($c),$ae->{address});
		}
		else
		{
		    #Send alert
		    $this->sendAlert($this->{nA}->getAlert($c),$ae->{address});
		}
	    }
	}
    }
}


sub queueAlert()
#Store alert in queue
  {
    my($this,$alert,$addressid)=@_;
    $alert->queued();
#    print "Queue alert $alertid\n";

#    my $sth=$this->{dbh}->prepare("insert into ko (brukerid,alertid,adrid) select $this->{id},$alertid,$addressid where not exists(select brukerid,alertid,adrid from ko where brukerid=$this->{id} and alertid=$alertid and adrid=$addressid)");
    #$sth->execute();

  }

sub sendAlert()
  {
    my($this,$alert,$addressid)=@_;

    if(!defined $this->{addrs})
      {
	$this->collectAddresses();
      }

    my $alertid=$alert->getID();

    #Check address type
    my $addr=$this->{addrs}[$addressid];

#    print "Send alert $alertid to user $this->{id}\n";
    #return;

    if($addr->{type}==1)
      {
	  my $subject=$alert->getEmailSubject('no');
	  my $body=$alert->getEmailBody('no');
	  if(length($subject)>0)
	  {
	      $this->sendEmail($addr->{address},$subject,$body);
	  }
      }
    elsif($addr->{type}==2)
    {
	my $msg=$alert->getSMSMsg('no');
	if(length($msg)>0)
	{
	    $this->sendSMS($addr->{address},$msg);
	}
    }
  }


sub sendSMS()
{
    my($this,$to,$msg)=@_;
    if(length($msg)==0)
    {
	print "Error: no SMS message\n";
    }

    print "SMS $to: $msg\n";
#    return; 
    $this->{dbh}->do("insert into smsutko (tlfnr,melding) values($to,'$msg')");
}

sub sendEmail()
{
    my($this,$to,$subject,$body)=@_;
    if(length($subject)==0)
    {
	print "Error: no subject defined\n";
	return;
    }


    print "EMAIL $to\tSubject: $subject\n";
#    return;

    open(SENDMAIL, "|$this->{sendmail}")
      or die "Can't fork for sendmail: $!\n";
    print SENDMAIL <<"EOF";
From: $this->{email_from}
To: $to
Subject: $subject

$body
EOF
    close(SENDMAIL)     or warn "sendmail didn't close nicely";
  }

sub checkActiveProfile()
  {
    my ($this,$alertid)=@_;
    my @ae;
    #Get time periods
    if(!defined $this->{timePeriod})
      {
	$this->collectTimePeriod();
      }

    my $tp=$this->{timePeriod};
    my $aes=$tp->{aE};
    foreach my $a (@$aes)
      {
	if($this->{eG}->checkAlert($a->{eGID},$this->{nA}->getAlert($alertid)))
	  {
	    push @ae,$a;
	  }
      }
    return @ae;
  }

sub checkRights()
  {
    my ($this,$alertid)=@_;
    #Get user groups
    if(!defined $this->{usergroups})
      {
	$this->collectUserGroups();
      }

    #Check user group rights
    my $ugs=$this->{usergroups};
    foreach my $ug (@$ugs)
      {
	#Get equipment groups that belongs to the user group
	my $egs=$this->{uG}->getEquipmentGroups($ug);
	foreach my $eg (@$egs)
	  {
	    if($this->{eG}->checkAlert($eg,$this->{nA}->getAlert($alertid)))
	      {
		return 1;
	      }
	  }
      }

    #Get extra user rigths
    if(!defined $this->{usergroups})
      {
	$this->collectEquipmentGroups()
      }

    my $egs=$this->{equipmentgroups};
    foreach my $eg (@$egs)
      {
	if($this->{eG}->checkAlert($eg,$this->{nA}->getAlert($alertid)))
	  {
	    return 1;
	  }
      }
    print "no rights: $alertid\n";
    return 0;
  }

1;


#  LocalWords:  addressid
