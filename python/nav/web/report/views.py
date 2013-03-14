#
# Copyright (C) 2003-2005 Norwegian University of Science and Technology
# Copyright (C) 2008-2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Handling web requests for the Report subsystem."""


from IPy import IP

from operator import itemgetter
from time import localtime, strftime
import csv
from django.http import HttpResponse, Http404, HttpResponseRedirect
import os
import re
from nav.django.utils import get_account

from nav.models import manage
from django.core.cache import cache

from nav import db
from nav.report.IPtree import getMaxLeaf, buildTree
from nav.report.generator import Generator, ReportList
from nav.report.matrixIPv4 import MatrixIPv4
from nav.report.matrixIPv6 import MatrixIPv6
from nav.report.metaIP import MetaIP
from nav.web.templates.MatrixScopesTemplate import MatrixScopesTemplate
from nav.web.templates.ReportListTemplate import ReportListTemplate
from nav.web.templates.ReportTemplate import ReportTemplate, MainTemplate
import nav.path

config_file_package = os.path.join(nav.path.sysconfdir, "report/report.conf")
config_file_local = os.path.join(nav.path.sysconfdir, "report/report.local.conf")
frontFile = os.path.join(nav.path.sysconfdir, "report/front.html")

def index(request):
    page = MainTemplate()
    request.content_type = "text/html"
    page.path = [("Home", "/"), ("Report", False)]
    page.title = "Report - Index"
    page.content = lambda:file(frontFile).read()
    return HttpResponse(page.respond())

def get_report(request, report_name):
    """Loads and displays a specific reports with optional search arguments"""
    query = _strip_empty_arguments(request)
    export_delimiter = _get_export_delimiter(query)

    if query != request.GET:
        # some arguments were stripped, let's clean up the URL
        return HttpResponseRedirect(
            "{0}?{1}".format(request.META['PATH_INFO'], query.urlencode()))

    return make_report(request, report_name, export_delimiter, query)

def _strip_empty_arguments(request):
    """Strips empty arguments and their related operator arguments from the
    QueryDict in request.GET and returns a new, possibly modified QueryDict.

    """
    query = request.GET.copy()

    deletable = [key for key, value in query.iteritems() if not value.strip()]
    for key in deletable:
        del query[key]
        if "op_{0}".format(key) in query:
            del query["op_{0}".format(key)]
        if "not_{0}".format(key) in query:
            del query["not_{0}".format(key)]

    return query

def _get_export_delimiter(query):
    """Retrieves the CSV export delimiter from a QueryDict, but only if the
    query indicates the CSV export submit button was pressed.

    If the delimiter is invalid, the export-related arguments are stripped
    from the query instance.

    """
    if 'exportcsv' in query and 'export' in query:
        delimiter = query.get('export')

        match = re.search(r"(\,|\;|\:|\|)", delimiter)
        if match:
            return match.group(0)
        else:
            del query['export']
            del query['exportcsv']

def matrix_report(request):

    request.content_type = "text/html"

    argsdict = request.GET or {}

    scope = None
    if argsdict.has_key("scope") and argsdict["scope"]:
        scope = IP(argsdict["scope"])
    else:
        # Find all scopes in database.
        connection = db.getConnection('webfront','manage')
        database = connection.cursor()
        database.execute("SELECT netaddr, description FROM prefix INNER JOIN vlan USING (vlanid) WHERE nettype='scope'")
        databasescopes = database.fetchall()

        if len(databasescopes) == 1:
            # If there is a single scope in the db, display that
            scope = IP(databasescopes[0])
        else:
            # Otherwise, show an error or let the user select from
            # a list of scopes.
            page = MatrixScopesTemplate()
            page.path = [("Home", "/"), ("Report", "/report/"),
                         ("Subnet matrix", False)]
            page.scopes = []
            for scope in databasescopes:
                page.scopes.append(scope)

            return HttpResponse(page.respond())

    # If a single scope has been selected, display that.
    if scope is not None:
        show_unused_addresses = True

        if argsdict.has_key("show_unused_addresses"):
            boolstring = argsdict["show_unused_addresses"]
            if boolstring == "True":
                show_unused_addresses = True
            elif boolstring == "False":
                show_unused_addresses = False

        matrix = None
        tree = buildTree(scope)

        if scope.version() == 6:
            end_net = getMaxLeaf(tree)
            matrix = MatrixIPv6(scope, end_net=end_net)

        elif scope.version() == 4:
            end_net = None

            if scope.prefixlen() < 24:
                end_net = IP("/".join([scope.net().strNormal(),"27"]))
                matrix = MatrixIPv4(scope, show_unused_addresses,
                                    end_net=end_net)

            else:
                max_leaf = getMaxLeaf(tree)
                bits_in_matrix = max_leaf.prefixlen()-scope.prefixlen()
                matrix = MatrixIPv4(scope, show_unused_addresses,
                                    end_net=max_leaf,
                                    bits_in_matrix=bits_in_matrix)

        else:
            raise UnknownNetworkTypeException, "version: " + str(scope.version())
        matrix_template_response = matrix.getTemplateResponse()

        # Invalidating the MetaIP cache to get rid of processed data.
        MetaIP.invalidateCache()

        return HttpResponse(matrix_template_response)



