#!/usr/bin/perl

#
# Dette er et bittelite script som henter ut alt i boks, 
# og oppdaterer prefiksid dersom scriptet mener den er feil :)
# 


use Pg;


my $db = "manage";
my $conn = db_connect($db);

my $sql = "SELECT boksid,ip,prefiksid FROM boks";
 
#print "$sql\n";
 
my $resultat = db_select($sql,$conn);
 
while(my @line = $resultat->fetchrow)
{
    $boks{$line[1]}{id} = $line[0];
    $boks{$line[1]}{prefiksid} = $line[2];
}
 
 
$sql = "SELECT prefiksid,nettadr FROM prefiks";
 
$resultat = db_select($sql,$conn);
 
while (my @line = $resultat->fetchrow)
{
    $prefiksdb{$line[1]} = $line[0];
}


foreach $ip (keys %boks)
{
    $prefiksid = getprefiks($ip); 

    if ($prefiksid ne $boks{$ip}{prefiksid})
    {
	print "Oppdaterer $ip prefiksid fra $boks{$ip}{prefiksid} til $prefiksid\n";

	$sql = "UPDATE boks SET prefiksid=$prefiksid WHERE boksid=$boks{$ip}{id}";

	db_execute($sql,$conn);

    }
}



###################################################

sub getprefiks
{
    # Tar inn ip, splitter opp og and'er med diverse
    # nettmasker. Målet er å finne en match med en allerede innhentet
    # prefiksid (hash over alle), som så returneres.
 
    my $ip = $_[0];
 
    my @masker = ("255.255.255.255","255.255.255.254","255.255.255.252","255.255.255.248","255.255.255.240","255.255.255.224","255.255.255.192","255.255.255.128","255.255.255.0","255.255.254.0","255.255.252.0");
 
    my $netadr;
    my $maske;
 
    foreach $maske (@masker)
    {
        $netadr = and_ip($ip,$maske);
 
        return $prefiksdb{$netadr} if (defined $prefiksdb{$netadr});
    }
 
#    print "Fant ikke prefiksid for $ip\n";
    return 0;
}

###############################################
 
sub and_ip
{
    my @a =split(/\./,$_[0]);
    my @b =split(/\./,$_[1]);
 
    for (0..$#a) {
        $a[$_] = int($a[$_]) & int($b[$_]);
    }
 
    return join(".",@a);
}
 
###############################################


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
    print "DATABASEFEIL: $sql\n".$conn->errorMessage
        unless ($resultat->resultStatus eq PGRES_COMMAND_OK);
    return $resultat;
}
