#
# Copyright (C) 2008-2011 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Generates the query and makes the report."""

import io
import re
from collections import namedtuple
from operator import attrgetter
from os.path import basename

from psycopg2 import sql

from nav.report.dbresult import DatabaseResult
from nav.report.report import Report

ReportTuple = namedtuple('ReportTuple', 'id title description report_files')


class Generator(object):
    """The maker and controller of the generating of a report"""

    sql = None

    def make_report(self, report_name, config_files, query_dict, config, dbresult):
        """Makes a report

        :param report_name: the name of the report that will be represented
        :param config_files: a list of all configuration files, sorted
        :param queryDict: mutable QueryDict
        :param config: the parsed configuration object, if cached
        :param dbresult: the database result, if cached

        :returns: a formatted report object and search parameters. Also returns
                  a parsed ReportConfig object and a DatabaseResult object to
                  be cached.

        """
        args = dict(query_dict.items())
        advanced = 0

        if not config:
            conf_parser = ConfigParser(config_files)
            parse_ok = conf_parser.parse_report(report_name)
            config = conf_parser.configuration
            if not parse_ok:
                return None, None, None, None, None, None, None

        arg_parser = ArgumentParser(config)

        # Remove non-query arguments
        to_remove = ["export", "page_size", "page_number"]
        for arg in to_remove:
            if arg in args:
                del args[arg]

        # Special cases
        if "exportcsv" in args:
            del args["exportcsv"]
            # Export *everything* in CSV file
            args["offset"] = 0
            args["limit"] = 0

        if "adv" in args:
            if args["adv"]:
                advanced = 1
            del args["adv"]

        (contents, neg, operator) = arg_parser.parse_query(args)

        # Check if there exists a cached database result for this query
        if dbresult:  # Cached
            report = Report(config, dbresult, query_dict)
            report.titlebar = report_name + " - report - NAV"

            return report, contents, neg, operator, advanced

        else:  # Not cached
            dbresult = DatabaseResult(config)
            self.sql = dbresult.sql

            report = Report(config, dbresult, query_dict)
            report.titlebar = report_name + " - report - NAV"

            return report, contents, neg, operator, advanced, config, dbresult


class ReportList(object):
    def __init__(self, config_files):
        self.reports = []
        report_dict = {}

        report_pattern = re.compile(r"^\s*(\S+)\s*\{(.*?)\}$", re.M | re.S | re.I)
        for config_file in config_files:
            contents = io.open(config_file, encoding='utf-8').read()
            for report in report_pattern.findall(contents):
                if report[0] in report_dict:
                    # overwrite configtext, but add config_file to list
                    report_dict[report[0]][0] = report[1]
                    report_dict[report[0]][1].append(basename(config_file))
                else:
                    report_dict[report[0]] = [
                        report[1],
                        [basename(config_file)],
                    ]

        parser = ConfigParser(config_files)

        for report_id, [configtext, report_files] in report_dict.items():
            parser.parse_configuration(configtext)
            report = parser.configuration

            self.reports.append(
                ReportTuple(
                    report_id,
                    report.title or report_id,
                    report.description or "",
                    report_files,
                )
            )

        self.reports.sort(key=attrgetter("id"))

    def get_report_list(self):
        return self.reports


class ConfigParser(object):
    """
    Loads the configuration files, parses the contents, and returns the results as a
    ReportConfig object instance
    """

    def __init__(self, config_files):
        """Loads the configuration files"""
        self.config_files = config_files
        self.config_list = []
        self.configuration = ReportConfig()

    def parse_report(self, report_name):
        """Parses the configuration files and returns a Report object according
        to the report_name.

        :param report_name: the name of the report, tells which part of
                            configuration files to use when making a
                            ReportConfig

        :returns: 1 when there was a report with that name, 0 otherwise

        the access methods will probably fit here
        """

        if not self.config_list:
            self.config_list = [
                io.open(config_file, encoding="utf-8").read()
                for config_file in self.config_files
            ]
        # Report names are matched literally. The name comes from the URL path,
        # so it must never be interpreted as a pattern.
        report_pattern = re.compile(
            r"^\s*" + re.escape(report_name) + r"\s*\{(.*?)\}$", re.M | re.S | re.I
        )
        matches = (report_pattern.search(config) for config in self.config_list)
        matches = [m for m in matches if m]

        for match in matches:
            # Later matches will override earlier matches:
            self.parse_configuration(match.group(1))

        if matches:
            self.configuration.report_id = report_name
            return True
        else:
            return False

    def parse_configuration(self, report_config):
        """Parses the right portion of the configuration and builds a
        ReportConfig object, stone by stone.

        :param report_config: the part of the configuration to build the
                             configuration from

        """

        conf_pattern = re.compile(r'^\s*\$(\S*)\s*\=\s*"(.*?)"\;?', re.M | re.S)
        conf_match = conf_pattern.findall(report_config)

        config = self.configuration

        for line in conf_match:
            key = line[0]
            value = line[1].replace('\n', ' ').strip()

            if key == "sql" or key == "query":
                config.sql = value
            elif key == "title":
                config.title = value
            elif key == "order_by" or key == "sort":
                config.add_trusted_sort(value.split(","))
            elif key == "skjul" or key == "hidden" or key == "hide":
                config.hidden.extend(value.split(","))
            elif key == "ekstra" or key == "extra":
                config.extra.extend(value.split(","))
            elif key == "sum" or key == "total":
                config.sum.extend(value.split(","))
            elif key == "description":
                config.description = value
            else:
                group_pattern = re.compile(r'^(?P<group>\S+?)_(?P<groupkey>\S+?)$')
                match = group_pattern.search(key)

                if match:
                    if match.group('group') == "navn" or match.group('group') == "name":
                        config.name[match.group('groupkey')] = value
                    elif match.group('group') == "url" or match.group('group') == "uri":
                        config.uri[match.group('groupkey')] = value
                    elif (
                        match.group('group') == "forklar"
                        or match.group('group') == "explain"
                        or match.group('group') == "description"
                    ):
                        config.explain[match.group('groupkey')] = value

                else:
                    config.add_trusted_where(key + "=" + value)


