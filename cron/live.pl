#!/usr/bin/perl 

#####################################
#
# Dette er arvtageren til Falkeblikk :)
#
#####################################

use Net::Ping;
use Pg;
use SNMP_util;
use English;



#use Mail::Sendmail; 

# 1) Lese config-fil
# 2) Sjekker at den selv har kontakt med verden (pinger seg ut.)
# 3) Henter ut ip'er som skal pinges fra database, legges i hash
# 4) Pinger dem.
# 5) Litt logikk for hvem som er i skygge av hvem, dersom en boks ikke
#    svarer på ping.

###########################################################
# Sjekker at det ikke står en annen versjon av live og går når denne starter
# (Laget av Knut-Helge.)
$pidfil = "/var/run/live.pl.pid";  
justme();  

open (PIDFIL, ">$pidfil");  
print PIDFIL $PID;  
close (PIDFIL);
#
##########################################################


#exit();


#print "Start: ",scalar localtime,"\n";

%boks = ();

###########################################################

$boxDownPrefix   = '.1.3.6.1.4.1.3001.2.1.1';
$boxShadowPrefix = '.1.3.6.1.4.1.3001.2.1.2';

$up   = '5';
$down = '4';

###########################################################
# Lese config-fil

$conf = '/usr/local/nav/etc/live.conf';
############################################################

open(CONF,$conf);
while (<CONF>)
{
    if (/^ut=/)
    {
	# forutsetter at det kun finnes en linje 
	# som begynner med ut= i live.conf

	($dummy,$veien_ut) = split(/=/);
	chomp($veien_ut);
	@veien_ut = split(/:/,$veien_ut);
    }

    elsif (/^alarm=/)
    {
	($dummy,$alarm_ut) = split(/=/);
	chomp($alarm_ut);
	@alarm_ut = split(/:/,$alarm_ut);
    }

    elsif (/^loggfil=/)
    {
	($dummy,$loggfil) = split(/=/);
	chomp($loggfil);
    }

    elsif (/^extfil=/)
    {
	($dummy,$extfil) = split(/=/);
	chomp($extfil);
    }

    elsif (/^extbokser=/)
    {
	($dummy,$extbokser) = split(/=/);
	chomp($extbokser);
    }
    
    elsif (/^ipadresse=/)
    {
	($dummy,$ipadresse) = split(/=/);
	chomp($ipadresse);
    }

}
close(CONF);

#print "veien ut: @veien_ut\n";
#print "alarm: @alarm_ut\n";
#print "loggfil: $loggfil\n";
#print "extfil: $extfil\n";
#print "extbokser: $extbokser\n";


#exit();
###########################################################

$p = Net::Ping->new("icmp");

foreach $host (@veien_ut)
{
    unless ($p->ping($host, 2))
    {
#	print "Finner ikke veien ut. Ikke kontakt med $host.\n";
#	print "Send melding!\n";

	# Sender sms til tlf som er oppgitt i live.conf

	$dato = scalar localtime;
	$text = "Live finner ikke veien ut $dato. Problem med $host.";
	
	foreach $tlf (@alarm_ut)
	{
	    @respons = `echo $text | /usr/local/bin/gnokii --sendsms $tlf`;
	}
	
	exit(0);
    }
#    else
#    {
#	print "$host ok.\n";
#    }
}

$p->close();


#exit();

#print "Veien ut er klar!!\n";

###########################################################


$db = "manage";
$conn = db_connect($db);


############################################################
# Plukker alle id'er i nettel
############################################################

$sql = "SELECT boksid,ip,sysname,boksvia2,boksvia3,watch,kat,typeid FROM boks";

$resultat = db_select($sql,$conn);

while(@svar = $resultat->fetchrow)
{
    $id=$svar[0];

    $boks{$id}{ip}      = $svar[1];
    $boks{$id}{sysName} = $svar[2];
    $boks{$id}{via2}    = $svar[3];
    $boks{$id}{via3}    = $svar[4];
    $boks{$id}{watch}   = $svar[5];
    $boks{$id}{kat}     = $svar[6];
    $boks{$id}{type}    = $svar[7];
    $boks{$id}{skygge}  = 'f';
    $boks{$id}{nede}    = 'f';    
}

######################################################

$sql2 = "SELECT statusid,boksid,fra,trap FROM status WHERE til IS NULL AND (trap=\'boxDown\' OR trap=\'boxShadow\')";

$resultat = db_select($sql2,$conn);

while(@svar = $resultat->fetchrow)
{
    $boks{$svar[1]}{nede} = 't';
    if ($svar[3] eq 'boxShadow')
    {
	$boks{$svar[1]}{skygge} = 't';
    }
}

#####################################################
# Hent watch-fil (dbmfil)

dbmopen (%extwatch, "$extfil", 0664);

#####################################################

$p = Net::Ping->new("icmp");
foreach $id (keys %boks)
{
    $ip = $boks{$id}{ip};

    if ($ip =~ /^\d/)
    {
	print "Pinger $boks{$id}{sysName} nå :)\n"; # if ($boks{$id}{kat} eq 'SRV');

	if ($boks{$id}{kat} eq 'SRV')
	{
	    $ip = $boks{$id}{sysName};
	}
	
	unless ($p->ping($ip, 2))
	{
	    ## Pinger nok en gang.
	    unless ($p->ping($ip, 3))
	    {
		# Har ikke svart på to påfølgende ping. Legger i liste, og venter litt med å pinge
		# en tredje gang. 
		# Dersom den var nede forrige runde, så antas den å være nede, 
		# og vi pinger ikke en siste gang. 
		# Det er allerede sendt trap på den, så det 
		# gidder vi heller ikke en gang til :)

		if ($boks{$id}{nede} eq 'f')
		{
		    push(@pingarray,$id);
		}
    
		# For tilfeller der en boks er i skygge, men fortsetter
		# å være nede etter at skyggen "har forsvunnet": Setter boksen i sunny,
		# og så har den litt tid på seg til å komme opp før den blir rapportert down.

		if (($boks{$id}{skygge} eq 't') && 
		    ($boks{$id}{nede} eq 't') && 
		    (($boks{$boks{$id}{via2}}{watch} eq 'f') ||
		    ($boks{$boks{$id}{via3}}{watch} eq 'f')))
		{
		    &sett_boks_ok($id);
		}

	    }
	    else
	    {
		&sett_boks_ok($id);
	    }
	}
	else
	{
	    &sett_boks_ok($id);
	}
    }
}

foreach $id (@pingarray)
{
    $ip = $boks{$id}{ip};

    ## Prøver å ping enda gang, med lengre timeout.
    unless ($p->ping($ip, 5))
    {
	if ($boks{$id}{watch} eq 't' && ($extbokser =~ /:$boks{$id}{type}:/) && !$extwatch{$id})
	{
	    $extwatch_new{$id}++;
	    $tid = scalar localtime;
	    open (LOG,">>$loggfil");
	    print LOG "$tid: $boks{$id}{sysName} paa extended watch\n";
	    close (LOG);
	}
	else
	{
	    &sett_boks_down($id);
	}
    }
    else
    {
	&sett_boks_ok($id);
    }
}

$p->close();

###########################
# Sende traps:
###########################

foreach $id (@downarray)
{
#    print "$id er i downarray\n";

    unless (($boks{$boks{$id}{via2}}{watch} eq 't')||
	    ($boks{$boks{$id}{via3}}{watch} eq 't'))
    {
	# Send ned-trap til TrapDetect
	@data = ("$boxDownPrefix.1.1", 'string', "$id");
	@data = (@data,"$boxDownPrefix.1.2", 'string', "$boks{$id}{sysName}");
	@data = (@data,"$boxDownPrefix.1.3", 'string', "$boks{$id}{ip}");
	&snmptrap($ipadresse, $boxDownPrefix, "Po", 6, $down, @data); 

	$tid = scalar localtime;
	open (LOG,">>$loggfil");
	print LOG "$tid: snmptrap ned: $boks{$id}{sysName}\n";
	close (LOG);

    }
    else
    {
	# boks er i skygge. Oppdater nettel.skygge
#	$update_skygge = $dbh->do('UPDATE nettel SET skygge=? WHERE id=?',{},('t',$id));
	@data = ("$boxShadowPrefix.1.1", 'string', "$id");
	@data = (@data,"$boxShadowPrefix.1.2", 'string', "$boks{$id}{sysName}");
	@data = (@data,"$boxShadowPrefix.1.3", 'string', "$boks{$id}{ip}");
	&snmptrap($ipadresse, $boxShadowPrefix, "Po", 6, $down, @data); 
	
	$tid = scalar localtime;
	open (LOG,">>$loggfil");
	print LOG "$tid: snmptrap skygge: $boks{$id}{sysName}\n";
	close (LOG);

    }
}

