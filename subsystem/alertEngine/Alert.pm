# Alert.pm
#
# Class that contains all relevant information about a specific alert.
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

package NAV::AlertEngine::Alert;
use NAV::AlertEngine::Log;
use strict;

sub new
#Constructor
  {
    my $this={};
    my $class=shift;
    $this->{dbh}=shift;
    $this->{id}=shift;
    $this->{log}=NAV::AlertEngine::Log->new();
    bless $this,$class;
    $this->collectInfo();
    return $this;
  }

sub collectInfo()
#Collects all relevant information
#Returns true if successful.
  {
    my $this=shift;

    my $sth = $this->{dbh}->prepare("select * from alertq where alertqid=$this->{id}");
    $sth->execute;

    $this->{alertq}=$sth->fetchrow_hashref();

    if($DBI::errstr)
      {
	  $this->{log}->printlog("Alert","collectInfo",$Log::error, "could not get information about alert");
	  return 0;
      }

    $this->{queued}=0;
    return 1;
  }

sub getInfo()
#Returns information from manage database related to the alert
{
    my ($this,$info)=@_;

    my ($db,$col)=split '\.',$info;

    $this->{log}->printlog("Alert","getInfo",$Log::debugging, "collecting info from table $db column $col");

    if(!defined $this->{$db})
    {
	#Collect table from manage database
	if($db eq "arp") {
	    $this->collecttable($db,"select a.* from arp a, netbox n where n.netboxid=$this->{alertq}->{netboxid} and a.netboxid=n.netboxid");
	}
	elsif($db eq "cam") {
	    $this->collecttable($db,"select c.* from cam c, netbox n where n.netboxid=$this->{alertq}->{netboxid} and c.netboxid=n.netboxid");
	}
	elsif($db eq "cat") {
	    $this->collecttable($db,"select c.* from cat c, netbox n where n.netboxid=$this->{alertq}->{netboxid} and n.catid=c.catid");
	}
	elsif($db eq "device") {
	    $this->collecttable($db,"select d.* from device d, netbox n where n.netboxid=$this->{alertq}->{netboxid} and d.deviceid=n.deviceid");
	}
	elsif($db eq "eventtype") {
	    $this->collecttable($db,"select * from eventtype where eventtypeid='$this->{alertq}->{eventtypeid}'");
	}
	elsif($db eq "gwport") {
	    $this->collecttable($db,"select g.* from gwport g,module m, netbox n where n.netboxid=$this->{alertq}->{netboxid} and m.deviceid=n.deviceid and g.moduleid=m.moduleid");
	}
	elsif($db eq "location") {
	    $this->collecttable($db,"select l.* from location l, room r, netbox n where n.netboxid=$this->{alertq}->{netboxid} and r.roomid=n.roomid and r.locationid=l.locationid");
	}
	elsif($db eq "mem") {
	    $this->collecttable($db,"select m.* from mem m, netbox n where n.netboxid=$this->{alertq}->{netboxid} and m.netboxid=n.netboxid");
	}
	elsif($db eq "module") {
	    $this->collecttable($db,"select m.* from module m, netbox n where n.netboxid=$this->{alertq}->{netboxid} and m.deviceid=n.deviceid");
	}
	elsif($db eq "netbox") {
	    $this->collecttable($db,"select * from netbox where netboxid=$this->{alertq}->{netboxid}");
	}
	elsif($db eq "netboxcategory") {
	    $this->collecttable($db,"select nc.* from netboxcategory nc, netbox n where n.netboxid=$this->{alertq}->{netboxid} and nc.netboxid=n.netboxid");
	}
	elsif($db eq "netboxinfo") {
	    $this->collecttable($db,"select ni.* from netboxinfo ni, netbox n where n.netboxid=$this->{alertq}->{netboxid} and ni.netboxid=n.netboxid");
	}
	elsif($db eq "org") {
	    $this->collecttable($db,"select o.* from org o, netbox n where n.netboxid=$this->{alertq}->{netboxid} and o.orgid=n.orgid");
	}
	elsif($db eq "prefix") {
	    $this->collecttable($db,"select p.* from prefix p, netbox n where n.netboxid=$this->{alertq}->{netboxid} and p.prefixid=n.prefixid");
	}
	elsif($db eq "product") {
	    $this->collecttable($db,"select p.* from product p, device d, netbox n where n.netboxid=$this->{alertq}->{netboxid} and d.deviceid=n.deviceid and p.productid=d.productid");
	}
	elsif($db eq "room") {
	    $this->collecttable($db,"select r.* from room r, netbox n where n.netboxid=$this->{alertq}->{netboxid} and r.roomid=n.roomid");
	}
	elsif($db eq "service") {
	    $this->collecttable($db,"select s.* from service s, netbox n where n.netboxid=$this->{alertq}->{netboxid} and s.netboxid=n.netboxid");
	}
	elsif($db eq "subsystem") {
	    $this->collecttable($db,"select * from subsystem where name=$this->{alertq}->{subid}");
	}
	elsif($db eq "swport") {
	    $this->collecttable($db,"select s.* from swport s,module m, netbox n where n.netboxid=$this->{alertq}->{netboxid} and m.deviceid=n.deviceid and s.moduleid=m.moduleid");
	}
	elsif($db eq "type") {
	    $this->collecttable($db,"select t.* from type t, netbox n where n.netboxid=$this->{alertq}->{netboxid} and t.typeid=n.typeid");
	}
	elsif($db eq "typegroup") {
	    $this->collecttable($db,"select tg.* from typegroup tg,type t, netbox n where n.netboxid=$this->{alertq}->{netboxid} and t.typeid=n.typeid and tg.typegroupid=t.typehroupid");
	}
	elsif($db eq "usage") {
	    $this->collecttable($db,"select u.* from usage u,vlan v,org o, netbox n where n.netboxid=$this->{alertq}->{netboxid} and o.orgid=n.orgid and v.orgid=o.orgid and u.usageid=v.usageid");
	}
	elsif($db eq "vendor") {
	    $this->collecttable($db,"select v.* from vendor v, product p, device d, netbox n where n.netboxid=$this->{alertq}->{netboxid} and d.deviceid=n.deviceid and p.productid=d.productid and v.vendorid=p.vendorid");
	}
	elsif($db eq "vlan") {
	    $this->collecttable($db,"select v.* from vlan v,org o, netbox n where n.netboxid=$this->{alertq}->{netboxid} and o.orgid=n.orgid and v.orgid=o.orgid");
	}
	elsif($db eq "alerttype") {
	    $this->collecttable($db,"select * from alerttype where alerttypeid=$this->{alertq}->{alerttypeid}");
	}
	else {
	    $this->{log}->printlog("Alert","getInfo",$Log::warning, "no support for table $db");
	}

    }
    return $this->{$db}->{$col};
}

