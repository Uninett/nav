#!/usr/bin/env python
# -*- coding: ISO8859-1 -*-
#
# Copyright 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Dumps core information from NAV to textfiles importable by editDB.
#
# Author: Stian Søiland <stain@itea.ntnu.no>
#
"""Dumps core information from NAV to textfiles importable by editDB."""

import sys
# Backup! =) 
sys._stdout = sys.stdout
from nav.db import manage

SEPARATOR=":"

def warn(msg):
    sys.stderr.write(msg + "\n")

def fail(resultcode, msg):
    warn(msg)
    sys.exit(resultcode)

def header(header):
    header = header.replace(":", SEPARATOR)
    print header

def lineout(line):
    # Remove any : in strings
    newline = [x.replace(SEPARATOR, "") for x in line]
    print SEPARATOR.join(newline)

class Handlers:
    def netbox(self):
        header("#roomid:ip:orgid:catid:[ro:serial:rw:function:subcat1:subcat2..]")
        allFunctions = manage.Netboxinfo.getAll(where="var='function'")
        for box in manage.Netbox.getAllIterator():
            line = []
            line.append(box.room.roomid)
            line.append(box.ip)
            line.append(box.org.orgid)
            line.append(box.cat.catid)
            line.append(box.ro or "")
            line.append(box.device.serial or box.sysname)
            line.append(box.rw or "")
            functions = [f.val for f in allFunctions 
                         if f.netbox == box]
            functions = str.join(", ", functions)
            line.append(functions)
            categories = box.getChildren(manage.Netboxcategory)
            categories = [cat.category for cat in categories]
            categories.sort()
            line.extend(categories)
            lineout(line)

    def org(self):
        header("#orgid[:parent:description:optional1:optional2:optional3]")
        for org in manage.Org.getAllIterator():
            line = []
            line.append(org.orgid)
            line.append(org.parent or "")
            line.append(org.descr or "")
            line.append(org.opt1 or "")
            line.append(org.opt2 or "")
            line.append(org.opt3 or "")
            lineout(line)
 
    def subcat(self):
        header("#subcatid:catid:description")
        for subcat in manage.Subcat.getAllIterator():
            line = []
            line.append(subcat.subcatid)
            line.append(subcat.cat.catid)
            line.append(subcat.descr)
            lineout(line)
  
    def usage(self):
        header("#usageid:descr")
        for usage in manage.Usage.getAllIterator():
            line = []
            line.append(usage.usageid)
            line.append(usage.descr)
            lineout(line)
   
    def location(self):
        header("#locationid:descr")
        for location in manage.Location.getAllIterator():
            line = []         
            line.append(location.locationid)
            line.append(location.descr)
            lineout(line)
    
    def room(self):
        header("#roomid[:locationid:descr:opt1:opt2:opt3:opt4]")
        for room in manage.Room.getAllIterator():         
            line = []         
            line.append(room.roomid)
            line.append(room.location.locationid)
            line.append(room.descr or "")
            line.append(room.opt1 or "")
            line.append(room.opt2 or "")
            line.append(room.opt3 or "")
            line.append(room.opt4 or "")
            lineout(line)
   
    def type(self):
        header("#vendorid:typename:sysoid[:description:frequency:cdp:tftp]")
        for type in manage.Type.getAllIterator():
            line = []
            line.append(type.vendor.vendorid)
            line.append(type.typename)
            line.append(type.sysobjectid)
            line.append(type.descr)
            line.append(str(type.frequency))
            line.append(str(type.cdp))
            line.append(str(type.tftp))
            lineout(line)

    def vendor(self):
        header("#vendorid")
        for vendor in manage.Vendor.getAllIDs():
            line = [vendor]
            lineout(line)
   
    def product(self):
        header("#vendorid:productno[:description]")
        for product in manage.Product.getAllIterator():
            line = []
            line.append(product.vendor.vendorid)
            line.append(product.productno)
            line.append(product.descr or "")
            lineout(line)

    def prefix(self):
        header("#prefix/mask:nettype[:orgid:netident:usage:description:vlan]")
        for prefix in manage.Prefix.getAllIterator():
            vlan = prefix.vlan
            line = []
            line.append(prefix.netaddr)
            line.append(vlan.nettype.nettypeid)
            line.append(vlan.org and vlan.org.orgid or "")
            line.append(vlan.usage and vlan.usage.usageid or "")
            line.append(vlan.description or "")
            line.append(vlan.vlan and str(vlan.vlan) or "")
            lineout(line)

    def service(self):
        global SEPARATOR
        old_sep = SEPARATOR
        if SEPARATOR==":":
            warn("Not smart to use : as separator for services, using ;")
            SEPARATOR=";"
        header("#ip/sysname:handler[:arg=value[:arg=value]]")
        for service in manage.Service.getAllIterator():
            line = []            
            line.append(service.netbox.sysname)
            line.append(service.handler)
            properties = ["%s=%s" % (p.property, p.value)
                          for p in service.getChildren(manage.Serviceproperty)]
            line.extend(properties)                  
            lineout(line)
        SEPARATOR = old_sep

def main():
    try:
        # Should
        from optparse import OptionParser
    except ImportError:
        try:
            from optik import OptionParser
        except ImportError:
            fail(1, "optik 1.4.1 or Python 2.3 or later needed "
                    "for command line) usage.\n"
                    "Download optik from "
                    "http://optik.sourceforge.net/ or upgrade Python.")
    usage = "usage: %prog [options]\n" \
            "Dumps NAV database to importable files."
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--seperator", dest="separator",
                      help="use SEP to seperate fields in output, "
                           "[default :]",
                      metavar="SEP", default=":")
    parser.add_option("-t", "--table", dest="table",
                      help="dump data from TABLE",
                      default="")
    parser.add_option("-o", "--output", dest="output",
                      help="dump data to FILE instead of stdout",
                      metavar="FILE") 
    parser.add_option("-a", "--all", dest="all", action="store_true",
                      help="dump all tables to files named TABLE.txt")
    (options, args) = parser.parse_args()

    if options.separator:
        global SEPARATOR
        SEPARATOR = options.separator
    
    if options.all:
        handlers = Handlers()
        for key in Handlers.__dict__.keys():
            if key[0] == "_":
                continue
            file = key + ".txt"    
            sys.stdout = sys._stdout    
            print "Dumping " + file
            try:
                # We're lazy and are using print all the way 
                sys.stdout = open(file, "w")
            except IOError, e:
                fail(2, "Could not open file %s: %s" % 
                        (options.output, e))
            handler = getattr(handlers, key)
            handler()
        sys.exit(0)      

    if options.output:
        try:
            # We're lazy and are using print all the way 
            sys.stdout = open(options.output, "w")
        except IOError, e:
            fail(2, "Could not open file %s: %s" % 
                    (options.output, e))
        except TypeError:
            fail(2, "You stupid moron")    
    
    handler = getattr(Handlers(), options.table, "")
    if not handler:
        tables = [table for table in Handlers.__dict__.keys() 
                  if not table[0] == "_"]
        tables.sort()              
        tables = str.join("\n", tables)
        fail(3, "You must select a valid table. Valid tables are:\n" + tables)

    # And run the handler
    handler()

if __name__ == "__main__":
    main()
