#!/usr/bin/perl
use strict;

if(do "txt2db.pl"){
    if(do "type2db.pl"){
	if(do "prefiks2db.pl"){
	    if(do "boks2db.pl"){
		if(do "prefiksid2db.pl"){
		    if(do "getprefiks.pl"){
			if(do "getgwport.pl"){
			    if(do "rootgwid2db.pl"){
				if(do "hsrpgw.pl"){
				    if(do "getswport.pl"){
					if(do "getgw.pl"){
					    if(do "getsw.pl"){
						if(do "getkant.pl"){
						    print "ferdig";
						} else {
						    print "FANT IKKE getkant\n";
						}
					    } else {
						print "FANT IKKE getsw\n";
					    }
					} else {
					    print "FANT IKKE getgw\n";
					}
				    } else {
					print "FANT IKKE getswport\n";
				    }
				} else {
				    print "FANT IKKE hsrpgw\n";
				}
			    } else {
				print "FANT IKKE rootgwid2db\n";
			    }
			} else {
			    print "FANT IKKE getgwport\n";
			}
		    } else {
			print "FANT IKKE getprefiks\n";
		    }
		} else {
		    print "FANT IKKE prefiksid2db\n";
		}
	    } else {
		print "FANT IKKE boks2db\n";
	    }
	} else {
	    print "FANT IKKE prefiks2db\n";
	}
    } else {
	print "FANT IKKE type2db\n";
    }
} else {
    print "FANT IKKE txt2db\n";
}

	
