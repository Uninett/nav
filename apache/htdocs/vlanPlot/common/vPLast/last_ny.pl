#!/usr/bin/perl -w
############################################################
# Beregner last på grunnlag av input fra Java Servermodul
# og printer det ut til STDOUT for innlesning av samme
# modul.
#
# Bruker kun database for innhenting av data.
#
# John Magne Bredal
# 26-06-2000
#
# Oppdatert 03-07-2000 JM
#  -Lagt til støtte for elink
#
# Oppdatert 06-07-2000 JM
#  -Fikset Gigabitbug, lagt til psykiatri- og ringve-gw manuelt
#
# Oppdatert 07-07-2000 JM
#  -Lagt til rett skriving av listCPUlast
#
# Oppdatert 07-07-2000 KE
#  -Fixet skriving av listCPUlast dersom net=0 og ingen uplink-ruter
#  -Tatt bort utskrift av 'Ingen RRD-fil for...' for switcher
#
# Oppdatert 26-07-2000 JM
#  -Fixet alternativ lastdata-henting hvis ruter=RSM
#
# Oppdatert 04-08-2000 KE
#  -Fixet problem med heng av scriptet dersom en av swid'ene har portname
#   som g†r til -gw.
#
# Oppdatert 23-01-2001 JM
#  -Scriptet bruker nye navn på tabellene i databasen
#
# Oppdatert 26-08-2001 JM
# - Oppdatert i følge nye tabelldefninisjoner og bruk av
#   PostGreSQL-database
############################################################

use Pg;
use strict;

my $dbh = &db_connect("manage", "manage", "eganam");

# Teit boolsk variable som er med pga. at skrivCPUlast kalles flere ganger.
my $CPULastskrevet = 0;

open (LOGG, ">test");
main(@ARGV);
close LOGG;

# Tar imot input fra STDIN og behandler den.
sub main {
    # Trengs for CGI
    print "Content-type:text/html\n\n";

    # tmp-variabler for data-innlesing
    my $buffer;
    my @par_sett;
    my $par;
    my $name;
    my $value;
    my %FORM;

    # Leser inn data fra web-browser
    if ($ENV{'REQUEST_METHOD'} eq "POST") {
	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
    } else
    {
	$buffer = $ENV{'QUERY_STRING'};
    }
    @par_sett = split(/&/, $buffer);
    foreach $par (@par_sett) {
	($name, $value) = split(/=/, $par);
	$value =~ tr/+/ /;
	$value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
	$FORM{$name} = $value;
    }

    # Legger data i rett variabel
    my (@netliste,@swliste);
    
    #    my $netliste = shift;
    #my $swliste = shift;
    #my $tid = shift;
    #my $type = shift;
    
    my $netliste = $FORM{'net'};
    my $swliste = $FORM{'sw'};
    my $tid = $FORM{'time'};
    my $type = $FORM{'type'};

    print LOGG "NET: $netliste\n";
    print LOGG "SW: $swliste\n";

    # Splitter opp nettlisten
    @netliste = split /,/, $netliste;

    # Splitter opp switchlisten
    @swliste = split /,/, $swliste;

    # Splitter opp fra/til-tid
    my($fra,$til) = split /,/, $tid;

    if ($type eq "avg") { $type = "AVERAGE"; } 
    else {$type = "MAX"; }

    $CPULastskrevet = 0;
    
    unless ($netliste[0] == 0) {
	finnRuterLast($fra, $til, $type, @netliste); 
    } else {
	print "listGwportOctetLast\n";
    }
    
    unless ($swliste[0] == 0) {
	finnSvitsjLast($fra, $til, $type, @swliste); 
    } else {
	print "listSwportOctetLast\n";
	print "listBoksBakplanLast\n";
    }
}

