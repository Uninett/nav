#!/usr/bin/perl
 
use Pg;
use CGI qw/:standard :html3/;
#use Time::Local;

print header(),start_html("Boks - info");


$apache_dir = '/usr/local/nav/navme/apache';
$navstart = "$apache_dir/vhtdocs/navstart.pl";
$navslutt = "$apache_dir/vhtdocs/navslutt.pl";


$sysName = param("sysName");

###########################################
# Kjører filen navstart, og skriver "print-linjene" til web
print `$navstart`;
###########################################

#unless ($dbh = DBI->connect("DBI:mysql:manage","nett","stotte"))
#{
#    print "<h4>Fikk ikke kontakt med databasen.</h4><p>";
#    print "<hr><i>grohi\@itea.ntnu.no</i>";
#    exit(0);
#}

$db = "manage";
$conn = db_connect($db);


$sql = "SELECT ip,boks.romid,typeid,orgid,kat,kat2,sted.descr,boksid,rom.descr FROM boks join rom USING (romid) join sted USING (stedid) WHERE sysName=\'$sysName\'";

$boksinfo = db_select($sql,$conn);

unless ($boksinfo->ntuples) # treff i databasen sysName
{
    print b("Ingen treff på $sysName."),p;
    # Avslutter $conn "old style":
    PQfinish($conn);
    print `$navslutt`;
    exit();

}
else
{
#    @rows = th({bgcolor=>e6e6e6},['navn','ip','nede siden','nedetid','info']);
    while (@svar = $boksinfo->fetchrow)
    {
	($ip,$rom,$type,$eier,$kat,$kat2,$sted,$boksid,$rombeskr)=@svar;
    }

    print "<h2><b>$sysName</b></h2><p>";

#print "$ip,$rom,$type,$eier,$kat,$kat2,$sted,$boksid<br>";

    @rows = ();
    
    push (@rows,td(["IP:",$ip]));
    push (@rows,td(["Type:",$type]));
    push (@rows,td(["Plassering:","$rom: $rombeskr, $sted"]));
    push (@rows,td(["Kategori:",$kat]));
    push (@rows,td(["Kategori2:",$kat2]));
    push (@rows,td(["Eier/Drifter:",uc($eier)]));
    


}
    print table({-border=>0 -cellpadding=>2 -cellspacing=>1},
	#    caption(b('Bokser nede')),
	    Tr(\@rows)
	    ),p;

#############
# Uplink - info

#$upsok = $dbh->prepare('select sysname,mp from swport,nettel where nettel.id=swid and portname like "n%" and idbak=?');
#$upsok->execute($nettelid);

#if ($upsok->rows)
#{
#    print "<tr><td>Uplink</td><td>";
#    while (@svar=$upsok->fetchrow_array)
#    {
#	print "<a href=/live/boks_info.pl?sysName=$svar[0]>$svar[0]</a> $svar[1]<br>";
#    }
#    print "</td></tr>";
#}
##############
#print "<tr><td colspan=2><a href=/live/hist_stat.pl?sysName=$sysName>Historikk</a></td></tr>";

#if ($kat eq 'HUB')
#{
#    &hent_org_kat;
#    ($org_enhet,$kat_enhet,$dummy) =split(/\-/,$sysName);
    
#    print "<tr><td valign=top>Funksjon:</td><td>Nettverkshub/svitsj for <b>$kats{$kat_enhet}</b> ved<br>";
#    print "<b>$orgs{$org_enhet}</b> som<br> sogner til telematikkrom i<br> $sted</td></tr>";
#}
#elsif ($kat eq 'SRV')
#{
#    print "<tr><td align=top>Funksjon:</td><td>$function</td></tr>";
#}

#print "</table>";

