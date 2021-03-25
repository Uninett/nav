#
# Copyright (C) 2013-2015 Uninett AS
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
"""Search & discovery functions for Graphite metric names and hierarchies"""

from collections import OrderedDict
import itertools
import json
from django.utils.six.moves.urllib.parse import urlencode, urljoin
from django.utils.six.moves.urllib.request import Request, urlopen
from django.utils.six.moves.urllib.error import URLError
from nav.metrics import CONFIG, errors
import string

LEGAL_METRIC_CHARACTERS = string.ascii_letters + string.digits + "-_"


def escape_metric_name(name):
    """
    Escapes any character of `name` that may not be used in graphite metric
    names.
    """
    if name is None:
        return name
    name = name.replace('\x00', '')  # some devices have crazy responses!
    name = ''.join([c if c in LEGAL_METRIC_CHARACTERS else "_" for c in name])
    return name


def join_series(names):
    """Joins a list of metric names to a single series list.

    :param names: A list of series/metric names.
    """
    splitnames = [n.split('.') for n in names]
    series = []
    for names in zip(*splitnames):
        uniq = OrderedDict.fromkeys(names)
        if len(uniq) > 1:
            name = '{%s}' % ",".join(uniq)
        else:
            name = "".join(uniq)
        series.append(name)
    return ".".join(series)


def get_all_leaves_below(top, ignored=None):
    """Gets a list of all leaf nodes in the metric hierarchy below top"""
    walker = nodewalk(top, ignored)
    paths = (leaves for (name, nonleaves, leaves) in walker)
    return list(itertools.chain(*paths))


def get_metric_leaf_children(path):
    """Returns a list of available graphite leaf nodes just below path.

    :param path: A path to a Graphite metric.
    :returns: A list of metric paths.

    """
    query = path + ".*"
    data = raw_metric_query(query)
    result = [node['id'] for node in data if node.get('leaf', False)]
    return result


def get_metric_nonleaf_children(path):
    """Returns a list of available graphite non-leaf nodes just below path.

    :param path: A path to a Graphite metric.
    :returns: A list of metric paths.

    """
    query = path + ".*"
    data = raw_metric_query(query)
    result = [node['id'] for node in data if not node.get('leaf', False)]
    return result


def nodewalk(top, ignored=None):
    """Walks through a graphite metric hierarchy.

    Basically works like os.walk()

    :param top: Path to the node to walk from.
    :param ignored: A list of node IDs to completely ignore.
    :returns: A generator that generates three-tuples of
              (name, nonleaves, leaves)

    """
    ignored = ignored or []
    nodes = raw_metric_query(top + '.*')
    nonleaves, leaves = [], []
    for node in nodes:
        if node['id'] in ignored:
            continue
        if node.get('leaf', False):
            leaves.append(node['id'])
        else:
            nonleaves.append(node['id'])

    yield top, nonleaves, leaves

    for name in nonleaves:
        for x in nodewalk(name):
            yield x


def raw_metric_query(query):
    """Runs a query for metric information against Graphite's REST API.

    :param query: A search string, e.g. "nav.devices.some-gw_example_org.*"
    :returns: A list of matching metrics, each represented by a dict.

    """
    base = CONFIG.get("graphiteweb", "base")
    url = urljoin(base, "/metrics/find")
    query = urlencode({'query': query})
    url = "%s?%s" % (url, query)

    req = Request(url)
    try:
        response_data = urlopen(req).read().decode('utf-8')
        return json.loads(response_data)
    except URLError as err:
        raise errors.GraphiteUnreachableError("{0} is unreachable".format(base), err)
    except ValueError:
        # response could not be decoded
        return []
    finally:
        try:
            response.close()
        except NameError:
            pass