# Legger alt som skal behandles i lister og kjører subrutiner som skriver til STDOUT.
sub finnRuterLast {

    my $fra = shift;
    my $til = shift;
    my $type = shift;
    my (@netid) = @_;
    my ($linkteller, $stamteller,$lanteller,$elinkteller) = (0,0,0,0);

    my ($ruterid, $link,$ruternavn,$linktype,$rsm,$speed);
    my (%ruterliste,@linkliste,@lanliste, @stamliste,@elinkliste);

    # Finner ruterid og link fra databasen, legger dem i egne lister.
    for (@netid) {
	# Spør etter link og ruter, legger i lista.
	my $getInfo = &db_select("SELECT g.interf, g.boksid, p.nettype, g.speed FROM gwport g, prefiks p WHERE g.gwportid=$_ and g.prefiksid=p.prefiksid",$dbh);

	if ($getInfo->ntuples == 0) {
	    print "Ingen slik nettid: $_\n";
	} else {
	    ($link, $ruterid, $linktype, $speed) = $getInfo->fetchrow;

	    $link = lc $link;
	    $link =~ s/\//_/g;

	    # Må ha en liste som holder på sammenhengen mellom ruter og link|stam|lan|elink.
	    # Legger alle de ulike intefacene i forskjellige lister, for senere behandling.
	    if ($linktype =~ m/(link|stam|lan|elink)/) {
		push @{$linkliste[$linkteller]}, $_, $ruterid, $link, $linktype, $speed;
		$linkteller++;
	    } else {
#		print "$linktype er ingen definert linktype\n";
	    }
	    
	    # Må ha ruternavn for å finne rett RRD-fil
	    my $getRuternavn = &db_select("SELECT sysName,typeid FROM boks WHERE boksid=$ruterid",$dbh);
	    if ($getRuternavn->ntuples == 0) {
#		print "Finner ikke ruter med id $ruterid\n";
	    } else {
		($ruternavn,$rsm) = $getRuternavn->fetchrow;
		$ruterliste{$ruterid} = [$ruternavn,$rsm];
	    }
	}
    }
    
    my $linkliste = @linkliste;
#    print "$stamliste,$linkliste,$lanliste\n";

    
    # Kjører en løkke på alle listene for å skrive ut lastdata for de 
    # forskjellige linkene.
    print "listGwportOctetLast\n";
    if ($linkliste > 0) {
	for (@linkliste) { 
	    &skrivLinkLast($fra,$til,$type,$_,%ruterliste); 
	}
    }
    &skrivCPULast($fra,$til,$type,%ruterliste);
}

# Subrutine som brukes av finnRuterLast. Skriver ut lastdata for de ulike ruterne.
sub skrivCPULast {
    use RRDs;

    my $RRD;
    my ($cpuverdi,$ruterid,$ruternavn,$rsm);
    my $fra = shift;
    my $til = shift;
    my $type= shift;
    my (%ruterliste) = @_;

#    print "Kjører denne\n";

    unless ($CPULastskrevet) {
	print "listBoksCPULast\n";
	$CPULastskrevet = 1;
    }

    while(($ruterid, $ruternavn) = each %ruterliste) {
	$ruternavn = @$ruternavn[0];
#	print "---$ruterid, $ruternavn, $rsm\n";
	if (-e "/home/cricket/cricket-data/routers/$ruternavn.rrd") {
	    $RRD = "/home/cricket/cricket-data/routers/$ruternavn.rrd";

	    my($graphret) = RRDs::graph "/dev/null",
	    "--start","$fra",
	    "--end","$til",
	    "DEF:value=$RRD:ds1:AVERAGE",
	    "PRINT:value:$type:%6.2lf";
	    my($ERROR) = RRDs::error;
	    warn "ERROR: $ERROR\n" if $ERROR ;

	    if (@$graphret[0] =~ /\d/) { $cpuverdi = @$graphret[0]; } else { $cpuverdi = 0; }
	    print "$ruterid,$cpuverdi\n";
	}
    }
}

