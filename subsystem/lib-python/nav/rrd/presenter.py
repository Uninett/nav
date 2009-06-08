# -*- coding: ISO8859-1 -*-
# $Id$
#
# Copyright 2003 Norwegian University of Science and Technology
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
# Authors: Erlend Mjaavatten <mjaavatt@itea.ntnu.no>
#
"""
Abstraction of the rrd_file and rrd_datasource fields in the main NAV database.

Consists of three classes, presentation beeing the one of most interest to other developers.

Quick example:

>>> a = presenter.presentation() # instansiate presentation object
>>> a.addDs(454)                 # Add rrd_datasourceid nr. 454 from rrd_datasource table, returns the default legend
'brev.stud - imap responsetime'
>>> a.timeLast('week')           # We are interested in the data from a week ago and until today
>>> a.average()
[0.0064152292421062644]          # imap responed with an average of 6milli.. hmm, whats the unit?
>>> a.units()
['s']                            # Ah. seconds, 6 ms then.
>>> a.addDs(427)                 # Add another datasource
'brev.stud - pop3 responsetime'
>>> a.average()                  # It still works
[1.0, 0.0028113913067105887]
>>> a.title = 'My Graph'         # You can set the title to what you want
>>> a.graphUrl()
'http://isbre.itea.ntnu.no/rrd/rrdBrowser/graph?id=348552316' # Returns a link to an image representing the two datasources. This link is valid for about ten minutes
"""

configfile = 'rrdBrowser.conf'
import nav.db
import nav.config
import time
import rrdtool
import random
import glob
import os
import warnings
import operator
from mx import DateTime
from os import path

unitmap = {'s'   : 'Seconds',
           '%'   : 'Percent',
           '100%': 'Percent',
           }

class rrd_file:
    """Class representing an rrd-file"""
    def __init__(self,rrd_fileid):
        cursor = nav.db.getConnection('rrdpresenter').cursor()
        cursor.execute("select * from rrd_file natural join netbox where rrd_fileid=%s"% rrd_fileid)
        result = cursor.dictfetchone()
        self.path     = result['path']
        self.filename = result['filename']
        self.netboxid = result['netboxid']
        self.key      = result['key']
        self.value    = result['value']
        self.subsystem= result['subsystem']
        self.sysname  = result['sysname']
        
    def fullPath(self):
        rrd_file_path = path.join(self.path,self.filename)
        return rrd_file_path

class datasource:
    """ Class representing a datasource.
    Can perform simple calculations on the datasource"""

    def __init__(self,rrd_datasourceid,linetype='LINE2'):
        cursor = nav.db.getConnection('rrdpresenter').cursor()    
        cursor.execute("select * from rrd_datasource where rrd_datasourceid=%s"% rrd_datasourceid)
        result = cursor.dictfetchone()
        self.name     = result['name']
        self.descr    = result['descr']
        self.dstype   = result['dstype']
        self.units    = result['units']
        self.rrd_datasourceid = result['rrd_datasourceid']
        self.linetype = linetype
        self.rrd_fileobj = rrd_file(result['rrd_fileid'])
        self.sysname = self.rrd_fileobj.sysname
        self.legend = '%s - %s' % (self.rrd_fileobj.sysname,self.descr)
        cursor.close()

    def getId(self):
        return self.rrd_datasourceid
    
    def __eq__(self,obj):
        return obj.rrd_datasourceid == self.rrd_datasourceid
    
    def __str__(self):
        return "%s - %s" % (self.name, self.descr)

    def __repr__(self):
        return "%s - %s" % (self.name, self.descr)

    def fullPath(self):
        return self.rrd_fileobj.fullPath()
    

