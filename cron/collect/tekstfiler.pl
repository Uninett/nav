#!/usr/bin/perl
####################
#
# $Id: tekstfiler.pl,v 1.10 2002/11/26 11:14:07 gartmann Exp $
# This file is part of the NAV project.
# tekstfiler reads text-files containing basic NAV information / configuration,
# and updates the database according to this.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;

require '/usr/local/nav/navme/lib/NAV.pm';
import NAV qw(:DEFAULT :collect);

my $path_local = &get_path("path_local");

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
$fil = $path_local."etc/kilde/org.txt";
$tabell = "org";
@felt = ("orgid","parent","descr","org2","org3","org4");
&spesiell_endring_org($db,$fil,$tabell,\@felt);
#--------------TYPE------------
&db_file_to_db(connection => $db,file => "etc/kilde/vendor.txt",table => "vendor",databasefields => ["vendorid"],filefields=>["vendorid"],index => ["vendorid"]);
&db_file_to_db(connection => $db,file => "etc/kilde/product.txt",table => "product",databasefields => ["vendorid","productno","descr"],index => ["vendorid","productno"]);
&db_file_to_db(connection => $db,file => "etc/kilde/cat.txt",table => "cat",databasefields => ["catid","descr"],filefields => ["catid","descr"],index => ["catid"]);
&db_file_to_db(connection => $db,file => "etc/kilde/typegroup.txt",table => "typegroup",databasefields => ["typegroupid","descr"],index => ["typegroupid"]);
&db_file_to_db(connection => $db,file => "etc/kilde/type.txt",table => "type",databasefields => ["vendorid","typename","typegroupid","sysobjectid","cdp","tftp","descr"],index => ["vendorid","typename"],filefields=>["vendorid","typename","typegroupid","descr","sysobjectid","cdp","tftp"]);

#--------------SLUTT-----------
&log_close;

sub spesiell_endring_org {
    my ($db,$fil,$tabell) = @_[0..2];
    my @felt = @{$_[3]};
#    my @felt = split(/:/,$felt);
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
