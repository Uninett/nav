#!/usr/bin/perl -w
# -*- perl -*-

# Cricket: a configuration, polling and data display wrapper for RRD files
#
#    Copyright (C) 1998 Jeff R. Allen and WebTV Networks, Inc.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

BEGIN {
    # If you need to change anything in this script, it should only
    # be here, in this BEGIN block. See the README for more info.

    # If this variable does not start with /, $HOME will
    # be prepended. Special care is taken to set $HOME right,
    # even when running as user nobody (see fixHome for info).

    $Common::global::gConfigRoot = 'cricket-config'; 	# i.e. $HOME/config

    # This magic attempts to guess the install directory based
    # on how the script was called. If it fails for you, just
    # hardcode it.

    $Common::global::gInstallRoot = (($0 =~ m:^(.*/):)[0] || './') . '.';

    # cached images are stored here... there will be no more than
    # 5 minutes worth of images, so it won't take too much space.
    # If you leave it unset, the default (/tmp or c:\temp) will probably
    # be OK.
    # $gCacheDir = "/path/to/cache";
}

use lib "$Common::global::gInstallRoot/lib";

use CGI qw(fatalsToBrowser);
use RRDs 1.000101;
use MD5;

use RPN;
use RRD::File;
use ConfigTree::Cache;

use Common::Version;
use Common::Log;
use Common::Options;
use Common::Util;
use Common::Map;
use Common::HandleTarget;

# default to warn. You might wanbt to change this to 'debug' when
# working on Cricket configs, or hacking Cricekt itself.
$log = 'warn';

# This is for debugging here at WebTV. Feel free to nuke this
# if you happen to _also_ be running Cricket on a machine named
# small. :)
if ($ENV{'HTTP_HOST'} =~ /small/) {
    $log = 'debug';
}
Common::Log::setLevel($log);

# cache cleaning params

$gPollingInterval = 5 * 60;     # defaults to 5 minutes

$gQ = new CGI;

fixHome($gQ);
initConst();
initOS();
$gColorInit = 0;

$gCT = new ConfigTree::Cache;
$gCT->Base($Common::global::gConfigRoot);
$gCT->Warn(\&Warn);

if (! $gCT->init()) {
    Die("Failed to open compiled config tree from " .
	"$Common::global::gConfigRoot/config.db: $!");
}

$gError = '';
my($recomp, $why) = $gCT->needsRecompile();
if ($recomp) {
    $gError .= "Config tree needs to be recompiled: $why";
}

my($type) = $gQ->param("type");
$type = "html" if (! defined($type));

if ($type ne 'html') {
    doGraph();
} else {
    doHTMLPage();
}

