#!/usr/bin/perl

use strict;
use DBI;
use Fcntl qw/:flock/;
use Mail::Sendmail;
use Time::Local 'timelocal_nocheck';

require "/usr/local/nav/navme/lib/database.pl";
require "/usr/local/nav/navme/lib/fil.pl";

use SNMP_util;

#PRIORITET
my $pri = "2";

#FIL
my $dir = "/usr/local/nav/navme/syslog/";
my $logdir = "/usr/local/nav/local/log/syslog/";
my $loggfil = "/usr/local/nav/local/log/cisco.log";
my $unntaksfil = "/usr/local/nav/local/etc/conf/syslog/unntak.txt";

#MAIL
my $mail_til_fra = "Syslog (auto)<gartmann\@pvv.ntnu.no>";
my $mail_subject = ". prioritet syslogmelding";
my $mail_topp = "Siste fem minutters syslogmeldinger av prioritet $pri eller viktigere:\n";
my $mail_bunn = "-- \nhttps://www.nav.ntnu.no/sec/syslog/";

#debugging;
my $mail = 1;  #sender mail ved 1
my $snmp = 0;  #sender snmp-traps ved 1

#----------------------
#henter ut syslog_info til en array

my @syslog = hent_syslog($loggfil);

my @bootlog;
my @feillogg;

my (%bare_boks,%bare_type,%boks_type);


#hvis syslog_info ikke er tom
if (scalar(@syslog)){
    my $send = 0;
    my @mail;


    &unntak($unntaksfil);

#    my $dbh = DBI->connect("dbi:mysql:syslog","syslogadmin","urg20ola");
    
#    my $sth = $dbh->prepare(q{
#	    INSERT INTO meldinger (tid, boks, bokstype, prioritet, type, beskrivelse) VALUES (?, ?, ?, ?, ?, ?)
#	    }) || die $dbh->errstr;

    my $conn = &db_connect("syslog","syslogadmin","urg20ola");

    my @felt = ("tid", "boks", "bokstype", "prioritet", "type", "beskrivelse");

#    open(MAILLOG, ">$dir/syslogsjekk.mail");
#henter inn antall linjer som var i loggen sist skriptet ble kjørt, og legger til de nye i databasen

    for (my $l = 0; $l < @syslog; $l++) {
	my @melding = &syslogsplit($conn, $syslog[$l]);
	unless ($melding[0] =~ /^1$/) { #systemfeil gir 1
	    my @db_hei = @melding[0..5];
	    &db_insert($conn,"meldinger",\@felt,\@db_hei);
#	    $sth->execute(@melding[0..5]);
	    if (defined($melding[3]) && $melding[3] < $pri + 1 && $melding[1] !~ /trolla-gw/i) {
		$melding[0] = rydd_tid($melding[0]);
		push(@mail, $melding[0]."\t".$melding[1]."\t".$melding[4]."\n".$melding[5]."\n");
		sendtrap($melding[0],$melding[1],$melding[4],$melding[5]) if $snmp;
		$send = 1;
	    }
	}
    }
#    close MAILLOG;
    send_mail(@mail) if $send && $mail;
#    logging(">>/var/log/boot.log",\@bootlog);
    logging(">>$logdir/feillogg.log",\@feillogg);
#    $sth->finish;
#    $dbh->disconnect;
}

sub hent_syslog {
    my $fil = $_[0];
    open(SYSLOG, "+<$fil") or die "her: $!";
    flock(SYSLOG, LOCK_EX) or die "klarte ikke å låse fila: $!";
    @_ = <SYSLOG>;
    truncate(SYSLOG,0); #slett gammel fil
    close SYSLOG;
    flock(SYSLOG, LOCK_UN);
    return @_;
}

