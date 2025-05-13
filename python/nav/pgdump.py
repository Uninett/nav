#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
import socket
from optparse import OptionParser
from datetime import datetime

from nav import buildconf
from nav.db import ConnectionParameters
from nav import pgsync

STD_DUMP_ARGS = ["--no-privileges", "--disable-triggers"]


def main():
    """Main program"""
    opts, _args = parse_args()

    export_pgvars()
    writeln("-- navpgdump invoked on %s at %s" % (socket.gethostname(), datetime.now()))

    if opts.exclude or opts.filters:
        writeln("-- args: %r" % sys.argv)

        pg_dump(STD_DUMP_ARGS + ["--schema-only"])
        excluded = set(opts.exclude).union(opts.filters.keys())
        pg_dump(
            STD_DUMP_ARGS
            + ["--data-only"]
            + ["--exclude-table=%s" % tbl for tbl in excluded]
        )

        if opts.filters:
            for table, where in opts.filters.items():
                filtered_dump(table, where)
    else:
        pg_dump(STD_DUMP_ARGS)

    msg(
        """
NAV database dump completed.
Use NAV's navsyncdb command with the -r option to roll back the dump.
"""
    )


def parse_args():
    """Parses program arguments"""
    parser = _make_optparser()
    (opts, args) = parser.parse_args()

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
    parser = OptionParser(
        description="Dumps the NAV PostgreSQL database as plain-text SQL to "
        "stdout, with optional data filtering.",
        version=buildconf.VERSION,
        epilog="The output of the program can be inserted into an empty "
        "PostgreSQL database using the psql program.",
    )
    parser.set_defaults(
        filters={},
        exclude=[],
    )

    opt = parser.add_option
    opt(
        "-e",
        "--exclude",
        action="append",
        type="string",
        dest="exclude",
        metavar="TABLE",
        help="Exclude TABLE data from dump",
    )
    opt(
        "-c",
        "--only-open-cam",
        action="store_true",
        dest="only_open_cam",
        help="Only dump open CAM records",
    )
    opt(
        "-a",
        "--only-open-arp",
        action="store_true",
        dest="only_open_arp",
        help="Only dump open ARP records",
    )
    opt(
        "-f",
        "--filter",
        type="string",
        action="callback",
        callback=_add_filter,
        metavar="FILTER",
        help="Filter a table's contents. "
        "FILTER must match "
        "<tablename>=<SQL where clause>",
    )
    return parser


def _add_filter(_option, _opt, value, parser):
    """Callback to parse a table filter value and add it to the filters dict"""
    try:
        table, where = value.split("=", 1)
        parser.values.filters[table.strip()] = where.strip()
    except ValueError as err:
        parser.error("invalid filter %r: %s" % (value, err))


def export_pgvars():
    """Exports NAV's db config as PG* environment variables"""
    params = ConnectionParameters.from_config()
    params.export(os.environ)


def filtered_dump(table, where):
    """Dumps table data using specific WHERE clause for filtering"""
    kwargs = dict(table=table, where=where)
    search_path = ",".join(pgsync.Synchronizer.required_namespaces)
    writeln("SET search_path TO %s;" % search_path)
    writeln("ALTER TABLE {table} DISABLE TRIGGER ALL;".format(**kwargs))
    writeln("COPY {table} FROM stdin;".format(**kwargs))
    psql(
        ["-c", "COPY (SELECT * FROM {table} WHERE {where}) TO STDOUT".format(**kwargs)]
    )
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