sub collecttable()
{
    my ($this,$name,$sql)=@_;

    $this->{log}->printlog("Alert","collecttable",$Log::debugging, "collecting info from table: $sql");
	
    my $sth=$this->{dbh}->prepare($sql);
    $sth->execute;
    $this->{$name}=$sth->fetchrow_hashref();
	    
    if($DBI::errstr)
    {
	$this->{log}->printlog("User","collecttable",$Log::error,"could not get information about table $name");
	return 0;
    }	    
}

sub getMsg()
{
    my ($this,$type,$lang)=@_;
    if(!defined $this->{alertvar})
    {
	$this->collectVar();
    }

    if(!defined $this->{alertvar}{$type}{$lang}) {
	$this->{log}->printlog("Alert","getMsg",$Log::warning, "no $type alert defined for language $lang for alertid $this->{id}");
	return "";
    }
    return $this->{alertvar}{$type}{$lang};
}

sub collectVar()
{
    my $this=shift;

    my $vars=$this->{dbh}->selectall_arrayref("select msgtype,language,msg from alertqmsg where alertqid=$this->{id}") || $this->{log}->printlog("Alert","collectVar",$Log::error, "could not get alertqmsg list");

    foreach my $var (@$vars)
    {
	$this->{alertvar}{$var->[0]}{$var->[1]}=$var->[2];
    }    
}

sub getEventtype()
{
    my $this=shift;
    return $this->{alertq}->{eventtypeid};
}

sub getSeverity()
{
    my $this=shift;
    return $this->{alertq}->{severity};
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
	$this->{log}->printlog("Alert","delete",$Log::debugging, "deleted alertqid=$this->{id}");	
	#$this->{dbh}->do("delete from alertq where alertqid=$this->{id}");    
    }
}

1;
