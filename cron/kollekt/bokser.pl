#!/usr/bin/perl -w

#use Socket;
use SNMP_util;
use strict;

my $vei = "/usr/local/nav/navme/lib";
require "$vei/database.pl";
require "$vei/snmplib.pl";
require "$vei/fil.pl";

my $conn = &db_connect("manage","navall","uka97urgf");

my $mib_sysname = ".1.3.6.1.2.1.1.5.0";
my $mib_type =     ".1.3.6.1.2.1.1.2.0";

my (%server,%db_server,%nettel,%db_nettel,%alle,%db_alle);

#sysname-endelser
#leses inn fra fil og legges i kolonseparert skalar
    my $fil_endelser = "/usr/local/nav/etc/conf/endelser.txt";
    my $endelser = &fil_endelser($fil_endelser);
    my %type = &db_hent_enkel($conn,"SELECT sysobjectid,typeid FROM type");
#-----------------------
#FILLESING: server.txt
my @felt_server = ("ip","romid","sysname","orgid","kat","kat2","ro");
my $fil_server = "/usr/local/nav/etc/server.txt";
%server = &fil_server($fil_server,scalar(@felt_server),$endelser);

#----------------------------------
#DATABASELESING

%db_server = &db_hent_hash($conn,"SELECT ".join(",", @felt_server )." FROM boks");
#legge til alle
for my $a (keys %db_server) {
    $db_alle{$a} = 1;
}

&db_endring($conn,\%server,\%db_server,\@felt_server,"boks");

#------------------------------
#FILLESING: nettel.txt
my @felt_nettel = ("ip","typeid","romid","sysname","orgid","kat","kat2","ro","rw");
my $fil_nettel = "/usr/local/nav/etc/nettel.txt";
%nettel = &fil_nettel($fil_nettel,scalar(@felt_nettel),$endelser);

#----------------------------------
#DATABASELESING
#felter som skal leses ut av databasen

%db_nettel = &db_hent_hash($conn,"SELECT ".join(",", @felt_nettel )." FROM boks");

#legge til i alle
for my $a (keys %db_nettel) {
    $db_alle{$a} = 1;
}
&db_endring($conn,\%nettel,\%db_nettel,\@felt_nettel,"boks");

#-----------------------------------
#DELETE
    my @felt_alle = ("ip");
    &db_sletting($conn,\%alle,\%db_alle,\@felt_alle,"boks");

sub fil_endelser {
    my $fil = $_[0];
    open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
    my @endelser;
    while (<FIL>) {
	next unless /^\./; 
	my $endelse = rydd($_);
	@endelser=(@endelser,$endelse);
    }
    close FIL;
    return join(":",@endelser);
}
sub fil_nettel{
    my ($fil,$felt,$endelser) = @_;
    
    open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
    while (<FIL>) {
	@_ = &fil_hent_linje($felt,$_);

	if(my $ip = $_[1]){
	    my $ro = $_[5];
	    my $temptype;
	    if($temptype = &snmp_type($ip,$ro,$mib_type)) {
		my $type = $type{$temptype};
		my $sysname = &snmp_sysname($ip,$ro,$mib_sysname,$endelser);
		if($type) {
		    @_ = ($ip,$type,$_[0],$sysname,$_[2],@_[3..6]);
		    @_ = map rydd($_), @_;
		    
		    $nettel{$_[0]} = [ @_ ];
		    $alle{$_[0]} = 1;
		}
	    }
	}
	
    }
    close FIL;
    return %nettel;
}
sub fil_server{
    my ($fil,$felt,$endelser) = @_;

    open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
    while (<FIL>) {

	@_ = &fil_hent_linje($felt,$_);

	my $ip;
	if($ip = &hent_ip($_[1])) {
	    @_ = ($ip,@_[0..5]);
	    @_ = map rydd($_), @_;
	    
	    my $sysname = &fjern_endelse($_[2],$endelser);
	    
	    $server{$_[0]} = [ @_[0..1],$sysname,@_[3..6] ];
	    $alle{$_[0]} = 1;
	}
    }
    close FIL;
    return %server;
}
return 1;