# Subrutine som brukes av finnRuterLast. Skriver ut lastdata for de ulike linkene (lan|stam|link)
sub skrivLinkLast {
    use RRDs;

    my $RRD;
    my $fra = shift;
    my $til = shift;
    my $type = shift;
    my $liste = shift;
    my (%ruterliste) = @_;

    my ($netid,$ruterid,$link,$linktype,$speed,$ruternavn,$rsm,$verdi1,$verdi2);

    $netid = @$liste[0];
    $ruterid = @$liste[1];
    $link = @$liste[2];
    $linktype = @$liste[3];
    $speed = @$liste[4];
    ($ruternavn,$rsm) = @{$ruterliste{$ruterid}};

#    print "Netid: $netid, Ruterid: $ruterid, Link: $link, Linktype: $linktype, Ruternavn: $ruternavn, $rsm\n";

    my $path = "/home/cricket/cricket-data/";
    if ($speed == 1000) {
	$path .= "giga-router-interfaces";
    } else {
	$path .= "router-interfaces";
    }
    
	if (-e "$path/$ruternavn/$link.rrd") {
	    $RRD = "$path/$ruternavn/$link.rrd";

	    if ($linktype eq "link") {
		# Hvis ruteren er en RSM og RSMlast finner en verdi skal vi ikke gjøre dette.
		unless (($rsm =~ /(RSM|MSFC)/) && (&RSMlast($ruternavn,$netid,$link,$fra,$til,$type,$speed)) ) {

		    my($graphret) = RRDs::graph "/dev/null",
		    "--start","$fra",
		    "--end","$til",
		    "DEF:inval=$RRD:ds1:AVERAGE",
		    "PRINT:inval:$type:%6.2lf";
		    my($ERROR) = RRDs::error;
		    warn "ERROR: $ERROR\n" if $ERROR ;

		    if (@$graphret[0] =~ /\d/) { $verdi1 = int(@$graphret[0]); } else { $verdi1 = 0; }
		    print "$netid,$verdi1\n";

		}

		# Hvis linktype er stam, lan eller elink må vi beregne både ut og inn på samme port.
	    } else {
		unless (($rsm =~ /(RSM|MSFC)/) && (&eRSMlast($ruternavn,$netid,$link,$fra,$til,$type,$speed)) ) {
		    my ($graphret,$xs,$ys) = RRDs::graph "/dev/null",
		    "--start","$fra",
		    "--end","$til",
		    "DEF:inval=$RRD:ds0:AVERAGE", # inn til port
		    "DEF:utval=$RRD:ds1:AVERAGE", # ut fra port
		    "PRINT:inval:$type:%6.2lf",
		    "PRINT:utval:$type:%6.2lf";
		    my($ERROR) = RRDs::error;
		    warn "ERROR: $ERROR\n" if $ERROR ;

		    if (@$graphret[0] =~ /\d/) { $verdi1 = int(@$graphret[0]); } else { $verdi1 = 0; }
		    if (@$graphret[1] =~ /\d/) { $verdi2 = int(@$graphret[1]); } else { $verdi2 = 0; }

		    print "$netid,$verdi2,$verdi1\n";
		}
	    }
	} else {
#	    print "Ingen rrd-fil for $link\n";
	}

}

