#!/usr/bin/perl 

#####################################
#
# live.pl pinger boksene som finnes i tabellen manage.boks, og sender traps ved endringer i status.
#
#####################################

use Net::Ping;
use Pg;
use SNMP_util;
use English;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $lib = &lib();
require "$lib/database.pl";


# 1) Lese config-fil
# 2) Sjekker at den selv har kontakt med verden (pinger seg ut.)
# 3) Henter ut ip'er som skal pinges fra database, legges i hash
# 4) Pinger dem.
# 5) Litt logikk for hvem som er i skygge av hvem, dersom en boks ikke
#    svarer på ping.

###########################################################
# Lese config-fil

$conf = '/usr/local/nav/local/etc/conf/live/live.conf';

open(CONF,$conf);
while (<CONF>)
{
    unless (/^\#|^\s+/)
    {
	($key,$string) = split(/=/);
	chomp($string);
	$config{$key}=$string;
    }
}

close(CONF);

############################################################


###########################################################
# Sjekker at det ikke står en annen versjon av live og går når denne starter
# (Laget av Knut-Helge.)
#$pidfil = "/var/run/live.pl.pid";  

justme();  

open (PIDFIL, ">$config{pidfil}");  
print PIDFIL $PID;  
close (PIDFIL);

$tid = scalar localtime;

$rundetid = "pid $PID\tstart $tid slutt";

##########################################################

%boks = ();

###########################################################

$p = Net::Ping->new("icmp");

(@veien_ut) = split(/:/,$config{ut});
(@alarm_ut) = split(/:/,$config{alarm});

foreach $host (@veien_ut)
{
#    print "Pinger $host\n";

    unless ($p->ping($host, 2))
    {
#	print "Finner ikke veien ut. Ikke kontakt med $host.\n";
#	print "Send melding!\n";

	# Sender sms til tlf som er oppgitt i live.conf

	$dato = scalar localtime;
	$text = "Live finner ikke veien ut $dato. Problem med $host.";

	open (LOG,">>$config{avbruttlog}");
	print LOG "$dato: Problem med veien ut. $host svarer ikke på ping.\n";
	close (LOG);
	

# Her ønsker vi egentlig å sende en nedtrap, men vi mangler både boksid og sysName
# Bør legge inn linje i databasen, ikke sende direkte.
	
	foreach $tlf (@alarm_ut)
	{
	    @respons = `echo $text | /usr/local/bin/gnokii --sendsms $tlf`;
	}
	
	exit(0);
    }
}

$p->close();


###########################################################

$conn = &db_connect("manage","navall","uka97urgf");


############################################################
# Plukker alle id'er i nettel
############################################################

$sql = "SELECT boksid,ip,sysname,watch,kat,typeid FROM boks";

$resultat = db_select($conn,$sql);

while(@svar = $resultat->fetchrow)
{
    $id=$svar[0];

#    print "$svar[1]\n";

    $boks{$id}{ip}      = $svar[1];
    $boks{$id}{sysName} = $svar[2];
    $boks{$id}{watch}   = $svar[3];
    $boks{$id}{kat}     = $svar[4];
    $boks{$id}{type}    = $svar[5];
    $boks{$id}{skygge}  = 'f';
    $boks{$id}{nede}    = 'f';    
    $boks{$id}{via2}    = '0';
    $boks{$id}{via3}    = '0';
}


#exit();

#######################
# V I A 3

$sql = "SELECT b.boksid,g.boksid FROM boks b JOIN prefiks USING (prefiksid),gwport g WHERE rootgwid=gwportid";

$resultat = db_select($conn,$sql);

while(@svar = $resultat->fetchrow)
{
    $boks{$svar[0]}{via3}    = $svar[1];
}

################################
# V I A 2

# Denne er litt kvasi...

$sql = "SELECT distinct boksid,boksbak FROM swport JOIN swportvlan USING (swportid) WHERE retning =\'n\' AND boksbak IS NOT NULL"; 

$resultat = db_select($conn,$sql);

while(@svar = $resultat->fetchrow)
{
    $boks{$svar[1]}{via2}    = $svar[0];
}

# Sjekker også andre veien for bokser med kat=KANT, men retning n har rangen :)


$sql = "SELECT distinct s.boksid,s.boksbak FROM swport s JOIN swportvlan USING (swportid),boks b where s.boksbak=b.boksid AND retning !=\'o\' AND (b.kat=\'SRV\' OR b.kat=\'KANT\')";

$resultat = db_select($conn,$sql);

while(@svar = $resultat->fetchrow)
{
    if ($boks{$svar[1]}{via2} == 0)
    {
	$boks{$svar[1]}{via2}    = $svar[0];
    }
}


######################################################

$sql = "SELECT statusid,boksid,fra,trap FROM status WHERE til IS NULL AND (trap=\'boxDown\' OR trap=\'boxShadow\')";

$resultat = db_select($conn,$sql);

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
#	print "Pinger $boks{$id}{sysName}  nå :)\n" if ($boks{$id}{sysName} eq 'itea-nettel-230-h');
#	print "Ping: $boks{$id}{sysName}\tvia2:$boks{$boks{$id}{via2}}{sysName}\tvia3:$boks{$boks{$id}{via3}}{sysName}\n";

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
		# å være nede etter at "det som skygger har kommet opp": Setter boksen i sunny,
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
		# Svarer på andre ping.
		&sett_boks_ok($id);
	    }
	}
	else
	{
	    # Svarer på første ping
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
	    open (LOG,">>$config{bokslog}");
	    print LOG "$tid: $boks{$id}{sysName} ($boks{$id}{ip}) paa extended watch\n";
	    close (LOG);
	}
	else
	{
	    &sett_boks_down($id);
	}
    }
    else
    {
	# Svarer på tredje ping.
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
	&send_trap($id,'down');
    }
    else
    {
	&send_trap($id,'shadow');
    }
}

