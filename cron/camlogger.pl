#!/usr/bin/perl

# Gi inn vlan som skal logges.
# Fikser masker og sånt "av seg selv".

use SNMP_util;
use DBI;
use Pg;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $lib = &lib();
require "$lib/database.pl";

$loggfil    = '/usr/local/nav/local/log/cam/camlogger.log';
$dbmprefix  = '/usr/local/nav/local/log/cam/camdb_';


%oppdat_hash = ();
$id = 0;
$totalt = 0;

if ($#ARGV eq '1')  # Har gitt inn intervall.
{	
    $start = $ARGV[0];
    $stopp = $ARGV[1];
    
    if ($start > $stopp)
    {
        print "Start må være mindre enn stopp!\n";
        exit(1);
    }
    
    $nett = ':';
    
    for ($i = $start; $i<= $stopp; $i++)
    {
        $nett = $nett.$i.":";
    }
}
else   # ikke intervall inn.
{
    if ($ARGV[0])
    {
        $nett = ':'.$ARGV[0].':';
    }
    else
    {
	print "Du mangler en range. Syntax: <fra> <til>\n";
	exit(1);
    }
}

#####################################
# main 

$start = localtime;
$start2 = time;


&les_boks;


######################

HUB: foreach $ip (sort keys %hubhash)
{   

    $dbmfil = $dbmprefix.$ip;

#    print "Starter henting fra $ip ",scalar localtime,"\n";

    %camtable=();
    %camtable_new = ();
    %camhash = ();
    $ny = $nny = $av = $nav = 0;

    $_=$hubhash{$ip}{igp};
    tr/\t/\|/;      # erstatte 'tab' med |
    s/u//g;         # fjerne alle u
    s/d//g;         # fjerne alle d
    $igp = $_;



    @arg = ($ip,$hubhash{$ip}{type},$hubhash{$ip}{pwd},$hubhash{$ip}{wpw},$hubhash{$ip}{igp});

###################

    $svar = &hentCamdata(@arg);

    if ($svar eq 'false')
    {
	print "Ikke resultat fra $ip\n";  # gir camhash eller starter ny runde.
	next HUB;
    }

    unless (dbmopen (%camtable, "$dbmfil", 0664))
    {
	if (-e $dbmfil) # fil eksisterer
	{
	    print "Kunne ikke åpne $dbmfil.\n";
	    next HUB;
	}
	else # opprett fil.
	{
	    print "$dbmfil vil ikke åpne seg, og eksisterer ikke :(\n";
	    next HUB;
	}
    }

    # Finn alle porter der det er registrert noe. (Både fra camhash og camtable)
    %uphash = ();
    while (($up,$maclist) = each(%camhash) ) 
    {
	$uphash{$up}++;
    }
    while (($up,$maclist) = each(%camtable) ) 
    {
	$uphash{$up}++;
    }

    # %uphash inneholder alle $up det er registrert noe på
    # kun en gang hver.


    while ( ($up,$n) = each(%uphash) )    
    {	
	$igp = 'xx';

	if ($up !~ $igp)    # $igp er listen med uplinker for $ip.
	{
	    
	    $camtable_new{$up} = $camhash{$up};

	    %machash = ();
	    @newlist = split(/:/,$camtable_new{$up});
	    @oldlist  = split(/:/,$camtable{$up});
	    
	    foreach $mac (@newlist)
	    { $machash{$mac}++ }
	    foreach $mac (@oldlist)
	    { $machash{$mac}++ }

	    # %machash inneholder alle mac på $up, kun en gang.
	    
	    while ( ($mac,$n) = each(%machash))
	    {
		if ($camtable{$up} =~ /$mac/)
		{
		    if ($camtable_new{$up} !~ /$mac/)  
		    {
			$id++;
			$oppdat_hash{$id}{hub} = $ip;
			$oppdat_hash{$id}{up}  = $up;
			$oppdat_hash{$id}{mac} = $mac;
			$oppdat_hash{$id}{status} = 'close';
		    }
		}
		else   # bare i $camtable_new{$up}
		{
		    $id++;

#		    print "INSERT: $ip\t$up\t$mac\n";

		    $oppdat_hash{$id}{hub} = $ip;
		    $oppdat_hash{$id}{up}  = $up;
		    $oppdat_hash{$id}{mac} = $mac;
		    $oppdat_hash{$id}{status} = 'insert';
		}
	    }
	}
    } 
    
    %camtable = %camtable_new;   # legger inn resultatene fra denne runden i
    dbmclose (%camtable);   # dbm-fil.	
    
#    print "$ip ok.\n";
    $totalt++;
}

$dbstart = time;

$ny = $slutt = '';

#print "Aapner databasen 2. gang: ",scalar localtime,"\n";

$dbh = DBI -> connect("DBI:mysql:manage","nett","stotte") || die "Kunne ikke åpne databasen: $!\n";

foreach $id (keys %oppdat_hash)
{
    if ($oppdat_hash{$id}{status} eq 'close')
    {
	$ok = $dbh->do('UPDATE cam SET til = NOW() WHERE hub=? AND up = ? AND mac = ? AND til IS NULL',{},($oppdat_hash{$id}{hub},$oppdat_hash{$id}{up},$oppdat_hash{$id}{mac}));
	$slutt++;
    }
    elsif ($oppdat_hash{$id}{status} eq 'insert')
    {

#	print "INSERT: $oppdat_hash{$id}{hub}\t$oppdat_hash{$id}{up}\t$oppdat_hash{$id}{mac}\n";

	$ok = $dbh->do('INSERT INTO cam (hub,up,mac,fra) VALUES (?,?,?,NOW())',{},($oppdat_hash{$id}{hub},$oppdat_hash{$id}{up},$oppdat_hash{$id}{mac}));
	$ny++;
    }
}
$dbh->disconnect;

$dbslutt = time;

#print "Lukker databasen 2.gang, ferdig: ",scalar localtime,"\n";
#print "Har vært gjennom $totalt hub'er.\n";

$dbdiff = $dbslutt - $dbstart;
$totdiff = $dbslutt - $start2;

$lines = $ny+$slutt;

$tot_pr_boks = int (($dbstart - $start2) / $totalt);

unless ($lines)
{
    $lines_pr_dbtid = 0;
}
else
{
    $lines_pr_dbtid = int $dbdiff / $lines;
}

($ukedag,$mnd,$dag,$tid,$aar) = split(/\s+/,$start);

if ($tot_pr_boks > 45)
{
    print "$tot_pr_boks pr. boks\t$dag $mnd $tid\t$nett\n";
}


open(LOGG,">>".$loggfil);
print LOGG "$dag $mnd $tid\tDB:$dbdiff\t$lines_pr_dbtid pr.linje($lines stk)\tTOT:$totdiff\t$totalt bokser\t$tot_pr_boks pr.boks\t$nett\n";
close(LOGG);

exit(0);

#####################################

sub les_boks
{
    $conn = &db_connect("manage","navall","uka97urgf");
    $sql = 'SELECT vlan,ip,ro,rw,typeid FROM boks JOIN prefiks USING (prefiksid) WHERE kat=\'KANT\' AND watch=\'f\' AND typeid NOT LIKE \'C\%\'';
    $resultat = db_select($conn,$sql);
    
    while(my @line = $resultat->fetchrow)
    {

	if ($nett =~ /:$line[0]:/)
	{
	    $hubhash{$line[1]}{type}= $line[4];
	    $hubhash{$line[1]}{pwd} = $line[2];
	    $hubhash{$line[1]}{wpw} = $line[3];

	    # Mangler oversikt over uplinkporter

#	    print "I hubhash: $line[1]\n";

	}
    }
}

########################################

sub hentCamdata
{
# Denne tar inn (ip, passwd, up/downlinkporter)
# Skal legge resultat inn i %camhash, hvis porten ikke er en u/d-link..

    ($ip,$type,$CSr,$CSw,@igp) = @_; 

    $sw3300mib   = '.1.3.6.1.4.1.43.10.22.2.1.3';
    $sw1100mib   = '.1.3.6.1.4.1.43.10.22.2.1.3';
    $ps40mib     = '.1.3.6.1.4.1.43.10.22.2.1.3';
    $ps10off8mib = '.1.3.6.1.4.1.43.10.9.5.1.6';
    
    @out =  &snmpwalk("$CSr\@$ip:161:1:3:2", $sw3300mib)   if $type eq SW3300;
    @out =  &snmpwalk("$CSr\@$ip:161:1:3:2", $sw1100mib)   if $type eq SW1100;
    @out =  &snmpwalk("$CSr\@$ip:161:1:3:2", $ps40mib)     if $type eq PS40;
    @out =  &snmpwalk("$CSr\@$ip:161:1:3:2", $ps10off8mib) if $type eq PS10;
    @out =  &snmpwalk("$CSr\@$ip:161:1:3:2", $ps10off8mib) if $type eq Off8;
    
    unless ($out[0])
    {
        return('false');
    }
    else
    {
        # Sletter innholdet i databasene i PS10 og Off8 (den sletter ikke disse selv):
        # Vet ikke helt hvordan det er med PS40, litt varierende indikasjoner der :)
        
        if (($type eq PS10)||($type eq Off8))
        {
            $slettmib = '.1.3.6.1.4.1.43.10.9.2';
            &snmpset("$CSw\@$ip",$slettmib,'integer',2);
        }
        
        foreach $line (@out)
        {
            if (($type eq SW1100)||($type eq SW3300)||($type eq PS40))
            {
                ($unit, $port, $dummy, $dummy, $dummy, $dummy, $dummy, $dummy, $ascii_mac) = split(/\.|:/, $line, 9);
            }
            else
            {
                ($unit, $port, $dummy, $ascii_mac) = split(/\.|:/, $line, 4);
            }
            #------------------------------------------
            $up = "$unit:$port";
            
            # Finne ut om port skal ignoreres:
            
            $ignorer_port = 'false';
            
            foreach $igpo (@igp)
            {
                if ($igpo =~ /$up$/) #hvis $igpo slutter paa $up. Funker uavh. av u/d/m/...
                {
                    $ignorer_port = 'true';
                }
            }

            if ($ignorer_port eq 'false')
            {
                $mac = unpack('H*', $ascii_mac);
                
                if ($camup[0])
                {@camup = (@camup,$up);}
                else
                {@camup = ($up);}
                
                if (defined $camhash{$up})
                {
                    $camhash{$up}= $camhash{$up}.":".$mac;
                }
                else
                {
                    $camhash{$up} = $mac;
                }
#		print "$up\t$mac\n";
            }
        }
        return('true');
    }
} # end sub hentCamdata


####################################################




