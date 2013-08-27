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
from nav.db import get_connection_parameters


EXCLUDED_TABLES = ["manage.cam", "manage.arp"]
STD_DUMP_ARGS = ["--no-privileges", "--disable-triggers"]
FILTERS = [
    ("manage.cam", "end_time >= 'infinity'"),
    ("manage.arp", "end_time >= 'infinity'"),
]


def main():
    """Main program"""
    export_pgvars()
    pg_dump(STD_DUMP_ARGS + ["--schema-only"])
    pg_dump(STD_DUMP_ARGS + ["--data-only"] +
            ["--exclude-table=%s" % tbl for tbl in EXCLUDED_TABLES])

    for table, where in FILTERS:
        filtered_dump(table, where)


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
        writeln("-- navpgdump: %r" % cmd)
    subprocess.check_call(cmd)


def writeln(string):
    """Flushes stdout and writes a string + a newline to it"""
    sys.stdout.flush()
    sys.stdout.write(string + "\n")
    sys.stdout.flush()


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


if __name__ == '__main__':
    main()
