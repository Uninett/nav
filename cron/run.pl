#!/usr/bin/perl
use strict;

if(do "txt2db.pl"){
    print "ferdig med txt2db\n";
    if(do "type2db.pl"){
	print "ferdig med type2db\n";
	if(do "prefiks2db.pl"){
	    print "ferdig med prefiks2db\n";
	    if(do "boks2db.pl"){
		print "ferdig med boks2db\n";
	#	if(do "prefiksid2boks.pl"){
	# 	    print "ferdig med prefiksid2boks\n";
		    if(do "getprefiks.pl"){
			print "ferdig med getprefiks\n";
			if(do "getgwport.pl"){
			    print "ferdig med getgwport\n";
			    if(do "rootgwid2db.pl"){
				print "ferdig med rootgwid2db\n";
				if(do "hsrpgw.pl"){
				    print "ferdig med hsrpgw\n";
				    if(do "getswport.pl"){
					print "ferdig med getswport.pl\n";
					if(do "getgw.pl"){
					    print "ferdig med getgw\n";
					    if(do "getsw.pl"){
						print "ferdig med getsw\n";
						if(do "getkant.pl"){
						    print "ferdig med getkant\n";
						    if(do "prefiksid2boks.pl"){
							print "ferdig med prefiksid2boks\n";
							
							print "ferdig!!!!!!";
						    } else {						    
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
#		} else {
#		    print "FANT IKKE prefiksid2boks\n";
#		}
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

	
