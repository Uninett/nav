#!/usr/bin/perl

use CGI qw/:standard :html3/;
use Pg;

print header(-Refresh=>'180; URL=./'), start_html('Status');


$db = "manage";
$conn = db_connect($db);


$apache_dir = '/usr/local/nav/navme/apache';
$navstart = "$apache_dir/vhtdocs/navstart.pl";
$navslutt = "$apache_dir/vhtdocs/navslutt.pl";

$htpasswd = "$apache_dir/htpasswd/.htpasswd-sroot"; 


###########################################
# Kjører filen navstart, og skriver "print-linjene" til web
print `$navstart`;
###########################################


$remote_user = $ENV{'REMOTE_USER'};
#$remote_user='grohi';


open (HTPASSWD, $htpasswd) || die "Får ikke åpnet $htpasswd";
$user_data{''}{'omraade'} = 'aapen';
while (<HTPASSWD>) 
{
    next if (/^\W/);
    ($user, $passord, $navn, $merknader, $omraade) = split(/\:/, $_);
    chomp ($user_data{$user}{'omraade'} = $omraade);
}
close(HTPASSWD);

print "<center>";


print h1('Status');
print "USER: $remote_user<br>TILGANG: $user_data{$remote_user}{omraade}<p>";



##############################################################
@rows=();

$sql = "SELECT sysName,ip,fra,NOW()-fra FROM status join boks using (boksid) WHERE trap=\'boxDown\' AND til is null AND boks.active=\'Y\'"; 

$boxDown = db_select($sql,$conn);

if ($boxDown->ntuples) # treff i databasen på boxDown
{
    @rows = th({bgcolor=>e6e6e6},['navn','ip','nede siden','nedetid','info']);
    while (@svar = $boxDown->fetchrow)
    {
	($svar[2],$dummy) = split(/\+/,$svar[2]);
	($day,$dummy,$hour,$min,$dummy) = split(/\s|:/,$svar[3]);
	$svar[3] = "$day d $hour h $min min";

	$color = 'red';
	
	push(@rows,td({color=>$color},[a({href=>"./hist_stat.pl?sysName=$svar[0]"},"$svar[0]"),font({color=>$color},"$svar[1]"),font({color=>$color},"$svar[2]"),font({color=>$color},"$svar[3]"),a({href=>"./boks_info.pl?sysName=$svar[0]"},img{src=>'../../pic/info.gif'})]));

    }


    print table({-border=>0 -cellpadding=>2 -cellspacing=>1},
		caption(b('Bokser nede')),
		Tr(\@rows)
		),p;
}
else
{
    print b('Ingen bokser nede');
}

############################################################################

@rows=();

$sql = "SELECT sysName,ip,fra,NOW()-fra FROM status join boks using (boksid) WHERE trap=\'boxShadow\' AND til is null AND boks.active=\'Y\'"; 

$boxShadow = db_select($sql,$conn);

if ($boxShadow->ntuples) # treff i databasen på boxShadow
{
    @rows = th({bgcolor=>e6e6e6},['navn','ip','nede siden','nedetid','info']);

    while (@svar = $boxShadow->fetchrow)
    {
	($svar[2],$dummy) = split(/\+/,$svar[2]);
	($day,$dummy,$hour,$min,$dummy) = split(/\s|:/,$svar[3]);
	$svar[3] = "$day d $hour h $min min";
	
	$color = 'darkgoldenrod';
	
	push(@rows,td({color=>$color},[a({href=>"./hist_stat.pl?sysName=$svar[0]"},"$svar[0]"),font({color=>$color},"$svar[1]"),font({color=>$color},"$svar[2]"),font({color=>$color},"$svar[3]"),a({href=>"./boks_info.pl?sysName=$svar[0]"},img{src=>'../../pic/info.gif'})]));

    }

    print table({-border=>0},
		caption(b('Bokser i skygge')),
		Tr(\@rows)
		),p;
}
else
{
    print b('Ingen bokser i skygge'),p;
}

print "Se ".a({href=>"./hist_stat.pl"},"historikk"),hr;

############################################################################

#@rows=();

#$sql = "SELECT melding.id,tidspkt,innlegger,melding FROM melding WHERE melding.status=?";

#$melding = db_select($sql,$conn);

#if ($melding->ntuples) # treff i databasen på boxShadow
#{
#    @headings = ('sysName','ip','fra');
#    @rows = th(\@headings);
#    while (@svar = $melding->fetchrow)
#    {
#	push(@rows,td([@svar]));
#    }

#    print table({-border=>undef},
#		caption(b('Meldinger')),
#		Tr(\@rows)
#		);
#}
#else
#{
#    print b('Meldinger');
#}


############################################################################

@rows=();

$sql = "SELECT sysName,ip,watch FROM boks where active=\'N\'";

$service = db_select($sql,$conn);

if ($service->ntuples) # treff i databasen på active=N
{
    @rows = th({bgcolor=>e6e6e6},['navn','ip','status','info']);

    while (@svar = $service->fetchrow)
    {
	$svar[2] = 'Up' if ($svar[2] eq 'f');  # ikke på watch
	$svar[2] = 'Down' if ($svar[2] eq 't');  # på watch

	$color = 'blue';
	
	push(@rows,td([a({href=>"./hist_stat.pl?sysName=$svar[0]"},"$svar[0]"),font({color=>$color},"$svar[1]"),font({color=>$color},"$svar[2]"),a({href=>"./boks_info.pl?sysName=$svar[0]"},img{src=>'../../pic/info.gif'})]));

    }

    print table({-border=>0},
		caption(b('Bokser på service')),
		Tr(\@rows)
		),p;
}
else
{
    print b('Ingen bokser på service'),p;
}


if ($user_data{$remote_user}{omraade} && $user_data{$remote_user}{omraade} ne 'aapen')
{
    print 'Sett boks på/av '.a({href=>"./boks_service.pl"},"service").'.';
}

print "</center>";

# Avslutter $conn "old style":
PQfinish($conn);


###########################################
# Kjører filen navslutt, og skriver "print-linjene" til web
print `$navslutt`;
###########################################



##############################################

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
