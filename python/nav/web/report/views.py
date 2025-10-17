#
# Copyright (C) 2008-2013 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Handling web requests for the Report subsystem."""

import logging
import hashlib
from functools import wraps

from collections import defaultdict, namedtuple
from time import localtime, strftime
import csv
import re
from os import stat
from os.path import join

from IPy import IP

from django.core.cache import cache
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse

from nav.models.manage import Prefix

from nav.report.IPtree import get_max_leaf, build_tree
from nav.report.generator import Generator, ReportList
from nav.report.matrixIPv4 import MatrixIPv4
from nav.report.matrixIPv6 import MatrixIPv6
from nav.report.metaIP import MetaIP
from nav.config import find_config_file, find_config_dir, list_config_files_from_dir

from nav.web.auth.utils import get_account
from nav.web.navlets import add_navlet


_logger = logging.getLogger(__name__)
IpGroup = namedtuple('IpGroup', 'private ipv4 ipv6')
CONFIG_DIR = join(find_config_dir() or "", "report", "report.conf.d/")
FRONT_FILE = find_config_file(join("report", "front.html"))
DEFAULT_PAGE_SIZE = 25
PAGE_SIZES = [25, 50, 100, 500, 1000]


def index(request):
    """Report front page"""

    context = {
        'title': 'Report - Index',
        'navpath': [('Home', '/'), ('Report', False)],
        'heading': 'Report Index',
    }

    with open(FRONT_FILE, 'r') as f:
        context['index'] = f.read()

    return render(request, "report/index.html", context)


def get_report_for_widget(request, report_name):
    """Fetches a report for display in a widget"""
    query = _strip_empty_arguments(request)
    export_delimiter = _get_export_delimiter(query)

    context = make_report(request, report_name, export_delimiter, query)
    return render(request, 'report/frag_report_table.html', context)


def get_report(request, report_name):
    """Loads and displays a specific reports with optional search arguments"""
    query = _strip_empty_arguments(request)
    export_delimiter = _get_export_delimiter(query)

    if query != request.GET:
        # some arguments were stripped, let's clean up the URL
        return HttpResponseRedirect(
            "{0}?{1}".format(request.META['PATH_INFO'], query.urlencode())
        )

    context = make_report(request, report_name, export_delimiter, query)
    if 'exportcsv' in request.GET:
        return context

    # Magic flag for adding sorting links to table
    context['add_sort_links'] = True
    context['page_sizes'] = PAGE_SIZES

    return render(request, 'report/report.html', context)


def _strip_empty_arguments(request):
    """Strips empty arguments and their related operator arguments from the
    QueryDict in request.GET and returns a new, possibly modified QueryDict.

    """
    query = request.GET.copy()

    deletable = [key for key, value in query.items() if not value.strip()]
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


def matrix_report(request, scope=None):
    """Subnet matrix view
    :type request: django.http.request.HttpRequest
    """
    show_unused = request.GET.get('show_unused_addresses', False)

    context = {
        'navpath': [
            ('Home', '/'),
            ('Report', reverse('report-index')),
            ('Subnet matrix', reverse('report-matrix')),
        ],
        'show_unused': show_unused,
    }

    if scope is None:
        scopes = Prefix.objects.filter(vlan__net_type='scope')
        if scopes.count() == 1:
            # If there is only one scope in the database display that scope
            scope = IP(scopes[0].net_address)
        else:
            # Else let the user select one
            context['scopes'] = group_scopes(scopes)
            return render(request, 'report/matrix.html', context)
    else:
        scope = IP(scope)

    matrix = create_matrix(scope, show_unused)

    hide_content_for_colspan = []
    if scope.version() == 4:
        hide_content_for_colspan = [1, 2, 4]

    context.update(
        {
            'matrix': matrix,
            'sub': matrix.end_net.prefixlen() - matrix.bits_in_matrix,
            'ipv4': scope.version() == 4,
            'family': scope.version(),
            'scope': scope,
            'hide_for': hide_content_for_colspan,
        }
    )

    return render(request, 'report/matrix.html', context)


def group_scopes(scopes):
    """Group scopes by version and type
    :type scopes: list[Prefix]
    """

    def _prefix_as_int(prefix):
        return IP(prefix.net_address).int()

    groups = defaultdict(list)
    for scope in scopes:
        prefix = IP(scope.net_address)
        if prefix.iptype() == 'PRIVATE':
            groups['private'].append(scope)
        elif prefix.version() == 4:
            groups['ipv4'].append(scope)
        elif prefix.version() == 6:
            groups['ipv6'].append(scope)

    if any([groups['private'], groups['ipv4'], groups['ipv6']]):
        return IpGroup(
            *[
                sorted(groups[x], key=_prefix_as_int)
                for x in ('private', 'ipv4', 'ipv6')
            ]
        )
    else:
        return []


def create_matrix(scope, show_unused):
    """Creates a matrix for the given scope"""
    tree = build_tree(scope)
    if scope.version() == 6:
        if scope.prefixlen() < 60:
            end_net = IP(scope.net().strNormal() + '/64')
            matrix = MatrixIPv6(scope, end_net=end_net)
        else:
            end_net = get_max_leaf(tree)
            matrix = MatrixIPv6(scope, end_net=end_net)
    elif scope.version() == 4:
        if scope.prefixlen() < 24:
            end_net = IP(scope.net().strNormal() + '/30')
            matrix = MatrixIPv4(scope, show_unused, end_net=end_net, bits_in_matrix=6)
        else:
            max_leaf = get_max_leaf(tree)
            bits_in_matrix = max_leaf.prefixlen() - scope.prefixlen()
            matrix = MatrixIPv4(
                scope, show_unused, end_net=max_leaf, bits_in_matrix=bits_in_matrix
            )
    else:
        raise UnknownNetworkTypeException('version: ' + str(scope.version))

    # Invalidating the MetaIP cache to get rid of processed data.
    MetaIP.invalidateCache()

    matrix.build()
    return matrix


