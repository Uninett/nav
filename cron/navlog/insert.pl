#!/usr/bin/perl
####################
#
# $Id: insert.pl,v 1.2 2002/11/25 12:13:56 gartmann Exp $
# This file is part of the NAV project.
# insert reads a number of log files from the navlog / syslog directory, parses
# the contents of the files, and inserts the data into the navlog database.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;
#use Fcntl qw/:flock/;
use Time::Local 'timelocal_nocheck';
require '/usr/local/nav/navme/lib/NAV.pm';
import NAV qw(:DEFAULT :collect :log);

use SNMP_util; #snmptraps sendes via denne

### setter mange parametre som sikkert skulle ligget i konfigurasjonsfil.

#PRIORITET
my $pri = "2";

#debugging;
my $mail = 1;  #sender mail ved 1
my $snmp = 1;  #sender snmp-traps ved 1
my $delete = 1;#sletter loggfiler etter uthenting ved 1

my $logdir = &get_path("path_navloglog");
my $unntaksfil = "/usr/local/nav/local/etc/conf/navlog/priority_exceptions.conf";

my %nav_conf = "/usr/local/nav/local/etc/conf/nav.conf";
my $admin_mail = $nav_conf{'ADMIN_MAIL'};

#MAIL
my $mail_to = 'Nav Administrator <'.$admin_mail.'>';
my $mail_from = 'NavLog <'.$admin_mail.'>';
my $mail_subject = ". prioritet syslogmelding";
my $mail_topp = "Siste 20 minutters NavLog-meldinger av prioritet $pri eller viktigere:\n";
my $webserver = `hostname`;
my $mail_bunn = "-- \nhttps://$webserver/sec/navlog/";

#TRAPS
my $trap_to = "localhost";
my $trap_from = "localhost";


#AINNA
$webserver =~ /^(\w+)\./;
my $log_sender_exception = $1;
#----------------------
#henter ut syslog_info til en array

my @bootlog; #denne brukes ikke i dag. var tiltenkt som en buffer for skriving til OS-bootlog.

my @feillogg;

my (%bare_boks,%bare_type,%boks_type);

my $conn = &db_get("insert");

my @system_fields = ("id","name");
my @origin_fields = ("id","name","systemid","category");
my @priority_fields = ("id","priority","keyword","description");
my @type_fields = ("id","systemid","facility","mnemonic","priorityid");
my @message_fields = ("time", "originid", "priority", "typeid", "message");

my %system = &db_select_hash($conn,"system",\@system_fields,1);
my %origin = &db_select_hash($conn,"origin",\@origin_fields,2,1);
my %priority = &db_select_hash($conn,"priority",\@priority_fields,0);
my %type = &db_select_hash($conn,"type",\@type_fields,1,2,3);

#hvis syslog_info ikke er tom
my $send = 0;
my @mail;

&unntak($unntaksfil);

opendir(DIR, $logdir) || die("Cannot open directory");


my @files = readdir(DIR);