sub syslogsplit {
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
    if ($a =~ /^(\w+)\s+(\d+)\s+(\d+)\:(\d+)\:.{2}\W+(\S+?(sw|gw|)\d*\.\w+\.\w+)\W+(?:(\d{4})|.*)\s+\W*(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+).*%(\w+ ??\w+-(\d)-?\w*):\s*(.*)$/) {
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
	$linje{prioritet} = $14;
	$linje{beskrivelse} = $15;

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
#	    my $dbh = DBI->connect("dbi:mysql:syslog","syslogadmin","urg20ola");
#	    my $sth = $dbh->prepare(q{
#		INSERT INTO errorsyslog (logg) VALUES (?)
#		}) || die $dbh->errstr;
#---------
#	    my @felt = ("logg");
#	    my @verdier = ($a);
#	    &db_insert($conn,"feillogg",\@felt,\@verdier);
#---------
#	    $sth->execute($_);
#	    $sth->finish;
#	    $dbh->disconnect;
	    print "\nlegger $a på feilloggen";
	    push(@feillogg,$a);
	}
    }
    
    elsif($a =~ /^(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\W+(\S+?(gw|sw|)\d*\.\w+\.\w+).*\W(\w+ ??\w+-(\d)-?\w*):\s*(.*)$/)
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
    $linje{prioritet} = &finn_prioritet($linje{boks},$linje{type},$linje{prioritet});

    if ($enten) {
	if(defined($linje{melding})) { #test for om linja i loggen er gyldig
#hvis ikke bokstype er definert, kall den "na"
	    if (!defined($linje{bokstype})) {$linje{bokstype} = "na";}
	}
#setter inn tallrepresentasjon av måned
#	$linje{mnd} =  finn_mnd($linje{mnd});

#setter på riktig år
#	$linje{ar} = finn_ar($linje{ar},$linje{mnd});
	
#legger til ekstra null hvor det bare finnes ett enkelt tall
	foreach $_ (keys(%linje)) {
#debugging	    print $_."\t".$linje{$_};
	    if ($linje{$_} =~ /^\d$/ && $_ ne "prioritet") {
		$linje{$_} = "0".$linje{$_};
	    }
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
	if($a =~ /\ bb\ /) {
#	    chomp;
	    print "\nlegger $a på feilloggen";
	    push(@bootlog,$a);
#	    open(BOOTLOG, ">>/var/log/boot.log");
#	    print BOOTLOG $a;
#	    close BOOTLOG;
	} else {
#	    my $dbh = DBI->connect("dbi:mysql:syslog","syslogadmin","urg20ola");
#	    my $sth = $dbh->prepare(q{
#		INSERT INTO errorsyslog (logg) VALUES (?)
#		}) || die $dbh->errstr;
#	    $sth->execute($_);
#	    $sth->finish;
#	    $dbh->disconnect;
#--------
#	    my @felt = ("logg");
#	    my @verdier = ($a);
#	    &db_insert($conn,"feillogg",\@felt,\@verdier);
#--------
	    print "\nlegger $a på feilloggen";
	    push(@feillogg, $a);
	}
    }
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
    my $filstrukt = $_[0];
    my @logg = @{$_[1]};
    open(FEILLOGG, $filstrukt);
    foreach (@logg) {
	print FEILLOGG $_;
    }
    close FEILLOGG;
}

sub send_mail {
    my @mail = @_;
    my %mail;
    my $hoy = "7";
    $mail{'Message'} = $mail_topp;
    foreach (@mail) {
	/-(\d)-/;
	if ($1 < $hoy) {
	    $hoy = $1; 
	}
	$mail{'Message'} .= "\n".$_;
    }
    $mail{'Message'} .= $mail_bunn; 
    $mail{'Subject'} = $hoy.$mail_subject;
    $mail{'To'} = $mail_til_fra;
    $mail{'Bcc'} = 'gartmann+itea_syslog@pvv.ntnu.no';
    $mail{'From'} = $mail_til_fra;
    $mail{'smtp'} = "bb.itea.ntnu.no";

    sendmail(%mail);
}

sub sendtrap {
    my $ipadresse = "129.241.190.200"; # Bigbud
    my $prefix = '.1.3.6.1.4.1.3001.4.2.1';

    my ($var1,$var2,$var3,$var4) = @_;
    my @data;

    my $string = "ifInOctets:hysteresis:8750000:10000000";

    my $newprefix = ".1.3.6.1.4.1.3001.4.2.1.1";

    push(@data, "$newprefix.1", 'string', "$var1"); # Datotidformat
    push(@data, "$newprefix.2", 'string', "$var2"); # Fra enhet 
    push(@data, "$newprefix.3", 'string', "$var3"); # Type 
    push(@data, "$newprefix.4", 'string', "$var4"); # Selve meldingen 

    &snmptrap($ipadresse, $prefix, "bb", 6, 1, @data);

}

sub unntak {
    my $fil = $_[0];
    my @linje;

    open (FIL, "<$fil") || die ("KUNNE IKKE ÅPNE FILA: $fil");
    foreach (<FIL>) {
	if(@linje = &fil_hent_linje(3,$_)){
	    if (($linje[0] ne "" || $linje[1] ne "") && $linje[2] ne ""){
		if ($linje[0] eq ""){
		    print "\n $_ blir lagt i bare_boks";
		    $bare_boks{$linje[1]} = $linje[2];
		} elsif ($linje[1] eq ""){
		    print "\n $_ blir lagt i bare_type";
		    $bare_type{$linje[0]} = $linje[2];
		} else {
		    print "\n $_ blir lagt i boks_type";
		    $boks_type{$linje[1]}{$linje[0]} = $linje[2];
		}
	    } else {
		print "\n $_ passet ikke inn";
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