##############################
#if ($kat eq 'GW')
#{
#    &hent_org_kat;
#    print "<h3>Brukere bak $sysName:</h3>";
#
#    $gwsok = $dbh->prepare('SELECT vlan,gwip,org,kat,komm,bits FROM subnet WHERE type=? AND ruter=? order by vlan'); 
#    $gwsok->execute('lan',$nettelid);
#
#    print "<table>";
#    print "<tr><th>Brukere</th><th>vlan</th><th>gwip/maske</th></tr>";
#    while (@line=$gwsok->fetchrow_array)
#    {
#	if ($line[3] =~ /\d$/)
#	{
#	    chop($line[3]);
#	}
#	print "<tr><td><li>$kats{$line[3]} ved $orgs{$line[2]}";
#
#	print " ($line[4])" if $line[4];
#	print "</td>";
#
#	print "<td>$line[0]</td><td>$line[1]/$line[5]</td></tr>";



##	print "<tr><td>$line[0]</td><td>$line[1]</td><td>$line[2]</td><td>$line[3]</td><td>$line[4]</td></tr>";
#    }
#    print "</table>";
#}

###############################
#if ($kat eq 'SW')
#{
#    &hent_org_kat;
#
#    $swsok=$dbh->prepare('SELECT distinct sw.vlan,org,kat,komm FROM swport sw,subnet su WHERE sw.vlan=su.vlan AND su.type=? AND sw.vlan!=? AND status=? AND swid=? ORDER BY vlan');
#    $swsok->execute('lan','Trunk','Up',$nettelid);#
#
#    while (@line=$swsok->fetchrow_array)
#    {
#	$vlan{$line[0]}{org}  = $line[1];
#	$vlan{$line[0]}{kat}  = $line[2];
#	$vlan{$line[0]}{komm} = $line[3];
#    }
#    $swsok->finish;

#    $swsok2 = $dbh->prepare('SELECT distinct trunk.vlan,subnet.org,subnet.kat,subnet.komm FROM swport,nettel,trunk,subnet WHERE swport.vlan=\'Trunk\' AND swportid=swport.id AND swid=nettel.id AND subnet.vlan=trunk.vlan AND portname like "n:%" AND swport.status=\'Up\' AND sysName=? AND subnet.org IS NOT NULL ORDER BY trunk.vlan');

#    $swsok2->execute($sysName);

#    while (@line=$swsok2->fetchrow_array)
#    {
#	$vlan{$line[0]}{org}  = $line[1];
#	$vlan{$line[0]}{kat}  = $line[2];
#	$vlan{$line[0]}{komm} = $line[3];
#    }
#    $swsok2->finish;


#    print "<h3>Brukere bak $sysName:</h3>";
#    print "<table>";
#    print "<tr><th>Brukere</th><th>vlan</th></tr>";#
#
#    foreach $vlan (sort by_number keys %vlan)
#    {
#	print "<tr>";

#	if ($vlan{$vlan}{kat} =~ /\d$/)
#	{
#	    chop($vlan{$vlan}{kat});
#	}
#	print "<td><li>$kats{$vlan{$vlan}{kat}} ved $orgs{$vlan{$vlan}{org}}";

#	print " ($vlan{$vlan}{komm})" if $vlan{$vlan}{komm};
#	print "</td>";
#	print "<td>$vlan</td></tr>";
#    }
#    print "</table>";
    
#}


# Avslutter $conn "old style":
PQfinish($conn);
###########################################
# Kjører filen navslutt, og skriver "print-linjene" til web
print `$navslutt`;
###########################################

#print end_html;


##############################################
##############################################

sub hent_org_kat
{
    $orgsok=$dbh->prepare('SELECT org,descr FROM organisasjon');
    $orgsok->execute();
    while (@line=$orgsok->fetchrow_array)
    {
	$orgs{$line[0]} = $line[1];
    }
    $orgsok->finish;
    
    $katsok=$dbh->prepare('SELECT kat,descr FROM brukerkat');
    $katsok->execute();
    while (@line=$katsok->fetchrow_array)
    {
	$kats{$line[0]} = $line[1];
    }
    $katsok->finish;
}

sub by_number
{
    if ($a < $b)
    { return -1 }
    elsif ($a == $b)
    { return 0 }
    elsif ($a > $b)
    { return 1 }
}

##########################################################

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