foreach $id (@uparray)
{
    if ($boks{$id}{skygge} eq 't')
    {
	@data = ("$boxShadowPrefix.1.1", 'string', "$id");
	@data = (@data,"$boxShadowPrefix.1.2", 'string', "$boks{$id}{sysName}");
	@data = (@data,"$boxShadowPrefix.1.3", 'string', "$boks{$id}{ip}");
	&snmptrap($ipadresse, $boxShadowPrefix, "Po", 6, $up, @data); 
#	print "Sender sunny-trap: $id_ $boks{$id}{sysName}\n";

	$tid = scalar localtime;
	open (LOG,">>$loggfil");
	print LOG "$tid: snmptrap sunny: $boks{$id}{sysName}\n";
	close (LOG);

    }
    elsif ($boks{$id}{skygge} eq 'f')
    {
	@data = ("$boxDownPrefix.1.1", 'string', "$id");
	@data = (@data,"$boxDownPrefix.1.2", 'string', "$boks{$id}{sysName}");
	@data = (@data,"$boxDownPrefix.1.3", 'string', "$boks{$id}{ip}");
	&snmptrap($ipadresse, $boxDownPrefix, "Po", 6, $up, @data);
#	print "Sender opp-trap: $id $boks{$id}{sysName}\n";

	$tid = scalar localtime;
	open (LOG,">>$loggfil");
	print LOG "$tid: snmptrap opp: $boks{$id}{sysName}\n";
	close (LOG);

    }
}

#print "Antall ok:        $ok\n";
#print "Antall ubesvarte: $nede\n";
#print "Slutt: ",scalar localtime,"\n";

# Overskriver gammel extwatch, og lukker.
%extwatch = %extwatch_new;
dbmclose(%extwatch);


exit(0);

##############################################
##############################################
sub sett_boks_ok
{
    $id_ = $_[0];
    
    if ($boks{$id_}{watch} eq 't')
    {
	$sql="UPDATE boks SET watch=\'f\' WHERE boksid=\'$id_\'";
	db_execute($sql,$conn);

	$boks{$id_}{watch} = 'f';

	$tid = scalar localtime;
	open (LOG,">>$loggfil");
	print LOG "$tid: $boks{$id_}{sysName} av watch\n";
	close (LOG);
    }
	
    if ($boks{$id_}{nede} eq 't')
    {
	$boks{$id_}{nede} = 'f';
	push (@uparray,$id_);
    } # end if nede=Y

} # end sett_boks_ok

##############################################

sub sett_boks_down
{
    $id_=$_[0];
    
    if ($boks{$id_}{watch} eq 'f')
    {
	
	$sql="UPDATE boks SET watch=\'t\' WHERE boksid=\'$id_\'";
	db_execute($sql,$conn);

	$boks{$id_}{watch} = 't';

	$tid = scalar localtime;
	open (LOG,">>$loggfil");
	print LOG "$tid: $boks{$id_}{sysName} paa watch\n";
	close (LOG);
    }
    else # watch = 't'
    {
	# Legg boks i downarray for sending av trap hvis 
	# den ikke er i status-tabell fra før (hvis nede=N) 
	
	if ($boks{$id_}{nede} eq 'f')
	{
	    $boks{$id_}{nede} = 't';
	    push (@downarray,$id_);

	    $tid = scalar localtime;
	    open (LOG,">>$loggfil");
	    print LOG "$tid: $boks{$id_}{sysName} nede\n";
	    close (LOG);
	    
	}
    }   
}

############################################

sub justme 
{
    my $pid;
    
    if (open PIDFIL, "<$pidfil") 
    {
        $pid = <PIDFIL>;
        kill(0, $pid) and die "$0 already running (pid $pid), bailing out";
        close (PIDFIL);
    }
}

###########################################

sub db_connect {
    my $db = $_[0];
    my $conn = Pg::connectdb("dbname=$db user=navall password=uka97urgf");
    die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
}
sub db_select {
    my $sql = $_[0];
    my $conn = $_[1];
    my $resultat = $conn->exec($sql);
    die "DATABASEFEIL: $sql\n".$conn->errorMessage
        unless ($resultat->resultStatus eq PGRES_TUPLES_OK);
    return $resultat;
}
sub db_execute {
    my $sql = $_[0];
    my $conn = $_[1];
    my $resultat = $conn->exec($sql);
    die "DATABASEFEIL: $sql\n".$conn->errorMessage
        unless ($resultat->resultStatus eq PGRES_COMMAND_OK);
    return $resultat;
}

##################################






