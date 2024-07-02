#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV)
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
"""Sorted statistics views."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from django.shortcuts import render
from django.core.cache import caches
from django.conf import settings
from django.core.cache.backends.base import InvalidCacheBackendError

from .forms import ViewForm
from . import CLASSMAP, TIMEFRAMES
from nav.metrics.errors import GraphiteUnreachableError
from nav.metrics.data import GRAPHITE_TIME_FORMAT

_logger = logging.getLogger(__name__)


def get_cache():
    return caches['sortedstats']


def cache_is_misconfigured():
    try:
        get_cache()
    except InvalidCacheBackendError:
        return True
    else:
        return False


def index(request):
    """Sorted stats search & result view"""
    result = None
    graphite_unreachable = False
    from_cache = None
    start_time = datetime.now()

    try:
        if 'view' in request.GET:
            form = ViewForm(request.GET)
            if form.is_valid():
                result, from_cache = process_form(form)

        else:
            form = ViewForm()

    except GraphiteUnreachableError:
        graphite_unreachable = True

    duration = (datetime.now() - start_time).total_seconds()
    context = {
        'title': 'Statistics',
        'navpath': [('Home', '/'), ('Statistics', False)],
        'result': result,
        'form': form,
        'graphite_unreachable': graphite_unreachable,
        'from_cache': from_cache,
        'duration': duration,
        'cache_misconfigured': cache_is_misconfigured(),
    }

    return render(request, 'sortedstats/sortedstats.html', context)


def process_form(form):
    """Returns graphite result based on form content"""
    result = None
    from_cache = True
    view = form.cleaned_data['view']
    timeframe = form.cleaned_data['timeframe']
    rows = form.cleaned_data['rows']
    cache_key = get_cache_key(view, timeframe, rows)
    if form.cleaned_data['use_cache']:
        try:
            cache = get_cache()
            result = cache.get(cache_key)
            if result and not result.data:
                result = None
        except InvalidCacheBackendError as e:
            _logger.error("Error accessing cache for ranked statistics: %s", e)
            result = None
    if not result:
        result = collect_result(view, timeframe, rows)
        from_cache = False
    return result, from_cache


def get_result(view, start, end, rows):
    """
    start/end valus must be supported by the graphite render API.
    They represent what graphite calls from/until.
    """
    cls = CLASSMAP[view]
    return cls(start=start, end=end, rows=rows)


def get_cache_key(view, timeframe, rows):
    return f"{view}_{timeframe}_{rows}"


def collect_result(view, timeframe, rows):
    timeout = TIMEFRAMES[timeframe]['cache_timeout']
    start, end = get_timestamps(timeframe)
    cache_key = get_cache_key(view, timeframe, rows)
    result = get_result(view, start, end, rows)
    result.collect()
    try:
        cache = get_cache()
        cache.set(cache_key, result, timeout=timeout)
    except InvalidCacheBackendError as e:
        _logger.error("Error accessing cache for ranked statistics: %s", e)
    return result


def get_timestamps(timeframe):
    delta = TIMEFRAMES[timeframe]['timedelta']
    end_dt = datetime.now(tz=ZoneInfo(settings.TIME_ZONE))
    end_timestamp = end_dt.strftime(GRAPHITE_TIME_FORMAT)
    start_dt = end_dt - delta
    start_timestamp = start_dt.strftime(GRAPHITE_TIME_FORMAT)
    return start_timestamp, end_timestamp