# Finner lastdata fra svitsjen i stedet for ruteren hvis det er en RSM.
# Tar inn ruternavn
sub RSMlast {

    my ($ruternavn,$netid,$vlan,$fra,$til,$type,$speed) = @_;
#    print "Input: $ruternavn,$netid,$vlan,$fra,$til,$type\n";

    my ($switchnavn,$svitsjid,$modul,$port,$verdi);

    my $returverdi = 0;

    # Filtrerer vekk tall fra ruternavn
    $ruternavn =~ s/(.+)gw\d*/$1sw/;
    $switchnavn = $ruternavn;
#    print "Svitsjnavn: $switchnavn\n";

    # Filtrerer vekk bokstaver fra vlan
    $vlan =~ s/\D+(\d+)/$1/;
#    print "Vlan: $vlan\n";

    # Må finne id på svitsj.
    my $getSvitsjId = &db_select("SELECT boksid FROM boks WHERE sysName='$switchnavn'",$dbh);

    if ($getSvitsjId->ntuples == 0) {
#	print "Finner ikke svitsj med navn $switchnavn\n";
    } else {
	$svitsjid = $getSvitsjId->fetchrow;
#	print "ID: $svitsjid\n";

	# Har svitsjid, må finne navn på rrd-fil, dvs. port ut fra svitsjen.
	my $getPortId = &db_select("SELECT sp.modul,sp.port FROM swport sp,swportvlan spv WHERE spv.vlan=$vlan AND sp.boksid=$svitsjid and sp.swportid=spv.swportvlanid",$dbh);

	if ($getPortId->ntuples == 0) {
#	    print "Finner ikke port!\n";
	} else {
	    ($modul,$port) = $getPortId->fetchrow;

	    # Setter sammen portnavnet
	    $port = $modul."_".$port;
#	    print "Funnet port: $port\n";

	    my $path = "/home/cricket/cricket-data/";
	    if ($speed == 1000) {
		$path .= "giga-switch-ports";
	    } else {
		$path .= "switch-ports";
	    }

	    # Spør rrd-filen etter data
	    if (-e "$path/$switchnavn/$port.rrd") {
		my $RRD = "$path/$switchnavn/$port.rrd";
		
		my($graphret) = RRDs::graph "/dev/null",
		"--start","$fra", 
		"--end","$til",
		"DEF:utvalue=$RRD:ds1:AVERAGE", #ds1 = ut fra port
		"PRINT:utvalue:$type:%6.2lf";
		my($ERROR) = RRDs::error;
		warn "ERROR: $ERROR\n" if $ERROR ;
		
		if (@$graphret[0] =~ /\d/) { $verdi = int(@$graphret[0]); } else { $verdi = 0; }
		print "$netid,$verdi\n"; 

		$returverdi = 1;

	    } else {
		#print "Ingen RRD-fil for $switchnavn, $port\n";
	    }
	}

    }

    return $returverdi;

}

sub eRSMlast {

    my ($ruternavn,$netid,$vlan,$fra,$til,$type,$speed) = @_;
#    print "Input: $ruternavn,$netid,$vlan,$fra,$til,$type\n";

    my ($switchnavn,$svitsjid,$modul,$port,$verdi1,$verdi2);

    my $returverdi = 0;

    # Filtrerer vekk tall fra ruternavn
    $ruternavn =~ s/(.+)gw\d*/$1sw/;
    $switchnavn = $ruternavn;
#    print "Svitsjnavn: $switchnavn\n";

    # Filtrerer vekk bokstaver fra vlan
    $vlan =~ s/\D+(\d+)/$1/;
#    print "Vlan: $vlan\n";

    # Må finne id på svitsj.
    my $getSvitsjId = &db_select("SELECT boksid FROM boks WHERE sysName='$switchnavn'",$dbh);

    if ($getSvitsjId->ntuples == 0) {
#	print "Finner ikke svitsj med navn $switchnavn\n";
    } else {
	$svitsjid = $getSvitsjId->fetchrow;
#	print "ID: $svitsjid\n";

	# Har svitsjid, må finne navn på rrd-fil, dvs. port ut fra svitsjen.
	my $getPortId = &db_select("SELECT sp.modul,sp.port FROM swport sp,swportvlan spv WHERE spv.vlan=$vlan AND sp.boksid=$svitsjid and sp.swportid=spv.swportvlanid",$dbh);

	if ($getPortId->ntuples == 0) {
#	    print "Finner ikke port!\n";
	} else {
	    ($modul,$port) = $getPortId->fetchrow;

	    # Setter sammen portnavnet
	    $port = $modul."_".$port;
#	    print "Funnet port: $port\n";

	    my $path = "/home/cricket/cricket-data/";
	    if ($speed == 1000) {
		$path .= "giga-switch-ports";
	    } else {
		$path .= "switch-ports";
	    }

	    # Spør rrd-filen etter data
	    if (-e "$path/$switchnavn/$port.rrd") {
		my $RRD = "$path/$switchnavn/$port.rrd";
		
		my($graphret) = RRDs::graph "/dev/null",
		"--start","$fra", 
		"--end","$til",
		"DEF:inval=$RRD:ds0:AVERAGE", # inn til port
		"DEF:utval=$RRD:ds1:AVERAGE", # ut fra port
		"PRINT:inval:$type:%6.2lf",
		"PRINT:utval:$type:%6.2lf";
		my($ERROR) = RRDs::error;
		warn "ERROR: $ERROR\n" if $ERROR ;

		if (@$graphret[0] =~ /\d/) { $verdi1 = int(@$graphret[0]); } else { $verdi1 = 0; }
		if (@$graphret[1] =~ /\d/) { $verdi2 = int(@$graphret[1]); } else { $verdi2 = 0; }
		
		print "$netid,$verdi2,$verdi1\n";

		$returverdi = 1;

	    } else {
		#print "Ingen RRD-fil for $switchnavn, $port\n";
	    }
	}

    }

    return $returverdi;

}

