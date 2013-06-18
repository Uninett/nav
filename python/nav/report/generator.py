#
# Copyright (C) 2003-2005 Norwegian University of Science and Technology
# Copyright (C) 2008-2011 UNINETT AS
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
"""Generates the query and makes the report."""

from nav.report.dbresult import DatabaseResult
from nav.report.report import Report
from urllib import unquote_plus
import nav.db
import re


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
        if "export" in args:
            del args["export"]

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
        contents = file(config_file).read()
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
            self.config = file(self.config_file).read()
            self.config_local = file(self.config_file_local).read()
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
            return True
        
        else:
            return False

    def parse_configuration(self, report_config):
        """Parses the right portion of the configuration and builds a
        ReportConfig object, stone by stone.

        :param report_config: the part of the configuration to build the
                             configuration from

        """

        conf_pattern = re.compile(r'^\s*\$(\S*)\s*\=\s*"(.*?)"\;?', re.M|re.S)
        conf_match = conf_pattern.findall(report_config)

        config = self.configuration

        for line in conf_match:

            key = line[0]
            value = line[1].replace('\n',' ').strip()

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
                        or match.group('group') == "name"
                        ):
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

    def __init__(self, configuration):
        """Initializes the configuration"""
        self.configuration = configuration

    def parse_query(self, query):
        """Parses the arguments of the uri, and modifies the
        ReportConfig-object configuration.

        :param query: a dict representing the argument-part of the uri

        """

        ## config is the configuration obtained from the configuration file
        config = self.configuration
        fields = {}
        nott = {}
        operator = {}
        safere = re.compile("(select|drop|update|delete).*(from|where)", re.I)

        for key, value in query.items():

            if key == "sql" or key == "query":
                #error("Access to make SQL-querys permitted")
                pass
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
            elif key == "offset":
                config.offset = value
            elif key == "limit":
                config.limit = value
            else:
                pattern = re.compile(r"^(?P<group>\S+?)_(?P<groupkey>\S+?)$")
                match = pattern.search(key)

                if match:
                    group = unquote_plus(match.group('group'))
                    group_key = unquote_plus(match.group('groupkey'))
                    if group in ("navn", "name"):
                        config.name[group_key] = value
                    elif group in ("url", "uri"):
                        config.uri[group_key] = value
                    elif group in ("forklar", "explain", "description"):
                        config.explain[group_key] = value
                    elif group == "not":
                        nott[group_key] = value
                    elif group == "op":
                        operator[group_key] = value
                    else:
                        match = None

                if not match:
                    if value:
                        fields[unquote_plus(key)] = unquote_plus(value)

        for key, value in fields.items():

            if not key in operator:
                operator[key] = "eq"
            # Set a default operator
            operat = "="

            if key in nott:
                neg = "not "
            else:
                neg = ""

            if value == "null":
                if neg:
                    operat = "is not"
                    neg = ""
                else:
                    operat = "is"
            else:
                if safere.search(value):
                    config.error = ("You are not allowed to make advanced sql"
                                    " terms")
                else:
                    if operator[key] == "eq":
                        if neg:
                            operat = "<>"
                            neg = ""
                        else:
                            operat = "="
                        value = intstr(value)
                    elif operator[key] == "like":
                        operat = "ilike"
                        value = intstr(value.replace("*","%"))
                    elif operator[key] == "gt":
                        if neg:
                            operat = "<="
                            neg = ""
                        else:
                            operat = ">"
                        value = intstr(value)

                    elif operator[key] == "geq":
                        if neg:
                            operat = "<"
                            neg = ""
                        else:
                            operat = ">="
                        value = intstr(value)
                    elif operator[key] == "lt":
                        if neg:
                            operat = ">="
                            neg = ""
                        else:
                            operat = "<"
                        value = intstr(value)
                    elif operator[key] == "leq":
                        if neg:
                            operat = ">"
                            neg = ""
                        else:
                            operat = "<="
                        value = intstr(value)
                    elif operator[key] == "in":
                        operat = "in"
                        inlist = value.split(",")
                        if inlist:
                            value = "(%s)" % ",".join(intstr(a.strip())
                                                      for a in inlist)
                        else:
                            config.error = ("The arguments to 'in' must be "
                                            "comma separated")

                    elif operator[key] == "between":
                        operat = "between"
                        between = value.split(",")
                        if not len(between) == 2:
                            between = value.split(":")
                        if len(between) == 2:
                            value = "%s and %s" % (intstr(between[0]),
                                                   intstr(between[1]))
                        else:
                            config.error = ("The arguments to 'between' must "
                                            "be comma separated")

            # query is now a unicode QueryDict to dict()...
            # here be DRAGONS, cute shoulder dragons!
            key = key.encode('UTF8')
            config.where.append(key + " " + neg + operat + " " + value)
        return fields, nott, operator


def intstr(arg):
    """Escapes a value for use in an SQL query"""
    return nav.db.escape(arg)


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

    def __repr__(self):
        template = ("ReportConfig(sql({0}) sql_select({1}) where({2}) "
                    "order_by({3}))")
        return template.format(self.sql, self.sql_select, self.where,
                               self.order_by)

    def make_sql(self):
        sql = "SELECT * FROM (%s) AS foo %s%s" % (self.sql,
                                                  self.wherestring(),
                                                  self.orderstring())
        return sql

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
                arg = "%s DESC" % arg.replace("-","")
            return arg

        sort = [_transform(s) for s in self.order_by]
        return " ORDER BY %s" % ",".join(sort) if sort else ""