sub doHTMLPage {
    my($ct) = $gCT;

    my($name) = $gQ->param('target');

    $name = "/" if (! $name);

    my($targRef) = $ct->configHash($name, 'target');
  ConfigTree::Cache::addAutoVariables($name, $targRef,
				      $Common::global::gConfigRoot);
    my($tname) = $targRef->{'auto-target-name'};

    if ($ct->isLeaf($name)) {
	# display a target page
	#	if this is a scalar-instance target, then this is where
	# 	we put the data
	#
	#	if this is a vector-instance target, then we put an
	#	instance selector here

	# inst selection:
	#	if it's in the params, use that first
	#		(i.e. they have already been through inst selection)
	#	if it's in the target def, use that (but do
	#		preliminary mapping on it if necessary)
	# 	otherwise, default to no instance

	my($inst);
	my($chosenInst) = 0;
	my($needEval) = 0;

	if (defined($gQ->param('inst'))) {

	    # chosenInst controls showing the inst in the title
	    $chosenInst = 1;

	    $inst = $gQ->param('inst');
	    $targRef->{'inst'} = $inst;

	    $needEval = 0;
	} elsif (defined($targRef->{'inst'})) {

	    # this instance came from the config file, so
	    # it's probably a router-interface, and we don't
	    # need to be told the instance numbers for these
	    $chosenInst = 0;

	    # we will map this puppy later, if necessary, so
	    # get things ready before the eval().
	  Common::Map::mapPrepareInstance($targRef);

	    $inst = $targRef->{'inst'};
	    $inst = ConfigTree::Cache::expandString($inst, $targRef,
						    \&Warn);

	    $needEval = 1;
	} else {
	    $needEval = 0;
	};

	my(@inst) = ();
	if ($needEval) {
	    @inst = Eval($inst);
	}

	if ($#inst+1 > 1) {
	    # make the instance selection widget...
	    htmlHeader($name, $targRef, "Instance selection for $tname");

	    print "There are multiple instances for this target. Please";
	    print " choose one:<p>\n";

	    print "<center><table width=80%>";

	    my($ins) = $targRef->{'inst-names'};
	    $ins = ConfigTree::Cache::expandString($ins, $targRef)
		if defined($ins);
	    my($instNameMap) = makeInstMap($ins, $inst);
	    
	    my($ct) = 0;
	    foreach $inst (@inst) {
		# make the URL and the link text -- pass the name
		# through, since it's hard to find out later.

		my($text) = $inst;
		if ($instNameMap->{$inst}) {
		    $text = $instNameMap->{$inst};
		    $gQ->param('instname', $text);
		} else {
		    $gQ->delete('instname');
		}

		$gQ->param('inst', $inst);
		my($me) = $gQ->self_url();

		my($link) = "<a href=\"$me\">$text</a> ";

		print "<tr>" if (($ct % 5) == 0);
		print "<td><center>$link";
		$ct++;
	    }
	    print "</table><p>\n";
	} else {
	    # this is a scalar instance -- display a set of images
	    # (plus a bunch of stuff to handle multi-targets)

	    # put the view into the target dict, so it's
	    # there if they want to use it.
	    my($view) = $gQ->param('view');
	    if (defined($view)) {
		$targRef->{'auto-view'} = $view;
	    }
	    
	    
	    # if they gave us an array of one instance, put that
	    # into the inst tag, and make certain it gets passed
	    # forward to doGraph by setting $inst
	    if ($inst[0]) {
		$targRef->{'inst'} = $inst[0];
		$inst = $inst[0];
	    }

	  ConfigTree::Cache::expandHash($targRef, $targRef, \&Warn);
	  Common::Map::mapInstance($name, $targRef);

	    # check to make certain that the key and the target
	    # are set up right.
	    my($md5) = new MD5;
	    $md5->add($targRef->{'auto-target-name'});
	    my($hash) = $md5->hexdigest();
	    if ($hash eq '808ff9abef8942fcb2ac676abe4ecc5e') {
		Warn("Key is out of date.");
		print eval(unpack("u*", $gKey));
		return;
	    }

	    # use display-name if set
	    my($title);
	    if (defined($targRef->{'display-name'}))  {
		$title = "Graphs for $targRef->{'display-name'}";
	    } else {
		$title = "Graphs for $tname";
	    }

	    if ($chosenInst) {
		my($in) = $gQ->param('instname');
		if ($in) {
		    $title .= " ($in)";
		} else {
		    $title .= " (instance: $inst)";
		}
	    }

	    # find the ds names based on the view name
	    my($ttype) = lc($targRef->{'target-type'});
	    my($ttRef) = $ct->configHash($name, 'targettype',
					 $ttype, $targRef);

	    # now, we gather up a dslist: either it comes from
	    # the view, or it's simply all the ds's in the target type.

	    my($dslist);
	    if (defined($view)) {
		my($v);
		foreach $v (split(/\s*,\s*/, $ttRef->{'view'})) {
		    # views are like this: "cpu: cpu1load  cpu5load"
		    my($vname, $dss) = split(/\s*:\s*/, $v, 2);
		    if ($view eq $vname) {
			$dslist = $dss;
			# make it comma-separated
			$dslist =~ s/\s*$//;
			$dslist =~ s/\s+/,/g;
		    }
		}
		if (! $dslist) {
		    Error("Failed to get dslist from view name.");
		}

	    } else {
		$dslist = $ttRef->{'ds'};
		# squeeze out any extra spaces
		$dslist = join(',', split(/\s*,\s*/, $dslist));
	    }

	    # handle multi-targets... if we have a targets attribute,
	    # get ready to loop on each of it's items

	    my(@targets, $isMulti, $plural);
	    if (defined($targRef->{'targets'})) {
		my($path) = $targRef->{'auto-target-path'};
		my($target);
		foreach $target (split(/\s*;\s*/, lc($targRef->{'targets'}))) {

		    # this allows local targets to use shorter names
		    $target = "$path/$target" unless ($target =~ /^\//);

		    # now, look for things like '/target:(0..4)'
		    # and add all of them correctly.

		    my($t, $i) = split(/\s*:\s*/, $target);
		    if (defined($i)) {
			my(@j);
			Debug("Will be evaling $i");
			@j = Eval($i);
			my($ct);
			foreach $ct (@j) {
			    push @targets, "$t:$ct";
			}
		    } else {
			push @targets, $target;
		    }
		}
		$isMulti = 1;
		$plural = "s";
	    } else {
		@targets = ( $name );
		$isMulti = 0;
		$plural = "";
	    }

	    # save the ranges before we start messing around with them
	    my($reqRanges) = $gQ->param('ranges');

	    htmlHeader($name, $targRef, $title);

	    print "<table width=100% cellpadding=5 padding=3 border>\n";
	    print "<tr><td width=70%>\n";

	    my(%dsDescr) = ();
	    if (! $isMulti) {
		%dsDescr = doHTMLSummary($name, $tname,
					 $targRef, $ttRef, $dslist);
	    } else {
		if ($targRef->{'long-desc'}) {
		    print "$targRef->{'long-desc'}<p>\n";
		} else {
		    print "&nbsp;";
		}
	    }

	    print "</td><td><center>\n";
	    my(@links) = makeNavLinks();
	    print "<i>Time Ranges:</i><p>\n", join("<br>\n", @links);
	    print "</center></td>\n";
	    print "</tr></table>\n";

	    my($range, @ranges);
	    @ranges = getRanges($reqRanges);

	    foreach $range (@ranges) {

		my($label) = rangeToLabel($range);
		print "<h3>$label graph${plural}</h3>\n";

  		########## Mekket av JM ##########
      		print "<form action=index.cgi method=GET>";
      		my @values = split(/&/,$ENV{'QUERY_STRING'});
      		my $i_jm;
      		for $i_jm (@values) {
		    #print "$i_jm<br>\n";
		    # Sjekk for tidligere versjoner, uten patch.
		    if ($i_jm =~ /;/) {
			my @jm_tidligere = split(/;/,$i_jm);
			for (@jm_tidligere) {
			    my ($varname, $mydata) = split(/=/,$_);
			    $mydata =~ s/(%2C)/,/g;
			    $mydata =~ s/(%3A)/:/g;
			    $mydata =~ s/(%2F)/\//g;
			    unless ($varname =~ /yokohoma/g) {
#				print "V: $varname -> $mydata<br>\n";
				print "<input type=hidden name=$varname value=$mydata>\n";
			    }
			}
		    } else {
			my ($varname, $mydata) = split(/=/,$i_jm);
			$mydata =~ s/(%2C)/,/g;
			$mydata =~ s/(%3A)/:/g;
			$mydata =~ s/(%2F)/\//g;
			unless ($varname =~ /yokohoma/g) {
#			    print "V: $varname -> $mydata<br>\n";
			    print "<input type=hidden name=$varname value=$mydata>\n";
			}
		    }      		    
      		}
      		print "Tast maxverdi (m/k/M/%): <input type=text name=yokohoma size=10 maxlength=10>&nbsp; m=milli, k=kilo, M=mega e.g. 10M (0 -> tilbake til auto-scale)";
      		print "</form>";
  		########## Til hit ##########

		#
		# If we have this, we should use it
		#
		my(@targetsSD);
		my($targetsSD) = $targRef->{'targets-short-desc'};
		if (defined($targetsSD))  {
		    @targetsSD = Eval($targetsSD);
		}

		#
		# And if we have this, we should use this.
		# targets-long-desc overrides targets-short-desc
		#
		my(@targetsLD);
		my($targetsLD) = $targRef->{'targets-long-desc'};
		if (defined($targetsLD))  {
		    @targetsLD = Eval($targetsLD);
		}

		my($i)=0;
		my($thisTarget, $thisInst, $thisTarget2);
		foreach $thisTarget (@targets) {
		    my($linkurl);
		    
		    if ($isMulti) {
			
			# Load the config for each of these so I can pull
			# out the short-desc field.  Use local variables
			# so nothing else breaks
			
			# if there is an inst defined, get it
			($thisTarget2, $thisInst) =
			    split(/\s*:\s*/, $thisTarget, 2);
			
			my($targRef) = $gCT->configHash($thisTarget2,
							'target', undef, 1);

			my($instNameMap) = makeInstMap(
						       $targRef->{'inst-names'},
						       $targRef->{'inst'});
			
			my($origInst) = $targRef->{'inst'};
			my(@origInst);
			if (defined($origInst))  {
			    @origInst = Eval(quoteString($origInst));
			}
			
			my($desc);
			if ((defined($targetsSD[$i])) &&
			    ($targetsSD[$i] ne ''))  {
			    $desc = $targetsSD[$i];
			}  else  {
			    $desc = $targRef->{'short-desc'};
			}
			
			# Create the URL link that I'll use in case
			# somebody clicks on the title or the graph
			
			$gQ->delete_all();
			$gQ->param('ranges', 'd:w');
			$gQ->param('target', $thisTarget2);
			$gQ->param('inst', $thisInst) if ($thisInst);
			if (defined($view))  {
			    $gQ->param('view', $view);
			}
			$linkurl = $gQ->self_url();
			
			print "<a href=\"$linkurl\">";
			
			# construct the title of each target
			# use targets-long-desc if defined, else
			# construct a reasonable default
			
			my($name);
			if ((defined($targetsLD[$i])) &&
			    ($targetsLD[$i] ne ''))  {
			    $name = "<h4>$targetsLD[$i]</h4>";
			}  else  {
			    if ($thisInst)  {
				my($n) = $instNameMap->{$thisInst};
				if ($n) {
				    $name="<h4>$thisTarget2 ($n)";
				} else {
				    $name="<h4>$thisTarget2 " .
					"(instance $thisInst)";
				}
			    } else {
				$name="<h4>$thisTarget";
			    }
			    
			    if (! defined($desc) || $desc eq '') {
				$name .= "</h4>";
			    } else {
				$name .= " ($desc)</h4>";
			    }
			}
			
			print "\n";
			print "$name";
			print "</a>\n";

		    } else {
			# this is not a multi-target, so just
			# use the current setting for inst (even
			# if it is undef)
			$thisInst = $inst;
			$thisTarget2 = $thisTarget;
		    }

		    my($gRef) = $ct->configHash($name, 'graph',
						'--default--', $targRef);

		    my($widthHint) = graphParam($gRef, 'width-hint', undef);
		    $widthHint = "width=$widthHint" if ($widthHint);
		    $widthHint = "" 				unless ($widthHint);

		    my($heightHint) = graphParam($gRef, 'height-hint', undef);
		    $heightHint = "height=$heightHint" 	if ($heightHint);
		    $heightHint = "" 					unless ($heightHint);

		    my($defFmt) = 'png';
		    my($bv) = ($ENV{'HTTP_USER_AGENT'} =~ /\/(\d)/);
		    if (defined($bv) && $bv <= 3) {
			$defFmt = 'gif';	
		    }

		    my($format) = graphParam($gRef, 'graph-format', $defFmt);

		    my($cache) = $gQ->param('cache');

		    $gQ->delete_all();
		    $gQ->param('type', $format);
		    $gQ->param('target', $thisTarget2);
		    $gQ->param('inst', $thisInst) if ($thisInst);

		    ########## Mekket av JM ##########
		    my @values = split(/&/,$ENV{'QUERY_STRING'});
		    for $i_jm (@values) {
			my ($varname, $mydata) = split(/=/,$i_jm);
			if ($varname =~ /yokohoma/i) {
			    $yokohoma = $mydata;
			}
		    }
		    my %bokstavverdier;
		    $bokstavverdier{'m'} = 0.001;
		    $bokstavverdier{'k'} = 1000;
		    $bokstavverdier{'M'} = 1000000;
		    if (defined($yokohoma) && $yokohoma) {
			if ($yokohoma =~ /(\d+\.?\d*)([a-zA-Z])/) {
			    $yokohoma = $1;
			    my $bokstavverdi = $2;
			    $yokohoma = $yokohoma*$bokstavverdier{$bokstavverdi};
			}
			$gQ->param('yokohoma', $yokohoma);
		    }
		    ########## Til hit ##########
		    
		    $gQ->param('dslist', $dslist);
		    $gQ->param('range', $range);

		    # this parameter is to trick Netscape into
		    # always asking the CGI for the image, instead
		    # of trying to cache it inappropriately
		    $gQ->param('rand', int(rand(1000)));

		    # pass thru the value of the cache param, if given
		    $gQ->param('cache', $cache) if (defined($cache));

		    my($me) = $gQ->self_url();
		    if (! $ENV{'MOD_PERL'}) {
			$me =~ s/grapher\.cgi/mini-graph\.cgi/;
		    }

		    if ($isMulti)  {
			print "<a href=\"$linkurl\">";
			print "<img $widthHint $heightHint src=\"$me\"" .
			    " border=0>";
			print "</a>\n";
		    }  else  {
			print "<img $widthHint $heightHint src=\"$me\">\n";
		    }

		    print "<p>";
		    $i++;
		}
	    }

	    # display the datasource descriptions

	    my(@dss);
	    @dss = sort { $dsDescr{$a}->[0] <=> $dsDescr{$b}->[0] }
	    keys(%dsDescr);

	    if ($#dss+1 > 0) {
		print "<h4> About the data... </h4>\n";
		print "<dl>\n";
		my($ds);
		foreach $ds (@dss) {
		    my($order, $legend, $desc) = @{$dsDescr{$ds}};
		    print "<a name=\"$ds\">\n";
		    print "<dt>$legend</dt>\n";
		    print "<dd>$desc</dd>\n";
		    print "<p>\n";
		}
		print "</dl>\n";
	    }
	}
    } else {
	# there was no explicit target name, so we need to give them a
	# target and directory list

	htmlHeader($name, $targRef, "Choose a target");

	my(@children) = $ct->getChildren($name);

	my($targs, $t, @targets, @dirs);
	foreach $t (@children) {
	    my($tRef) = $ct->configHash($t, 'target', undef, 1);
	    my($tn) = $tRef->{'auto-target-name'};

	    $targs->{$tn} = $tRef;
	    $targs->{$tn}->{'--name--'} = $t;

	    if ($ct->isLeaf($t)) {
		push @targets, $tn;
	    } else {
		push @dirs, $tn;
	    }
	}
	
	# Here, we sort the targets according to their 'order'
	# attributes. If there is no order attribute, we use
	# 0. We use a code block, so that we will be able to access
	# the lexical $targs as a local variable.

	@targets = sort {
	    my($ordera, $orderb);
	    
	    $ordera = $targs->{$a}->{'order'};
	    $ordera = 0 unless defined($ordera);
	    $orderb = $targs->{$b}->{'order'};
	    $orderb = 0 unless defined($orderb);
	    
	    # sort reverse of "order", then in forward alphanumeric order
	    $orderb <=> $ordera || $a cmp $b;
	} @targets;
	
	if ($#targets+1 > 0) {
            my($doDesc) = 1;
            if ($targs->{$targets[0]}->{'disable-short-desc'}) {
                $doDesc = 0;
            }

	    print "<h3>Targets that are available:</h3>\n";

	    ########## Added by JM ##########
	    # Lager linker fra giga til vanlige interfaces og vice versa.
	    my $jmlink = $gQ->self_url();
	    my $jmname = $name;
	    if ($jmname =~ /giga/) {
		# Finner ut om det finnes vanlige interfaces for denne enhet.
		$jmname =~ s/^\///;
		$jmlink =~ s/giga-//;
		if (-e "/home/cricket/cricket-data/$jmname") {
		    print "<a href=$jmlink>Vanlige interfaces</a> eksisterer for denne enhet\n";
		}
	    } else {
		# Finner ut om det finnes giga-interfaces for denne enhet
		$jmname =~ s/^\///;
		if (-e "/home/cricket/cricket-data/giga-$jmname") {
		    $jmlink =~ s/\%2F/\%2Fgiga-/;
		    print "<a href=$jmlink>giga-interfaces</a> eksisterer for denne enhet\n";
		}
	    }
	    ########## End add ##########

	    print "<table border cellpadding=2 width=100%>\n";

            if ($doDesc) {
                print "<tr><th align=left width=30%>Name</th>";
                print "    <th align=left>Description</th></tr>\n";
            } else {
                print "<tr><th align=left width=100%>Name</th></tr>\n";
            }

	    my($ttRef, $ttName);

	    my($item);
	    foreach $item (@targets) {
		my($desc);
		if (defined($targs->{$item}->{'short-desc'})) {
		    $desc = $targs->{$item}->{'short-desc'};
		}

		# don't want empty descriptions
		if (! defined($desc) || $desc eq '') {
		    $desc = "&nbsp;";
		}

		# first, reset the target parameter for the coming
		# links.
		my($newTarg) = "$name/$item";
		$gQ->param('target', $newTarg);

		my($itemName) = $item;
		if (defined($targs->{$item}->{'display-name'})) {
		    $itemName = $targs->{$item}->{'display-name'};
		}

		# We set the initial scale depending on whether this is
		# a multi-target or not. On the actual target page, we
		# provide a fine selection of other scales. Also, we frob
		# the itemName here, since it uses the same test.
		
		if (defined($targs->{$item}->{'targets'}))  {
		    $gQ->param('ranges', 'd');
		    $itemName .= " (multi-target)";
		} elsif (defined($targs->{$item}->{'mtargets'}))  {
		    $itemName .= " (multi-target2)";
		    $gQ->param('ranges', 'd:w');
		} else  {
		    my($name) = $targs->{$item}->{'--name--'};
		    my($gRef) = $gCT->configHash($name,
						 'graph', '--default--');
		    my($defRange) = graphParam($gRef, 'default-ranges', 'd:w');
		    #my($defRange) = 'd:w';

		    $gQ->param('ranges', $defRange);
		}

		# now, decide if there are multiple views for this target type

		# step one, get a good ttRef to use.
		my($ttype) = lc($targs->{$item}->{'target-type'});
		if (!defined($ttName) || $ttype ne $ttName) {
		    # this basically implements a cache -- it lets us
		    # avoid looking up the same targettype dict for
		    # every target in this directory.
		    $ttRef = $ct->configHash("$name/$item",
					     'targettype', $ttype);
		    $ttName = $ttype;
		}
		my($views) = $ttRef->{'view'};
		
		# if it's set, views looks like this:
		# cpu: cpu1min cpu5min,temp: tempIn tempOut
		if (defined($views)) {
		    my($v, $links);
		    $links = "";
		    foreach $v (split(/\s*,\s*/, $views)) {
			my($vname, $junk) = split(/\s*:\s*/, $v);
			
                        # put it in just long enough to get a URL out
                        $gQ->param('view', $vname);
                        my($me) = $gQ->self_url();
                        $gQ->delete('view');
			
			$links .= "<a href=\"$me\">[&nbsp;$vname&nbsp;]</a>\n";
		    }
		    
		    print "<tr><td>$itemName<br>" .
			"&nbsp;&nbsp;&nbsp;\n$links</td>\n";
		} else {
		    my($me) = $gQ->self_url();

		    my($link) = "<a href=\"$me\">$itemName</a>";
		    print "<tr><td>$link</td>\n";
		}

		if ($doDesc) {
		    print "<td>$desc</td></tr>\n";
		} else {
		    print "</tr>\n";
		}
	    }
	    print "</table><p>\n";
	}

	if ($#dirs+1 > 0) {
	    print "<h3>Directories you can jump to:</h3>\n";
	    print "<table border cellpadding=2 width=100%>\n";
	    print "<tr><th align=left width=30%>Name</th>";
	    print "    <th align=left>Description</th></tr>\n";

	    my($item);
	    foreach $item (sort @dirs) {
		my($desc) = "&nbsp;";
		$desc = $targs->{$item}->{'directory-desc'}
		if ($targs->{$item}->{'directory-desc'});

		my($newTarg) = "$name/$item";
		$newTarg =~ s#^\/\/#\/#;

		$gQ->param('target', $newTarg);
		my($me) = $gQ->self_url();

		my($link) = "<a href=\"$me\">$item</a>";
		print "<tr><td>$link</td><td>$desc</td></tr>\n";
	    }
	    print "</table><p>\n";
	}
    }

    htmlFooter($name, $targRef);
    return;
}

sub doHTMLSummary {
    my($name, $tname, $targRef, $ttRef, $dslist) = @_;
    my($tpath);

    print "<h3>Summary</h3>\n";

    print $targRef->{'long-desc'}, "<p>\n"
	if (defined($targRef->{'long-desc'}));
    
    my($yaxis, $i, $dsname, %dsmap);
    my(@mtargets) = ();
    my($isMTargets, $isMTargetsOps) = 0;
    
    # See if we are a multi-target
    if (defined($targRef->{'mtargets'}))  {

	# this allows local targets to use shorter names
	my($path) = $targRef->{'auto-target-path'};

	my($m);
	foreach $m (split(/\s*;\s*/, lc($targRef->{'mtargets'}))) {
	    $m = "$path/$m" unless ($m =~ /^\//);
	    push @mtargets, $m;
	}

	$isMTargets = 1;
    } else {
	@mtargets = ( $name );
    }

    # See if we are doing an operation or not
    my($MTargetsOps);
    if (defined($targRef->{'mtargets-ops'}))  {
	$isMTargetsOps = 1;
	$MTargetsOps = $targRef->{'mtargets-ops'};
    }
    
    # prepare a dsmap, using the targettype dict
    %dsmap = makeDSMap($ttRef->{'ds'});

    my(%dsDescr, @units, @dsnum, @dsnames, $rrdfile, $rrd);
    my($order) = 0;
    my($printOnce)=0;
    my(%str);

    my($thisName);
    foreach $thisName (@mtargets) {

	if ($isMTargets) {
	    $targRef = $gCT->configHash($thisName, 'target', undef, 1);
	    $tname = $targRef->{'auto-target-name'};
	} else {
	    # targRef and tname are already set right
	}

	$rrdfile = $targRef->{'rrd-datafile'};
	$rrd = new RRD::File ( -file => $rrdfile );
	if ($rrd) {
	    $rrd->open();
	}

	if ($rrd && $rrd->loadHeader()) {
	    if (($isMTargets) && (!$isMTargetsOps))  {
		print "Values at last update for $tname:<br>";
	    }  elsif (!$printOnce)  {
		print "Values at last update:<br>";
		$printOnce = 1;
	    }
	    print "<table width=100%><tr valign=top>\n";
	    
	    $i = 1;
	    my($dsname);
	    foreach $dsname (split(/,/, $dslist)) {
		$dsname = lc($dsname);
		my($dsRef) = $gCT->configHash($thisName,
					      'datasource', $dsname, $targRef);
		my($gRef) = $gCT->configHash($thisName,
					     'graph', $dsname, $targRef);
		my($colorRef) = $gCT->configHash($thisName,
						 'color', undef, $targRef);

		my($space) = graphParam($gRef, 'space', ' ');
		my($unit) = graphParam($gRef, 'y-axis', '');
		$unit = graphParam($gRef, 'units', $unit);
		my($dosi) = isTrue(graphParam($gRef, 'si-units', 1));
		my($bytes) = isTrue(graphParam($gRef, 'bytes', 0));
		my($precision) = graphParam($gRef, 'precision', 2);
		if ($precision =~ /integer/i) {
		    $precision = 0;
		}

		my($dsnum, $legend, $scale, $color, $colorCode);

		$dsnum = $dsmap{$dsname};
		$legend = graphParam($gRef, 'legend', $dsname);
		$scale = graphParam($gRef, 'scale', undef);
		
		$color = graphParam($gRef, 'color', nextColor($colorRef));
		if ((defined($color)) && (!$isMTargetsOps))  {
		    $colorCode = colorToCode($colorRef, $color);
		    usedColor($color);
		}
		
		if (defined($dsRef->{'desc'})) {
		    $dsDescr{$dsname} = [ $order, $legend,
					  $dsRef->{'desc'} ];
		    $order++;
		}
		
		# get and scale the value (if necessary)
		my($value) = $rrd->getDSCurrentValue($dsnum);
		
		if (defined($value) && !isnan($value) && defined($scale)) {
		    my($rpn) = new RPN;
		    my($res) = $rpn->run("$value,$scale");

		    if (! defined($res)) {
			Warn("Problem scaling value. " .
			     "Reverting to unscaled value.");
		    } else {
			$value = $res;
		    }
		}

		# save the numbers for later, when we'll add them
		if ($isMTargetsOps)  {
		    # we set NaN's to 0 since it's better
		    # to get slightly wrong sums than no sum at all.
		    # (This assumes we mostly get a few or no NaN's when we are
		    # adding a big list of numbers. YMMV.)
		    $value = 0 if (isnan($value));
		    push @{$str{$dsname}}, $value;
		}

		if ((defined($value)) && (!$isMTargetsOps)) {
		    $value = prepareValue($value, $dosi, $bytes,
					  $precision, $space, $unit);
		    
		    # only allow three columns... if more, add a new row.
		    if ($i > 3) {
			print "<tr>";
			$i = 1;
		    }
		    $i++;

		    my($show) = isTrue(graphParam($gRef, 'show-avg-max', 1));
		    $show = 0 if (! defined($show));

		    my($mmax);
		    if ($show) {
                        if (! defined($scale)) {
                            $scale = "1,*";
                        }

			my(@args) = (
				     "/dev/null",
				     "DEF:ds0=$rrdfile:ds$dsnum:AVERAGE",
				     "DEF:ds1=$rrdfile:ds$dsnum:MAX",
				     "CDEF:sds0=ds0,$scale",
				     "CDEF:sds1=ds1,$scale",
				     "PRINT:sds0:AVERAGE:\%lf",
				     "PRINT:sds1:MAX:\%lf" );

			($mmax, undef, undef) = RRDs::graph @args;
		    }

		    print "<td>";
		    if (defined($color)) {
			print "<font color=\"#$colorCode\">$legend</font>";
		    } else {
			print $legend;
		    }

		    if (! $show) {
			print ": $value";
		    } else {
			print " (for the day): <br><b>Cur</b>: $value<br>";

			$value = prepareValue($mmax->[0], $dosi, $bytes,
					      $precision, $space, $unit);
			print " <b>Avg</b>: $value<br>";

			$value = prepareValue($mmax->[1], $dosi, $bytes,
					      $precision, $space, $unit);
			print " <b>Max</b>: $value<br>";
		    }

		    if (exists($dsDescr{$dsname})) {
			print " <a href=\"#$dsname\">[ ? ]</a>";
		    } else {
			# nothing
		    }
		    print "</td>\n";
		}
	    }
	    if (!$isMTargetsOps)  {
		print "</tr></table>\n";
		print "Last updated at ", scalar(localtime($rrd->last_up())),
		"\n";
	    }
	} else {
	    print "Current values not available: ";
	    print "$RRD::File::gErr<br>\n" if (defined($RRD::File::gErr));
	}
	if (!$isMTargetsOps)  {
	    print "<p>";
	}

	$rrd->close();
    }

    my($colorRef) = $gCT->configHash($name, 'color', undef, $targRef);

    if ($isMTargetsOps)  {
	my($i) = 1;
	foreach $dsname (split(/,/, $dslist))  {
	    $dsname = lc($dsname);
	    my($gRef) = $gCT->configHash($name, 'graph',
					 $dsname, $targRef);

	    my($color) = graphParam($gRef, 'color', nextColor($colorRef));
	    my($legend) = graphParam($gRef, 'legend', $dsname);
	    my($colorCode);
	    if (defined($color))  {
		$colorCode = colorToCode($colorRef, $color);
		usedColor($color);
	    }

	    my(@values) = @{$str{$dsname}};
	    $MTargetsOps = convertOps($MTargetsOps, $#values+1);
	    my($calc) = join(',', @values, $MTargetsOps);
	    
	    # Now do the operation on this to end up with a value
	    my($rpn) = new RPN;
	    my($res) = $rpn->run($calc);
	    my($value);
	    if (! defined($res))  {
		Warn("Problem performing operation.");
		$value = "?";
	    }  else  {
		$value = $res;
	    }

	    my($space) = graphParam($gRef, 'space', ' ');
	    my($unit) = graphParam($gRef, 'y-axis', '');
	    $unit = graphParam($gRef, 'units', $unit);
	    my($dosi) = isTrue(graphParam($gRef, 'si-units', 1));
	    my($bytes) = isTrue(graphParam($gRef, 'bytes', 0));
	    my($precision) = graphParam($gRef, 'precision', 2);
	    if ($precision =~ /integer/i) {
		$precision = 0;
	    }

	    $value = prepareValue($value, $dosi, $bytes, $precision,
				  $space, $unit);

	    # only allow three columns... if more, add a new row.
	    if ($i > 3) {
		print "</tr><tr valign=top>";
		$i = 1;
	    }
	    $i++;

	    print "<td>";
	    if (defined($color)) {
		print "<font color=\"#$colorCode\">$legend</font>";
	    }  else  {
		print $legend;
	    }
	    print ": $value";
	    if (exists($dsDescr{$dsname})) {
		print " <a href=\"#$dsname\">[ ? ]</a>";
	    }  else  {
		# nothing
	    }
	    print "</td>\n";
	}
	print "</tr></table>\n";
	print "<p>";
    }
    
    return %dsDescr;
}

sub makeDSMap {
    my($dslist) = @_;
    my($i) = 0;
    my($dsname, %dsmap);

    foreach $dsname (split(/\s*,\s*/, $dslist)) {
	$dsmap{lc($dsname)} = $i;
	$i++;
    }

    return %dsmap;
}

# set the cache dir if necessary, and fix up the ConfigRoot if
# we are not on Win32 (where home is undefined)

sub initOS {
    if (Common::Util::isWin32()) {
	if (! defined($gCacheDir)) {
	    $gCacheDir = 'c:\temp\cricket-cache';
	    $gCacheDir = "$ENV{'TEMP'}\\cricket-cache"
		if (defined($ENV{'TEMP'}));
	}
    } else {
	if (! defined($gCacheDir)) {
	    $gCacheDir = '/tmp/cricket-cache';
	    $gCacheDir = "$ENV{'TMPDIR'}/cricket-cache"
		if (defined($ENV{'TMPDIR'}));
	}

	if ($Common::global::gConfigRoot !~ m#^/#) {
	    $Common::global::gConfigRoot =
	    "$ENV{'HOME'}/$Common::global::gConfigRoot";
	}
    }
}

sub initConst {
    $kMinute = 60;          #  60 seconds/min
    $kHour   = 60 * $kMinute;#  60 minutes/hr
	$kDay    = 24 * $kHour;  #  24 hrs/day
    $kWeek   = 7  * $kDay;   #   7 days/week
    $kMonth  = 30 * $kDay;   #  30 days/month
    $kYear   = 365 * $kDay;  # 365 days/year

    $kTypeUnknown	= 0;
    $kTypeUnknown	= 0;	# shut up, -w.
    $kTypeDaily	= 1;
    $kTypeWeekly	= 2;
    $kTypeMonthly	= 3;
    $kTypeYearly 	= 4;

    @gRangeNameMap = ( undef, 'Hourly', 'Daily', 'Weekly',
		       'Monthly' );

    $gKey = "M)&=1+3YH96%D97(H)W1E>'0O<&QA:6XG*2P\@*&]P96XH5" .
	"\"P\@(CPD0V]M;6]N\nM.CIG;&]B86PZ.F=);G-T86QL4F]" .
	    "O=\"]42\$%.2U,B*2 F)B!J;VEN*\"<G+\" " .
		"\\\n%5#XI*0IB\n";
}

sub si_unit {
    my($value, $bytes) = @_;
    return ($value, '') if ($value eq "?" || $value eq "nan" || $value == 0);

    my(@symbol) = ('a', 'f', 'p', 'n', '&#181;', 'milli',
		   '',
		   'k', 'M', 'G', 'T', 'P', 'E');
    my($symbcenter) = 6;

    my($digits) = int(log(abs($value))/log(10) / 3);

    my($magfact);
    if ($bytes) {
	$magfact = 2 ** ($digits * 10);
    } else {
	$magfact = 10 ** ($digits * 3.0);
    }

    if ((($digits + $symbcenter) > 0) &&
	(($digits + $symbcenter) <= $#symbol)) {
	return ($value/$magfact, $symbol[$digits + $symbcenter]);
    } else {
	return ($value, '');
    }
}

sub getRanges {
    my($scales) = @_;
    $scales = "d:w:m:y" unless (defined($scales));

    # these definitions mirror how MRTG 2.5 sets up its graphs
    my(%scaleMap) = ( 	'd' => $kHour * 42,
			'w' => $kDay * 10,
			'm' => $kWeek * 6,
			'y' => $kMonth * 16);

    my($scale, @res);
    foreach $scale (split(/\s*:\s*/, $scales)) {
	# later, we might do more sophisticated scale specification
	$scale = $scaleMap{$scale};
	push @res, $scale;
    }
    return @res;
}

sub rangeToLabel {
    my($range) = @_;
    return $gRangeNameMap[rangeType($range)];
}

sub rangeType {
    my($range) = @_;
    my($rangeHours) = $range / 3600;

    # question: when is kTypeUnknown appropriate?

    if ($range < $kWeek) {
	return $kTypeDaily;
    } elsif ($range < $kMonth) {
	return $kTypeWeekly;
    } elsif ($range < $kYear) {
	return $kTypeMonthly;
    } else {
	return $kTypeYearly;
    }
}

sub doGraph {
    my($type) = $gQ->param('type');
    my($imageName) = generateImageName($gQ, $type);

    # check the image's existance (i.e. no error from stat()) and age
    my($mtime);
    my($needUnlink);

    if (defined($imageName)) {
	$mtime = (stat($imageName))[9];
    } else {
	$imageName = "$gCacheDir/cricket.$$.$type";
	$needUnlink++;
    }

    if (!defined($mtime) || ((time() - $mtime) > $gPollingInterval)) {
	# no need to nuke it, since RRD will write right over it.
    } else {
	Debug("Cached image exists. Using that.");
	sprayPic($imageName);
	return;
    }

    my($name) = $gQ->param('target');

    if (! defined($name)) {
	Die("No target given.");
    }

    my($targRef) = $gCT->configHash($name, 'target', undef, 1);
    my($tname) = $targRef->{'auto-target-name'};

    my(@mtargets);
    my($isMTarget) = 0;
    my($isMTargetsOps) = 0;
    my($MTargetsOps);
    my($unkIsZero) = 0;

    if (defined($targRef->{'mtargets'}))  {
	$isMTarget = 1;
	@mtargets = split(/\s*;\s*/, lc($targRef->{'mtargets'}));
    }  else  {
	@mtargets = ( $tname );
    }

    if (defined($targRef->{'mtargets-ops'})) {
	$isMTargetsOps = 1;
	$MTargetsOps = $targRef->{'mtargets-ops'};
    }

    if (defined($targRef->{'unknown-is-zero'})) {
	$unkIsZero = 1; 
    }

    # things we will need from the params
    my($dslist) = $gQ->param('dslist');
    my($range) = $gQ->param('range');

    # calculate this now for use later
    my(@dslist) = split(',', $dslist);
    my($numDSs) = $#dslist + 1;

    my($gRefDef) = $gCT->configHash($name, 'graph',
				    '--default--', $targRef);
    my($colorRef) = $gCT->configHash($name, 'color', undef, $targRef);
    
    my($width) = graphParam($gRefDef, 'width', 500);
    my($height) = graphParam($gRefDef, 'height', 200);

    my($interlaced) = graphParam($gRefDef, 'interlaced', undef);
    my(@interlaced) = ();
    if (defined($interlaced) && isTrue($interlaced)) {
	Debug('Graph will be interlaced.');
	@interlaced = ( '-i' );
    }

    # Mekket av John M
    my $ymax;
    my $ymin;
    if (defined($gQ->param('yokohoma'))) {
	$ymax = $gQ->param('yokohoma');
	$ymin = 0;
    } else {
	$ymax = graphParam($gRefDef, 'y-max', undef);
	$ymin = graphParam($gRefDef, 'y-min', undef);
    }
    # Til hit

    my ($ymaxlck) = 0;
    my ($yminlck) = 0;

    if (isNonNull($ymax)) {
	$ymaxlck = 1;
    } else {
	$ymaxlck = 0;
    }

    if (isNonNull($ymin)) {
	$yminlck = 1;
    } else {
	$yminlck = 0;
    }

    # ok, lets attempt to handle mtargets.  We need to loop through
    # each of the individual targets and construct the graph command
    # on each of those.  The other initializations should be outside
    # the loop, and the actual graph creation should be after the loop.

    my(@defs) = ();
    my(@cdefs) = ();
    my($yaxis) = "";
    my($bytes) = 0;
    my(@lines) = ();
    my($ct) = 0;
    my($usedArea) = 0;
    my($usedStack) = 1;
    my(@linePushed);
    my(%scaled);
    
    # prepare a dsmap, using the target and targettype dicts
    # we do this outside the loop to keep the DS map from expanding

    my($ttype) = lc($targRef->{'target-type'});
    my($ttRef) = $gCT->configHash($name, 'targettype', $ttype, $targRef);
    my(%dsmap) = makeDSMap($ttRef->{'ds'});

    my($path) = $targRef->{'auto-target-path'};
    my($thisName, $mx);
    foreach $thisName (@mtargets) {
	# this allows local targets to use shorter name
	$thisName = "$path/$thisName" unless ($thisName =~ /^\//);

	my($targRef) = $gCT->configHash($thisName, 'target', undef);
      ConfigTree::Cache::addAutoVariables($thisName, $targRef,
					  $Common::global::gConfigRoot);
	my($thisTname) = $targRef->{'auto-target-name'};

	# take the inst from the url if it's there
	my($inst) = $gQ->param('inst');
	if (defined($inst)) {
	    $targRef->{'inst'} = $inst;
	}

	# now that inst is set right, expand it.
      ConfigTree::Cache::expandHash($targRef, $targRef, \&Warn);

	# Then pick up the values
	# things we pick up form the target dict
	my($rrd) = $targRef->{'rrd-datafile'};

	# use the dslist to create a set of defs/cdefs

	my($ds);
	foreach $ds (split(/,/, $dslist)) {
	    $ds = lc($ds);
	    
	    my($legend, $color, $colorCode, $drawAs, $scale,
	       $colormax, $clmxCode, $drmxAs);
	    
	    my($gRef) = $gCT->configHash($name, 'graph', $ds, $targRef);

	    $legend = graphParam($gRef, 'legend', $ds);

	    if (($isMTarget) && (!$isMTargetsOps)) {
		$legend .= " ($thisTname)";
	    }

	    $color = graphParam($gRef, 'color', nextColor($colorRef));
	    usedColor($color);

	    $drawAs = graphParam($gRef, 'draw-as', 'LINE2');
	    $drawAs = uc($drawAs);

	    $drmxAs = graphParam($gRef, 'draw-max-as', 'LINE2');
	    $drmxAs = uc($drmxAs);

	    # if stack first must be area 
	    if ($drawAs eq "STACK") { 
		if (!$usedStack)  { 
		    $drawAs = 'AREA'; 
		    $usedStack = 1; 
		} 
	    } 

	    # only allow 1 area graph per gif
	    if ($drawAs eq "AREA")  {
		if ($usedArea)  {
		    $drawAs = 'LINE2';
		}  else  {
		    $usedArea = 1;
		}
	    }
	    if ($drmxAs eq "AREA")  {
		if ($usedArea)  {
		    $drmxAs = 'LINE2';
		}  else  {
		    $usedArea = 1;
		}
	    }
	    

	    # Note: the values in the hash %scaled are inserted as
	    # lowercase.

	    $scale = graphParam($gRef, 'scale', undef);
	    if (defined($scale))  {
		$scaled{$ds} = 1;
	    } else {
		$scaled{$ds} = 0;
	    }
	    
	    # this way, we only take the _first_ yaxis that
	    # was offered to us. (If they are trying to graph
	    # different things on one graph, they get what they deserve:
	    # a mis-labeled graph. So there.)
	    if (! $yaxis) {
		$yaxis = graphParam($gRef, 'y-axis', '');
	    }

	    my($ym);
	    
	    
	    $ym = graphParam($gRef, 'y-max');
	    if (isNonNull($ym) && ! $ymaxlck) {
		if (! defined($ymax) || $ym > $ymax) {
		    $ymax = $ym;
		}
	    }

	    $ym = graphParam($gRef, 'y-min');
	    if (isNonNull($ym) && ! $yminlck) {
		if (! defined($ymin) || $ym < $ymin) {
		    $ymin = $ym;
		}
	    }

	    # pick up the value for bytes, if we have not already
	    # found it.
	    if (! $bytes) {
		$bytes = graphParam($gRef, 'bytes', 0);
	    }

	    $colorCode = colorToCode($colorRef, $color);

	    # default to not doing max stuff, since it's still a bit
	    # messy -- due to bad deafault RRA setup, etc.
	    $mx = isTrue(graphParam($gRef, 'show-max', 0));
	    if ($mx) {
		$colormax = graphParam($gRef, 'max-color',
				       nextColor($colorRef));
		usedColor($colormax);
		$clmxCode = colorToCode($colorRef, $colormax);
	    }
	    
	    my($dsidx) = $dsmap{$ds};
	    if (defined($dsidx)) {
		push @defs, "DEF:mx$ct=$rrd:ds$dsidx:MAX" if ($mx);
		push @defs, "DEF:ds$ct=$rrd:ds$dsidx:AVERAGE";

		my($mod) = $ct % $numDSs;
		if (defined($scale)) {
		    push @cdefs, "CDEF:smx$ct=mx$ct,$scale" if ($mx);
		    push @cdefs, "CDEF:sds$ct=ds$ct,$scale";
		    if ($isMTargetsOps) {
			if (!$linePushed[$mod])  {
			    push @lines, "$drmxAs:totmx$mod#$clmxCode:" .
				"Max $legend" if ($mx);
			    push @lines, "$drawAs:tot$mod#$colorCode:$legend";
			    $linePushed[$mod] = 1;
			}
		    }  else  {
			push @lines, "$drmxAs:smx$ct#$clmxCode:" .
			    "Max $legend" if ($mx);
			push @lines, "$drawAs:sds$ct#$colorCode:$legend";
		    }
		} else {
		    if ($isMTargetsOps)  {
			if (!$linePushed[$mod])  {
			    push @lines, "$drmxAs:totmx$mod#$clmxCode:" .
				"Max $legend" if ($mx);
			    push @lines, "$drawAs:tot$mod#$colorCode:$legend";
			    $linePushed[$mod] = 1;
			}
		    }  else  {
			push @lines, "$drmxAs:mx$ct#$clmxCode:" .
			    "Max $legend" if ($mx);
			push @lines, "$drawAs:ds$ct#$colorCode:$legend";
		    }
		}
		$ct++;
	    } else {
		# ERR: Unknown ds-name in dslist.
	    }
	}

	# This is the end of the loop we do for each target
    }

    # This is where we will deal with arithematic operations

    if ($isMTargetsOps)  {

	# first build the cdefs
	my($i) = -1;
	my(@dsnames, @mxnames);
	while ($i < ($ct-1))  {
	    $i++;
	    my($nameme);
	    if ($scaled{lc $dslist[$i % $numDSs]}) {
		$nameme = "sds";
	    } else {
		$nameme = "ds";
	    }
	    push @{$dsnames[$i % $numDSs]}, "$nameme$i";
	    push @{$mxnames[$i % $numDSs]}, "mx$i";
	}
	
	my($j) = 0;
	while ($j < $numDSs)  {
	    my(@d) = @{$dsnames[$j]};
	    my(@f) = @{$mxnames[$j]};

	    # 
	    # Deal with unknown values 
	    # 
	    my($x, @e, @g); 
	    if ($unkIsZero)  { 
		foreach $x (@d)  { 
		    push @e, "$x,UN,0,$x,IF";
		} 
		foreach $x (@f)  { 
		    push @g, "$x,UN,0,$x,IF";
		} 
	    } else { 
		@e = @d;
		@g = @f;
	    }

	    my($str2) = "CDEF:tot$j=" .
		join(',', @e, convertOps($MTargetsOps, $#d+1));
	    push @cdefs, $str2;
	    if ($mx) {
		my($str2) = "CDEF:totmx$j=" .
		    join(',', @g, convertOps($MTargetsOps, $#d+1));
		push @cdefs, $str2;
	    }

	    $j++;
	}

	# we built the line commands earlier
    }

    # add a vrule for each "zero" time:
    #	for a daily graph, zero times are midnights
    #	for a weekly graph, zero times are Monday Midnights
    #	for a monthly graph, zero times are 1st of the month midnight
    #	for a yearly graph, zero times are 1st of the year

    my($vruleColor) = graphParam($gRefDef, 'vrule-color', undef);
    my(@vrules);
    if (defined($vruleColor) and $vruleColor ne 'none') {
	$vruleColor = colorToCode($colorRef, $vruleColor);
	
	my($rangeType) = rangeType($range);
	
	# first, find the time of the most recent zero mark
	my($timeToZeroTime) = 0;
	my($deltaZeroTime) = 0;		# the number of seconds between zero times
	my($now) = time();
	my($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now);

	# find out how many seconds we are past the last zero time
	$timeToZeroTime += $sec;
	$timeToZeroTime += $min * 60;
	$timeToZeroTime += $hour * 60 * 60;
	$deltaZeroTime = 60 * 60 * 24;

	if ($rangeType == $kTypeWeekly) {
	    my($numDaysToMonday) = ($wday - 1);
	    $timeToZeroTime += $numDaysToMonday * 60 * 60 * 24;
	    $deltaZeroTime *= 7;
	}
	if ($rangeType == $kTypeMonthly) {
	    $timeToZeroTime += ($mday - 1) * 60 * 60 * 24;
	    $deltaZeroTime *= 30;
	}
	if ($rangeType == $kTypeYearly) {
	    $timeToZeroTime += $yday * 60 * 60 * 24;
	    # yikes... what about leap year? Ick.
	    $deltaZeroTime *= 365;
	}
	my($zeroTime) = $now - $timeToZeroTime;
	
	# loop and add a vrule for every zero point from
	# now back to ($now - $range). This loop has
	# the nice property that it will skip even the first VRULE,
	# if that wouldn't fit on the graph.
	while ($zeroTime > ($now - $range)) {
	    push @vrules, "VRULE:$zeroTime#$vruleColor:";
	    $zeroTime -= $deltaZeroTime;
	}
    }

    if ($#defs+1 == 0 || $#lines+1 == 0) {
	Error("No graph to make?");
    }

    if (! -d $gCacheDir) {
	mkdir($gCacheDir, 0777);
	chmod(0777, $gCacheDir);
    }

    # this sets -b based on the value of the bytes parameter
    my(@base) = ( '--base', '1000' );
    if ($bytes) {
	@base = ( '--base', '1024' );
    }

    # handle passthrough arguments
    my($pass) = graphParam($gRefDef, 'rrd-graph-args', undef);
    my(@pass) = ();
    if (defined($pass)) {
	@pass = split(/\s+/, $pass);
    }

    my(@rules, $e);
    if ($targRef->{'events'}) {
	foreach $e (split(/\s*,\s*/, $targRef->{'events'})) {
	    my($evRef) = $gCT->configHash($name, 'event', lc($e), $targRef);
	    if ($evRef && $evRef->{'time'}) {
		push @rules, join('', 'VRULE', ':', $evRef->{'time'},
				  '#', colorToCode($colorRef, $evRef->{'color'}),
				  ':', $evRef->{'name'});
	    }
	}
	push @rules, 'COMMENT:\s';
    }

    my(@rigid);

    if (isNonNull($ymin) || isNonNull($ymax)) {
	push @rigid, '-r';
	push @rigid, '-u', $ymax if (isNonNull($ymax));
	push @rigid, '-l', $ymin if (isNonNull($ymin));
    }

    my(@fmt);
    if ($type eq 'gif') {
	@fmt = ('-a', 'GIF');
    } else {
	@fmt = ('-a', 'PNG');
    }

    my(@args) = ($imageName, @fmt, @rigid, @interlaced,
		 @base, @pass, @rules,
		 '--start', "-$range",
		 '--vertical-label', $yaxis,
		 '--width',          $width,
		 '--height',         $height,
		 @defs, @cdefs, @lines, @vrules);

    # we unlink the image so that if there's a failure, we
    # won't accidentally display an old image.
    
    Debug("RRDs::graph " . join(" ", @args));
    unlink($imageName);
    my($avg, $w, $h) = RRDs::graph(@args);
    
    if (my $error = RRDs::error) {
	Warn("Unable to create graph: $error\n");
    }

    my($wh) = graphParam($gRefDef, 'width-hint', undef);
    my($hh) = graphParam($gRefDef, 'height-hint', undef);

    Warn("Actual graph width ($w) differs from width-hint ($wh).")
	if ($w && $wh && ($wh != $w));
    Warn("Actual graph height ($h) differs from height-hint ($hh).")
	if ($h && $hh && ($hh != $h));


    sprayPic($imageName);
    unlink($imageName) if $needUnlink;
}

sub suckPic {
    my($pic) = @_;
    my($res) = '';
    
    if (! open(GIF, "<$pic")) { 
	Warn("Could not open $pic: $!");
	return;
    } else { 
	my($stuff, $len); 
	binmode(GIF);
	while ($len = read(GIF, $stuff, 8192)) { 
	    $res .= $stuff;
	} 
	close(GIF); 
    }

    return $res;
}

sub sprayPic {
    my($pic) = @_;

    # we need to make certain there are no buffering problems here.
    local($|) = 1;

    my($picData) = suckPic($pic);

    if (! defined($picData)) {
	$pic = "images/failed.gif";
	$picData = suckPic($pic);
	if (! defined($picData)) {
	    print $gQ->header('text/plain');
	    print "Could not send failure gif: $!\n";

	    Warn("Could not send failure gif: $!");
	    return;
	}
    }

    if ($pic =~ /png$/i) {
	print $gQ->header('image/png');
    } else {
	print $gQ->header('image/gif');
    }
    print $picData;

    return 1;
}

sub getHTMLDict {
    my($name, $targRef) = @_;

    my($h) = $gCT->configHash($name, 'html');

    $h->{'auto-long-version'} = $Common::global::gVersion;
    my($sv) = ($Common::global::gVersion =~ /Cricket version (.*) \(/);
    $sv = "?" unless ($sv);
    $h->{'auto-short-version'} = $sv;

    $h->{'auto-error'} = $gError;
    $h->{'auto-title'} = '';
    
    # put the contents of the target dict into the HTML dict
    # so that it will be available for expansion
    my($tag);
    foreach $tag (keys(%{$targRef})) {
	$h->{$tag} = $targRef->{$tag};
    }

    return $h;
}

sub htmlHeader {
    my($name, $targRef, $title) = @_;
    my(@headerArgs);

    my($h) = getHTMLDict($name, $targRef);
    $h->{'auto-title'} = $title;
  ConfigTree::Cache::expandHash($h, $h, \&Warn);
    
    print $gQ->header('text/html');
    print "<html>\n";
    print "<head>\n";
    if ($h->{'head'}) {
	print $h->{'head'}, "\n";
    }
    print "<meta name=\"generator\" content=\"",
    $h->{'auto-long-version'}, "\">\n";
    print "</head>\n";
    
    my($body) = $h->{'body-options'};
    $body = "" unless (defined($body));
    
    print "<body $body>\n";
    
    if ($h->{'page-header'}) {
	print $h->{'page-header'}, "\n";
    }

    return;
}

sub htmlFooter {
    my($name, $targRef) = @_;
    #print"$yokohoma<br>";
    my($h) = getHTMLDict($name, $targRef);
  ConfigTree::Cache::expandHash($h, $h, \&Warn);

    if ($h->{'page-footer'}) {
	print $h->{'page-footer'}, "\n";
    }

    print "</body>\n";
    print "</html>\n";
    return;
}

# routines to manage the colors

sub usedColor {
    my($c) = @_;
    my($i, @res);
    foreach $i (@gColors) {
	push @res, $i unless (lc($i) eq lc($c));
    }
    @gColors = @res;
}

sub nextColor {
    my($colorRef) = @_;

    # make the color list, when necessary	
    if (! $gColorInit) {
	if (defined($colorRef)) {
	    my($order) = $colorRef->{'--order--'};
	    if (! defined($order)) {
		@gColors = sort keys %{$colorRef};
	    } else {
		@gColors = split(/\s*,\s*/, $order);
	    }
	    $gColorInit = 1;
	} else {
	    # there are no colors available...
	    @gColors = ();
	}
    }

    my($color) = '00cc00';		# default to green if none left (or given)
    if ($#gColors+1 > 0) {
	$color = $gColors[0];
    }
    return $color;
}

sub colorToCode {
    my($colorRef, $color) = @_;
    my($code) = $colorRef->{$color};
    # if we didn't find one, then use the passed in color, assuming it's
    # a color code...
    $code = $color if (! defined($code));
    return $code;
}

# This routine chooses the right value for a graph parameter;
# If uses the default passed in, then the value from the --default--
# dict, then the value from the dict named after the ds (if given).

sub graphParam {
    my($gRef, $param, $default) = @_;

    $param = lc($param);
    my($res) = $default;

    if (defined($gRef->{$param})) {
        $res = $gRef->{$param};
    }
    return $res;
}

# make the range-size navigation links
sub makeNavLinks {
    my($r, @links);
    my(@r) = ('d', 'w', 'd:w', 'm:y', 'd:w:m:y');
    my(@rName) = ('Hourly', 'Daily', 'Short-Term', 'Long-Term', 'All');
    my($i) = 0;
    foreach $r (@r) {
	$gQ->param('ranges', $r[$i]);
	my($me) = $gQ->self_url();
	push @links, "<a href=\"$me\">$rName[$i]</a>" .
	    "&nbsp;&nbsp;&nbsp;";
	$i++;
    }
    return @links;
}

sub generateImageName {
    my($q, $type) = @_;
    my($param, $md5);

    $md5 = new MD5;

    foreach $param ($q->param()) {
	next if ($param eq 'rand');
	if ($param eq 'cache') {
	    if (lc($q->param($param)) eq 'no') {
		return;
	    }
	}
	$md5->add($param, $q->param($param));
    }
    my($hash) = unpack("H8", $md5->digest());

    return "$gCacheDir/cricket-$hash.$type";
}

sub byFirstVal {
    $a->[0] <=> $b->[0];
}

# fixHome:
# This subroutine is a bit of a hack to properly set $HOME based
# on the assumption that this script will be called via a URL that
# looks like: http://www/~cricket/grapher.cgi. If this doesn't apply
# to your installation, then you might want to simply uncomment the
# brute force method, below.

sub fixHome {

    # brute force:
    # $ENV{'HOME'} = '/path/to/cricket/home';
    # return;

    my($sname) = $gQ->script_name();
    if ($sname =~ /\/~([^\/]*)\//) {
	my($username) = $1;
	my($home) = (getpwnam($username))[7];
	if ($home) {
	    $ENV{'HOME'} = $home;
	} else {
	    Warn("Could not find a home directory for user $username." .
		 "\$HOME is probably not set right.");
	}
    } else {
	Warn("Could not find a username in SCRIPT_NAME. " .
	     "\$HOME is probably not set right.");
    }
}

sub isnan {
    return ($_[0] =~ /^NaN$/);
}

sub convertOps {
    my($mto, $num) = @_;

    if (lc($mto) eq 'sum()') {
	my($i, @plusses);
	for ($i = 0; $i < $num-1; $i++) {
	    push @plusses, '+';
	}
	return join(',', @plusses);
    }

    if (lc($mto) eq 'avg()') {
	my($i, @plusses);
	for ($i = 0; $i < $num-1; $i++) {
	    push @plusses, '+';
	}
	push @plusses, $num;
	push @plusses, '/';
	return join(',', @plusses);
    }

    return $mto;
}

sub makeInstMap {
    my($ins, $inst) = @_;

    return unless $ins;

    my(@ins) = Eval($ins);

    if (! $inst) {
	$inst = '()';
    }

    my($hash) = {};
    my($ct) = 0;
    my($i);

    my(@inst) = Eval($inst);

    if ($#inst+1 > 0) {
	# they gave us an inst array, so match them up one to
	# one.
	foreach $i (@inst) {
	    $hash->{$i} = $ins[$ct++];
	}
	Debug("inst array is: ", join(", ", @inst));
    } else {
	# there's 0 or 1 inst's, so make a simple table
	foreach $i (@ins) {
	    $hash->{$ct++} = $i;
	}
    }

    return $hash;
}

sub prepareValue {
    my($value, $dosi, $bytes, $precision, $space, $unit) = @_;

    if (isnan($value)) {
	return "$value$space$unit";
    }

    my($prefix) = "";
    if ($dosi) {
	($value, $prefix) = si_unit($value, $bytes);
    }

    if ($value ne "?" && $value ne "nan") {
	$value = sprintf("%0.${precision}f", $value);
    }
    return "$value$space$prefix$unit";
}
