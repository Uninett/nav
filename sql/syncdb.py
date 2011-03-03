#!/usr/bin/env python
#
# Copyright (C) 2008, 2011 UNINETT AS
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
"""Program to synchronize NAV database schema changes"""
import sys
import os
import re
from optparse import OptionParser
import subprocess

import psycopg2

from nav.db import get_connection_parameters, get_connection_string

def main():
    """Main program"""
    (options, args) = parse_args()

    verify_password_is_configured()

    if options.create_database:
        create_database()

    sql_dir = os.path.dirname(sys.argv[0])
    sync = Synchronizer(sql_dir)
    try:
        sync.connect()
    except psycopg2.OperationalError, err:
        die(err)

    sync.synchronize()

def parse_args():
    """Builds an OptionParser and returns parsed program arguments"""
    parser = OptionParser(
        description=
        "Synchronizes your NAV database schema with the latest changes.",

        epilog=
        "To create the database, this program assumes it can access the "
        "PostgreSQL client binaries as the postgres superuser.  Either run "
        "this program under the postgres shell account, or set the environment "
        "variables required to connect as the superuser to your PostgreSQL "
        "server (PGHOST, PGPASSWORD, and if necessary, PGPORT)"
        )
    parser.add_option("-c", "--create",
                      action="store_true", dest="create_database",
                      help="Create NAV database")
    return parser.parse_args()

def verify_password_is_configured():
    opts = ConnectionParameters.from_config()
    if not opts.password:
        die("No password configured for %s user in db.conf" % opts.user)

def create_database():
    """Create a database using PostgreSQL command line clients"""
    nav_opts = ConnectionParameters.from_config()
    postgres_opts = ConnectionParameters.for_postgres_user()
    postgres_opts.export(os.environ)

    if not user_exists(nav_opts.user):
        create_user(nav_opts.user, nav_opts.password)

    print "Creating database %s owned by %s" % (nav_opts.dbname, nav_opts.user)
    trap_and_die(subprocess.CalledProcessError,
                 "Failed creating database %s" % nav_opts.dbname,
                 check_call, ["createdb",
                              "--owner=%s" % nav_opts.user,
                              "--encoding=utf-8", nav_opts.dbname])

    trap_and_die(
        subprocess.CalledProcessError,
        "Failed installing PL/pgSQL language in database %s" % nav_opts.dbname,
        check_call,
        ["createlang", "plpgsql", nav_opts.dbname])

def user_exists(username):
    """Returns True if a database user exists.

    Uses the psql command client, so environment should be set.

    """
    try:
        output = popen(
            ["psql",
             "-P", "tuples_only",
             "--no-align",
             "-c", "SELECT rolname FROM pg_roles WHERE rolname='%s'" % username,
             "template1"],
            stdout=subprocess.PIPE).communicate()[0]
    except subprocess.CalledProcessError:
        die("Failed checking for the existence of user %s" % username)

    return username in output

def create_user(username, password):
    """Creates a database user,

    Uses the createdb and psql command line clients, so environment should be
    set.

    """
    print "Creating database user %s" % username
    trap_and_die(subprocess.CalledProcessError,
                 "Failed creating user %s" % username,
                 check_call,
                 ["createuser",
                  "--no-superuser", "--no-createdb",
                  "--no-createrole", username])
    trap_and_die(subprocess.CalledProcessError,
                 "Failed setting %s user's password",
                 check_call,
                 ["psql", "--quiet", "-c",
                  "ALTER USER %s WITH PASSWORD '%s';" % (username, password),
                  "template1"])

NO_SUCH_FILE = 2
NO_PERMISSION = 13
def handle_missing_binaries(func):
    """Decorates func to handle errors from the subprocess module."""
    messages = {
        NO_SUCH_FILE: "Cannot find PostgreSQL client program",
        NO_PERMISSION: "No permission to run PostgreSQL client program"
        }

    def _decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OSError, err:
            program = args[0][0]
            if err.errno in messages:
                die("%s: %s" % (messages[err.errno], program))
            else:
                raise
    return _decorator

@handle_missing_binaries
def check_call(*args, **kwargs):
    """subprocess.check_call with OSError handling"""
    return subprocess.check_call(*args, **kwargs)

@handle_missing_binaries
def popen(*args, **kwargs):
    """subprocess.Popen with OSError handling"""
    return subprocess.Popen(*args, **kwargs)

