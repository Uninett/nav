# EquipmentGroups.pm
#
# Class that contains information about all available equipment groups
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

package EquipmentGroups;

use strict;
use IP;
use Log;

#my $dbh;
#my %info;

sub new
#Constructor
  {
    my $this={};
    shift;
    $this->{dbh}=shift;

    #Access control fields
    $this->{datatype}{string}=0;
    $this->{datatype}{int}=1;
    $this->{datatype}{ip}=2;
    
    #Access control type
    $this->{type}{eq}=0;
    $this->{type}{more}=1;
    $this->{type}{moreeq}=2;
    $this->{type}{less}=3;
    $this->{type}{lesseq}=4;
    $this->{type}{neq}=5;
    $this->{type}{in}=11;
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

    my $egs=$this->{dbh}->selectall_arrayref("select id,accountid from utstyrgruppe");

    if($DBI::errstr)
      {
	$this->{log}->printlog("EquipmentGroups","collectInfo",$Log::error,"could not get list of equipment groups");
	return 0;
      }

    foreach my $eg (@$egs)
      {
	$this->{info}[$eg->[0]]->{user}=$eg->[1];
	my $efs=$this->{dbh}->selectall_arrayref("select uf.id, uf.accountid, gtf.inkluder, gtf.prioritet,gtf.positiv from utstyrgruppe ug,gruppetilfilter gtf, utstyrfilter uf where ug.id=$eg->[0] and ug.id=gtf.utstyrgruppeid and uf.id=gtf.utstyrfilterid order by gtf.prioritet");
	
	if($DBI::errstr)
	  {
	      $this->{log}->printlog("EquipmentGroups","collectInfo",$Log::error,"could not get list of equipment filters\n");
	    return 0;
	  }

	my $c=0;
	foreach my $ef (@$efs)
	  {
	    $this->{info}[$eg->[0]]->{filters}[$c]->{userid}=$ef->[1];
	    $this->{info}[$eg->[0]]->{filters}[$c]->{included}=$ef->[2];
	    $this->{info}[$eg->[0]]->{filters}[$c]->{priority}=$ef->[3];
	    $this->{info}[$eg->[0]]->{filters}[$c]->{positive}=$ef->[4];

	    my $fms=$this->{dbh}->selectall_arrayref("select fm.id,fm.matchfelt,fm.matchtype,fm.verdi,mf.valueid,mf.datatype from filtermatch fm,utstyrfilter uf,matchfield mf where fm.utstyrfilterid=uf.id and uf.id=$ef->[0] and fm.matchfelt=mf.matchfieldid");

	    if($DBI::errstr)
	      {
		  $this->{log}->printlog("EquipmentGroups","collectInfo",$Log::error,"could not get list of equipment filters\n");
		return 0;
	      }
	
	    my $c2=0;
	    foreach my $fm (@$fms)
	      {
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{field}=$fm->[1];
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{type}=$fm->[2];
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{value}=$fm->[3];
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{valueid}=$fm->[4];
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{datatype}=$fm->[5];
		$c2++;
	      }
	    $c++;
	  }
      }

    return 1;
  }

