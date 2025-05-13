#!/usr/bin/env python
#
# Copyright (C) 2008, 2011-2013 Uninett AS
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
"""Program to synchronize NAV database schema changes"""

import sys
import os
import re
from optparse import OptionParser
import subprocess
from textwrap import wrap
from errno import ENOENT, EACCES
from pathlib import Path
import psycopg2

from nav.db import ConnectionParameters
from nav.colors import colorize, print_color
from nav.colors import COLOR_CYAN, COLOR_YELLOW, COLOR_RED, COLOR_GREEN
from nav.util import resource_files, resource_bytes


def main():
    """Main program"""
    (options, _args) = parse_args()

    verify_password_is_configured()

    if options.drop_database:
        drop_database()
    if options.create_database:
        create_database()
    if options.restore_file:
        restore_from_dump(options.restore_file)

    sync = Synchronizer('nav.models', options.apply_out_of_order_changes)
    try:
        sync.connect()
    except psycopg2.OperationalError as err:
        die(err)

    sync.synchronize()


def parse_args():
    """Builds an OptionParser and returns parsed program arguments"""
    parser = OptionParser(
        description="Synchronizes your NAV database schema with the latest changes.",
        epilog="To create the database, this program assumes it can access the "
        "PostgreSQL client binaries as the postgres superuser.  Either run "
        "this program under the postgres shell account, or set the environment "
        "variables required to connect as the superuser to your PostgreSQL "
        "server (PGHOST, PGPASSWORD, and if necessary, PGPORT)",
    )
    parser.add_option(
        "-c",
        "--create",
        action="store_true",
        dest="create_database",
        help="Create NAV database",
    )
    parser.add_option(
        "-r",
        "--restore",
        metavar="FILE",
        action="store",
        type="string",
        dest="restore_file",
        help="Restore a database from the SQL dump in FILE. To "
        "use input from stdin, specify - as the filename.",
    )
    parser.add_option(
        "--drop-database",
        action="store_true",
        dest="drop_database",
        help="Drops the NAV database if it already exists. THIS "
        "IS A DESTRUCTIVE OPERATION!",
    )
    parser.add_option(
        "-o",
        "--out-of-order",
        default=False,
        action="store_true",
        dest="apply_out_of_order_changes",
        help="Apply missing schema changes even when they are "
        "older than the newest applied change",
    )
    return parser.parse_args()


def verify_password_is_configured():
    """Verifies that a password has been configured in db.conf"""
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

    print("Creating database %s owned by %s" % (nav_opts.dbname, nav_opts.user))
    trap_and_die(
        subprocess.CalledProcessError,
        "Failed creating database %s" % nav_opts.dbname,
        check_call,
        ["createdb", "--owner=%s" % nav_opts.user, "--encoding=utf-8", nav_opts.dbname],
    )


def drop_database():
    """Drops an existing database using PostgreSQL command line clients"""
    nav_opts = ConnectionParameters.from_config()
    postgres_opts = ConnectionParameters.for_postgres_user()
    postgres_opts.export(os.environ)

    print("Dropping database %s" % nav_opts.dbname)
    trap_and_die(
        subprocess.CalledProcessError,
        "Failed to drop database %s" % nav_opts.dbname,
        check_call,
        ["dropdb", "--if-exists", nav_opts.dbname],
    )


def restore_from_dump(filename):
    """Restores a NAV database from an SQL dump produced by pg_dump"""
    postgres_opts = ConnectionParameters.for_postgres_user()
    postgres_opts.export(os.environ)
    nav_opts = ConnectionParameters.from_config()

    print("Restoring database %s from file %s" % (nav_opts.dbname, filename))
    trap_and_die(
        subprocess.CalledProcessError,
        "Failed to restore database %s from file %s" % (nav_opts.dbname, filename),
        check_call,
        ["psql", "--quiet", "-f", filename, nav_opts.dbname],
    )


def user_exists(username):
    """Returns True if a database user exists.

    Uses the psql command client, so environment should be set.

    """
    try:
        output = popen(
            [
                "psql",
                "-P",
                "tuples_only",
                "--no-align",
                "-c",
                "SELECT rolname FROM pg_roles WHERE rolname='%s'" % username,
                "template1",
            ],
            stdout=subprocess.PIPE,
        ).communicate()[0]
    except subprocess.CalledProcessError:
        die("Failed checking for the existence of user %s" % username)

    return username in output.decode('UTF-8')


def create_user(username, password):
    """Creates a database user,

    Uses the createdb and psql command line clients, so environment should be
    set.

    """
    print("Creating database user %s" % username)
    trap_and_die(
        subprocess.CalledProcessError,
        "Failed creating user %s" % username,
        check_call,
        ["createuser", "--no-superuser", "--no-createdb", "--no-createrole", username],
    )
    trap_and_die(
        subprocess.CalledProcessError,
        "Failed setting %s user's password",
        check_call,
        [
            "psql",
            "--quiet",
            "-c",
            "ALTER USER %s WITH PASSWORD '%s';" % (username, password),
            "template1",
        ],
    )


