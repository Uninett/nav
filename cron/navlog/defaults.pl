#!/usr/bin/perl
####################
#
# $Id: defaults.pl,v 1.2 2002/11/25 12:13:56 gartmann Exp $
# This file is part of the NAV project.
# defaults reads a file containing the configuration of messages that will be
# used in NAVlog at a later stage. The contents is saved into the type table of
# the navlog database, so that they can be used when making log messages.
#
# Copyright (c) 2002 by NTNU, ITEA nettgruppen
# Authors: Sigurd Gartmann <gartmann+itea@pvv.ntnu.no>
#
####################

use strict;
require '/usr/local/nav/navme/lib/NAV.pm';
import NAV qw(:DEFAULT :collect :log);


### Leser alle filene i et directory, og oppdaterer innholdet i navlog.type.defaultmessage hvis nødvendig.

my $conn = &db_get("insert");
my $directory = "/usr/local/nav/navme/etc/message/";

my @system_fields = ("id","name");
my %system = &db_select_hash($conn,"system",\@system_fields,1);

my $table = "type";
my @type_logdefaults = ("systemid","facility","mnemonic","priorityid","defaultmessage");

my %defaults;
my %old_defaults = &db_select_hash($conn,$table,\@type_logdefaults,0,1,2);

### Henter alle filene i katalogen
opendir(DIR, $directory) || die("Cannot open directory");

my @files = readdir(DIR);

for my $fil (@files) {

    ### alle filer som slutter på .txt (og ikke noe mer)
    if($fil =~ /(\w+)\.txt$/){

	my $system = $1;

	# finner systemets neste id-nummer.
	my $system_id;
	unless(exists($system{$system})){
	    $system_id = &make_and_get_sequence_number($conn,"system","id");
	    my $temp = [$system_id,$system];
	    &db_insert($conn,"system",\@system_fields,$temp);
	    $system{$system} = $temp;
	} else {
	    $system_id = $system{$system}[0];
	}

	my @log = &get_log($directory.$fil);

	for (my $l = 0; $l < @log; $l++) {
	    if($log[$l] =~ /^\s*(\S+)\-(\d+)\-(\S+)\s*\:\s*(.*?)\s*(?:\#.*)?$/){
		$defaults{$system_id}{$1}{$3} = [$system_id,$1,$3,($2+1),$4];
	    }
	}
    }
}
&db_safe(connection=>$conn,
	 table=>$table,
	 fields=>\@type_logdefaults,
	 index=>['systemid','facility','mnemonic'],
	 new=>\%defaults,
	 old=>\%old_defaults,
	 insert=>'nolog'
	 );