def report_list(request):

    page = ReportListTemplate()
    request.content_type = "text/html"

    # Default config
    report_list = ReportList(config_file_package).get_report_list()
    map(itemgetter(1), report_list)
    report_list = sorted(report_list, key=itemgetter(1))

    # Local config
    report_list_local = ReportList(config_file_local).get_report_list()
    map(itemgetter(1), report_list_local)
    report_list_local = sorted(report_list_local, key=itemgetter(1))

    name = "Report List"
    name_link = "reportlist"
    page.path = [("Home", "/"), ("Report", "/report/"), (name, "/report/" + name_link)]
    page.title = "Report - " + name
    page.report_list = report_list
    page.report_list_local = report_list_local

    return HttpResponse(page.respond())



def make_report(request, report_name, export_delimiter, query_dict):

    # Initiating variables used when caching
    report = contents = neg = operator = adv = dbresult = result_time = None

    query_dict_no_meta = query_dict.copy()
    # Deleting meta variables from uri to help identifying if the report
    # asked for is in the cache or not.
    if 'offset' in query_dict_no_meta: del query_dict_no_meta['offset']
    if 'limit' in query_dict_no_meta: del query_dict_no_meta['limit']
    if 'export' in query_dict_no_meta: del query_dict_no_meta['export']
    if 'exportcsv' in query_dict_no_meta: del query_dict_no_meta['exportcsv']

    helper_remove = dict((key, query_dict_no_meta[key]) for key in query_dict_no_meta)
    for key, val in helper_remove.items():
        if val == "":
            del query_dict_no_meta[key]

    uri_strip = dict((key, query_dict_no_meta[key]) for key in query_dict_no_meta)
    username = get_account(request).login
    mtime_config = os.stat(config_file_package).st_mtime + os.stat(config_file_local).st_mtime
    cache_name = 'report_' + username + '_' + '_' + report_name + str(mtime_config)

    def _fetch_data_from_db():
        (report, contents, neg, operator, adv, config, dbresult) = gen.make_report(report_name, config_file_package, config_file_local, query_dict, None, None)
        if not report:
            raise Http404
        result_time = strftime("%H:%M:%S", localtime())
        cache.set(cache_name, (uri_strip, report, contents, neg, operator, adv, config, dbresult, result_time))
        return (report, contents, neg, operator, adv, result_time)

    gen = Generator()
    # Caching. Checks if cache exists for this user, that the cached report is
    # the one requested and that config files are unchanged.
    if cache.get(cache_name) and cache.get(cache_name)[0] == uri_strip:
        report_cache = cache.get(cache_name)
        dbresult_cache = report_cache[7]
        config_cache = report_cache[6]
        if not config_cache or not dbresult_cache or not report_cache:
            # Might happen if last report was N/A or invalid request, config
            # then ends up being None.
            (report, contents, neg, operator, adv, result_time) = _fetch_data_from_db()
        else:
            (report, contents, neg, operator, adv) = gen.make_report(report_name, None, None, query_dict, config_cache, dbresult_cache)
            result_time = cache.get(cache_name)[8]
            dbresult = dbresult_cache

    else: # Report not in cache, fetch data from DB
        (report, contents, neg, operator, adv, result_time) = _fetch_data_from_db()

    if cache.get(cache_name) and not report:
        raise RuntimeWarning("Found cache entry, but no report. Ooops, panic!")

    if export_delimiter:
        return generate_export(request, report, report_name, export_delimiter)
    else:
        request.content_type = "text/html"
        page = ReportTemplate()
        page.result_time = result_time
        page.report = report
        page.contents = contents
        page.operator = operator
        page.neg = neg

        namename = ""
        if report:
            namename = report.title
            if not namename:
                namename = report_name
            namelink = "/report/"+report_name

        else:
            namename = "Error"
            namelink = False

        page.path = [("Home", "/"), ("Report", "/report/"),
                     (namename, namelink)]
        page.title = "Report - "+namename
        page.old_uri = "{0}?{1}&".format(request.META['PATH_INFO'],
                                         request.GET.urlencode())
        page.adv_block = bool(adv)

        if report:
            #### A maintainable list of variables sent to template
            # Searching
            page.operators = {"eq": "=",
                              "like": "~",
                              "gt": "&gt;",
                              "lt": "&lt;",
                              "geq": "&gt;=",
                              "leq": "&lt;=",
                              "between": "[:]",
                              "in":"(,,)",
                              }
            page.operatorlist = ["eq", "like", "gt", "lt", "geq", "leq",
                                 "between", "in"]
            page.descriptions = {
                "eq": "equals",
                "like": "contains substring (case-insensitive)",
                "gt": "greater than",
                "lt": "less than",
                "geq": "greater than or equals",
                "leq": "less than or equals",
                "between": "between (colon-separated)",
                "in":"is one of (comma separated)",
                }
            # CSV Export dialects/delimiters
            page.delimiters = (",", ";", ":", "|")

        return HttpResponse(page.respond())



def generate_export(request, report, report_name, export_delimiter):
    def _cellformatter(cell):
        if isinstance(cell.text, unicode):
            return cell.text.encode('utf-8')
        else:
            return cell.text

    response = HttpResponse(mimetype="text/x-csv; charset=utf-8")
    response["Content-Type"] = "application/force-download"
    response["Content-Disposition"] = (
        "attachment; filename=report-%s-%s.csv" %
        (report_name, strftime("%Y%m%d", localtime()))
        )
    writer = csv.writer(response, delimiter=str(export_delimiter))

    # Make a list of headers
    header_row = [_cellformatter(cell) for cell in report.table.header.cells]
    writer.writerow(header_row)

    # Make a list of lists containing each cell. Considers the 'hidden' option
    # from the config.
    rows = []
    for row in report.table.rows:
        rows.append([_cellformatter(cell) for cell in row.cells])
    writer.writerows(rows)

    return response



class UnknownNetworkTypeException(Exception): pass