def handle_missing_binaries(func):
    """Decorates func to handle errors from the subprocess module."""
    messages = {
        ENOENT: "Cannot find PostgreSQL client program",
        EACCES: "No permission to run PostgreSQL client program",
    }

    def _decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OSError as err:
            program = args[0][0]
            if err.errno in messages:
                die("%s: %s" % (messages[err.errno], program))
            else:
                raise

    return _decorator


@handle_missing_binaries
@colorize(COLOR_YELLOW)
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
    except exception:  # noqa: BLE001
        die(message)


def die(errormsg, exit_code=1):
    """Print errormsg to stderr and terminates process with exit_code"""
    print(errormsg, file=sys.stderr)
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
        ('manage', 'manage.sql', 'types.sql'),
        ('profiles', 'navprofiles.sql'),
        ('logger', 'logger.sql'),
        ('arnold', 'arnold.sql'),
        ('radius', 'radius.sql'),
        ('manage', 'manage2.sql'),
        (None, 'indexes.sql'),
    ]

    def __init__(self, resource_module, apply_out_of_order_changes=False, config=None):
        self.resource_module = resource_module
        self.connection = None
        self.cursor = None
        self.apply_out_of_order_changes = apply_out_of_order_changes
        self.finder = ChangeScriptFinder(self.resource_module)
        if config:
            self.connect_options = config
        else:
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
        self.verify_namespaces()
        self.verify_search_path()
        self.verify_hstore_extension()

        if self.is_empty_database():
            print("Your database appears empty")
            self.install_baseline()

        self.apply_changes()

    def verify_search_path(self):
        """Verifies that the database's search_path contains the namespaces
        NAV needs.

        """
        self.cursor.execute('SHOW search_path')
        search_path = self.cursor.fetchone()[0]
        schemas = [s.strip() for s in search_path.split(',')]

        add_schemas = [
            wanted for wanted in self.required_namespaces if wanted not in schemas
        ]

        if add_schemas:
            print(
                (
                    "Existing namespaces in %s search path: %s. Adding %s."
                    % (
                        self.connect_options.dbname,
                        ", ".join(schemas),
                        ", ".join(add_schemas),
                    )
                )
            )
            schemas.extend(add_schemas)
            sql = 'ALTER DATABASE "%s" SET search_path TO %s' % (
                self.connect_options.dbname,
                ", ".join(schemas),
            )
            self.cursor.execute(sql)
        self.connection.commit()
        self.connect()  # must reconnect to activate the new search path

    def verify_namespaces(self):
        """Verifies that the database has the namespaces NAV needs"""
        self.cursor.execute('SELECT nspname FROM pg_namespace')
        namespaces = [r[0] for r in self.cursor.fetchall()]

        add_namespaces = [
            wanted for wanted in self.required_namespaces if wanted not in namespaces
        ]

        if add_namespaces:
            print(
                (
                    "Adding namespaces to database %s: %s"
                    % (self.connect_options.dbname, ", ".join(add_namespaces))
                )
            )
            for namespace in add_namespaces:
                self.cursor.execute("CREATE SCHEMA %s" % namespace)
        self.connection.commit()

    def is_empty_database(self):
        """Returns True if the database appears to be empty"""
        return not self.is_legacy_database() and not self.is_schema_logged()

    def is_legacy_database(self):
        """Returns True if the legacy nav_schema_version table is present"""
        self.cursor.execute(
            "SELECT COUNT(*) FROM pg_tables WHERE tablename = 'nav_schema_version'"
        )
        count = self.cursor.fetchone()[0]
        return count == 1

    def is_schema_logged(self):
        """Returns True if the schema_change_log table is present"""
        self.cursor.execute(
            "SELECT COUNT(*) FROM pg_tables WHERE tablename = 'schema_change_log'"
        )
        count = self.cursor.fetchone()[0]
        return count == 1

    def verify_hstore_extension(self):
        """
        Installs the hstore extension to dbname if not already present.

        Installation takes place in the namespace mentioned first in the
        search path, which should be the manage namespace in NAV's case.

        """
        postgres_opts = ConnectionParameters.for_postgres_user()
        postgres_opts.export(os.environ)

        self.cursor.execute("SELECT COUNT(*) FROM pg_extension WHERE extname='hstore'")
        (count,) = self.cursor.fetchone()
        if count > 0:
            return

        print(
            "Creating hstore extension in database {0}".format(
                self.connect_options.dbname
            )
        )

        trap_and_die(
            subprocess.CalledProcessError,
            "Failed to install the hstore extension, maybe you need "
            "to run as the postgres superuser?",
            check_call,
            [
                "psql",
                "--quiet",
                "-c",
                "CREATE EXTENSION hstore WITH SCHEMA manage;",
                self.connect_options.dbname,
            ],
        )

    def install_baseline(self):
        """Installs the baseline NAV schema"""
        print("Installing baseline schema")
        for schema in self.schemas:
            namespace = schema[0]
            files = schema[1:]
            if namespace:
                self.cursor.execute('SET search_path TO %s' % namespace)
            for filename in files:
                self.execute_sql_file(os.path.join("sql/baseline", filename))

            self.cursor.execute('RESET search_path')
        self.connection.commit()

    def apply_changes(self):
        """Finds and applies outstanding schema change scripts."""
        applied = self.get_all_applied_changes()
        newest = applied[-1]
        missing = self.finder.get_missing_changes(applied)

        old_versions = [m for m in missing if m < newest]
        new_versions = [m for m in missing if m > newest]

        if old_versions:
            if self.apply_out_of_order_changes:
                print("Applying outstanding schema changes out of order")
                self.apply_versions(old_versions)
            else:
                print(
                    "\n".join(
                        wrap(
                            "There are outstanding schema changes older than the "
                            "newest applied one.  The ordering of schema changes "
                            "may be significant, so I'm not applying these changes "
                            "unless you force me with the -o option:"
                        )
                    )
                )
                print()
                self.print_script_list(old_versions)
                if new_versions:
                    print("\nOutstanding new schema changes:\n")
                    self.print_script_list(new_versions)
                sys.exit(2)

        if new_versions:
            print("Applying outstanding schema changes")
            self.apply_versions(new_versions)

        if not old_versions and not new_versions:
            print("No outstanding schema changes.")

    def print_script_list(self, versions):
        """Prints a list of found change scripts based on a list of versions"""
        available = self.finder.as_dict()
        for version in versions:
            print(available.get(version, version))

    def apply_versions(self, versions):
        """Applies the change scripts for a list of versions"""
        available = self.finder.as_dict()
        for version in versions:
            script = available[version]
            self.apply_change_script(version, script)

    def get_newest_applied_change(self):
        """Returns the (major, minor, point) of the newest logged change"""
        return self.get_all_applied_changes()[-1]

    def get_first_applied_change(self):
        """Returns the (major, minor, point) of the first logged change"""
        return self.get_all_applied_changes()[0]

    def get_all_applied_changes(self):
        """Returns a list of the (major, minor, point) of all logged changes,
        ordered from oldest to newest.

        """
        if self.is_legacy_database():
            return [(-1, -1, -1)]

        self.cursor.execute(
            """
            SELECT major, minor, point
            FROM schema_change_log
            ORDER BY major ASC, minor ASC, point ASC
            """
        )
        return self.cursor.fetchall()

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
            (major, minor, point, basename),
        )

    def execute_sql_file(self, filename):
        """Executes a single SQL file.

        Terminates the process if there are errors.

        """
        sql = self._read_sql_file(filename)
        print_color("%-20s " % (filename + ":"), COLOR_CYAN, newline=False)
        try:
            self.cursor.execute(sql)
        except (psycopg2.DataError, psycopg2.ProgrammingError) as err:
            print_color(str(err) or type(err).__name__, COLOR_RED)
            sys.exit(2)
        else:
            print_color("OK", COLOR_GREEN)

    def _read_sql_file(self, filename):
        return resource_bytes(self.resource_module, filename)