class ArgumentParser(object):
    """Handler of the uri arguments"""

    GROUP_PATTERN = re.compile(r"^(?P<group>\S+?)_(?P<groupkey>\S+?)$")

    def __init__(self, configuration):
        """Initializes the configuration"""
        # config is the config obtained from the config file
        self.config = configuration
        self.fields = {}
        self.negated = {}
        self.operator = {}

    def parse_query(self, query):
        """Parses the arguments of the uri, and modifies the
        ReportConfig-object configuration.

        :param query: a dict representing the argument-part of the uri

        """
        self._parse_arguments(query)
        self._parse_fields()

        return self.fields, self.negated, self.operator

    def _parse_arguments(self, query):
        for argument, value in query.items():
            self._parse_single_argument(argument, value)

    def _parse_single_argument(self, arg, value):
        if arg == "title":
            self.config.title = value
        elif arg in ("order_by", "sort"):
            self.config.add_untrusted_sort(value.split(","))
        elif arg in ("skjul", "hidden", "hide"):
            self.config.hidden.extend(value.split(","))
        elif arg in ("ekstra", "extra"):
            # Extra columns come from report configuration only. The argument
            # is still consumed, so a stale one saved in a widget does not fall
            # through to become a column filter.
            pass
        elif arg in ("sum", "total"):
            self.config.sum.extend(value.split(","))
        elif arg == "offset":
            self.config.offset = value
        elif arg == "limit":
            self.config.limit = value
        else:
            if not self._parse_argument_as_group(arg, value) and value:
                self.fields[arg] = value

    def _parse_argument_as_group(self, arg, value):
        match = self.GROUP_PATTERN.search(arg)
        if not match:
            return False

        group = match.group('group')
        group_key = match.group('groupkey')
        if group in ("navn", "name"):
            self.config.name[group_key] = value
        elif group in ("url", "uri"):
            # Links come from report configuration only. The argument is still
            # consumed, so a stale one saved in a widget does not fall through
            # to become a column filter.
            pass
        elif group in ("forklar", "explain", "description"):
            self.config.explain[group_key] = value
        elif group == "not":
            self.negated[group_key] = value
        elif group == "op":
            self.operator[group_key] = value
        else:
            return False

        return True

    def _parse_fields(self):
        for field, value in self.fields.items():
            self._parse_single_field(field, value)

    def _parse_single_field(self, field, value):
        if field not in self.operator:
            self.operator[field] = "eq"
        # Set a default operator
        operat = "="
        negate = "not " if field in self.negated else ""
        multi = False

        if value == "null":
            operat, negate = ("is not", "") if negate else ("is", negate)
            value = None
        else:
            fieldoper = self.operator[field]
            if fieldoper == "eq":
                operat, negate = ("<>", "") if negate else ("=", negate)
            elif fieldoper == "like":
                operat = "ilike"
                value = value.replace("*", "%")
            elif fieldoper == "gt":
                operat, negate = ("<=", "") if negate else (">", negate)

            elif fieldoper == "geq":
                operat, negate = ("<", "") if negate else (">=", negate)
            elif fieldoper == "lt":
                operat, negate = (">=", "") if negate else ("<", negate)
            elif fieldoper == "leq":
                operat, negate = (">", "") if negate else ("<=", negate)
            elif fieldoper == "in":
                if "*" in value:
                    operat = "ilike"
                    value = [elem.replace("*", "%") for elem in value.split(",")]
                    multi = True
                else:
                    operat = "in"
                    value = tuple(value.split(","))

            elif fieldoper == "between":
                operat = "between %s and"
                between = value.split(",")
                if not len(between) == 2:
                    between = value.split(":")
                if len(between) == 2:
                    value = between
                else:
                    self.config.error = (
                        "The arguments to 'between' must be comma- or colon-separated"
                    )
                    value = [None, None]

        term = f"{{col}} {negate}{operat} %s"
        if multi:
            _combinator = " and " if negate else " or "
            term = f"({_combinator.join(term for _ in value)})"
        self.config.add_untrusted_where(field, term)
        if isinstance(value, list):
            self.config.parameters.extend(value)
        else:
            self.config.parameters.append(value)


