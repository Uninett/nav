# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""Helper functions and classes for radius accounting in NAV"""

from __future__ import division, absolute_import
from socket import gethostbyaddr, herror, gaierror
from re import match, sub
import time

from .radius_config import DATEFORMAT_DB, ACCT_REAUTH_TIMEOUT


class HostCache(object):
    """
    Offers method to look up IP adresses, while caching the
    result to speed up operation.
    """

    def __init__(self):
        self.cache = {}

    def lookup_ip_address(self, ip):
        """
        Perform a reverse DNS lookup for ip.

        Uses self.cache to speed up results when the same ip is
        lookup up several times during one session.

        :param ip: IP address to look up
        """

        if ip is None:
            return None
        if ip not in self.cache:
            try:
                self.cache[ip] = gethostbyaddr(ip)[0]
            except (herror, gaierror):
                # if lookup fails, return the input address
                self.cache[ip] = ip

        return self.cache[ip]


def humanize_time(seconds):
    """
    Convert seconds into days, hours, minutes, seconds and make some nice output

    :param seconds: the seconds you want converted
    :returns: A string formatted as DD HH MM SS
    """

    times = _calc_time(seconds)

    returnvar = ""
    days, hours, minutes, seconds = (0, 1, 2, 3)

    if times[days]:
        returnvar = "%sd " % times[days]
    if times[hours]:
        returnvar += "%sh " % times[hours]
    if times[minutes]:
        returnvar += "%sm " % times[minutes]
    if times[seconds]:
        returnvar += "%ss " % times[seconds]

    return returnvar


def _calc_time(seconds):
    """Calculate days/hours/minutes from seconds.

    :param seconds: integer containing the seconds we want calculated
    :returns: A tuple of (days, hours, minutes, seconds)

    """
    if not seconds:
        seconds = 0

    days = 0
    hours = 0
    minutes = 0
    remainder = seconds

    # Sometimes (very rare) the acctsessiontime turns out to be in the negative.
    # Not sure why this happens, but this if at least secures correct output
    # Need to look into this.

    if seconds >= 0:
        days = remainder // 86400
        remainder %= 86400
        hours = remainder // 3600
        remainder %= 3600
        minutes = remainder // 60
        remainder %= 60
        seconds = remainder

    return days, hours, minutes, seconds


def humanize_bytes(number, unit="B"):
    """
    Translates an integer into a human-readable string. The number will be
    scaled using T/G/M/K prefixes and the specified unit.

    :param number: The number of bytes to convert into more human readable form.
    :param unit: The unit suffix to use in the produced string.

    """
    tera, giga, mega, kilo, number = _scale(number)

    if tera > 0:
        output = "%i.%2i T%s" % (tera, giga, unit)
    elif giga > 0:
        output = "%i.%2i G%s" % (giga, mega, unit)
    elif mega > 0:
        output = "%i.%2i M%s" % (mega, kilo, unit)
    elif kilo > 0:
        output = "%i.%2i K%s" % (kilo, number, unit)
    elif number > 0:
        output = "%i %s" % (number, unit)
    else:
        output = "Unknown"

    return output


def _scale(number):
    if number is None:
        number = 0

    tera, number = divmod(number, 1024**4)
    giga, number = divmod(number, 1024**3)
    mega, number = divmod(number, 1024**2)
    kilo, number = divmod(number, 1024)

    return tera, giga, mega, kilo, number


def calculate_stop_time(acctstarttime, acctstoptime, acctsessiontime):
    """
    Checks if session is still active, and returns an appropriate string.

    :param acctstarttime: Session start time
    :param acctstoptime: Session stop time
    :param acctsessiontime: How long the session has lasted

    """
    start_time = str(acctstarttime)
    stop_time = None
    session_time = 0

    if acctstoptime:
        stop_time = str(acctstoptime)
    if acctsessiontime:
        session_time = int(acctsessiontime)

    # Since time.strptime does not handle fractions of a second,
    # check if our starttime contains fractions before using strptime,
    # and remove them if it does.
    if match(r'.+\d\.\d+', start_time):
        start_time = sub(r'\.\d+', '', start_time)

    # Make tuple of the time string
    time_tuple = time.strptime(start_time, DATEFORMAT_DB)
    # Convert to seconds since epoch
    time_seconds = time.mktime(time_tuple)

    # Check if session is still active
    if stop_time is None:
        if (time_seconds + session_time) > (time.time() - ACCT_REAUTH_TIMEOUT):
            stop_time = "Still Active"
        else:
            stop_time = "Timed Out"
    else:
        stop_time = remove_fractions(stop_time)

    return stop_time


def remove_fractions(timestamp):
    """
    Removes the fractions of a second part from the timestamps so we don't
    have to display them on the webpage.
    """

    tstring = str(timestamp)

    if match(r'.+\d\.\d+', tstring):
        formatted_time = sub(r'\.\d+', '', tstring)
    else:
        formatted_time = tstring

    return formatted_time