class ChangeScriptFinder(list):
    """Handles locating change scripts"""

    script_pattern = re.compile(
        r"^sc\.(?P<major>\d+)\.(?P<minor>\d+)\.(?P<point>\d+)\.(?P<type>sql)$"
    )

    def __init__(self, resource_module):
        super(ChangeScriptFinder, self).__init__()
        self.resource_module = resource_module
        self._find_change_scripts()

    def _find_change_scripts(self):
        changes_dir = Path('sql/changes')
        scripts = []
        sql_path = resource_files(self.resource_module).joinpath(changes_dir)
        for path in sql_path.iterdir():
            filename = path.name
            if self.script_pattern.match(str(filename)):
                scripts.append(str(changes_dir / filename))
        self[:] = scripts

    def get_missing_changes(self, versions):
        """Returns a list of available schema changes that are missing from
        the versions list.

        Version scripts older than the oldest version in the versions lists
        will not be considered.

        """
        applied = sorted(versions)
        oldest = applied[0]
        scripts = self.as_dict()
        available = sorted(ver for ver in scripts.keys() if ver >= oldest)

        return sorted(set(available).difference(applied))

    def as_dict(self):
        """Returns the contents of the script list as a dictionary.

        :returns: {(major, minor, point): 'scriptfile'}

        """
        return dict((self.script_to_version(script), script) for script in self)

    @classmethod
    def script_to_version(cls, filename):
        """Converts a change script filename to a (major,minor,point) version
        number.

        """
        filename = os.path.basename(filename)
        match = cls.script_pattern.match(filename)
        return (
            int(match.group('major')),
            int(match.group('minor')),
            int(match.group('point')),
        )


if __name__ == '__main__':
    main()