sub checkAlert()
#Check to see if equipement in alert is part of this equipment group.
  {
    my ($this,$eGID,$alert)=@_;

    my $filters=$this->{info}[$eGID]->{filters};

    my $alertid=$alert->getID();
    $this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "checking to see if alertid $alertid is in equipmentgroup $eGID");

    #Get numExclude and numInclude
    my $numExclude=0;
    my $numInclude=0;
    foreach my $filter (@$filters)
      {
	if($filter->{included})
	  {
	    $numInclude++;
	  }
	else
	  {
	    $numExclude++;
	  }
      }

    #Go through filters
    my $ret=0;
    foreach my $ef (@$filters)
      {
	my $fms=$ef->{filterMatch};
	foreach my $fm (@$fms)
	  {
	    my $match=$this->checkMatch($fm,$alert);

	    if($ef->{positive}==0) {
		$this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "inverted filter(NOT)");
		if($match==1) {
		    $match=0;
		} else {
		    $match=1;
		}
	    }

	    if($match==1 && $ef->{included}==1)
	      {
		$ret=1;
	      }
	    elsif($match && !$ef->{included})
	      {
		$this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "exclude");
		$ret=0;
	      }
	
	    if($ret==1 && $numExclude==0)
	      {
		  $this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "Alertid $alertid is in equipmentgroup $eGID");
		  return $ret;
	      }
	    elsif(!$ret && !$numInclude)
	      {
		  $this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "Alertid $alertid is not in equipmentgroup $eGID");
		  return $ret;
	      }

	    if($ef->{included})
	      {
		$numInclude--;
	      }
	    else
	      {
		$this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "exclude");
		$numExclude--;
	      }
	  }
      }

    if($ret==0) {
	$this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "Alertid $alertid is not in equipmentgroup $eGID");
    } else {
	$this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "Alertid $alertid is in equipmentgroup $eGID");
    }

    return $ret;
  }

sub checkMatch()
  {
    my ($this,$fm,$alert)=@_;
    my $ret;
    $ret=0;

    #Get correct info from alert
    my $info=$alert->getInfo($fm->{valueid});

    if($fm->{datatype}==$this->{datatype}{string}) {
	$ret=$this->checkString($fm->{type},$fm->{value},$info);
    }
    elsif($fm->{datatype}==$this->{datatype}{int}) {
	$ret=$this->checkInt($fm->{type},$fm->{value},$info);
    }
    elsif($fm->{datatype}==$this->{datatype}{ip}) {
	$ret=$this->checkIP($fm->{type},$fm->{value},$info);
    }
    else {
	$ret=$this->checkString($fm->{type},$fm->{value},$info);
    }

    $this->{log}->printlog("EquipmentGroups","checkMatch",$Log::debugging, "datatype=$fm->{datatype} type=$fm->{type} value=$fm->{value} info=$info ret=$ret");

    return $ret;
  }

sub checkString()
{
    my ($this,$type,$value,$str)=@_;
    my $match=0;
    my @strings;

    if($type==$this->{type}{in}) {
	@strings=split(/\|/,$value);
	foreach my $s (@strings) {
	    if($str eq $s) {
		return 1;
	    }
	}
	return 0;
    } else {
	if($value eq $str) {
	    $match=1;
	}
	
	if($type==$this->{type}{eq}) {
	    return $match;
	} else {
	    return !$match;
	}
    }
	
}

sub checkInt()
{
    my ($this,$type,$value,$int)=@_;
    if($type==$this->{type}{eq}) {
	if($int==$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{more}) {
	if($int>$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{moreeq}) {
	if($int>=$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{less}) {
	if($int<$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{lesseq}) {
	if($int<=$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{ne}) {
	if($int!=$value) {
	    return 1;
	}	    
    }
    return 0;	
}


sub checkStringRegExp()
{
    my ($this,$type,$value,$name)=@_;
    
    my $match=0;

    if($name=~/$value/)
    {
	$match=1;
    }

    if($type==$this->{type}{eq})
    {
	return $match;
    }
    if($type==$this->{type}{nq})
    {
	return !$match;
    }

    return 0;
}

sub checkIP()
# Suports following formats:
# 10.0.0.1,10.0.0.2,10.1.1.0/24 - multiple IP addresses can be
# specified using , to seperate them.
  {
    my ($this,$type,$value,$ipaddr)=@_;

    my @list=split ",",$value;

    my $match=0;

    my $ip1;
    my $ip2=new NetAddr::IP($ipaddr);
    if(!$ip2) {
	return 0;
    }

    foreach my $addr (@list)
    {
	$ip1=new NetAddr::IP($addr);
	if(!$ip1) {
	    return 0;
	}
	if($ip1->contains($ip2)) 
	{
	    $match=1;
	}
    }
    
    if($type==$this->{type}{eq})
    {
	return $match;
    }
    if($type==$this->{type}{nq})
    {
	return !$match;
    }
    
    return 0;
  }

1;
