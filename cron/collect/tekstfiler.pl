#!/usr/bin/perl
use strict;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $lib = &lib();
my $localkilde = &localkilde();
my $kilde = "etc/kilde/";
require "$lib/database.pl";
require "$lib/fil.pl";
&log_open;
#-------------ALLE-------------
my $db = &db_get("tekstfiler");
my ($fil,$tabell,@felt);
#--------------USE-------------
&db_file_to_db(connection => $db,file => "etc/kilde/anv.txt",table => "usage",databasefields => ["usageid","descr"],index => ["usageid"]);
#--------------STED------------
&db_file_to_db(connection => $db,file => "etc/kilde/sted.txt",table => "location",databasefields => ["locationid","descr"],index => ["locationid"]);
#--------------ROM-------------
&db_file_to_db(connection => $db,file => "etc/kilde/rom.txt",table => "room",databasefields => ["roomid","locationid","descr","room2","room3","room4","room5"],index => ["roomid"]);
#--------------ORG-------------
$fil = "$localkilde/org.txt";
$tabell = "org";
@felt = ("orgid","parent","descr","org2","org3","org4");
&spesiell_endring_org($db,$fil,$tabell,join(":",@felt),join(":",@felt));
#--------------TYPE------------
&db_file_to_db(connection => $db,file => "etc/kilde/vendor.txt",table => "vendor",databasefields => ["vendorid"],index => ["vendorid"]);
&db_file_to_db(connection => $db,file => "etc/kilde/product.txt",table => "product",databasefields => ["vendorid","productno","descr"],index => ["vendorid","productno"]);
&db_file_to_db(connection => $db,file => "etc/kilde/cat.txt",table => "cat",databasefields => ["catid","descr"],index => ["catid"]);
&db_file_to_db(connection => $db,file => "etc/kilde/typegroup.txt",table => "typegroup",databasefields => ["typegroupid","descr"],index => ["typegroupid"]);
&db_file_to_db(connection => $db,file => "etc/kilde/type.txt",table => "type",databasefields => ["vendorid","typename","typegroupid","sysobjectid","cdp","tftp","descr"],index => ["vendorid","typename"],filefields=>["vendorid","typename","typegroupid","descr","sysobjectid","cdp","tftp"]);

#--------------SLUTT-----------
&log_close;

sub spesiell_endring_org {
    my ($db,$fil,$tabell,$felt) = @_;
    my @felt = split(/:/,$felt);
    my %ny = &fil_hent($fil,scalar(@felt));
    #leser fra database
    my %gammel = &db_hent_hash($db,"SELECT ".join(",", @felt )." FROM $tabell ORDER BY $felt[0]");
    for my $feltnull (keys %ny) {
	unless($ny{$feltnull}[1]){
	    &db_endring_per_linje($db,\@{$ny{$feltnull}},\@{$gammel{$feltnull}},\@felt,$tabell,$feltnull);
	}
    }
    &db_endring($db,\%ny,\%gammel,\@felt,$tabell);

    &db_sletting($db,\%ny,\%gammel,\@felt,$tabell);
}
