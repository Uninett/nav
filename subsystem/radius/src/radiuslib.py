# -*- coding: utf-8 -*-
#
# Copyright 2003-2004 Norwegian University of Science and Technology
# Copyright 2006-2007 UNINETT AS
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
#
#
# Author: Roger Kristiansen <roger.kristiansen@gmail.com>
#
# Description: Helper functions and classes for radius accounting in NAV


from __future__ import division
from socket import gethostbyaddr, herror, gaierror
from re import match, sub
import time
import urllib

from radius_config import DATEFORMAT_DB, ACCT_REAUTH_TIMEOUT


class HostCache:
    """
    Offers method to look up IP adresses, while caching the
    result to speed up operation.
    """

    def __init__(self):
        self.cache = {}

    def lookupIPAddress(self, ip):
        """
        Perform a reverse DNS lookup for ip.

        Uses self.cache to speed up results when the same ip is
        lookup up several times during one session.

        Keyword arguments:
        ip      - ip address to lookup
        """

        if ip is None:
            return None
        if ip not in self.cache:
            try:
                self.cache[ip] = gethostbyaddr(ip)[0]
            except herror, gaierror:
                # if lookup fails, return the input address
                self.cache[ip] = ip

        return self.cache[ip]



def calcTime(seconds):
    """Calculate days/hours/minutes from seconds.

    Keyword arguments:
    seconds - integer containing the seconds we want calculated
              (default "tuple")

    Return:
    Tuple (days, hours, minutes, seconds)

    """

    if not seconds: seconds = 0

    days = 0
    hours = 0
    minutes = 0
    remainder = seconds

    # Sometimes (very rare) the acctsessiontime turns out to be in the negative.
    # Not sure why this happens, but this if at least secures correct output
    # Need to look into this.
    
    if seconds >= 0:
        days = remainder // 86400
        remainder = remainder % 86400
        hours = remainder // 3600
        remainder = remainder % 3600
        minutes = remainder // 60
        remainder = remainder % 60
        seconds = remainder

    return (days, hours, minutes, seconds)



def makeTimeHumanReadable(seconds):
    """
    Convert seconds into days, hours, minutes, seconds and make some nice output

    Keyword Arguments:
    seconds     - the seconds you want converted

    Return:
    A string in the format dd, hh, mm, ss
    """

    time = calcTime(seconds)

    returnvar = ""
    days, hours, minutes, seconds = (0,1,2,3)

    if time[days]:
        returnvar = "%sd " % time[days]
    if time[hours]:
        returnvar += "%sh " % time[hours]
    if time[minutes]:
        returnvar += "%sm " % time[minutes]
    if time[seconds]:
        returnvar += "%ss " % time[seconds]

    return returnvar




def calcBytes(bytes):

    if bytes == None:
        bytes = 0

    terraBytes, bytes   = divmod(bytes, 1024**4)
    gigaBytes, bytes    = divmod(bytes, 1024**3)
    megaBytes, bytes    = divmod(bytes, 1024**2)
    kiloBytes, bytes    = divmod(bytes, 1024)

    return (terraBytes, gigaBytes, megaBytes, kiloBytes, bytes)


def makeBytesHumanReadable(bytes):
    """
    Translates an integer representing bytes, into TB/GB/MB/KB values.

    Keyword arguments:
    bytes       - the number of bytes to convert into more human readable form
    """
    data = calcBytes(bytes)

    if data[0] > 0:
        output = "%i.%2i TB" % (data[0], data[1])
    elif data[1] > 0:
        output = "%i.%2i GB" % (data[1], data[2])
    elif data[2] > 0:
        output = "%i.%2i MB" % (data[2], data[3])
    elif data[3] > 0:
        output = "%i.%2i KB" % (data[3], data[4])
    elif data[4] > 0:
        output = "%i B" % data[4]
    else:
        output = "Unknown"

    return output


def showStopTime(acctstarttime, acctstoptime, acctsessiontime):
    """
    Checks if session is still active, and returns an appropriate string.

    Keyword arguments:
    acctstarttime   - Session start time
    acctstoptime    - Session stop time
    acctsessiontime - How long the session has lasted
    """
    startTime = str(acctstarttime)
    stopTime = None
    sessionTime = 0
 
    if acctstoptime:
        stopTime = str(acctstoptime)
    if acctsessiontime:
        sessionTime = int(acctsessiontime)

    # Since time.strptime does not handle fractions of a second, 
    # check if our starttime contains fractions before using strptime,
    # and remove them if it does.
    if match(r'.+\d\.\d+', startTime):
        startTime = sub(r'\.\d+', '', startTime)
        
    # Make tuple of the time string
    timeTuple = time.strptime(startTime, DATEFORMAT_DB)
    # Convert to seconds since epoch
    timeSeconds = time.mktime(timeTuple)

    # Check if session is still active
    if stopTime == None:
        if (timeSeconds + sessionTime) > (time.time()-ACCT_REAUTH_TIMEOUT):
            stopTime = "Still Active"
        else:
            stopTime = "Timed Out"
    else:
        stopTime = removeFractions(stopTime)

    return stopTime 


def removeFractions(timestamp):
    """
    Removes the fractions of a second part from the timestamps so we don't
    have to display them on the webpage.
    """
    
    ts = str(timestamp)
    
    if match(r'.+\d\.\d+', ts):
        formattedTime = sub(r'\.\d+', '', ts)
    
    return formattedTime


def makeSearchURL(page, changeFields, form):
    """
    Creates search URL

    Keyword arguments:
    page                - What we want to place before the "?".
    changeFields        - Dictionary with key/value pairs that we want to
                          change in the search.
    form                - SearchForm object
    """

    urlValues = {}

    for field in changeFields.keys():
        urlValues[str(field)] = str(changeFields[field])
        
    for field in form.__dict__.items():
        if not str(field[0]) in changeFields.keys():
            urlValues[str(field[0])] = str(field[1])

    return page + "?" + urllib.urlencode(urlValues) + "&amp;send=Search"


def getSortOrder(sortField, currentField, sortOrder):
    sortOrder = sortOrder.upper()
    
    # If we click on a link a second time, to change the search order
    if sortField == currentField:
        if sortOrder == "ASC":
            sortOrder = "DESC"
        else:
            sortOrder = "ASC"
    else:
        # If the link hasn't been clicked, we want to default to 
        # ascending search order.
        sortOrder = "ASC"

    return sortOrder