class presentation:
    def __init__(self, tf='day', ds=''):
        self.datasources = []
        self.none = None
        self.graphHeight = 150
        self.graphWidth  = 500
        self.title = ''
        self.timeLast(tf)
        self.timeframe = tf
        self.showmax = 0
        self.yaxis = 0
        if ds != '':
            self.addDs(ds)
        

    def serialize(self):
        repr = {}
        repr['datasources'] = []
        for ds in self.datasources:
            repr['datasources'].append(ds.getId())
        repr['timeframe'] = self.timeframe
        return repr
        
    def _updateTitle():
        for i in self.datasources:
            blapp

    def units(self):
        """Returns the units of the rrd_datasources contained in the presentation object"""
        units = []
        for i in self.datasources:
            units.append(i.units)
        return units
        

    def addDs(self,ds_id):
        """Adds a datasource to the presentation, returns the default legend"""
        ds = datasource(ds_id)
        self.datasources.append(ds)
        return ds.legend

    def __str__(self):
        return str(self.datasources)

    def __repr__(self):
        return str(self.datasources)

    def fetchValid(self):
        """Return the raw rrd-data as a list of dictionaries
        {'start':starttime in unixtime,
        'stop':stoptime in unixtime,
        'data':[data,as,list]}"""
        returnList = []
        for datasource in self.datasources:
            try:
                raw = rrdtool.fetch(datasource.fullPath(),
                                    'AVERAGE','-s '+self.fromTime,
                                    '-e '+self.toTime)

                returnDict = {}
                returnDict['start']  = raw[0][0]
                returnDict['stop']   = raw[0][1]
                returnDict['deltaT'] = raw[0][2]        
            
                row = list(raw [1]).index(datasource.name)
                invalid = 0
                data = []

                for i in raw[2]:
                    if type(i[row]) == type(None):
                        #                    data.append(self.none)
                        invalid += 1
                    else:
                        data.append(i[row])
                    returnDict['data'] = data
                    returnDict['invalid'] = invalid

            except rrdtool.error:
                returnDict = {}
                returnDict['start'] = ''
                returnDict['stop'] = ''
                returnDict['deltaT'] = ''
                returnDict['data'] = ''
                returnDict['invalid'] = ''
            returnList.append(returnDict)                
        return returnList

    def sum(self):
        """Returns the sum of the valid  rrd-data"""
        sumList = []
        dataList = self.fetchValid()        
        for data in dataList:
            sum = 0
            for i in data['data']:
                sum += i
            sumList.append(sum)
        return sumList
    
    def max(self):
        """Returns the local maxima of the valid rrd-data"""
        maxList = []
        for presentation in self.fetchValid():
            maxList.append(max(presentation['data']))
        return maxList

    def average(self, onErrorReturn=0, onNanReturn=0):
        """
        Returns the average of the valid rrd-data using rrdtool graph.

        onErrorReturn is the value appended to the returnlist if an
        error occured while fetching the value, default 0 (zero).

        onNanReturn is the value appended to the return list if a NaN
        value was the result of the average calculation, default=0
        (zero).
        """
        rrdvalues = []
        rrdstart = "-s %s" %self.fromTime
        rrdend = "-e %s" %self.toTime

        for datasource in self.datasources:
            # The variablename (after def) is not important, it just
            # needs to be the same in the DEF and PRINT. We use
            # datasource.name.

            rrddef = "DEF:%s=%s:%s:AVERAGE" %(datasource.name,
                                              datasource.fullPath(),
                                              datasource.name)
            rrdprint = "PRINT:%s:AVERAGE:%%lf" %(datasource.name)

            try:
                # rrdtool.graph returns a tuple where the third
                # element is a list of values. We fetch only one
                # value, hence the rrdtuple[2][0]
                rrdtuple = rrdtool.graph('/dev/null', rrdstart, rrdend,
                                         rrddef, rrdprint)
                rrdvalue = rrdtuple[2][0]
                # This works ok with nan aswell.
                realvalue = float(rrdvalue)
                if str(realvalue) == 'nan':
                    rrdvalues.append(onNanReturn)
                else:
                    rrdvalues.append(realvalue)
            except rrdtool.error, e:
                # We failed to fetch a value. Append onErrorReturn to
                # the list
                rrdvalues.append(onErrorReturn)

        return rrdvalues


    def min(self):
        """Returns the local minima of the valid rrd-data"""
        minList = []
        for presentation in self.fetchValid():
            minList.append(min(presentation['data']))
        return minList

        
    def validPoints(self):
        """Returns list of [number of points,number of invalid points, invalid/number of points]"""
        valid = []
        a = self.fetchValid()
        for i in a:
            ret = [len(i['data'])]
            ret.append(i['data'].count(self.none))
            ret.append(ret[1]/float(ret[0]))
            valid.append(ret)
        return valid
            
    def timeLast(self,timeframe='day', value=1):
        """Sets the timeframe of the presentation
        Currently valid timeframes: year,month,week,hour,day,minute"""
        self.toTime = 'now'
        if timeframe   == 'year':
            self.fromTime = 'now-%sY' % value
            self._timeFrame = 'year'
            
        elif timeframe == 'month':
            self.fromTime = 'now-%sm' % value
            self._timeFrame = 'month'

        elif timeframe == 'week':
            self.fromTime = 'now-%sw' % value
            self._timeFrame = 'week'
            
        elif timeframe == 'day':
            self.fromTime = 'now-%sd' % value
            self._timeFrame = 'day'
            
        elif timeframe == 'hour':
            self.fromTime = 'now-%sh' % value
            self._timeFrame = 'hour'
            
        elif timeframe == 'day':
            self.fromTime = 'now-%sd' % value
            self._timeFrame = 'day'
        
        else:
            self.fromTime = 'now-%smin' % value
            self._timeFrame = 'minute'
             
    def removeAllDs(self):
        """Removes all datasources from the presentation object"""
        self.datasources = []
    
    def removeDs(self,ds_id):
        """Removes the datasource specified by rrd_datasourceid"""
        ds = datasource(ds_id)
        self.datasources.remove(ds)

    def setYAxis(self, y):
        self.yaxis = y
    
    def graphUrl(self):
        """Generates an url to a image representing the current presentation"""
        url = 'graph.py'
        index = 0
        params = ['-w' + str(self.graphWidth),
                  '-h' + str(self.graphHeight),
                  '-s' + self.fromTime,
                  '-e' + self.toTime,
                  '--no-minor',
                  ]
        try:
            params.append('-t %s' % self.title)
        except NameError:
            pass

        if self.yaxis:
            params.append('--rigid')  # Rigid boundry mode
            params.append('--upper-limit')
            params.append(str(self.yaxis)) # allows 'zooming'
        units = []    
       
        for ds in self.datasources:
            color_max = {0:'#6b69e1',
                         1:'#007F00',
                         2:'#7F0000',
                         3:'#007F7F',
                         4:'#7F7F00'
                         ,5:'#7F007F'
                         ,6:'#000022'
                         ,7:'#002200'
                         ,8:'#220000'}            

            color ={0:"#00cc00",
                    1:"#0000ff",
                    2:"#ff0000",
                    3:"#00ffff",
                    4:"#ff00ff",
                    5:"#ffff00",
                    6:"#cc0000",
                    7:"#0000cc",
                    8:"#0080C0",
                    9:"#8080C0",
                    10:"#FF0080",
                    11:"#800080",
                    12:"#0000A0",
                    13:"#408080",
                    14:"#808000",
                    15:"#000000",
                    16:"#00FF00",
                    17:"#0080FF",
                    18:"#FF8000",
                    19:"#800000",
                    20:"#FB31FB"}

            #color = {0:'#0F0CFF',
            #         1:'#00FF00',
            #         2:'#FF0000',
            #         3:'#00FFFF',
            #         4:'#FFFF00',
            #         5:'#FF00FF',
            #         6:'#000044',
            #         7:'#004400',
            #         8:'#440000'}
            rrd_variable = 'avg'+str(index)
            rrd_max_variable = 'max'+str(index)
            rrd_filename = ds.fullPath()
            rrd_datasourcename = ds.name
            linetype = ds.linetype
            linetype_max = 'LINE1'
            legend = ds.legend
            if ds.units and ds.units.count("%"):
                # limit to [0,100]
                params += ['--upper-limit', '100', '--lower-limit', '0']
            params += ['DEF:'+rrd_variable+'='+rrd_filename+':'+rrd_datasourcename+':AVERAGE']
            # Define virtuals to possibly do some percentage magical
            # flipping
            virtual = 'CDEF:v_'+rrd_variable+'='
            if ds.units and ds.units.startswith('-'):
                # availability is flipped up-side down, revert
                # and show as percentage
                virtual += '1,%s,-' % rrd_variable
                units.append(ds.units[1:])
            else:
                if ds.units:
                    units.append(ds.units)
                virtual += rrd_variable
            if ds.units and ds.units.endswith("%"):
                # percent, check if we have to do some scaling...
                scalingfactor = ds.units[:-1] # strip %
                if scalingfactor.startswith('-'):
                    scalingfactor = scalingfactor[1:]
                try:
                    int(scalingfactor)
                    virtual += ',100,*'
                except ValueError:
                    pass
                
            params += [virtual]
            params += [linetype+':v_'+rrd_variable+color[index % len(color)]+':'+''+legend+'']

            a = rrdtool.info(rrd_filename)
            # HVA I HELVETE SKJER HER!?!?!??!?!
            if self.showmax and 'MAX' in [a.get('rra')[i].get('cf') for i in range(len(a.get('rra')))] :
                legend += ' - MAX'
                params += ['DEF:'+rrd_max_variable+'='+rrd_filename+':'+rrd_datasourcename+':MAX']
                virtual = 'CDEF:v_'+rrd_max_variable+'='
                if ds.units and ds.units.startswith('-'): # begins with -
                    # availability is flipped up-side down, revert
                    # and show as percentage
                    virtual += '1,%s,-' % rrd_max_variable
                else:
                    virtual += rrd_max_variable

                if ds.units and ds.units.endswith("%"):
                    # percent, check if we have to do some scaling...
                    scalingfactor = ds.units[:-1] # strip %
                    if scalingfactor.startswith('-'):
                        scalingfactor = scalingfactor[1:]
                    try:
                        int(scalingfactor)
                        virtual += ',100,*'
                    except ValueError:
                        pass
            
                params += [virtual]
                params += [linetype_max+':v_'+rrd_max_variable+color_max[index]+':'+''+legend+'']
                
            index += 1
            
        if index == 0:
            params += ["COMMENT:''"]
        if units:
            params.insert(0,'-v')
            # Ok, join together with / if there is several
            # different units
            def uniq(list):
                a = {}
                return [x for x in list
                        if not a.has_key(x) and a.setdefault(x,True)]
            units = uniq(units)
            unitStrings = []
            for unit in units:
                unitStrings.append(unitmap.get(unit, unit))
            params.insert(1, '/'.join(unitStrings))
        id = self.genImage(*params)
        return '/rrd/image=%s/' % str(id)

    def genImage (self,*rrd_params):
        conf = nav.config.readConfig(configfile)
        id = str(random.randint(1,10**9))
        imagefilename = conf['fileprefix'] + id + conf['filesuffix']
        rrd_params = (imagefilename,) + rrd_params
        try:
            size = rrdtool.graph(*rrd_params)
        except rrdtool.error, err:
            pass
        deadline = 60*10
        for i in glob.glob('/tmp/rrd*'):
            if os.path.getmtime(i) <  (time.time() - deadline):
                try:
                    os.unlink(i)
                except:
                    pass
        return id


class page:
    def __init__(self, repr=None):
        """
        repr must be a dict as created by serialize()
        """
        self.presentations = []
        self.timeframe = "day"
        self.name = ''
        self.timeframeIndex = 1
        if repr:
            self.deSerialize(repr)

    def deSerialize(self, repr):
        if type(repr) != dict:
            return
        presentations = repr['presentations']
        self.timeframe = repr['timeframe']
        for pres in presentations:
            newPres = presentation(tf=self.timeframe)
            for ds in pres['datasources']:
                newPres.addDs(ds)
            self.presentations.append(newPres)
    def serialize(self):
        repr = {}
        repr['presentations'] = []
        for i in self.presentations:
            repr['presentations'].append(i.serialize())
        repr['timeframe'] = self.timeframe
        repr['name'] = self.name
        return repr
    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name
       

        
def graph(req,id):
    conf = nav.config.readConfig(configfile)
    filename = conf['fileprefix'] + id + conf['filesuffix']
    req.content_type  = 'image/gif'
    req.send_http_header()
    f = open(filename)
    req.write(f.read())
    f.close()
