#
# Copyright (C) 2003-2005 Norwegian University of Science and Technology
# Copyright (C) 2008-2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Handling web requests for the Report subsystem."""


from IPy import IP

from operator import itemgetter
from time import localtime, strftime
import csv
import os
import re

# this is just here to make sure Django finds NAV's settings file
# pylint: disable=W0611
from django.core.cache import cache
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.db import connection

from nav.report.IPtree import getMaxLeaf, buildTree
from nav.report.generator import Generator, ReportList
from nav.report.matrixIPv4 import MatrixIPv4
from nav.report.matrixIPv6 import MatrixIPv6
from nav.report.metaIP import MetaIP
import nav.path

from nav.web.navlets import add_navlet


CONFIG_FILE_PACKAGE = os.path.join(nav.path.sysconfdir, "report/report.conf")
CONFIG_FILE_LOCAL = os.path.join(nav.path.sysconfdir,
                                 "report/report.local.conf")
FRONT_FILE = os.path.join(nav.path.sysconfdir, "report/front.html")
DEFAULT_PAGE_SIZE = 25


def index(request):
    """Report front page"""

    context = {
        'title': 'Report - Index',
        'navpath': [('Home', '/'), ('Report', False)],
        'heading': 'Report Index'
    }

    with open(FRONT_FILE, 'r') as f:
        context['index'] = f.read()

    return render_to_response("report/index.html", context,
                              RequestContext(request))


def get_report_for_widget(request, report_name):
    """Fetches a report for display in a widget"""
    query = _strip_empty_arguments(request)
    export_delimiter = _get_export_delimiter(query)
    username = request.account.login

    context = make_report(username, report_name, export_delimiter, query)
    return render(request, 'report/frag_report_table.html', context)


def get_report(request, report_name):
    """Loads and displays a specific reports with optional search arguments"""
    query = _strip_empty_arguments(request)
    export_delimiter = _get_export_delimiter(query)
    username = request.account.login

    if query != request.GET:
        # some arguments were stripped, let's clean up the URL
        return HttpResponseRedirect(
            "{0}?{1}".format(request.META['PATH_INFO'], query.urlencode()))

    context = make_report(username, report_name, export_delimiter, query)
    # Magic flag for adding sorting links to table
    context['add_sort_links'] = True
    return render_to_response('report/report.html', context,
                              RequestContext(request))


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

        match = re.search(r"(,|;|:|\|)", delimiter)
        if match:
            return match.group(0)
        else:
            del query['export']
            del query['exportcsv']