foreach $id (@uparray)
{
    if ($boks{$id}{skygge} eq 't')
    {
	&send_trap($id,'sunny');
    }
    elsif ($boks{$id}{skygge} eq 'f')
    {
	&send_trap($id,'up');
    }
}

#print "Antall ok:        $ok\n";
#print "Antall ubesvarte: $nede\n";
#print "Slutt: ",scalar localtime,"\n";

# Overskriver gammel extwatch, og lukker.
%extwatch = %extwatch_new;
dbmclose(%extwatch);

$tid = scalar localtime;

$rundetid = "$rundetid $tid";

open (LOG,">>$config{rundelog}");
print LOG "$rundetid\n";
close (LOG);

exit(0);

##############################################

sub send_trap
{
    $id_    = $_[0];
    $trap   = $_[1];

# $trap kan være down, up, shadow, sunny 

    $prefix = $status = '';

    $string = "id:$id_ sysName:$boks{$id_}{sysName} IP:$boks{$id_}{ip}";

    if ($trap eq 'down')
    { 
	$prefix = $config{boxDownPrefix}; $status = $config{downPrefix}; 

	$sql = "INSERT INTO status (trapsource,trap,trapdescr,tilstandsfull,boksid,fra) VALUES ('bb','boxDown',\'$string\','Y',\'$id_\',NOW())";

    }
    elsif ($trap eq 'up')
    { 
	$prefix = $config{boxDownPrefix}; $status = $config{upPrefix}; 
	
	$sql = "UPDATE status SET til=NOW() WHERE til IS NULL AND boksid=\'$id_\' AND trapdescr = \'$string\' AND trap='boxDown'";

    }
    elsif ($trap eq 'shadow')
    { 
	$prefix = $config{boxShadowPrefix}; $status = $config{downPrefix}; 
	
	$sql = "INSERT INTO status (trapsource,trap,trapdescr,tilstandsfull,boksid,fra) VALUES ('bb','boxDown',\'$string\','Y',\'$id_\',NOW())";
    }
    elsif ($trap eq 'sunny')
    { 
	$prefix = $config{boxShadowPrefix}; $status = $config{upPrefix}; 

	$sql = "UPDATE status SET til=NOW() WHERE til IS NULL AND boksid=\'$id_\' AND trapdescr = \'$string\' AND trap='boxShadow'";

    }

#    db_execute($conn,$sql);

#    if (($trap eq 'down') || ($trap eq 'up'))
#    {
#	$tid1 = scalar localtime;
#	$til = 'nettstotte@itea.ntnu.no';
#	$subject = "$trap: $boks{$id_}{sysName} ($boks{$id_}{ip})";
#	
#	open(MAIL, "|mail -s '$subject' $til");
#	print MAIL "$tid1 $trap: $string";
#	close(MAIL);
#    }

    @data = ("$prefix.1.1", 'string', "$id_");
    @data = (@data,"$prefix.1.2", 'string', "$boks{$id_}{sysName}");
    @data = (@data,"$prefix.1.3", 'string', "$boks{$id_}{ip}");
    &snmptrap($config{ipadresse}, $prefix, $config{boksnavn}, 6, $status, @data);
    
    $tid = scalar localtime;
    open (LOG,">>$config{bokslog}");
    print LOG "$tid: snmptrap $trap: $boks{$id_}{sysName} ($boks{$id_}{ip})\n";
    close (LOG);

}
##############################################
sub sett_boks_ok
{
    $id_ = $_[0];
    
    if ($boks{$id_}{watch} eq 't')
    {
	$sql="UPDATE boks SET watch=\'f\' WHERE boksid=\'$id_\'";
	db_execute($conn,$sql);

	$boks{$id_}{watch} = 'f';

	$tid = scalar localtime;
	open (LOG,">>$config{bokslog}");
	print LOG "$tid: $boks{$id_}{sysName} ($boks{$id_}{ip} av watch\n";
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
	db_execute($conn,$sql);

	$boks{$id_}{watch} = 't';

	$tid = scalar localtime;
	open (LOG,">>$config{bokslog}");
	print LOG "$tid: $boks{$id_}{sysName} ($boks{$id_}{ip}) paa watch\n";
	close (LOG);
    }
    else # watch = 't'
    {
	# Legg boks i downarray for sending av ned-trap hvis 
	# den ikke er i status-tabell fra før (hvis nede=f) 
	
	if ($boks{$id_}{nede} eq 'f')
	{
	    $boks{$id_}{nede} = 't';
	    push (@downarray,$id_);

	    $tid = scalar localtime;
	    open (LOG,">>$config{bokslog}");
	    print LOG "$tid: $boks{$id_}{sysName} ($boks{$id_}{ip}) nede\n";
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

	$tid = scalar localtime;
	open (LOG,">>$config{avbruttlog}");
	print LOG "$tid: Runde avbrutt pga allerede eksisterende prosess med pid $pid\n";
	close (LOG);
    }
}

###########################################
