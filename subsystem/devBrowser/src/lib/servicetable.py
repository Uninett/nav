# -*- coding: UTF-8 -*-
#
# Copyright 2002-2004 Norwegian University of Science and Technology
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
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Stian Soiland <stain@itea.ntnu.no>
#

"""Datastructure for service monitor.
Retrieves and contains the current state of services (uptime, response
time), and to be cached for rapid sorting and recurrent display.
(checking the statistics on all services is a large task we don't want
to do to often)
"""

try:
    from mod_python import apache
except:
    pass
import random
import time
import forgetHTML as html

from nav.db import manage
from nav.errors import *
from nav import db
from nav.web import tableview
from nav.web import urlbuilder
from nav.rrd import presenter

_serviceStates = {
    'y': 'Up',
    'n': 'Down',
    's': 'Shadow',
}
def downSince(service):
    where = ["eventtypeid='serviceState'"]
    where.append("end_time='infinity'")
    alerts = service.getChildren(manage.Alerthist, 'subid', where)
    if not alerts:
        return None
    # Eh.. there should be only one with end_time==infinity
    lastAlert = alerts[-1]
    return lastAlert.start_time

def _getServiceState(service):
    if not service.active:
        return "Service"
    return _serviceStates.get(service.up, "Unknown")



class ServiceTable:
    def __init__(self, servicenames=[], netboxes=[], sort=2):
        where = []
        if servicenames:
            handlers = [db.escape(h) for h in servicenames]
            handlers = ','.join(handlers)
            where.append('handler in (%s)' % handlers)
        if netboxes:
            netboxids = [str(nbox._getID()[0]) for nbox in netboxes]
            netboxids = ','.join(netboxids)
            where.append('netboxid in (%s)' % netboxids)

        self.services = manage.Service.getAll(where=where)
        if not self.services:
            raise NoServicesFound
        self.netboxes = netboxes
        self.servicenames = servicenames
        self.sort = sort
        self.datasources = {"STATUS":"Availability",
                            "RESPONSETIME":"Responsetime",
                            }
        self.includeRrdStatus = self.datasources.has_key('STATUS')
        self.includeResponsetime = False
        self.timeframes = ['Day', 'Week', 'Month']
        self.rrdpresenter = presenter.presentation()
        self._findDataSources()
        self.createHeader()
        self.createTableBody()
        self.html['class'] = 'listtable'
        self.html.sortBy=self.sort
        self.html.sort()

    def _findDataSources(self):
        serviceIDs = [db.escape(str(s.serviceid)) for s in self.services]
        serviceIDs = ','.join(serviceIDs)
        allDataSourcesSQL = """
            SELECT rrd_datasourceid,
                value AS serviceid,
                name AS ds
            FROM rrd_datasource JOIN rrd_file ON
                (rrd_file.rrd_fileid=rrd_datasource.rrd_fileid)
            WHERE key='serviceid' and value IN (%s)""" % serviceIDs
        connection = db.getConnection('default')
        cursor = connection.cursor()
        cursor.execute(allDataSourcesSQL)
        result = cursor.fetchall()
        for row in result:
            (rrd_datasourceid, serviceid, ds) = row
            serviceid = int(serviceid)
            # forgetSQLs cache should (..) make sure that this is
            # the cached version of the same thingie as in
            # self.services
            service = manage.Service(serviceid)
            if not hasattr(service, 'datasources'):
                service.datasources = {}
            service.datasources[ds] = rrd_datasourceid

    def defineDatasources(self, ds):
        # expects a dict, but we should check for it...
        self.datasources = ds
    def createHeader(self):
        """Creates the table heading """
        headers = []
        headers.append("Status")
        if len(self.netboxes) != 1 :
            # If we only have one netbox, there will be no need
            # to show it's name
            headers.append("Server")
            headers.append("Organization")
        if len(self.servicenames) != 1:
            # No need to show servicename if we only display
            # one service...
            headers.append("Handler")
        if self.includeRrdStatus:
            headers.extend(self.timeframes)
        if self.includeResponsetime:
            headers.extend(self.timeframes)
        headers.append("Actions")

        #self.html = tableview.TableView(*headers, baseurl="all", sortBy=self.sort)
        self.html = tableview.TableView(*headers)
    def createTableBody(self):
        for service in self.services:
            row = []

            status = _getServiceState(service)
            if service.up == 'y':
                statusLight = html.Image(src="/images/lys/green.png", alt="Up")
            elif service.up == 'n':
                statusLight = html.Image(src="/images/lys/red.png", alt="Down")
            elif service.up == 's':
                statusLight = html.Image(src="/images/lys/yellow.png", alt="Shadow")
            if service.up != 'y':
                since = downSince(service)
                title = 'since %s' % since
            else:
                title = ''
            statusspan = html.Span()
            statusspan.append(statusLight)
            statusspan.append(status)
            status = html.TableCell(statusspan, title=title)
            row.append(status)

            if len(self.netboxes) != 1:
                netbox = urlbuilder.createLink(service.netbox)
                row.append(netbox)
                org = service.netbox.org
                if org:
                    org = urlbuilder.createLink(org, content=org.descr or org.orgid)
                    row.append(org)
                else:
                    row.append("")
            if len(self.servicenames) != 1:
                handler = urlbuilder.createLink(division="service",
                                                id=service.handler)
                row.append(handler)

            for ds in self.datasources.keys():
                if not self.includeResponsetime and \
                    ds == 'RESPONSETIME':
                        continue
                for timeframe in self.timeframes:
                    stat = self.getServiceRrds(service, timeframe, ds)
                    row.append(stat)

            actionspan = html.Span()
            editLink = urlbuilder.createLink(service, subsystem="seeddb", content="[Edit]")
            actionspan.append(editLink)
            maintLink = urlbuilder.createLink(service,
                                              subsystem='maintenance',
                                              content='[Schedule maintenance]')
            actionspan.append(maintLink)
            row.append(actionspan)
            self.html.add(_class=service.up, *row)

    def getServiceRrds(self, service, timeframe, ds):
        # reuse the same presenter
        rrd = self.rrdpresenter
        rrd.removeAllDs()
        timeframe = timeframe.lower()
        rrd.timeLast(timeframe)

        try:
            dsID = service.datasources[ds]
        except Exception,e:
            return ""
        rrd.addDs(dsID)

        value = rrd.average()
        if not value:
            return ""
        else:
            value = value[0]


        if ds == "STATUS":
            # convert to availability percent.
            # only your boss understands this
            # number :)
            value = (1-value)*100
            result = tableview.Value(value, "%")
        else:
            result = tableview.Value(value, decimals=3)

        # Just for fun, could be some real numbers on certainty
        link = urlbuilder.createLink(subsystem="rrd",
                division="datasources",
                id=service.datasources.values(),
                tf=timeframe, content=result)
        link['title'] = "&sigma;%0.2f" % random.random()
        return link