def trap_and_die(exception, message, func, *args, **kwargs):
    """Traps exception and dies during call to func with *args and **kwargs.

    If exception is caught, message is printed and the process is terminated.

    """
    try:
        return func(*args, **kwargs)
    except exception:
        die(message)

def die(errormsg, exit_code=1):
    """Print errormsg to stderr and terminates process with exit_code"""
    print >> sys.stderr, errormsg
    sys.exit(exit_code)


class Synchronizer(object):
    """Handles schema synchronization for a database."""
    required_namespaces = (
        'manage',
        'profiles',
        'logger',
        'arnold',
        'radius',
        )

    schemas = [
        ('manage', 'manage.sql', 'types.sql', 'snmpoid.sql'),
        ('profiles', 'navprofiles.sql'),
        ('logger', 'logger.sql'),
        ('arnold', 'arnold.sql'),
        ('radius', 'radius.sql'),
        (None, 'indexes.sql'),
        ]

    def __init__(self, sql_dir):
        self.sql_dir = sql_dir
        self.connection = None
        self.cursor = None
        self.connect_options = ConnectionParameters.from_config()

    def connect(self):
        """Connects the synchronizer to the NAV configured database."""
        dsn = str(self.connect_options)
        self.connection = psycopg2.connect(dsn)
        read_committed = 1
        self.connection.set_isolation_level(read_committed)
        self.cursor = self.connection.cursor()

    def synchronize(self):
        """Begins the synchronization process."""
        self.verify_search_path()
        self.verify_namespaces()

        if self.is_empty_database():
            print "Your database appears empty"
            self.install_baseline()

        self.apply_changes()

    def verify_search_path(self):
        """Verifies that the database's search_path contains the namespaces
        NAV needs.

        """
        self.cursor.execute('SHOW search_path')
        search_path = self.cursor.fetchone()[0]
        schemas = [s.strip() for s in search_path.split(',')]

        add_schemas = [wanted
                       for wanted in self.required_namespaces
                       if wanted not in schemas]

        if add_schemas:
            schemas.extend(add_schemas)
            print ("Adding namespaces to %s search_path: %s" %
                   (self.connect_options.dbname, ", ".join(add_schemas)))
            sql = ('ALTER DATABASE "%s" SET search_path TO %s' %
                   (self.connect_options.dbname, ", ".join(add_schemas)))
            self.cursor.execute(sql)
        self.connection.commit()
        self.connect() # must reconnect to activate the new search path

    def verify_namespaces(self):
        """Verifies that the database has the namespaces NAV needs"""
        self.cursor.execute('SELECT nspname FROM pg_namespace')
        namespaces = [r[0] for r in self.cursor.fetchall()]

        add_namespaces = [wanted
                          for wanted in self.required_namespaces
                          if wanted not in namespaces]

        if add_namespaces:
            print ("Adding namespaces to database %s: %s" %
                   (self.connect_options.dbname, ", ".join(add_namespaces)))
            for namespace in add_namespaces:
                self.cursor.execute("CREATE SCHEMA %s" % namespace)
        self.connection.commit()

    def is_empty_database(self):
        """Returns True if the database appears to be empty"""
        return not self.is_legacy_database() and not self.is_schema_logged()

    def is_legacy_database(self):
        """Returns True if the legacy nav_schema_version table is present"""
        self.cursor.execute(
            "SELECT COUNT(*) FROM pg_tables "
            "WHERE tablename = 'nav_schema_version'")
        count = self.cursor.fetchone()[0]
        return count == 1

    def is_schema_logged(self):
        """Returns True if the schema_change_log table is present"""
        self.cursor.execute(
            "SELECT COUNT(*) FROM pg_tables "
            "WHERE tablename = 'schema_change_log'")
        count = self.cursor.fetchone()[0]
        return count == 1

    def install_baseline(self):
        """Installs the baseline NAV schema"""
        print "Installing baseline schema"
        baseline_dir = os.path.join(self.sql_dir, 'baseline')
        for schema in self.schemas:
            namespace = schema[0]
            files = schema[1:]
            if namespace:
                self.cursor.execute('SET search_path TO %s' % namespace)
            for filename in files:
                self.execute_sql_file(os.path.join(baseline_dir, filename))

            self.cursor.execute('RESET search_path')
        self.connection.commit()

    def apply_changes(self):
        """Finds and applies outstanding schema change scripts."""
        (major, minor, point) = self.get_last_applied_change()
        finder = ChangeScriptFinder(self.sql_dir)
        new_scripts = finder.get_updates_since(major, minor, point)

        if new_scripts:
            print "Applying outstanding schema changes"
            for (version, script) in new_scripts:
                self.apply_change_script(version, script)

        else:
            print "No outstanding schema changes."

    def get_last_applied_change(self):
        """Returns the (major, minor, point) of the latest logged change"""
        if self.is_legacy_database():
            return -1, -1, -1

        self.cursor.execute(
            """
            SELECT major, minor, point
            FROM schema_change_log
            ORDER BY date_applied DESC
            LIMIT 1
            """)
        return self.cursor.fetchone()

    def apply_change_script(self, version, script):
        """Applies a specific change script."""
        self.execute_sql_file(script)
        self.log_schema_change(version, script)
        self.connection.commit()

    def log_schema_change(self, version, script):
        """Logs a successful schema change"""
        major, minor, point = version
        basename = os.path.basename(script)
        self.cursor.execute(
            """
            INSERT INTO schema_change_log (major, minor, point, script_name)
            VALUES (%s, %s, %s, %s)
            """,
            (major, minor, point, basename)
            )


    def execute_sql_file(self, filename):
        """Executes a single SQL file.

        Terminates the process if there are errors.

        """
        sql = file(filename, 'rb').read()
        print "%-20s" % (filename + ":"),
        try:
            self.cursor.execute(sql)
        except (psycopg2.DataError, psycopg2.ProgrammingError), err:
            print err
            sys.exit(2)
        else:
            print "OK"