def report_list(request):
    """Automated report list view"""
    report_list = ReportList(list_config_files_from_dir(CONFIG_DIR)).get_report_list()

    context = {
        'title': 'Report - Report List',
        'navpath': [
            ('Home', '/'),
            ('Report', '/report/'),
            ('Report List', '/report/reportlist'),
        ],
        'heading': 'Report list',
        'report_list': report_list,
    }

    return render(request, 'report/report_list.html', context)


def make_report(request, report_name, export_delimiter, query_dict, paginate=True):
    """Makes a report

    :param paginate: Introduced to be able to toggle display of the paginate
                     elements. Used in the widget rendering.
    """
    # Initiating variables used when caching
    report = contents = neg = operator = adv = result_time = None

    if not report_name:
        return None

    # Pagination related variables
    page_number = query_dict.get('page_number', 1)
    page_size = get_page_size(request)

    query_string = "&".join(
        ["%s=%s" % (x, y) for x, y in query_dict.items() if x != 'page_number']
    )

    config_files = list_config_files_from_dir(CONFIG_DIR)
    account = get_account(request)

    @report_cache(
        (
            account.login,
            report_name,
            [stat(path).st_mtime for path in config_files],
        ),
        query_dict,
    )
    def _fetch_data_from_db():
        (report, contents, neg, operator, adv, config, dbresult) = gen.make_report(
            report_name, config_files, query_dict, None, None
        )
        if not report:
            raise Http404
        result_time = strftime("%H:%M:%S", localtime())
        return report, contents, neg, operator, adv, result_time

    gen = Generator()

    report, contents, neg, operator, adv, result_time = _fetch_data_from_db()

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
            'current_page_range': find_page_range(page_number, paginator.page_range),
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
                'eq',
                'like',
                'gt',
                'lt',
                'geq',
                'leq',
                'between',
                'in',
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

        navpath = [('Home', '/'), ('Report', '/report/'), (page_name, page_link)]
        adv_block = bool(adv)

        context.update(
            {
                'title': 'Report - {0}'.format(page_name),
                'navpath': navpath,
                'adv_block': adv_block,
            }
        )

        return context


def get_page_size(request):
    """Gets the page size based on preferences"""
    account = get_account(request)
    key = account.PREFERENCE_KEY_REPORT_PAGE_SIZE

    if 'page_size' in request.GET:
        page_size = request.GET.get('page_size')
        if account.preferences.get(key) != page_size:
            account.preferences[key] = page_size
            account.save()
    elif key in account.preferences:
        page_size = account.preferences[key]
    else:
        page_size = DEFAULT_PAGE_SIZE

    return page_size


def find_page_range(page_number, page_range, visible_pages=5):
    """Finds a suitable page range given current page.

    Tries to make an even count of pages before and after page_number
    """
    length = len(page_range)
    page_number = int(page_number)

    if length <= visible_pages:
        return page_range

    padding = visible_pages // 2
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

    response = HttpResponse(content_type="text/x-csv; charset=utf-8")
    response["Content-Type"] = "application/force-download"
    response["Content-Disposition"] = "attachment; filename=report-%s-%s.csv" % (
        report_name,
        strftime("%Y%m%d", localtime()),
    )
    writer = csv.writer(response, delimiter=str(export_delimiter))

    # Make a list of headers
    header_row = [cell.text for cell in report.table.header.cells]
    writer.writerow(header_row)

    # Make a list of lists containing each cell. Considers the 'hidden' option
    # from the config.
    rows = []
    for row in report.table.rows:
        rows.append([cell.text for cell in row.cells])
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
        'query_string': request.POST.get('query_string'),
    }

    account = get_account(request)
    add_navlet(account, navlet, preferences)

    return HttpResponse()


def report_cache(key_items, query_dict):
    """Report caching decorator.

    Any exception that occurs while attempting to get or set cache items are
    logged and subsequently ignored. We can still do our work, albeit slower.

    :param key_items: A list of values that make up the request key

    :param query_dict: The request query parameter dictionary; used to
                       extract the "advanced search" parameters used in the
                       request, so these can be included in the cache key
    """
    keys = ['report'] + list(key_items) + [_query_dict_hash(query_dict)]
    cache_key = ':'.join(str(k).replace(' ', '') for k in keys)

    def _decorator(func):
        def _cache_lookup(*args, **kwargs):
            try:
                data = cache.get(cache_key)
            except Exception:  # noqa: BLE001
                _logger.exception("Exception occurred while hitting the cache")
                data = None

            if not data:
                data = func(*args, **kwargs)
                try:
                    cache.set(cache_key, data)
                except Exception:  # noqa: BLE001
                    _logger.exception("Exception occurred while caching")

            return data

        return wraps(func)(_cache_lookup)

    return _decorator


def _query_dict_hash(query_dict):
    """Makes a unique hash from a report query_dict, excluding every known
    parameter that is not related to filtering the report contents (i.e.
    arguments that do not affect the SQL result itself should not be part of
    the cache key).

    """
    non_key_args = [
        'offset',
        'limit',
        'export',
        'exportcsv',
        'page_number',
        'page_size',
    ]
    stripped_dict = {
        key: value
        for key, value in query_dict.items()
        if key not in non_key_args and value != ""
    }
    data = repr(stripped_dict).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


class UnknownNetworkTypeException(Exception):
    """Unknown network type"""

    pass