for my $fil (@files) {

    # tar bare med de som ikke slutter med ~
    # tar vare på filas fornavn
    if($fil =~ /(\w+)\.log$/){

	my $system = $1;

	# finner systemets neste id-nummer.
	my $system_id;
	unless(exists($system{$system})){
	    $system_id = &make_and_get_sequence_number($conn,"system","id");
	    my $temp = [$system_id,$system];
	    &db_insert($conn,"system",\@system_fields,$temp);
	    $system{$system} = $temp;
	} else {
	    $system_id = $system{$system}[0];
	}

	my @log = &get_log($logdir.$fil,$delete);

	for (my $l = 0; $l < @log; $l++) {
	    my @melding = &log_split($conn, $log[$l]);
	    unless ($melding[0] =~ /^1$/) { #systemfeil gir 1

		my $time = $melding[0];
		my $origin_name = $melding[1];
		my $category_name = $melding[2];
		
		$melding[4] =~ /^(.*)-\d*-(.*)$/;
		my $facility = $1;
		my $mnemonic = $2;

		my $priority = $melding[3]+1;
		my $message = $melding[5];
#		print "$facility $priority $mnemonic $message\n";

		my $origin_id;
		unless(exists($origin{$system_id}{$origin_name})){
		    $origin_id = &make_and_get_sequence_number($conn,"origin","id");
		    my $temp = [$origin_id,$origin_name,$system_id,$category_name];
		    &db_insert($conn,"origin",\@origin_fields,$temp);
		    $origin{$system_id}{$origin_name} = $temp;
		} else {
		    $origin_id = $origin{$system_id}{$origin_name}[0];
		}

		my $type_id;
		unless(exists($type{$system_id}{$facility}{$mnemonic})){
		    $type_id = &make_and_get_sequence_number($conn,"type","id");
		    my $temp = [$type_id,$system_id,$facility,$mnemonic,$priority];
		    &db_insert($conn,"type",\@type_fields,$temp);
		    $type{$system_id}{$facility}{$mnemonic} = $temp;;
		} else {
		    $type_id = $type{$system_id}{$facility}{$mnemonic}[0];
		}

		&db_insert($conn,"message",\@message_fields,[$time,$origin_id,$priority,$type_id,$message]);

		if (defined($melding[3]) && $melding[3] < $pri + 1 && $melding[1] !~ /trolla-gw/i) {
		    $melding[0] = rydd_tid($melding[0]);
		    push(@mail, "Fra ".$system.":\n".$melding[0]."\t".$melding[1]."\t".$melding[4]."\n".$melding[5]."\n");
		    sendtrap($melding[0],$melding[1],$melding[4],$melding[5]) if $snmp;
		    $send = 1;
		}
	    }
	}
    }
}
send_mail(@mail) if $send && $mail;
logging($conn,\@feillogg);

