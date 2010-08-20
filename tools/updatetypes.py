#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2006 UNINETT AS
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
"""This script produces UPDATE statements suitable to update a NAV type table.

Typically, this is used by the upstream authors to create an SQL script that
will bring the type data of users' installations up-to-date.  The script will
access a NAV database by way of the standard db.conf configuration file.
"""
import sys
import nav.db

__author__ = 'Morten Vold <morten.vold@uninett.no>'

selectsql = 'SELECT vendorid, typename, cdp, tftp, cs_at_vlan, chassis, ' \
            'descr, sysobjectid FROM "type"'
updatesql = 'UPDATE "type" SET vendorid=%s, typename=%s, cdp=%s, tftp=%s, ' \
            'cs_at_vlan=%s, chassis=%s, descr=%s ' \
            'WHERE sysobjectid=%s;'

def escape(v):
    """Escape a value before entering it in to the db"""
    if v is None:
        return "NULL"
    else:
        return nav.db.escape(str(v))

def main(args):
    """Main execution flow"""
    conn = nav.db.getConnection('default')

    cursor = conn.cursor()
    cursor.execute(selectsql)
    if cursor.rowcount > 0:
        print "BEGIN;\n"
        for row in cursor.fetchall():
            values = [escape(v) for v in row]
            print updatesql % tuple(values)
        print "\nCOMMIT;"

    conn.close()
    
if __name__ == '__main__':
    main(sys.argv[1:])
