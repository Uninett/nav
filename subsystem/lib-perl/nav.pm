package nav;

require Exporter;
use strict;
use Pg;

my $NAVDIR = "/usr/local/nav/";

our @ISA = qw(Exporter);
our @EXPORT = qw(config connection execute);
our @EXPORT_OK = qw(config connection execute);

# Parse a config file with VAR=VALUE assignments, ignoring
# leading/trailing whitespace and comments.
#

sub config {
    my $conffile = shift or return undef;

    open(my $FD, $conffile) || die "Could not open $conffile: $!\n";
    my %hash = map { /\s*(.+?)\s*=\s*(.*?)\s*(\#.*)?$/ && $1 => $2 } 
    grep { !/^(\s*\#|\s+)$/ && /.+=.*/ } <$FD>;
    close($FD);

    return %hash;
}

sub connection {
    my $myself = $_[0];

    my %hash = &config($NAVDIR.'local/etc/conf/db.conf');
			
    my $db_user = $hash{'script_'.$myself};
    my $db_passwd = $hash{'userpw_'.$db_user};
    unless($db_passwd){
	die "Database password information not supplied in database configuration file\n";
    }
    my $db_db = $hash{'db_'.$db_user};
    my $db_host = $hash{'dbhost'};
    my $db_port = $hash{'dbport'};
						    
    my $conn = Pg::connectdb("host=$db_host port=$db_port dbname=$db_db user=$db_user password=$db_passwd");
    die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
    return $conn;
}

sub execute {
    my $sql = $_[1];
    my $conn = $_[0];
    if($sql =~ /^\s*(select)/i){
	my $resultat = $conn->exec($sql);
	unless ($resultat->resultStatus eq PGRES_TUPLES_OK){
	    &skriv("DATABASE-ERROR", "sql=$sql", "message=".$conn->errorMessage);
	}
	return $resultat;
    } else {

	my $resultat = $conn->exec($sql);
	unless ($resultat->resultStatus eq (PGRES_COMMAND_OK||PGRES_TUPLES_OK)){
	    die($conn->errorMessage);
	}
	return 1;
    }
}
