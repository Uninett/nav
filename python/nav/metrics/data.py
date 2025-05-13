#
# Copyright (C) 2013 Uninett AS
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
#
"""Retrieval and calculations on raw numbers from Graphite metrics"""

import codecs
from datetime import datetime
import json
import logging
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from nav.metrics import CONFIG, errors
from nav.metrics.templates import (
    metric_path_for_packet_loss,
    metric_path_for_roundtrip_time,
)
from nav.util import chunks

_logger = logging.getLogger(__name__)

MAX_TARGETS_PER_REQUEST = 100
GRAPHITE_TIME_FORMAT = "%H:%M_%Y%m%d"


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
    start_time = datetime.now()

    data = get_metric_data(target, start, end)
    result = {}
    for target in data:
        dpoints = [
            d[0] for d in target['datapoints'] if not (ignore_unknown and d[0] is None)
        ]
        if dpoints:
            if None in dpoints:
                avg = None
            else:
                avg = sum(dpoints) / len(dpoints)
            result[target['target']] = avg

    _logger.debug(
        'Got metric average for %s targets in %s seconds',
        len(data),
        datetime.now() - start_time,
    )
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
    if not target:
        return []  # no point in wasting time on http requests for no data

    base = CONFIG.get("graphiteweb", "base")
    url = urljoin(base, "/render/")

    # What does Graphite accept of formats? Lets check if the parameters are
    # datetime objects and try to force a format then
    if isinstance(start, datetime):
        start = start.strftime(GRAPHITE_TIME_FORMAT)
    if isinstance(end, datetime):
        end = end.strftime(GRAPHITE_TIME_FORMAT)

    query = {
        'target': target,
        'from': start,
        'until': end,
        'format': 'json',
    }
    query = urlencode(query, True)

    _logger.debug("get_metric_data%r", (target, start, end))
    req = Request(url, data=query.encode('utf-8'))
    try:
        response = urlopen(req)
        json_data = json.load(codecs.getreader('utf-8')(response))
        _logger.debug("get_metric_data: returning %d results", len(json_data))
        return json_data
    except HTTPError as err:
        _logger.error(
            "Got a 500 error from graphite-web when fetching %swith data %s",
            err.url,
            query,
        )
        _logger.error("Graphite output: %s", err.fp.read())
        raise errors.GraphiteUnreachableError("{0} is unreachable".format(base), err)
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


DEFAULT_TIME_FRAMES = ('day', 'week', 'month')
DEFAULT_DATA_SOURCES = ('availability', 'response_time')
METRIC_PATH_LOOKUP = {
    'availability': metric_path_for_packet_loss,
    'response_time': metric_path_for_roundtrip_time,
}


def get_netboxes_availability(
    netboxes,
    data_sources=DEFAULT_DATA_SOURCES,
    time_frames=DEFAULT_TIME_FRAMES,
    start_time=None,
    end_time=None,
):
    """Calculates and returns an availability data structure for a list of
    netboxes.

    :type netboxes: list[Netbox] | QuerySet[Netbox]
    :type data_sources: list[str]
    :type time_frames: list[str]
    """
    if not netboxes:
        return {}

    assert all(x in DEFAULT_TIME_FRAMES for x in time_frames)
    assert all(x in DEFAULT_DATA_SOURCES for x in data_sources)

    result = {}
    targets = []

    for netbox in netboxes:
        result[netbox.id] = {}
        for data_source in data_sources:
            metric_resolver = METRIC_PATH_LOOKUP[data_source]
            data_source_id = metric_resolver(netbox.sysname)
            targets.append(data_source_id)

            result[netbox.id][data_source] = {
                'data_source': data_source_id,
            }

    if start_time:
        populate_for_interval(result, targets, netboxes, start_time, end_time)
    else:
        populate_for_time_frame(result, targets, netboxes, time_frames)

    return result


def populate_for_interval(result, targets, netboxes, start_time, end_time):
    """Populate results based on a time interval"""
    avg = {}
    for request in chunks(targets, MAX_TARGETS_PER_REQUEST):
        avg.update(get_metric_average(request, start=start_time, end=end_time))

    for netbox in netboxes:
        root = result[netbox.id]

        # Availability
        if 'availability' in root:
            pktloss = avg.get(root['availability']['data_source'])
            if pktloss is not None:
                pktloss = 100 - (pktloss * 100)
            root['availability'] = pktloss

        # Response time
        if 'response_time' in root:
            root['response_time'] = avg.get(root['response_time']['data_source'])


def populate_for_time_frame(result, targets, netboxes, time_frames):
    """Populate results based on a list of time frames"""
    for time_frame in time_frames:
        avg = {}
        for request in chunks(targets, MAX_TARGETS_PER_REQUEST):
            avg.update(get_metric_average(request, start="-1%s" % time_frame))

        for netbox in netboxes:
            root = result[netbox.id]

            # Availability
            if 'availability' in root:
                pktloss = avg.get(root['availability']['data_source'])
                if pktloss is not None:
                    pktloss = 100 - (pktloss * 100)
                root['availability'][time_frame] = pktloss

            # Response time
            if 'response_time' in root:
                root['response_time'][time_frame] = avg.get(
                    root['response_time']['data_source']
                )
