#! /usr/bin/perl -w
#
# Engine.pm
#
#    Dette er hovedklassen som kj¿rer kontinuerlig og henter ut data og sender
# ut alarmer.
#
# (author) Andreas Aakre Solberg, Aug 2002
#          Arne Øslebø, UNINETT

package Engine;

use lib '/home/arneos/perl/lib/perl5/site_perl/5.8.0/i386-linux-thread-multi';

use strict 'vars';
use diagnostics;
use DBI;
use UserGroups;
use Alert;
use EquipmentGroups;
use NewAlerts;
use User;

use Data::Dumper;

# Konstruktor..
sub new {
	my ($class,$cfg)=@_;
	my $this = {};
	# oppretter en databaseforbindelse til profildatabasen
	                              # db host name passwd
	bless $this,$class;

	$this->{dbh_user} = DBI->connect("dbi:Pg:dbname=$cfg->{db_usersdb};host='$cfg->{db_host}'",$cfg->{db_user}, $cfg->{db_passwd}, undef) || die $DBI::errstr;
	$this->{dbh_alert} = DBI->connect("dbi:Pg:dbname='$cfg->{db_alertdb}';host='$cfg->{db_host}'", $cfg->{db_user}, $cfg->{db_passwd}, undef) || die $DBI::errstr;

	$this->{cfg}=$cfg;
	return $this;
}

# Sletter PID-filen.
sub delete_pidfile() {
	if (-f '/tmp/alertengine.pid') {
		unlink('/tmp/alertengine.pid');
	}
}

# funksjon som kalles nŒr daemonen kj¿res ned..
sub shutdownConstruct() {
	my $this = shift;

	# returnerer en lukning (closure) som inneholder referanse til riktig Engine::objekt.
	return sub {
		my $signal_recv = shift;
		&delete_pidfile;
		print  "Got signal :" . $signal_recv . ":! nice shutdown.\n\n";
		
		$this->disconnectDB();

		exit(0);
	}
}

#Disconnects from DB
sub disconnectDB()
  {
    my $this=shift;
    $this->{dbh_user}->disconnect;
    $this->{dbh_alert}->disconnect;
  }

sub checkAlerts()
#Check new alerts
  {
    my $this=shift;

    my $nA=NewAlerts->new($this->{dbh_alert},$this->{lastAlertID});
    my $num=$nA->getAlertNum();
    my $uG=undef;
    my $eG=undef;
    if($num)
      {
	$uG=UserGroups->new($this->{dbh_user});
	$eG=EquipmentGroups->new($this->{dbh_user});
      }


#    my $list=$uG->getEquipmentGroups(1);
#    for my $l (@$list)
#      {
#	print "1 $l\n";
			  #      }

    #Get list us users
    my $users=$this->{dbh_user}->selectall_arrayref("select id from bruker where aktivprofil is not NULL") || print "ERROR: could not get list of active users";
    foreach my $userid (@$users)
      {
	my $user=User->new($userid->[0],$this->{dbh_user},$this->{cfg});
	$user->checkAlertQueue();
	if($num)
	  #If there are new active alarts
	  {
	    $user->checkNewAlerts($nA,$uG,$eG);
	  }
      }
	
    $this->{lastAlertID}=$nA->finished();
  }



# Dette er selve deamonen som gŒr i evig l¿kke til den blir stanset.
sub run() {
	my $this = shift;

	# shutdownconstruct returnerer en funksjonsreferanse til en funksjon
	# som har en referanse til $this objektet innebygget i sin scope.
	# Den er n¿dt til Œ ha en referanse til $this for Œ kunne kalle close
	# pŒ databasehandleren som ligger lagret som en instansvaribel i objektet.
	$SIG{QUIT} = &shutdownConstruct($this);
	$SIG{TERM} = &shutdownConstruct($this);
	
	while (1) {
		my $tf = time();
		#print "Running and living happy...\n";
		
		$this->checkAlerts();

		my $te = time();
		my $tdiff = $te - $tf;
		#print "Elapsed time alertsession: " . $tdiff . " seconds.\n\n\n";
		
		open var_dump, '>/tmp/vardump.txt';
		print  var_dump Dumper($this);
		close (var_dump);
		sleep($this->{cfg}->{sleep});
	}
}

1;
