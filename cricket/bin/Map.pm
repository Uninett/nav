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
#
#    BUGS : If you try to get an interface description from windows computers
#           it returns a 0 byte at the end.
#           ex : snmpwalk windowshost public 1.3.6.1.2.1.2.2.1.2
#                returns : MS TCP Loopback interface00
#           and when you try to compare this with your config file it fails.
#	    The problem has been fixed  with :$name  =~ s/\000//g; in line 169. 
#        
#
package Common::Map;

use snmpUtils;
use Common::Log;
use Common::Util;

# This sets up the target right to sneak through the instance
# evaluation code... we do the actual mapping after the target
# gets expanded.

sub mapPrepareInstance {
    my($target) = @_;
    my($inst) = $target->{'inst'};

    return unless defined($inst);

    Debug("Preparing $inst");
    my($mapkey) = ($inst =~ /^map\((.*)\)$/);
    return unless defined($mapkey);

    # ok, if we got this far, we have a mapkey, so put it into
    # the target dict for later, and fake the inst into an
    # eval-able thing so that we can squeak through the instance
    # eval code.

    $target->{'--mapkey--'} = lc($mapkey);
    $target->{'inst'} = "0";

    return;
}

sub mapInstance {
    my($name, $target) = @_;

    # Don't try to map it if we should be touching it:
    return if defined($target->{'targets'});
    return if defined($target->{'mtargets'});
    if ($Common::global::isCollector) {
        # we only honor collect=false in the collector, since
        # we still need to map it in the grapher so that we
        # have the right instance number on hand in the grapher.
        return if (defined($target->{'collect'}) &&
                   isFalse($target->{'collect'}));
    }

    my($mapkey) = $target->{'--mapkey--'};
    # there's no work to do, so leave.
    return unless (defined($mapkey));

    # if there's no file for some reason, all this fails
    # correctly -- i.e. no meta data is returned.
    my($rrd, $file);
    $file = $target->{'rrd-datafile'};
    $rrd = new RRD::File ( -file => $file );

    # we only want to check the cache if we are coming
    # through here for the first time... see retrieveData
    # the the "second coming" of mapInstance.

    my($metaRef) = $rrd->getMeta();
    if (defined($target->{'--verify-mapkey--'})) {
        # Lose the cached last-inst to force the SNMP walk,
        # since evidently the cached one didn't work.
        delete($metaRef->{'last-inst'});
    }

    # if cached, try to use it, but warn the retriever it needs to
    # verify the inst. if not cached, do a lookup.

    my($cachedInst) = $metaRef->{'last-inst'};
    if (defined($cachedInst)) {
        $target->{'inst'} = $cachedInst;
        $target->{'--verify-mapkey--'} = $mapkey;
    } else {
        my($inst) = mapLookup($name, $target);
        if (! defined($inst)) {
            # set the inst key to null so that our target ends up
            # unresolveable -- i.e. the OID will come out useless
            $target->{'inst'} = '';

            Warn("Failed to map instance for " .
                 $target->{'auto-target-name'} .
                 ". Instance is now set to nothing.");
        } else {
            $target->{'inst'} = $inst;

            # save it for next time
            $metaRef->{'last-inst'} = $inst;
            $rrd->setMeta($metaRef);
        }
    }
}

# lookup does the hard work. mapkey tells us which map entry
# to use. then we use the ds and match tags in that entry
# to find the instance number

sub mapLookup {
    my($name, $target) = @_;

    my($mapkey) = $target->{'--mapkey--'};
    return unless defined($mapkey);

    my($mapRef) = $Common::global::gCT->configHash($name,
                                                   'map', $mapkey, $target);
    my($match) = $mapRef->{'match'};
    if (! defined($match)) {
        Warn("No match tag found in map entry $mapkey");
        return;
    }
    $match = ConfigTree::Cache::expandString($match, $target, \&Warn);

    # this is expected to hold a string like this: comm@host:port
    my($snmp) = $target->{'snmp'};

    if (! defined($main::gMapCache{$snmp}->{$mapkey})) {
        # cache does not exist, so try to load it
        my($baseOID) = $mapRef->{'base-oid'};

        my($oidMap) = $Common::global::gCT->configHash($name, 'oid');
        my($oid) = Common::Util::mapOid($oidMap, $baseOID);

        if (! defined($oid)) {
            Warn("Missing base-oid in $mapkey map entry.");
            return;
        }

        my($hp) = $snmp;
        $hp =~ s/^.*@//;        # remove the community string, if it's there
        # (This keeps it out of the logfiles, which seems like
        # a good idea.)

        Info("Walking $baseOID for $hp to resolve $mapkey mapping");
        my(@ret) = snmpUtils::walk($snmp, $oid);

        my($row);
        foreach $row (@ret) {
            my($inst, $name) = split(':', $row, 2);
	    #Windows interfaces returns a 0 byte at the enda.
	    #The sentence above fix this problem.
	    $name  =~ s/\000//g;
            $main::gMapCache{$snmp}->{$mapkey}->{$name} = $inst;
        }
    }

    # find the inst number -- either by using a regexp match,
    # or by a simple table lookup.

    # does it look like a regexp? (i.e. "/^foo$/") (we allow
    # whitespace, in case they are incompetent with the quote key...
    if ($match =~ /^\s*\/(.*)\/\s*$/) {
        # this is a regexp
        $match = $1;

        Debug("Regexp is /$match/i");

        # this resets the iterator, so the each will get everything
        scalar keys(%{$main::gMapCache{$snmp}->{$mapkey}});

        my($name, $inst);
        while (($name, $inst) = each(%{$main::gMapCache{$snmp}->{$mapkey}})) {
            Debug("  checking: $name");
            if ($name =~ /$match/i) {
                return $inst;
            }
        }
        # didn't match anything... return nothing.
        return;
    } else {
        Debug("Attempting lookup on $match.");
        return $main::gMapCache{$snmp}->{$mapkey}->{$match};
    }
}

1;

# Local Variables:
# mode: perl
# indent-tabs-mode: nil
# tab-width: 4
# perl-indent-level: 4
# End:
