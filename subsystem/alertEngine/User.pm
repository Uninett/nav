# User.pm
#
# Class that contains all relevant information about a specific user.
#
# Copyright 2002-2004 UNINETT AS
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

package NAV::AlertEngine::User;

use NAV::Path;
use strict;
use NAV::AlertEngine::Log;
use diagnostics;

$User::msgtype[1]="email";
$User::msgtype[2]="sms";

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
    $this->{log}=NAV::AlertEngine::Log->new();

    $this->{DAILY}=1;
    $this->{WEEKLY}=2;
    $this->{MAX}=3;

    bless $this,$class;
    $this->collectInfo();
    return $this;
  }

sub collectInfo()
#Collects all relevant information
#Returns true if successful.
  {
    my $this=shift;
    my $sth=$this->{dbh}->prepare("select p.activeprofile, ap.value,extract('dow' from now()),a.login from account a, preference p,accountproperty ap where p.accountid=a.id and a.id=$this->{id} and ap.accountid=a.id and ap.property='language'");

    $sth->execute();

    my $info=$sth->fetchrow_arrayref();

    if($DBI::errstr)
      {
	$this->{log}->printlog("User","collectInfo",$Log::error,"could not get account information about acountid=$this->{id}");
	return 0;
      }

    if(!defined($info)) {
	my $sth=$this->{dbh}->prepare("select p.activeprofile, 'en',extract('dow' from now()),a.login from account a, preference p where p.accountid=a.id and a.id=$this->{id}");

	$sth->execute();
	
	$info=$sth->fetchrow_arrayref();
	
	if($DBI::errstr)
	{
	    $this->{log}->printlog("User","collectInfo",$Log::error,"could not get account information about acountid=$this->{id}");
	    return 0;
	}
    }

    $this->{activeProfile}=$info->[0];
    $this->{lang}=$info->[1];
    $this->{day}=$info->[2];

    $this->{sms}=system("$NAV::Path::bindir/hasPrivilege.py $info->[3] alerttype sms");

    if(!$this->{lang}) {
	$this->{log}->printlog("User","collectInfo",$Log::error,"no language defined for acountid=$this->{id}");
    }

    return 1;
  }

