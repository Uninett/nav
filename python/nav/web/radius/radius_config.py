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
#

# Enable reloading of imported modules
DEBUG = 1

DB = "manage"
DB_USER = "radius"

""" Alternate configuration for separate DB-users with read and write
rights. Comment out the DB_USER above and uncomment the next two lines
to enable this. NB! Some modification to views.py and db.conf must
also be done to enable this. See INSTALL for instructions.
"""
# DB_USER_READ = "radius_front"
# DB_USER_WRITE = "radius_back"

##############################################################################
# Module config
##############################################################################

# "Translation" of the module names into more human readable form.
MODULES = {
    "acctsearch": "Accounting Log",
    "acctcharts": "Accounting Charts",
    "logsearch": "Error Log",
}

# Maps pages/subsections to modules
SECTIONS = {
    "acctsearch": ["acctsearch", "acctdetail"],
    "acctcharts": ["acctcharts"],
    "logsearch": ["logsearch", "logdetail"],
}


# The order in which the menu is displayed. Remove item to remove it from menu
MENUORDER = ("acctsearch", "acctcharts", "logsearch")

INDEX_PAGE = 'acctsearch'


##############################################################################
# Radius Log
##############################################################################

# Database table containing radius log
LOG_TABLE = "radiuslog"

# Keep records for 1 month
LOG_EXPIRY = "1 month"

LOG_FIELDDESCRIPTIONS = {
    "time": "Timestamp",
    "type": "Type",
    "message": "Message",
    "status": "Status",
    "username": "Username",
    "client": "Client",
    "port": "Port",
    "view": "View",
}

# Fields to display in the search results
LOG_SEARCHRESULTFIELDS = ("time", "type", "message")

# Fields to display on the details page
LOG_DETAILFIELDS = ("time", "type", "message", "status", "username", "client", "port")


##############################################################################
# Radius Accounting
##############################################################################

# Table containg our accounting data
ACCT_TABLE = "radiusacct"


# Reauthentication-interval in seconds. Helps decide when a session should be
# displayed as "Timed out"
# I've set it to 60 seconds longer than the actual reauth interval, because the
# searches might take a while
ACCT_REAUTH_TIMEOUT = 960


# Associate database fields with proper descriptions
ACCT_DBFIELDSDESCRIPTIONS = {
    "acctuniqueid": "Session ID",
    "username": "Username",
    "nasipaddress": "NAS IP Address",
    "nasporttype": "NAS Port Type",
    "cisconasport": "Cisco NAS Port",
    "calledstationid": "Called Station (NAS)",
    "callingstationid": "Calling Station (Client)",
    "framedprotocol": "Framed Protocol",
    "framedipaddress": "Framed IP Address",
    "acctstarttime": "Session Start",
    "acctstoptime": "Session Stop",
    "acctsessiontime": "Duration",
    "acctterminatecause": "Termination Cause",
    "acctinputoctets": "Uploaded Data",
    "acctoutputoctets": "Downloaded Data",
}

# Fields to display when viewing session details
ACCT_DETAILSFIELDS = (
    "acctuniqueid",
    "username",
    "nasipaddress",
    "nasporttype",
    "cisconasport",
    "calledstationid",
    "callingstationid",
    "framedprotocol",
    "framedipaddress",
    "acctstarttime",
    "acctstoptime",
    "acctsessiontime",
    "acctterminatecause",
    "acctinputoctets",
    "acctoutputoctets",
)

# Fields to display when viewing a search result. Changing this without editing
# RadiusSearchTemplate.tmpl will just end in a mess. Leave it as it is.
ACCT_SEARCHRESULTFIELDS = (
    "username",
    "framedipaddress",
    "nasipaddress",
    "acctstarttime",
    "acctstoptime",
    "acctsessiontime",
    "acctuniqueid",
)

##############################################################################

# The format we want to use when searching for a specific date and time.
DATEFORMAT_SEARCH = "%Y-%m-%d %H:%M"

# Format of the string you get when you select the datetime field in the DB If
# your datetime field contains fractions of a second, you can just ignore
# them, as they will be stripped in the showStopTime helper function.
DATEFORMAT_DB = "%Y-%m-%d %H:%M:%S"