class ReportConfig(object):
    def __init__(self):
        self.description = ""
        self.explain = {}
        self.extra = []
        self.hidden = []
        self.limit = ""
        self.name = {}
        self.offset = ""
        self.sql = None
        self.sql_select = []
        self.sum = []
        self.title = ""
        self.uri = {}
        self.parameters = []
        self.report_id = ''
        self.error = None
        # Sort and filter clauses are tracked by provenance. The _trusted lists
        # hold admin-defined entries from report.conf. The _untrusted lists hold
        # entries derived from the request query string. They are kept apart so
        # they can be rendered differently when the SQL is built.
        self._order_by_trusted = []
        self._order_by_untrusted = []
        self._where_trusted = []
        self._where_untrusted = []

    @property
    def order_by(self):
        """All sort tokens, untrusted (request) ones first, as plain strings.

        Kept unquoted so UI code (make_table_headers) can match them against
        column names.
        """
        return self._order_by_untrusted + self._order_by_trusted

    def add_trusted_sort(self, tokens):
        """Prepend trusted sort tokens defined in report.conf."""
        self._order_by_trusted = _clean_tokens(tokens) + self._order_by_trusted

    def add_untrusted_sort(self, tokens):
        """Prepend untrusted sort tokens taken from the request query string."""
        self._order_by_untrusted = _clean_tokens(tokens) + self._order_by_untrusted

    def add_trusted_where(self, clause):
        """Append a trusted WHERE clause defined in report.conf."""
        self._where_trusted.append(clause)

    def add_untrusted_where(self, field, term):
        """Register an untrusted WHERE clause from the request query string.

        `field` is the raw column name. `term` is the rest of the clause as a
        template with a `{col}` placeholder. wherestring() quotes `field` and
        fills the template.
        """
        self._where_untrusted.append((field, term))

    def __repr__(self):
        template = (
            "<ReportConfig sql={0!r}, sql_select={1!r}, where={2!r}, "
            "parameters={3!r}, order_by={4!r} >"
        )
        where = self._where_trusted + [
            term.format(col=field) for field, term in self._where_untrusted
        ]
        return template.format(
            self.sql, self.sql_select, where, self.parameters, self.order_by
        )

    def make_sql(self, connection):
        """Build the final SQL and its parameters.

        The connection is used to quote request-supplied identifiers (see
        quote_identifier).
        """
        sql = "SELECT * FROM (%s) AS foo %s%s" % (
            self.escaped_sql,
            self.wherestring(connection),
            self.orderstring(connection),
        )
        return sql, self.parameters

    def wherestring(self, connection):
        clauses = list(self._where_trusted)
        for field, term in self._where_untrusted:
            quoted = quote_identifier(field, connection)
            clauses.append(term.format(col=quoted))
        if clauses:
            return " WHERE " + " AND ".join(clauses)
        else:
            return ""

    def orderstring(self, connection):
        terms = [
            _quoted_sort_term(token, connection) for token in self._order_by_untrusted
        ]
        terms += [_verbatim_sort_term(token) for token in self._order_by_trusted]
        return " ORDER BY %s" % ",".join(terms) if terms else ""

    @property
    def escaped_sql(self):
        """Returns an 'escaped' version of the configured SQL statement.
        Wildcard signs, '%' are doubles, as to not interfer with parameter
        references when feeding the psycopg2 driver.

        """
        if self.sql:
            return self.sql.replace("%", "%%")


def _verbatim_sort_term(token):
    """Render a config-defined ORDER BY term verbatim.

    A leading '-' selects descending order. The name is emitted unquoted, since
    config tokens may be expressions rather than bare column names.
    """
    descending, name = _split_descending(token)
    return "%s DESC" % name if descending else name


def _quoted_sort_term(token, connection):
    """Render a request-supplied ORDER BY term with a quoted identifier.

    A leading '-' selects descending order. The column name is quoted by the
    driver so it cannot inject SQL.
    """
    descending, name = _split_descending(token)
    quoted = quote_identifier(name, connection)
    return "%s DESC" % quoted if descending else quoted


def quote_identifier(name, connection):
    """Quote an untrusted string as a single SQL identifier.

    psycopg2 needs a live connection to quote an identifier. psycopg 3 does not,
    so its migration can drop the argument.

    The driver leaves '%' alone. psycopg2 reads it as a placeholder when
    parameters are bound, so it is doubled here. Without bound parameters the
    doubling survives, and a column named with '%' then fails to match, which is
    safe.
    """
    quoted = sql.Identifier(name).as_string(connection)
    return quoted.replace("%", "%%")


def _split_descending(token):
    """Split a sort token into (descending, name).

    Only a leading '-' marks descending order; any other dash stays in the name.
    """
    descending = token.startswith("-")
    return descending, token[1:] if descending else token


def _clean_tokens(tokens):
    """Strip whitespace from sort tokens and drop empty ones.

    Sort columns are quoted, so a stray space would become part of the column
    name. Empty tokens (from a trailing comma) would quote the empty string.
    """
    return [stripped for token in tokens if (stripped := token.strip())]
