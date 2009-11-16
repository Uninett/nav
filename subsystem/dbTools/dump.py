#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright (C) 2004,2009 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Dumps core information from NAV to textfiles importable by editDB."""


import sys
# Backup! =) 
sys._stdout = sys.stdout
from nav.models import manage
import nav.models.service

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
    print SEPARATOR.join(newline).encode('utf-8')

class Handlers:
    def netbox(self):
        header("#roomid:ip:orgid:catid:[ro:serial:rw:function:subcat1:subcat2..]")
        allFunctions = manage.NetboxInfo.objects.filter(key='function')
        for box in manage.Netbox.objects.all():
            line = []
            line.append(box.room_id)
            line.append(box.ip)
            line.append(box.organization_id)
            line.append(box.category_id)
            line.append(box.read_only or "")
            line.append(box.device.serial or box.sysname)
            line.append(box.read_write or "")
            functions = allFunctions.filter(netbox=box)
            functions = str.join(", ", functions)
            line.append(functions)
            categories = box.subcategories.all()
            categories = [cat.id for cat in categories]
            categories.sort()
            line.extend(categories)
            lineout(line)

    def org(self):
        header("#orgid[:parent:description:optional1:optional2:optional3]")
        for org in manage.Organization.objects.all():
            line = []
            line.append(org.id)
            if org.parent:
                parent = org.parent.id
            else:
                parent = ""
            line.append(parent)
            line.append(org.description or "")
            line.append(org.optional_1 or "")
            line.append(org.optional_2 or "")
            line.append(org.optional_3 or "")
            lineout(line)
 
    def subcat(self):
        header("#subcatid:catid:description")
        for subcat in manage.Subcategory.objects.all():
            line = []
            line.append(subcat.id)
            line.append(subcat.category.id)
            line.append(subcat.description)
            lineout(line)
  
    def usage(self):
        header("#usageid:descr")
        for usage in manage.Usage.objects.all():
            line = []
            line.append(usage.id)
            line.append(usage.description)
            lineout(line)
   
    def location(self):
        header("#locationid:descr")
        for location in manage.Location.objects.all():
            line = []         
            line.append(location.id)
            line.append(location.description)
            lineout(line)
    
    def room(self):
        header("#roomid[:locationid:descr:opt1:opt2:opt3:opt4]")
        for room in manage.Room.objects.all():         
            line = []         
            line.append(room.id)
            line.append(room.location.id)
            line.append(room.description or "")
            line.append(room.optional_1 or "")
            line.append(room.optional_2 or "")
            line.append(room.optional_3 or "")
            line.append(room.optional_4 or "")
            lineout(line)
   
    def type(self):
        header("#vendorid:typename:sysoid[:description:frequency:cdp:tftp]")
        for type in manage.NetboxType.objects.all():
            line = []
            line.append(type.vendor.id)
            line.append(type.name)
            line.append(type.sysobject)
            line.append(type.description)
            line.append(str(type.frequency))
            line.append(str(type.cdp or False))
            line.append(str(type.tftp or False))
            lineout(line)

    def vendor(self):
        header("#vendorid")
        for vendor in manage.Vendor.objects.all():
            line = [vendor.id]
            lineout(line)
   
    def product(self):
        header("#vendorid:productno[:description]")
        for product in manage.Product.objects.all():
            line = []
            line.append(product.vendor.id)
            line.append(product.product_number)
            line.append(product.description or "")
            lineout(line)

    def prefix(self):
        header("#prefix/mask:nettype[:orgid:netident:usage:description:vlan]")
        for prefix in Prefix.objects.all():
            vlan = prefix.vlan
            line = []
            line.append(prefix.net_address)
            line.append(vlan.net_type.id)
            line.append(vlan.organization and vlan.organization.id or "")
            line.append(vlan.net_ident or "")
            line.append(vlan.usage and vlan.usage.id or "")
            line.append(vlan.description or "")
            line.append(vlan.vlan and str(vlan.vlan) or "")
            lineout(line)


    def service(self):
        global SEPARATOR
        old_sep = SEPARATOR
        if SEPARATOR==":":
            # (since it is used in URLs for HTTP checker and we don't
            # have a defined way to escape it) 
            warn("Not smart to use : as separator for services, using ;")
            SEPARATOR=";"
        header("#ip/sysname:handler[:arg=value[:arg=value]]")
        allProperties = nav.models.service.ServiceProperty.objects.all()
        for service in nav.models.service.Service.objects.all():
            line = []            
            line.append(service.netbox.sysname)
            line.append(service.handler)
            properties = ["%s=%s" % (p.property, p.value)
                          for p in allProperties if p.service == service]
            line.extend(properties)                  
            lineout(line)
        SEPARATOR = old_sep

def main():
    try:
        # Available from Python 2.3
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
        parser.print_help()
        tables = [table for table in Handlers.__dict__.keys() 
                  if not table[0] == "_"]
        tables.sort()              
        tables = str.join(" ", tables)
        fail(3, "\nERROR: You must select a valid table. Valid tables are:\n" + tables)

    # And run the handler
    handler()

if __name__ == "__main__":
    main()
