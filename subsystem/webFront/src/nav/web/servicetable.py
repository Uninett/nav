"""
$Id$

This file is part of the NAV project.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Magnus Nordseth <magnun@itea.ntnu.no>,
         Stian Søiland <stain@itea.ntnu.no> 

"""

from mod_python import apache
import random
import time
import forgetHTML as html

from nav.db import manage
from nav.errors import *
from nav import database
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
    def __init__(self, servicenames=[], netboxes=[], sort=0):
        where = []
        if servicenames:
            handlers = [database.escape(h) for h in servicenames]
            handlers = ','.join(handlers)
            where.append('handler in (%s)' % handlers)
        if netboxes:
            netboxids = [str(nbox.netboxid) for nbox in netboxes]
            netboxids = ','.join(netboxids)
            where.append('netboxid in (%s)' % netboxids)
            
        self.services = manage.Service.getAll(where=where)
        if not self.services:
            raise NoServicesFound
        self.netboxes = netboxes
        self.servicenames = servicenames
        self.sort = sort
        self.includeRrdStatus = 1
        self.includeResponsetime = 1
        self.datasources = {"STATUS":"Availability",
                            "RESPONSETIME":"Responsetime"
                            }
        self.timeframes = ['Day', 'Week', 'Month']
        self.rrdpresenter = presenter.presentation()
        self._findDataSources()
        self.createHeader()
        self.createTableBody()
        self.html['class'] = "serviceNetbox"
        self.html.sortBy=self.sort
        self.html.sort()
    
    def _findDataSources(self):
        serviceIDs = [str(s.serviceid) for s in self.services]
        serviceIDs = ','.join(serviceIDs)
        allDataSourcesSQL = """
            SELECT rrd_datasourceid, 
                value AS serviceid, 
                name AS ds
            FROM rrd_datasource JOIN rrd_file ON
                (rrd_file.rrd_fileid=rrd_datasource.rrd_fileid) 
            WHERE key='serviceid' and value IN (%s)""" % serviceIDs
        cursor = database.cursor()
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
        if len(self.netboxes) != 1 :
            # If we only have one netbox, there will be no need
            # to show it's name
            headers.append("Server")
        if len(self.servicenames) != 1:
            # No need to show servicename if we only display
            # one service...
            headers.append("Handler")
        headers.append("Status")
        if self.includeRrdStatus:
            headers.extend(self.timeframes)
        if self.includeResponsetime:
            headers.extend(self.timeframes)
        #self.html = tableview.TableView(*headers, baseurl="all", sortBy=self.sort)
        self.html = tableview.TableView(*headers)
    def createTableBody(self):
        for service in self.services:
            row = []
            if service.up == 'y':
                status = ""
            elif service.up == 'n':
                status = html.Image(href="/images/lys/red.png", alt="")
            elif service.up == 's':
                status = html.Image(href="/images/lys/yellow.png", alt="")
            if len(self.netboxes) != 1:
                netbox = urlbuilder.createLink(service.netbox)
                row.append(netbox)
            if len(self.servicenames) != 1:
                handler = urlbuilder.createLink(division="service",
                                                id=service.handler)
                row.append(handler)
            status = _getServiceState(service)
            if service.up != 'y':
                since = downSince(service)
                #status += ' since %s' % since
                status = html.TableCell(status, title="since %s" % since)
            row.append(status)
            for ds in self.datasources.keys():
                for timeframe in self.timeframes:
                    stat = self.getServiceRrds(service, timeframe, ds)
                    row.append(stat)
            self.html.add(_class=service.up, *row)
            
    def getServiceRrds(self, service, timeframe, ds):
        # reuse the same presenter
        rrd = self.rrdpresenter
        rrd.removeAllDs()
        timeframe = timeframe.lower()
        if timeframe == 'day':
            rrd.timeLastDay()
        elif timeframe == 'week':
            rrd.timeLastWeek()
        elif timeframe == 'month':
            rrd.timeLastMonth()
        else:
            raise "Unknown timeframe: %s" % timeframe
    
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
            result = tableview.ValueCell(value, "%")
        else:
            result = tableview.ValueCell(value, decimals=3)

        # Just for fun, could be some real numbers on certainty
        result['title'] = "&Sigma;%0.2f" % random.random()

        return result    
   