# Finner lastdata for alle svitsjer og porter ut fra svitsjene basert på swportlisten som er input.
sub finnSvitsjLast {

    use RRDs;

    my $fra = shift;
    my $til = shift;
    my $type = shift;
    my (@swid) = @_;
    my $teller = 0;

    my (%svitsjListe, @swportliste, %ruterliste);
    my($switchid,$modul,$port,$switchnavn, $portname, $speed);

    # Finner switchid og port ut fra databasen og legger dem i egne lister.
    for (@swid) {
	my $getInfo = &db_select("SELECT boksid, modul, port, portnavn, speed FROM swport where swportid=$_",$dbh);

	($switchid, $modul, $port, $portname, $speed) = $getInfo->fetchrow;
	$port = $modul."_".$port;

	# Må ha en liste som holder på sammenhengen mellom svitsj og link.
	push @{$swportliste[$teller]}, $_, $switchid, $port, $speed;
	$teller++;

#	print "Portname: $portname\n";
	# Hvis det er en svitsj i andre enden, må vi ha bakplanlast på den også
	if ($portname =~ m/.+:(.+-sw)/) {
	    my $sysName = $1;
#	    print "Funnet svitsj i andre enden: $sysName\n";

	    my $finnSvitsjNavn = &db_select("SELECT boksid FROM boks WHERE sysName='$sysName'",$dbh);
	    if ($finnSvitsjNavn->ntuples == 0) {
#		print "Finner ingen svitsj med navn $sysName\n";
	    } else {
		my $switchbakid = $finnSvitsjNavn->fetchrow;
#		print "Legger inn $switchbakid, $sysName\n";
		$svitsjListe{$switchbakid} = $sysName;
	    }
	# Eller det kan være en gw i andre enden.
	} elsif ($portname =~ m/.+:(.+-gw\w?)/) {
	    my $sysName = $1;
#	    print "Funnet ruter i andre enden: $sysName\n";

	    my $finnRuterNavn = &db_select("SELECT boksid FROM boks WHERE sysName='$sysName'",$dbh);
	    if ($finnRuterNavn->ntuples == 0) {
#		print "Finner ingen ruter med navn $sysName\n";
	    } else {
		my $ruterid = $finnRuterNavn->fetchrow;
		if (($sysName eq "psykiatri-gw") || ($sysName eq "ringve-gw")) {
		    $sysName .= "-trlos";
		    $ruterliste{$ruterid} = [$sysName];
		} else {
		    $ruterliste{$ruterid} = [$sysName];
		}
	    }
	}

	# Finner svitsjnavn for svitsjene som skal finnes last på.
	my $finnSvitsjNavn = &db_select("SELECT sysName FROM boks WHERE boksid=$switchid",$dbh);

	if ($finnSvitsjNavn->ntuples == 0) {
	    print "Finner ingen svitsj med id $switchid\n";
	} else {
	    $svitsjListe{$switchid} = $finnSvitsjNavn->fetchrow;
	}
    }
    # Må gjøres pga. last skal vises når man ser på en svitsj.
    my @keys = keys %ruterliste;
    my @values = values %ruterliste;
    my $antall = @keys;
    if ($antall > 0) {
	&skrivCPULast($fra,$til,$type,%ruterliste);
    } else
    {
	    unless ($CPULastskrevet) {
		print "listBoksCPUlast\n";
		$CPULastskrevet = 1;
	    }
    }

    my ($verdi, $verdi1, $verdi2, $RRD);

    # Beregner last på bakplanet på svitsjene
    print "listBoksBakplanLast\n";
    while(($switchid, $switchnavn) = each %svitsjListe) {
	if (-e "/home/cricket/cricket-data/switches/$switchnavn.rrd") {
	    $RRD = "/home/cricket/cricket-data/switches/$switchnavn.rrd";

	    my($graphret) = RRDs::graph "/dev/null",
	    "--start","$fra",
	    "--end","$til",
	    "DEF:value=$RRD:ds0:AVERAGE",
	    "PRINT:value:$type:%6.2lf";
	    my($ERROR) = RRDs::error;
            warn "ERROR: $ERROR\n" if $ERROR ;

	    if (@$graphret[0] =~ /\d/) { $verdi = @$graphret[0]; } else { $verdi = 0; }
	    print "$switchid,$verdi\n";
	}
    }

    # Beregner last på portene ut fra switchen
    print "listSwportOctetLast\n";

    for (@swportliste) {
	my $swportid = @$_[0];
	my $swid = @$_[1];
	$port = @$_[2];
	my $speed = @$_[3];
	$switchnavn = $svitsjListe{$swid};

#	print "Swportid: $swportid, Switchid: $swid, Port: $port, Switchnavn: $switchnavn\n";

	my $path = "/home/cricket/cricket-data/";
	if ($speed == 1000) {
	    $path .= "giga-switch-ports";
	} else {
	    $path .= "switch-ports";
	}

	$port = lc($port);
	if (-e "$path/$switchnavn/$port.rrd") {
	    $RRD = "$path/$switchnavn/$port.rrd";

	    my($graphret) = RRDs::graph "/dev/null",
	    "--start","$fra",
	    "--end","$til",
	    "DEF:invalue=$RRD:ds0:AVERAGE", #ds0 = inn til port
	    "DEF:utvalue=$RRD:ds1:AVERAGE", #ds1 = ut fra port
	    "PRINT:invalue:$type:%6.2lf",
	    "PRINT:utvalue:$type:%6.2lf";
	    my($ERROR) = RRDs::error;
            warn "ERROR: $ERROR\n" if $ERROR ;
	    
	    if (@$graphret[0] =~ /\d/) { $verdi1 = int(@$graphret[0]); } else { $verdi1 = 0; }
	    if (@$graphret[1] =~ /\d/) { $verdi2 = int(@$graphret[1]); } else { $verdi2 = 0; }
	    print "$swportid,$verdi2,$verdi1\n"; 

	} else {
	    #print "Ingen RRD-fil for $switchnavn, $port\n";
	}
    }
}

sub db_connect {
    my $db = $_[0];
    my $user = $_[1];
    my $pass = $_[2];
    my $conn = Pg::connectdb("dbname=$db user=$user password=$pass");
    die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
}

sub db_select {
    my $sql = $_[0];
    my $conn = $_[1];
    my $resultat = $conn->exec($sql);
    print "DATABASEFEIL: $sql\n".$conn->errorMessage
        unless ($resultat->resultStatus eq PGRES_TUPLES_OK);
    return $resultat;
}

sub db_execute {
    my $sql = $_[0];
    my $conn = $_[1];
    my $resultat = $conn->exec($sql);
    print "DATABASEFEIL: $sql\n".$conn->errorMessage
        unless ($resultat->resultStatus eq PGRES_COMMAND_OK);
#die er byttet med print

    return $resultat;
}