class ChangeScriptFinder(list):
    """Handles locating change scripts"""
    script_pattern = re.compile(
        r"^sc\.(?P<major>\d+)\.(?P<minor>\d+)\.(?P<point>\d+)\.(?P<type>sql)$")

    def __init__(self, sql_dir):
        super(ChangeScriptFinder, self).__init__()
        self.sql_dir = sql_dir
        self._find_change_scripts()

    def _find_change_scripts(self):
        changes_dir = os.path.join(self.sql_dir, 'changes')
        scripts = [os.path.join(changes_dir, f)
                   for f in os.listdir(changes_dir)
                   if self.script_pattern.match(f)]
        self[:] = scripts

    def get_updates_since(self, major, minor, point):
        """Returns a list of schema change scripts available since (major,
        minor,point).

        The list consists of (version, script_file) tuples, and is sorted by
        version numbers.

        """
        scripts = [(self.script_to_version(s), s) for s in self]
        return sorted([(version, s) for (version, s) in scripts
                       if version > (major, minor, point)])

    @classmethod
    def script_to_version(cls, filename):
        """Converts a change script filename to a (major,minor,point) version
        number.

        """
        filename = os.path.basename(filename)
        match = cls.script_pattern.match(filename)
        return (int(match.group('major')),
                int(match.group('minor')),
                int(match.group('point')))


class ConnectionParameters(object):
    """Database Connection parameters"""

    def __init__(self, dbhost, dbport, dbname, user, password):
        self.dbhost = dbhost
        self.dbport = dbport
        self.dbname = dbname
        self.user = user
        self.password = password

    @classmethod
    def from_config(cls):
        """Initializes and returns parameters from NAV's config"""
        return cls(*get_connection_parameters())

    @classmethod
    def from_environment(cls):
        """Initializes and returns parameters from environment vars"""
        params = [os.environ.get(v, None) for v in
                  ('PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD')]
        return cls(*params)

    @classmethod
    def for_postgres_user(cls):
        """Returns parameters suitable for logging in the postgres user using
        PostgreSQL command line clients.
        """
        config = cls.from_config()
        environ = cls.from_environment()

        if not environ.dbhost and config.dbhost != 'localhost':
            environ.dbhost = config.dbhost
        if not environ.dbport and config.dbport:
            environ.dbport = config.dbport

        return environ

    def export(self, environ):
        """Exports parameters to environ.

        Supply os.environ to export to subprocesses.

        """
        added_environ = dict(zip(
            ('PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD'),
            self.as_tuple()))
        for var, val in added_environ.items():
            if val:
                environ[var] = val

    def as_tuple(self):
        """Returns parameters as a tuple"""
        return (self.dbhost,
                self.dbport,
                self.dbname,
                self.user,
                self.password)

    def __str__(self):
        return get_connection_string(self.as_tuple())

if __name__ == '__main__':
    main()
