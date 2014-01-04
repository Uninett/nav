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
"""Retrieval and calculations on raw numbers from Graphite metrics"""

import simplejson
from urllib import urlencode
import urllib2
from urlparse import urljoin
from nav.metrics import CONFIG, errors


def get_metric_average(target, start="-5min", end="now", ignore_unknown=True):
    """Calculates the average value of a metric over a given period of time

    :param target: A metric path string or a list of multiple metric paths
    :param start: A start time specification that Graphite will accept.
    :param end: An end time specification that Graphite will accept.
    :param ignore_unknown: Ignore unknown values when calculating the average.
                           Unless True, any unknown data in the series will
                           result in an average value of None.
    :returns: A dict of {target: average_value} items. Targets that weren't
              found in Graphite will not be present in the dict.

    """
    data = get_metric_data(target, start, end)
    result = {}
    for target in data:
        dpoints = [d[0] for d in target['datapoints']
                   if not (ignore_unknown and d[0] is None)]
        if dpoints:
            if None in dpoints:
                avg = None
            else:
                avg = sum(dpoints) / len(dpoints)
            result[target['target']] = avg
    return result


def get_metric_max(target, start="-5min", end="now"):
    data = get_metric_data(target, start, end)
    result = {}
    for target in data:
        dpoints = [d[0] for d in target['datapoints'] if d[0] is not None]
        if dpoints:
            if None in dpoints:
                maximum = None
            else:
                maximum = max(dpoints)
            result[target['target']] = maximum
    return result


def get_metric_data(target, start="-5min", end="now"):
    """
    Retrieves raw datapoints from a graphite target for a given period of time.

    :param target: A metric path string or a list of multiple metric paths
    :param start: A start time specification that Graphite will accept.
    :param end: An end time specification that Graphite will accept.

    :returns: A raw, response from Graphite. Normally a list of dicts that
              represent the names and datapoints of each matched target,
              like so::

                  [{'target': 'x', 'datapoints': [(value, timestamp), ...]}]

    """
    base = CONFIG.get("graphiteweb", "base")
    url = urljoin(base, "/render/")

    query = {
        'target': target,
        'from': start,
        'until': end,
        'format': 'json',
    }
    query = urlencode(query, True)

    req = urllib2.Request(url, data=query)
    try:
        response = urllib2.urlopen(req)
        return simplejson.load(response)
    except urllib2.URLError as err:
        raise errors.GraphiteUnreachableError(
            "{0} is unreachable".format(base),err)
    finally:
        try:
            response.close()
        except NameError:
            pass
