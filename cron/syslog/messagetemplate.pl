#!/usr/bin/perl

use strict;

require "/usr/local/nav/navme/lib/database.pl";
require "/usr/local/nav/navme/lib/fil.pl";

my $dir = "/usr/local/nav/navme/etc/message/";
opendir(DIR, $dir) || die("Cannot open directory");

my @files = readdir(DIR);

my $connection = &db_connect("syslog","syslogadmin","urg20ola");
my $table = "messagetemplate";
my @felt = ("id","class","type","message");

for (@files) {
    if(/(\w+)\.\w+/){
	open (FIL, $dir.$_) || die("Cannot open file $!");
	my $class = $1;
	my $sql = "select ".join(",",@felt)." from ".$table." where class = \'".$class."\'";
	my %oldtemplate = &db_hent_hash($connection,$sql);
	my %newtemplate = ();
	while(<FIL>){
	    if(/^((\w+)\-\d\-(\w+))\s*\:\s*?(.*)$/){
		my $id = $2.'-'.$3;
		@_ = ($id,$class,$1,$4);
		@_ = map rydd($_), @_;
		$newtemplate{$id} = [ @_ ];
	    }
	}
	close FIL;

	for my $key (keys %newtemplate){
	    if(exists($oldtemplate{$key}[0])){
		for my $field (0..$#{$newtemplate{$key}}) {
		    if($newtemplate{$key}[$field] ne $oldtemplate{$key}[$field]){
			&db_update($connection, $table, $felt[$field], $oldtemplate{$key}[$field], $newtemplate{$key}[$field], "id=\'$key\' and class=\'$class\'");
		    }
		}
	    } else {
		&db_insert($connection,$table,\@felt,\@{$newtemplate{$key}});
	    }
	}
	for my $key (keys %oldtemplate){
	    unless(exists($newtemplate{$key}[0])){
		&db_delete($connection,$table,"id=\'$key\' and class=\'$class\'");
	    }
	}

#    &db_alt($connection, 1, 1, $table, \@felt, \%newtemplate, \%oldtemplate, [0]);

    }
}

close(DIR);