sub log_split {
    my $conn = $_[0];
    my $a = $_[1];

    my $enten = 0;
    my %linje;

#de første femten tegnene i meldingen er syslogens timestamp, og er
#bestemt av syslog, gjør derfor regne med at de alltid vil være 15 tegn.
#Søket tar mye lengre tid hvis ikke.
#deretter kommer minst ett ikke-ord (minst en fordi det kanskje kan dukke
#opp flere mellomrom eller andre merkelige tegn).
#senderadressen er spesifisert som ikke-blanke-tegn.ord.ord med et
#ikke-ord etterpå.
#deretter får vi et eventuelt årstall (fra SWene) eller en teller som vi
#ignorerer (fra GWene) etterfulgt av et (mulig) mellomrom. Det kan dukke
#opp mange merkelige sekvenser av enda merkeligere tegn, så dette er
#kanskje best.
#vi får så datoen som et ord (måned i bokstaver), blanke tegn, ett eller
#flere tall (dag), blanke tegn, ett eller flere tall (time), kolon, ett
#eller flere tall (minutt), kolon, ett eller flere tall (sekund), med noen
#vilkårlige tegn etter.
#meldingstypene starter med %, fortsetter med ord (kan være ett mellomrom,
#jfr Cisco), -, prioritetstall, -, mnemonic (ikke nødvendigvis), kolon,
#mulige mellomrom før selve meldingen på slutten av linja.

    if ($a =~ /^(\w+)\s+(\d+)\s+(\d+)\:(\d+)\:.{2}\W+(\S+?(sw|gw|gsw|)\d*\.\w+\.\w+)\W+(?:(\d{4})|.*)\s+\W*(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+).*%(.*?):\s*(.*)$/) {
	my ($ar,$mnd,$sysmnd);
	$linje{sysmnd} = $sysmnd = finn_mnd($1);
	$linje{sysdag} = $2;
	$linje{systime} = $3; #syslogens egen time.
	$linje{sysmin} = $4; #syslogens eget minutt. Brukes for å teste om bokser har feil klokke. 
	$linje{boks} = $5;
	$linje{bokstype} = $6;
	$linje{mnd} = $mnd = finn_mnd($8);
	$linje{ar} = $ar = finn_ar($7,$mnd);
	$linje{dag} = $9;
	$linje{time} = $10;
	$linje{min} = $11;
	$linje{sek} = $12;
	$linje{type} = $13;
	$linje{beskrivelse} = $14;
	$13 =~ /.*-(\d+)-??.*/;
	$linje{prioritet} = $1;

	my $timediff = abs(timelocal_nocheck(0, $11, $10, $9, $mnd-1, $ar) - timelocal_nocheck(0, $4, $3, $2, $sysmnd-1, $ar));
	$enten = 1;

#tester om boksen har feil klokke
#OBS sjekker bare på timer og minutter!
#	unless($linje{sysmin}>$linje{min}-5&&$linje{systime}==$linje{time}||$linje{sysmin}<$linje{min}+5&&$linje{systime}==$linje{time}) {

	if($timediff>18000){
#	    my $t = scalar localtime timelocal_nocheck(0, $9, $8, $7, $mnd-1, $ar);
#	    my $t = scalar localtime timelocal_nocheck(0, $2, $1, $7, $mnd-1, $ar);
#---------
#setter bb-s systemtid.
	    $linje{mnd} = $linje{sysmnd};
	    $linje{dag} = $linje{sysdag};
	    $linje{time} = $linje{systime};
	    $linje{min} = $linje{sysmin};

#---------
#bygger opp systemmelding
	    $a = "Klokke er usynkronsiert: ".$a;
	    push(@feillogg,$a);
	}
    }
    
    elsif($a =~ /^(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\W+(\S+?(gw|sw|gsw|)\d*\.\w+\.\w+).*\W(\w+ ??\w+-(\d)-?\w*):\s*(.*)$/)
    {
	$linje{mnd} = finn_mnd($1);
	$linje{dag} = $2;
	$linje{time} = $3;
	$linje{min} = $4;
	$linje{sek} = $5;
	$linje{boks} = $6;
	$linje{bokstype} = $7;
	$linje{type} = $8;
	$linje{prioritet} = $9;
	$linje{melding} = $10;
	$linje{ar} = undef;
	$enten = 1;

    }    
    ### nav-meldinger.
    elsif($a =~ /^\w*\s??(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\s*(\d+|)\W+(\S+?)(?:\.(\w*)).*\W(\w+-(\d)-?\w*):\s*(.*)$/)
    {
	$linje{mnd} = finn_mnd($1);
	$linje{dag} = $2;
	$linje{time} = $3;
	$linje{min} = $4;
	$linje{sek} = $5;
	$linje{ar} = $6;
	$linje{boks} = $7;
	$linje{bokstype} = $8;
	$linje{type} = $9;
	$linje{prioritet} = $10;
	$linje{beskrivelse} = $11;
	
	$enten = 1;

    }

    $linje{prioritet} = &finn_prioritet($linje{boks},$linje{type},$linje{prioritet});

    if ($enten) {
	if(defined($linje{melding})) { #test for om linja i loggen er gyldig
#hvis ikke bokstype er definert, kall den "na"
	    if (!defined($linje{bokstype})) {$linje{bokstype} = "na";}
	}

	my @melding;
	$melding[0] = $linje{ar}."-".$linje{mnd}."-".$linje{dag}." ".$linje{time}.":".$linje{min}.":".$linje{sek}; #klokkeslett yyyymmddHHMMSS
	$melding[1] = $linje{boks}; #avsenderboks
	$melding[2] = $linje{bokstype}; #bokstype (ruter/svitsj)
	$melding[3] = $linje{prioritet}; #prioritet
	$melding[4] = $linje{type}; #meldingstype
	$melding[5] = $linje{beskrivelse}; #description
	return @melding;

    } else {
	if($a =~ /\b$log_sender_exception\b/) {
	    push(@bootlog,$a);
	} else {
	    push(@feillogg, $a);
	}
    }
	print $log_sender_exception."\n";
}

sub rydd_tid {
    $_ = $_[0];
    s/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/$3\.$2\.$1 $4:$5:$6/;
    return $_;
}

sub finn_ar {
    $_ = $_[0];
    my $mnd = $_[1];
    my $ar = 1900 + (localtime(time))[5];

    #setter på riktig år
    if (!defined) { #året er ikke satt av boksen selv
	if ((localtime(time-86400))[5] ne (localtime(time))[5]) {
#hvis året i går er forskjellig fra året i dag
	    if($mnd eq "01") { 
#hvis måneden er januar sett det nye året
		$_ = $ar;
	    } elsif ($mnd eq "12") {
#hvis måneden er desember, sett det gamle året
		$_ = $ar - 1;
	    }
	} else {
#hvis året i går er likt året i dag sett inn året
	    $_ = $ar;
	}
    }
    return $_;
}

sub finn_mnd {
    $_ = $_[0];
          SWITCH: {
	      s/Jan/01/i && last SWITCH;
	      s/Feb/02/i && last SWITCH;
	      s/Mar/03/i && last SWITCH;
	      s/Apr/04/i && last SWITCH;
	      s/May/05/i && last SWITCH;
	      s/Jun/06/i && last SWITCH;
	      s/Jul/07/i && last SWITCH;
	      s/Aug/08/i && last SWITCH;
	      s/Sep/09/i && last SWITCH;
	      s/Oct/10/i && last SWITCH;
	      s/Nov/11/i && last SWITCH;
	      s/Dec/12/i && last SWITCH;
      }
    return $_;
}

sub logging {
    my $conn = $_[0];
    my @logg = @{$_[1]};
    foreach (@logg){
	chomp;
	&db_insert($conn,"errorerror",["message"],[$_]);
    }
}

sub send_mail {

    use Mail::Sendmail;

    my @mail = @_;
    my %mail;
    my $hoy = "7"; # settes initielt til 7, settes lavere autamatisk
    my $message = $mail_topp;
    foreach (@mail) {
	/-(\d)-/;
	if ($1 < $hoy) {
	    $hoy = $1; 
	}
	$message .= "\n".$_;
    }
    $message .= $mail_bunn; 
    my $subject = $hoy.$mail_subject;


    %mail = ( To      => $mail_to,
	      From    => $mail_from,
	      Subject => $subject,
	      Message => $message
	      );
    
    unless (sendmail(%mail)) {
	print "Feil under sending av mail:\n ".$Mail::Sendmail::error;
    }

}

sub sendtrap {
   
    #.ntnu.nav.syslog
    my $prefix = '.1.3.6.1.4.1.3001.1.5';

    my ($var1,$var2,$var3,$var4) = @_;
    my @data;

    #.ntnu.nav.syslog.suboids
    my $newprefix = ".1.3.6.1.4.1.3001.1.5.1";

    push(@data, "$newprefix.1", 'string', "$var1"); # Datotidformat
    push(@data, "$newprefix.2", 'string', "$var2"); # Fra enhet 
    push(@data, "$newprefix.3", 'string', "$var3"); # Type 
    push(@data, "$newprefix.4", 'string', "$var4"); # Selve meldingen 

    &snmptrap($trap_from, $prefix, $trap_to, 6, 1, @data);
# 1: fra (ip)
# 3: til / hostname (ip)

}

sub unntak {
    my $fil = $_[0];
    my @linje;

    open (FIL, "<$fil") || die ("KUNNE IKKE ÅPNE FILA: $fil");
    foreach (<FIL>) {
	if(@linje = &fil_hent_linje(3,$_)){
	    if (($linje[2] ne "" || $linje[1] ne "") && $linje[0] ne ""){
		if ($linje[2] eq ""){
#		    print "\n $_ blir lagt i bare_type";
		    $bare_type{$linje[1]} = $linje[0];
		} elsif ($linje[1] eq ""){
#		    print "\n $_ blir lagt i bare_boks";
		    $bare_boks{$linje[2]} = $linje[0];
		} else {
#		    print "\n $_ blir lagt i boks_type";
		    $boks_type{$linje[1]}{$linje[2]} = $linje[0];
		}
	    } else {
#		print "\n $_ passet ikke inn";
	    }
	}
    }
    close FIL;
}

sub finn_prioritet {
    my $boks = $_[0];
    my $type = $_[1];
    my $gammel_prioritet = $_[2];

    if(exists($boks_type{$boks}{$type})){
	return $boks_type{$boks}{$type};
    } elsif (exists($bare_type{$type})){
	return $bare_type{$type};
    } elsif (exists($bare_boks{$boks})){
	return $bare_boks{$boks};
    } else {
	return $gammel_prioritet;
    }
}