sub collectAddresses()
  {
    my $this=shift;

    #Collect information about addresses
    my $addrs=$this->{dbh}->selectall_arrayref("select adresse,type,id from alarmadresse where accountid=$this->{id}");

    if($DBI::errstr)
      {
	$this->{log}->printlog("User","collectAddresses",$Log::error,"could not get information about addresses for acount id=$this->{id}");
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

    my $tps;
    
    if(!$this->{activeProfile}) {
		$this->{log}->printlog("User","collectTimePeriod",$Log::debugging,"no active profile");
		return;
    }

	# 	The 'helg' field in the database table 'tidsperiode' specifies wether 
	# this timeperiod is for weekdays or weekend or both.
	#		1 all week	Monday	-	Sunday
	#		2 weekdays 	Monday	-	Friday
	#		3 weekend 	Saturday-	Sunday
	#	Postresql day of week is an integer from 0 to 6, where 
	# 0 is sunday, 1 monday and 6 saturday

	my $tpquery;
	my $exceptHelgType;

	# If NOW is sunday or saturday
    if($this->{day}==0 || $this->{day}==6) {
   		# Set except type to 2, which means all time periods except weekdays
		$exceptHelgType = 2;

	# if not, NOW is a week-day.
	} else {
   		# Set except type to 2, which means all time periods except weekdays
		$exceptHelgType = 3;
	}	
	
	# 	Extract all timeperiods valid, and sort by which starttime is most recent. The somewhat nasty SQL 
	# is an implementation of a interval modulo 24hour function, and what neccessary to support time 
	# periods spanning midnight.
	$tpquery = "
		SELECT id, helg, starttid FROM (
			 SELECT *, date_trunc('day', localtimestamp) + (localtime - starttid) - 
				date_trunc('day', date_trunc('day', localtimestamp) + (localtime - starttid)) AS s 
			FROM tidsperiode 
			WHERE brukerprofilid = $this->{activeProfile} AND helg != $exceptHelgType
			ORDER BY s LIMIT 1
		) q";

	# Execute generated query.
	$tps = $this->{dbh}->selectall_arrayref($tpquery);

	# Exctract first row, which is the most recent time period set active 
    my $tp=$tps->[0];

    if(!defined $tp) {
		$this->{log}->printlog("User","collectTimePeriod",$Log::debugging,"no time period available");
		return;
    }

    if($DBI::errstr)
      {
	  $this->{log}->printlog("User","collectTimePeriod",$Log::error,"could not get information about time periods");
	  return 0;
      }

    $this->{timePeriod}->{weekend}=$tp->[1];
    $this->{timePeriod}->{starttime}=$tp->[2];
    my $aEs=$this->{dbh}->selectall_arrayref("select alarmadresseid,utstyrgruppeid,vent from varsle where tidsperiodeid=$tp->[0]");

	if($DBI::errstr)
	{
		$this->{log}->printlog("User","collectTimePeriod",$Log::error,"could not get information about addresses");
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

    $this->{log}->printlog("User","collectTimePeriod",$Log::debugging,"collected $c2 alarm addresses");

    if($c2==0) {
	$this->{log}->printlog("User","collectTimePeriod",$Log::warning,"could not get information about addresses for timeperiodid=$tp->[0]");
	return 0;
    }

    return 1;
  }

sub collectUserGroups()
  {
    my $this=shift;
    #Collect list of user groups that the user is member of

    my $ugs=$this->{dbh}->selectall_arrayref("select groupid from accountingroup where accountid=$this->{id}");

    if($DBI::errstr)
      {
	  $this->{log}->printlog("User","collectUserGroups",$Log::error,"could not get information about user groups");
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
    my $egs=$this->{dbh}->selectall_arrayref("select utstyrgruppeid from brukerrettighet where accountid=$this->{id}");

    if($DBI::errstr)
      {
	  $this->{log}->printlog("User","collectEquipmentGroups",$Log::error,"could not get information about time periods");
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
    my $qa=shift;
    $this->{eG}=shift;
    my $send=0;
    my $c=0;
    
    $this->{log}->printlog("User","checkAlertQueue",$Log::debugging,"checking queued alerts for user $this->{id}");
    
    #Get list of queued alerts
    my $qas=$qa->getUserAlertIDs($this->{id});
    
    foreach my $aid (@$qas) {
	$this->{log}->printlog("User","checkAlertQueue",$Log::debugging,"chekcing queued alert $aid->{alertid}");
	#Check active profile
	my $aes=$this->checkActiveProfile($aid->{alertid},$qa);
	$c=0;
	$send=0;
	foreach my $ae (@$aes)
	{
	    $c++;
	    if(!$ae->{queue}){
		$this->sendAlert($qa->getAlert($aid->{alertid}),$ae->{address});
		$send++;
	    } else {
		#Check daily
		if($aid->{day} && $ae->{queue}==$this->{DAILY}) {
		    $this->prepareSendAlert($qa->getAlert($aid->{alertid}),$ae->{address});
		    $this->{dbh}->do("update preference set lastsentday=now() where accountid=$this->{id}");    
		    $send++;
		} elsif($aid->{week} && $ae->{queue}==$this->{WEEKLY}) {
		    $this->prepareSendAlert($qa->getAlert($aid->{alertid}),$ae->{address});
		    $this->{dbh}->do("update preference set lastsentweek=now() where accountid=$this->{id}");    
		    $send++;
		} elsif($aid->{max} && $ae->{queue}==$this->{MAX}) {
		    $this->prepareSendAlert($qa->getAlert($aid->{alertid}),$ae->{address});
		    $send++;
		}
	    }
	}

	if($c==0) {
	    $this->prepareSendAlert($qa->getAlert($aid->{alertid}),$aid->{addressid});
	}
	if($send==$c) {	    
	    $qa->deleteAlert($aid->{alertid},$this->{id},$aid->{addressid});
	}
    }		        

    $this->sendPreparedAlerts();
}


sub checkNewAlerts()
#Checks the new alerts and sends or queues them
{
    my $this=shift;
    ($this->{nA},$this->{uG},$this->{eG})=@_;
    my $alertsnum=$this->{nA}->getAlertNum();
    
    $this->{log}->printlog("User","checkNewAlerts",$Log::debugging, "processing new alerts for user $this->{id}");

    for(my $c=0;$c<$alertsnum;$c++)
    {
	#check permissions
	
	if($this->checkRights($c))
	  {
	    #check active profile
	    my $aes=$this->checkActiveProfile($c,$this->{nA});

	    foreach my $ae (@$aes)
	    {
		if($ae->{queue})
		{
		    #Queue alert
		    $this->queueAlert($this->{nA}->getAlert($c),$ae->{address});
		}
		else
		{
		   # my $k;
		   # my $v;
		   # while (($k, $v) = each(%$ae)) {
			#print "$k=$v\n";
		#    }

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
    my $alertid=$alert->getID();
    $alert->queued();
    
#    print "Queue alert $alertid\n";
    $this->{log}->printlog("User","queueAlert",$Log::informational,"queued alert $alertid to address $addressid");

    my $sth=$this->{dbh}->prepare("insert into queue (accountid,addrid,alertid,time) select $this->{id},$addressid,$alertid,now() where not exists(select accountid from queue where accountid=$this->{id} and alertid=$alertid and addrid=$addressid)");
    $sth->execute();
  }

sub prepareSendAlert()
{
    my($this,$alert,$addressid)=@_;

    if(!defined $this->{addrs})
      {
	$this->collectAddresses();
      }

    my $alertid=$alert->getID();

    $this->{log}->printlog("User","prepareSendAlert",$Log::debugging,"prepared queued alert $alertid for sending");

    #Check address type
    my $addr=$this->{addrs}[$addressid];

    if(defined $this->{prepareSendAlert}) {
	@{$this->{prepareSendAlert}{$addressid}}=$this->{prepareSendAlert}{$addressid}->[0]."\n\n\n".$alert->getMsg($User::msgtype[$addr->{type}],$this->{lang});
    } else {
	@{$this->{prepareSendAlert}{$addressid}}="Subject: ".$Log::cfg->{email_queue_subject}{$this->{lang}}."\n".$alert->getMsg($User::msgtype[$addr->{type}],$this->{lang});
    }
}

sub sendPreparedAlerts()
{
    my $this=shift;

    foreach my $addrid (keys(%{$this->{prepareSendAlert}})) {
	my $addr=$this->{addrs}[$addrid];
	my $func=\&{"send$User::msgtype[$addr->{type}]"};
	$this->{log}->printlog("User","sendPreparedAlerts",$Log::debugging,"sending prepared alerts");
	if(length($User::msgtype[$addr->{type}])>0) {
	    $this->$func($addr->{address},$this->{prepareSendAlert}{$addrid}->[0]);
	}
    }
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
      
      if(!$addr->{type}) {
	  $this->{log}->printlog("User","sendAlert",$Log::error,"no address type defined");
	  return;
      }

      my $func=\&{"send$User::msgtype[$addr->{type}]"};
      
      $this->$func($addr->{address},$alert->getMsg($User::msgtype[$addr->{type}],$this->{lang}),$alert);
  }


sub sendsms()
{
    my($this,$to,$msg,$alert)=@_;
    if(length($msg)==0)
    {
	$this->{log}->printlog("User","sendSMS",$Log::error,"no SMS message defined");
	return;
    }

    $this->{log}->printlog("User","sendSMS",$Log::informational,"SMS $to: $msg");

    my $severity=$alert->getSeverity();

    $this->{dbh}->do("insert into smsq (phone,msg,severity,time) values($to,'$msg',$severity,now())");
}

sub sendemail()
{
    my($this,$to,$msg)=@_;
    my $now=localtime;
    my($subject,$body);

    if(!defined $msg) {
	$this->{log}->printlog("User","sendEmail",$Log::error,"no msg defined");
	return;
    }

    $msg=~/^Subject: (.*)\n/;
    $subject=$1;
    $msg=~s/^Subject: (.*)\n//;
    $body=$msg;
    if(length($subject)==0)
    {
	$this->{log}->printlog("User","sendEmail",$Log::error,"no subject defined");
	return;
    }
    
    $this->{log}->printlog("User","sendEmail",$Log::informational,"EMAIL $to\tSubject: $subject");

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
    my ($this,$alertid,$alerts)=@_;
    my $ae;

    $this->{log}->printlog("User","checkActiveProfile",$Log::debugging, "checking active profile for user $this->{id}");

    #Get time periods
    if(!defined $this->{timePeriod})
      {
	$this->collectTimePeriod();
      }

    my $tp=$this->{timePeriod};
    my $aes=$tp->{aE};
    my $check;

    foreach my $a (@$aes)
      {
	  $check=$this->{eG}->checkAlert($a->{eGID},$alerts->getAlert($alertid));
	  if($check)
	  {
	    push @$ae,$a;	    
	  }
      }
    return $ae;
  }

sub checkRights()
  {
    my ($this,$alertid)=@_;

    $this->{log}->printlog("User","checkRights",$Log::debugging, "checking rights for user $this->{id}");
    
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
		  #Correct permissions
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
	      #Correct permissions
	      return 1;
	  }
      }

    $this->{log}->printlog("User","checkRights",$Log::debugging,"no rights: $alertid");
    return 0;
  }

1;


#  LocalWords:  addressid
