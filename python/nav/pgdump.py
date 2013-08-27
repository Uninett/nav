#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Program to dump the raw contents of the NAV PostgreSQL database,
with optional data filtering.
"""
import sys
import os
import subprocess
from optparse import OptionParser

from nav.db import get_connection_parameters


STD_DUMP_ARGS = ["--no-privileges", "--disable-triggers"]


def main():
    """Main program"""
    opts, _args = parse_args()

    export_pgvars()
    if opts.exclude or opts.filters:
        writeln("-- navpgdump\n-- args: %r" % sys.argv)

        pg_dump(STD_DUMP_ARGS + ["--schema-only"])
        excluded = set(opts.exclude + opts.filters.keys())
        pg_dump(STD_DUMP_ARGS + ["--data-only"] +
                ["--exclude-table=%s" % tbl for tbl in excluded])

        if opts.filters:
            for table, where in opts.filters.items():
                filtered_dump(table, where)
    else:
        pg_dump(STD_DUMP_ARGS)

    msg("""
NAV database dump completed.
Don't forget to run NAV's syncdb.py after rolling back the dump.
""")


def parse_args():
    """Parses program arguments"""
    parser = _make_optparser()
    (opts, args) = parser.parse_args()

    filters = {}
    for filtr in opts.filters:
        try:
            table, where = filtr.split("=", 1)
            filters[table.strip()] = where.strip()
        except ValueError, err:
            parser.error("invalid filter %r: %s" % (filtr, err))
    opts.filters = filters

    if opts.only_open_cam and "cam" in opts.exclude:
        parser.error("--exclude cam and --only-open-cam are mutually exclusive")
    if opts.only_open_cam and "cam" in opts.filters:
        parser.error("cam filter and --only-open-cam are mutually exclusive")
    if opts.only_open_arp and "arp" in opts.exclude:
        parser.error("--exclude arp and --only-open-arp are mutually exclusive")
    if opts.only_open_cam and "arp" in opts.filters:
        parser.error("arp filter and --only-open-arp are mutually exclusive")

    if opts.only_open_cam:
        opts.filters["cam"] = "end_time >= 'infinity'"
    if opts.only_open_arp:
        opts.filters["arp"] = "end_time >= 'infinity'"

    return opts, args


def _make_optparser():
    parser = OptionParser()
    opt = parser.add_option

    opt("--exclude", action="append", type="string", dest="exclude", default=[],
        metavar="TABLE", help="Exclude TABLE data from dump")
    opt("--only-open-cam", action="store_true", dest="only_open_cam",
        help="Only dump open CAM records")
    opt("--only-open-arp", action="store_true", dest="only_open_arp",
        help="Only dump open ARP records")
    opt("--filter", action="append", type="string", dest="filters", default=[],
        metavar="FILTER", help="Filter a table contents. "
                               "FILTER must match "
                               "<tablename>=<SQL where clause>")
    return parser


def export_pgvars():
    """Exports NAV's db config as PG* environment variables.

    These variables are used by PostgreSQL command line clients to connect to
    a PostgreSQL database.

    """
    var = ('PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD')
    val = get_connection_parameters()
    pgenv = dict(zip(var, val))
    os.environ.update(pgenv)
    return pgenv


def filtered_dump(table, where):
    """Dumps table data using specific WHERE clause for filtering"""
    kwargs = dict(table=table, where=where)
    writeln("ALTER TABLE {table} DISABLE TRIGGER ALL;".format(**kwargs))
    writeln("COPY {table} FROM stdin;".format(**kwargs))
    psql(["-c",
          "COPY (SELECT * FROM {table} WHERE {where}) TO STDOUT".format(
              **kwargs)])
    writeln("\\.\n")
    writeln("ALTER TABLE {table} ENABLE TRIGGER ALL;".format(**kwargs))


def pg_dump(args):
    """Runs pg_dump in a subprocess"""
    return pgcmd('pg_dump', args)


def psql(args):
    """Runs psql in a subprocess"""
    return pgcmd('psql', args, False)


def pgcmd(cmd, args, comment=True):
    """Runs a given PostgreSQL related command, sending its output to stdout"""
    cmd = [cmd]
    cmd.extend(args)
    if comment:
        writeln("-- pgcmd: %r" % cmd)
    subprocess.check_call(cmd)


def writeln(string):
    """Flushes stdout and writes a string + a newline to it"""
    sys.stdout.flush()
    sys.stdout.write(string + "\n")
    sys.stdout.flush()


def msg(message):
    """Writes a message to stderr"""
    strings = [s for s in message.split("\n") if s]
    for string in strings:
        sys.stderr.write("navpgdump: " + string + "\n")
    sys.stderr.flush()

if __name__ == '__main__':
    main()
