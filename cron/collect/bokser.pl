#!/usr/bin/perl

#use Socket;
use SNMP_util;
use strict;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $lib = &lib();
my $localkilde = &localkilde();
my $localconf = &localconf();
require "$lib/database.pl";
require "$lib/snmplib.pl";
require "$lib/fil.pl";

&log_open;

my $conn = &db_connect("manage","navall","uka97urgf");

my $mib_sysname = ".1.3.6.1.2.1.1.5.0";
my $mib_type =     ".1.3.6.1.2.1.1.2.0";

my (%server,%db_server,%nettel,%db_nettel,%alle,%db_alle);

#unntak: bokser på watch
my %db_unntak = ();#&db_hent_enkel($conn,"select ip,watch from boks where watch='y' or watch='t'");

#sysname-endelser
#leses inn fra fil og legges i kolonseparert skalar
    my $fil_endelser = "$localconf/endelser.txt";
    my $endelser = &fil_endelser($fil_endelser);
    my %type = &db_hent_enkel($conn,"SELECT sysobjectid,typeid FROM type");
#-----------------------
#FILLESING: server.txt
my @felt_server = ("ip","sysname","romid","orgid","kat","kat2","ro");
my $fil_server = "$localkilde/server.txt";
%server = &fil_server($fil_server,scalar(@felt_server),$endelser);

#----------------------------------
#DATABASELESING

#hadde tenkt å ha med watch her, men vi bruker ikke snmp på servere per dags dato. Kan bare settes på når de ikke blir tatt med da de ikke svarer på snmp.
%db_server = &db_hent_hash($conn,"SELECT ".join(",", @felt_server )." FROM boks where kat = 'SRV'");
#legge til alle
for my $a (keys %db_server) {
    my $ip = $db_server{$a}[0];
    $db_alle{$ip} = 1;
}
&db_endring($conn,\%server,\%db_server,\@felt_server,"boks");

#------------------------------
#FILLESING: nettel.txt
my @felt_nettel = ("ip","sysname","typeid","romid","orgid","kat","kat2","ro","rw");
my $fil_nettel = "$localkilde/nettel.txt";
%nettel = &fil_nettel($fil_nettel,scalar(@felt_nettel),$endelser,\%db_unntak);

#----------------------------------
#DATABASELESING
#felter som skal leses ut av databasen

%db_nettel = &db_hent_hash($conn,"SELECT ".join(",", @felt_nettel )." FROM boks where kat <> 'SRV'");

#legge til i alle
for my $a (keys %db_nettel) {
    my $ip = $db_nettel{$a}[0];
    $db_alle{$ip} = 1;
}
&db_nettel_endring($conn,\%nettel,\%db_nettel,\@felt_nettel,"boks");

#-----------------------------------
#DELETE
    my @felt_alle = ("ip"); # felt som fungerer som sletteindex, i.e. ip
    &db_sletting($conn,\%alle,\%db_alle,\@felt_alle,"boks");


&log_close;

# end main
#-----------------------------------------------------------------------

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
    my ($fil,$felt,$endelser) = @_[0..2];
    my %unntak = %{$_[3]};
    
    open (FIL, "<$fil") || die ("kunne ikke åpne $fil");
    while (<FIL>) {
	@_ = &fil_hent_linje($felt,$_);
	my $ip = $_[1];
	if($ip&&!exists($unntak{$ip})){
	    my $ro = $_[5];
	    if (my @passerr = $ro =~ /(\W)/g){ #sier fra hvis det finnes non-alfanumeriske tegn i passordet, og skriver ut (bare) disse tegnene.
		my $passerr = join "",@passerr;
		&skriv("TEXT-COMMUNITY", "ip=$ip","illegal=$passerr");
	    }
	    if (my @passerr = $_[6] =~ /(\W)/g){ #sier fra hvis det finnes non-alfanumeriske tegn i passordet, og skriver ut (bare) disse tegnene.
		my $passerr = join "",@passerr;
		&skriv("TEXT-COMMUNITY", "ip=$ip","illegal=$passerr");
	    }
	    my $temptype;
	    my $sysname;
# gammel    ($sysname,$temptype) = &snmp_system(1,$ip,$ro,$endelser);
	    ($sysname,$temptype) = &snmpsystem($ip,$ro,$endelser);
	    my $type = $type{$temptype};
	    if($sysname){
		unless($type){
		    &skriv("TEXT-TYPE","ip=$ip","type=$temptype");
		}
		@_ = ($ip,$sysname,$type,$_[0],$_[2],@_[3..6]);
		@_ = map rydd($_), @_;
		
		$nettel{$ip} = [ @_ ];
	    }
	    # må legges inn så lenge den eksisterer i fila, uavhengig av snmp
	    $alle{$ip} = 1;
#	    print $sysname.$type."\n";
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
	    @_ = ($ip,@_[0..1],lc($_[2]),uc($_[3]),@_[4..5]);
	    @_ = map rydd($_), @_;
	    
	    my $sysname = &fjern_endelse($_[2],$endelser);
	    
	    $server{$ip} = [ $ip,$sysname,$_[1],@_[3..6] ];
	    $alle{$ip} = 1;
	}
    }
    close FIL;
    return %server;
}
sub db_nettel_endring {
#helt lik
    my $db = $_[0];
    my %ny = %{$_[1]};
    my %gammel = %{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];
    for my $feltnull (keys %ny) {
	&db_nettel_endring_per_linje($db,\@{$ny{$feltnull}},\@{$gammel{$feltnull}},\@felt,$tabell,$feltnull);
    }
}
sub db_nettel_endring_per_linje {
    my $db = $_[0];
    my @ny = @{$_[1]};
    my @gammel = @{$_[2]};
    my @felt = @{$_[3]};
    my $tabell = $_[4];
    my $id = $_[5];
    
    #eksisterer i databasen?
    if($gammel[0]) {
#-----------------------
#UPDATE
	for my $i (0..$#felt ) {
	    if(defined( $gammel[$i] ) && defined( $ny[$i] )){
#		print "NY: $ny[$i] GAMMEL: $gammel[$i]\n";
		unless($ny[$i] eq $gammel[$i]) {
		    #oppdatereringer til null må ha egen spørring
		    if ($ny[$i] eq "" && $gammel[$i] ne ""){
			&db_oppdater($db,$tabell,$felt[$i],$gammel[$i],"null",$felt[0],$id);
		    } else {
			
			&db_oppdater($db,$tabell,$felt[$i],"\'$gammel[$i]\'","\'$ny[$i]\'",$felt[0],$id);
		    }
		}
	    }
	}
    }else{
#-----------------------
#INSERT
	&db_sett_inn($db,$tabell,join(":",@felt),join(":",@ny));
	
    }
}