def matrix_report(request):
    """Subnet matrix view"""

    show_unused = request.GET.get('show_unused_addresses', False)

    context = {
        'navpath': [
            ('Home', '/'),
            ('Report', '/report/'),
            ('Subnet matrix', False)
        ],
        'show_unused': show_unused
    }

    if 'scope' not in request.GET:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT netaddr, description
            FROM prefix
            INNER JOIN vlan USING (vlanid)
            WHERE nettype='scope'
        """.strip())

        if cursor.rowcount == 1:
            # Id there is only one scope in the database,
            # display that scope
            scope = IP(cursor.fetchone()[0])
        else:
            # Else let the user select from a list
            scopes = cursor.fetchall()
            context['scopes'] = scopes
            return render_to_response(
                'report/matrix.html',
                context,
                context_instance=RequestContext(request))
    else:
        scope = IP(request.GET.get('scope'))

    tree = buildTree(scope)
    if scope.version() == 6:
        end_net = getMaxLeaf(tree)
        matrix = MatrixIPv6(scope, end_net=end_net)
    elif scope.version() == 4:
        if scope.prefixlen() < 24:
            end_net = IP(scope.net().strNormal() + '/30')
            matrix = MatrixIPv4(scope, show_unused, end_net=end_net,
                                bits_in_matrix=6)
        else:
            max_leaf = getMaxLeaf(tree)
            bits_in_matrix = max_leaf.prefixlen() - scope.prefixlen()
            matrix = MatrixIPv4(
                scope,
                show_unused,
                end_net=max_leaf,
                bits_in_matrix=bits_in_matrix)
    else:
        raise UnknownNetworkTypeException(
            'version: ' + str(scope.version))

    # Invalidating the MetaIP cache to get rid of processed data.
    MetaIP.invalidateCache()

    matrix.build()

    hide_content_for_colspan = []
    if scope.version() == 4:
        hide_content_for_colspan = [1, 2, 4]

    context.update({
        'matrix': matrix,
        'sub': matrix.end_net.prefixlen() - matrix.bits_in_matrix,
        'ipv4': scope.version() == 4,
        'hide_for': hide_content_for_colspan
    })

    return render_to_response(
        'report/matrix.html',
        context,
        context_instance=RequestContext(request))


def report_list(request):
    """Automated report list view"""

    key = itemgetter(1)

    reports = ReportList(CONFIG_FILE_PACKAGE).get_report_list()
    reports.sort(key=key)

    reports_local = ReportList(CONFIG_FILE_LOCAL).get_report_list()
    reports_local.sort(key=key)

    context = {
        'title': 'Report - Report List',
        'navpath': [
            ('Home', '/'),
            ('Report', '/report/'),
            ('Report List', '/report/reportlist'),
        ],
        'heading': 'Report list',
        'report_list': reports,
        'report_list_local': reports_local,
    }

    return render_to_response('report/report_list.html', context,
                              RequestContext(request))


def make_report(username, report_name, export_delimiter, query_dict,
                paginate=True):
    """Makes a report

    :param page_size: The number of rows shown for each page
    :param paginate: Introduced to be able to toggle display of the paginate
                     elements. Used in the widget rendering.
    """
    # Initiating variables used when caching
    report = contents = neg = operator = adv = result_time = None

    if not report_name:
        return None

    # Pagination related variables
    page_number = query_dict.get('page_number', 1)
    page_size = query_dict.get('page_size', DEFAULT_PAGE_SIZE)
    query_string = "&".join(["%s=%s" % (x, y)
                             for x, y in query_dict.iteritems()
                             if x != 'page_number'])

    query_dict_no_meta = query_dict.copy()
    # Deleting meta variables from uri to help identifying if the report
    # asked for is in the cache or not.
    meta_to_delete = ['offset', 'limit', 'export', 'exportcsv', 'page_number',
                      'page_size']
    for meta in meta_to_delete:
        if meta in query_dict_no_meta:
            del query_dict_no_meta[meta]

    helper_remove = dict((key, query_dict_no_meta[key])
                         for key in query_dict_no_meta)
    for key, val in helper_remove.items():
        if val == "":
            del query_dict_no_meta[key]

    uri_strip = dict((key, query_dict_no_meta[key])
                     for key in query_dict_no_meta)
    mtime_config = (os.stat(CONFIG_FILE_PACKAGE).st_mtime +
                    os.stat(CONFIG_FILE_LOCAL).st_mtime)
    cache_name = 'report_%s__%s%s' % (username, report_name, mtime_config)

    def _fetch_data_from_db():
        (report, contents, neg, operator, adv, config, dbresult) = (
            gen.make_report(report_name, CONFIG_FILE_PACKAGE,
                            CONFIG_FILE_LOCAL, query_dict, None, None))
        if not report:
            raise Http404
        result_time = strftime("%H:%M:%S", localtime())
        cache.set(cache_name,
                  (uri_strip, report, contents, neg, operator, adv, config,
                   dbresult, result_time))
        return report, contents, neg, operator, adv, result_time

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
            (report, contents, neg, operator, adv,
             result_time) = _fetch_data_from_db()
        else:
            (report, contents, neg, operator, adv) = (
                gen.make_report(report_name, None, None, query_dict,
                                config_cache, dbresult_cache))
            result_time = cache.get(cache_name)[8]

    else:  # Report not in cache, fetch data from DB
        (report, contents, neg, operator, adv,
         result_time) = _fetch_data_from_db()

    if cache.get(cache_name) and not report:
        raise RuntimeWarning("Found cache entry, but no report. Ooops, panic!")

    if export_delimiter:
        return generate_export(report, report_name, export_delimiter)
    else:

        paginator = Paginator(report.table.rows, page_size)
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            page_number = 1
            page = paginator.page(page_number)

        context = {
            'heading': 'Report',
            'result_time': result_time,
            'report': report,
            'paginate': paginate,
            'page': page,
            'current_page_range': find_page_range(page_number,
                                                  paginator.page_range),
            'query_string': query_string,
            'contents': contents,
            'operator': operator,
            'neg': neg,
        }

        if report:
            # A maintainable list of variables sent to the template

            context['operators'] = {
                'eq': '=',
                'like': '~',
                'gt': '&gt;',
                'lt': '&lt;',
                'geq': '&gt;=',
                'leq': '&lt;=',
                'between': '[:]',
                'in': '(,,)',
            }

            context['operatorlist'] = [
                'eq', 'like', 'gt', 'lt',
                'geq', 'leq', 'between', 'in'
            ]

            context['descriptions'] = {
                'eq': 'equals',
                'like': 'contains substring (case-insensitive)',
                'gt': 'greater than',
                'lt': 'less than',
                'geq': 'greater than or equals',
                'leq': 'less than or equals',
                'between': 'between (colon-separated)',
                'in': 'is one of (comma separated)',
            }

            context['delimiters'] = (',', ';', ':', '|')

            page_name = report.title or report_name
            page_link = '/report/{0}'.format(report_name)
        else:
            page_name = "Error"
            page_link = False

        navpath = [('Home', '/'),
                   ('Report', '/report/'),
                   (page_name, page_link)]
        adv_block = bool(adv)

        context.update({
            'title': 'Report - {0}'.format(page_name),
            'navpath': navpath,
            'adv_block': adv_block,
        })

        return context


def find_page_range(page_number, page_range, visible_pages=5):
    """Finds a suitable page range given current page.

    Tries to make an even count of pages before and after page_number
    """
    length = len(page_range)
    page_number = int(page_number)

    if length <= visible_pages:
        return page_range

    padding = visible_pages / 2
    start = page_number - 1 - padding
    if start < 0:
        start = 0

    end = start + visible_pages
    if end >= length:
        end = length
        start = length - visible_pages

    return page_range[start:end]


def generate_export(report, report_name, export_delimiter):
    """Generates a CSV export version of a report"""
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


def add_report_widget(request):
    """
    :type request: HttpRequest
    """

    report_id = request.POST.get('report_id')
    if not report_id:
        return HttpResponse('No report name supplied', status=400)

    navlet = 'nav.web.navlets.report.ReportWidget'
    preferences = {
        'report_id': report_id,
        'query_string': request.POST.get('query_string')
    }

    add_navlet(request.account, navlet, preferences)

    return HttpResponse()


class UnknownNetworkTypeException(Exception):
    """Unknown network type"""
    pass
