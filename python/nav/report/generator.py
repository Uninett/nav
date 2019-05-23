#
# Copyright (C) 2008-2011 Uninett AS
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
from __future__ import unicode_literals

import io
import re

from nav.report.dbresult import DatabaseResult
from nav.report.report import Report


class Generator(object):
    """The maker and controller of the generating of a report"""
    sql = None

    def make_report(self, report_name, config_file, config_file_local,
                    query_dict, config, dbresult):
        """Makes a report

        :param report_name: the name of the report that will be represented
        :param config_file: the configuration file where the definition resides
        :param config_file_local: the local configuration file where changes to
                                the default definition resides
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
            conf_parser = ConfigParser(config_file, config_file_local)
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

    def __init__(self, config_file):

        self.reports = []

        report_pattern = re.compile(r"^\s*(\S+)\s*\{(.*?)\}$",
                                    re.M | re.S | re.I)
        contents = io.open(config_file, encoding='utf-8').read()
        reports = report_pattern.findall(contents)

        parser = ConfigParser(config_file, None)

        for rep in reports:
            configtext = rep[1]
            rep = rep[0]

            parser.parse_configuration(configtext)
            report = parser.configuration

            self.reports.append((rep, report.title or rep,
                                 report.description or None))

    def get_report_list(self):
        return self.reports


class ConfigParser(object):
    """Loads the configuration files, parses the contents - the local
    configuration the default, and returns the results as a ReportConfig object
    instance

    """

    def __init__(self, config_file, config_file_local):
        """Loads the configuration files"""
        self.config_file = config_file
        self.config_file_local = config_file_local
        self.config = None
        self.config_local = None
        self.configuration = ReportConfig()

    def parse_report(self, report_name):
        """Parses the configuration file and returns a Report object according
        to the report_name.

        :param report_name: the name of the report, tells which part of
                            configuration files to use when making a
                            ReportConfig

        :returns: 1 when there was a report with that name, 0 otherwise

        the access methods will probably fit here
        """

        if self.config is None:
            self.config = io.open(self.config_file, encoding='utf-8').read()
            self.config_local = io.open(self.config_file_local,
                                        encoding='utf-8').read()
        report_pattern = re.compile(r"^\s*" + report_name + r"\s*\{(.*?)\}$",
                                    re.M | re.S | re.I)
        match = report_pattern.search(self.config)
        local_match = report_pattern.search(self.config_local)

        if match:
            self.parse_configuration(match.group(1))
        if local_match:
            # Local report config overloads default report config.
            self.parse_configuration(local_match.group(1))

        if match or local_match:
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
                config.order_by = value.split(",") + config.order_by
            elif key == "skjul" or key == "hidden" or key == "hide":
                config.hidden.extend(value.split(","))
            elif key == "ekstra" or key == "extra":
                config.extra.extend(value.split(","))
            elif key == "sum" or key == "total":
                config.sum.extend(value.split(","))
            elif key == "description":
                config.description = value
            else:
                group_pattern = re.compile(
                    r'^(?P<group>\S+?)_(?P<groupkey>\S+?)$')
                match = group_pattern.search(key)

                if match:
                    if (match.group('group') == "navn"
                        or match.group('group') == "name"):
                        config.name[match.group('groupkey')] = value
                    elif (match.group('group') == "url"
                          or match.group('group') == "uri"
                          ):
                        config.uri[match.group('groupkey')] = value
                    elif (match.group('group') == "forklar"
                          or match.group('group') == "explain"
                          or match.group('group') == "description"
                          ):
                        config.explain[match.group('groupkey')] = value

                else:
                    config.where.append(key + "=" + value)


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
            self.config.order_by = value.split(",") + self.config.order_by
        elif arg in ("skjul", "hidden", "hide"):
            self.config.hidden.extend(value.split(","))
        elif arg in ("ekstra", "extra"):
            self.config.extra.extend(value.split(","))
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
            self.config.uri[group_key] = value
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
                    self.config.error = ("The arguments to 'between' "
                                         "must be comma- or colon-separated")
                    value = [None, None]

        self.config.where.append(field + " " + negate + operat + " %s")
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
        self.order_by = []
        self.sql = None
        self.sql_select = []
        self.sum = []
        self.title = ""
        self.uri = {}
        self.where = []
        self.parameters = []
        self.report_id = ''
        self.error = None

    def __repr__(self):
        template = ("<ReportConfig sql={0!r}, sql_select={1!r}, where={2!r}, "
                    "parameters={3!r}, order_by={4!r} >")
        return template.format(self.sql, self.sql_select, self.where,
                               self.parameters, self.order_by)

    def make_sql(self):
        sql = "SELECT * FROM (%s) AS foo %s%s" % (self.escaped_sql,
                                                  self.wherestring(),
                                                  self.orderstring())
        return sql, self.parameters

    def wherestring(self):
        where = self.where
        if where:
            alias_remover = re.compile(r"(.+)\s+AS\s+\S+", re.I)
            where = [alias_remover.sub(r"\g<1>", word) for word in where]
            return " WHERE " + " AND ".join(where)
        else:
            return ""

    def orderstring(self):
        def _transform(arg):
            if arg.startswith("-"):
                arg = "%s DESC" % arg.replace("-", "")
            return arg

        sort = [_transform(s) for s in self.order_by]
        return " ORDER BY %s" % ",".join(sort) if sort else ""

    @property
    def escaped_sql(self):
        """Returns an 'escaped' version of the configured SQL statement.
        Wildcard signs, '%' are doubles, as to not interfer with parameter
        references when feeding the psycopg2 driver.

        """
        if self.sql:
            return self.sql.replace("%", "%%")
