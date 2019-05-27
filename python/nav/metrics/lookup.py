#
# Copyright (C) 2013 Uninett AS
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
"""Functions for reverse-mapping metric names to NAV objects"""

import re

from django.utils.lru_cache import lru_cache
from django.utils.six import iteritems
from nav.models.manage import Netbox, Interface, Prefix, Sensor


__all__ = ['reverses', 'lookup']
_reverse_handlers = []


def _lookup(metric):
    """
    Looks up a NAV object from a metric path.

    :param metric: A Graphite metric path.
    :type metric: str
    :return: If a match was found, a Model instance from any model in the
             nav.models package.

    """
    for pattern, func in _reverse_handlers:
        match = pattern.search(metric)
        if match:
            return func(**match.groupdict())


# pylint: disable=C0103
lookup = lru_cache(maxsize=200)(_lookup)


def reverses(pattern):
    """Decorator to map regex patterns to reverse lookup functions"""
    try:
        pattern.pattern
    except AttributeError:
        pattern = re.compile(pattern)

    def _decorator(func):
        _reverse_handlers.append((pattern, func))
        return func

    return _decorator


### Reverse lookup functions

@reverses(r'\.devices\.(?P<sysname>[^.]+)\.ports\.(?P<ifname>[^\.]+)')
def _reverse_interface(sysname, ifname):
    return (_single_like_match(Interface, related=['netbox'],
                               sysname=sysname, ifname=ifname) or
            _single_like_match(Interface, related=['netbox'],
                               sysname=sysname, ifdescr=ifname))


@reverses(r'\.devices\.(?P<sysname>[^.]+)\.sensors\.(?P<name>[^\.]+)')
def _reverse_sensor(sysname, name):
    return _single_like_match(Sensor, related=['netbox'],
                              sysname=sysname, internal_name=name)


@reverses(r'\.devices\.(?P<sysname>[^.]+)\.cpu\.(?P<cpuname>[^.]+)')
def _reverse_device_cpu(sysname, cpuname):
    netbox = _single_like_match(Netbox, sysname=sysname)
    sysname = getattr(netbox, 'sysname', sysname)
    return "%s: %s" % (sysname, cpuname)


@reverses(r'\.devices\.(?P<sysname>[^.]+)\.system\.')
def _reverse_uptime(sysname):
    netbox = _single_like_match(Netbox, sysname=sysname)
    if hasattr(netbox, 'sysname'):
        return netbox
    else:
        return sysname


@reverses(r'\.devices\.(?P<sysname>[^.]+)$')
def _reverse_device(sysname):
    return _single_like_match(Netbox, sysname=sysname)


@reverses(r'\.prefixes\.(?P<netaddr>[^.]+)')
def _reverse_prefix(netaddr):
    return _single_like_match(Prefix, netaddr=netaddr)


### Helper functions

def _single_like_match(model, related=None, **kwargs):
    args = [("{field}::TEXT LIKE %s".format(field=key), value)
            for key, value in iteritems(kwargs)]
    where, params = zip(*args)
    qset = model.objects.extra(where=where, params=params)
    if related:
        qset = qset.select_related(*related)
    if len(qset) == 1:
        return qset[0]
