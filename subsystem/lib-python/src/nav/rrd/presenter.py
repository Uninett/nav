"""

$Id$

rrd.presenter module

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




Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Erlend Mjaavatten <mjaavatt@itea.ntnu.no>
"""

configfile = 'rrdBrowser.conf'
import nav.db
import nav.config
import time
import rrdtool
import random
import glob
import os 
from mx import DateTime
from os import path

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
        cursor.close()
        
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


    def __eq__(self,obj):
        return obj.rrd_datasourceid == self.rrd_datasourceid


    
    def __str__(self):
        return "%s - %s" % (self.name, self.descr)

    def __repr__(self):
        return "%s - %s" % (self.name, self.descr)

    def fullPath(self):
        return self.rrd_fileobj.fullPath()
    

class presentation:
    def __init__(self,ds=''):
        self.datasources = []
        self.none = None
        self.graphHeight = 195
        self.graphWidth  = 500
        self.title = ''
        self.timeLast('day')
        if ds != '':
            self.addDs(ds)
        

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
        """Return the raw rrd-data as a list of dictionaries {'start':starttime in unixtime,'stop':stoptime in unixtime,'data':[data,as,list]}"""
        returnList = []
        for datasource in self.datasources:
            try:
                raw = rrdtool.fetch(datasource.fullPath(),'AVERAGE','-s '+self.fromTime,'-e '+self.toTime)

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
    
    def average(self):
        """Returns the average of the valid rrd-data"""
        sumList = []
        dataList = self.fetchValid()        
        for data in dataList:
            sum = 0
            for i in data['data']:
                sum += i
            sumList.append(sum)

            
        try:
            return map(lambda x,y:x/y['data'].__len__(),sumList,dataList)
        except ZeroDivisionError:
            return 0
        
    def max(self):
        """Returns the local maxima of the valid rrd-data"""
        maxList = []
        for presentation in self.fetchValid():
            maxList.append(max(presentation['data']))
        return maxList

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
            
    def timeLastYear(self):
        """Set the timeframe. DEPRECATED Use timeLast('year') instead!"""
        self.toTime   = 'now'
        self.fromTime = 'now-1Y'
        self.timeFrame = 'year'        

    def timeLastMonth(self):
        """Set the timeframe. DEPRECATED Use timeLast('month') instead!"""        
        self.toTime   = 'now'
        self.fromTime = 'now-1m'
        self.timeFrame = 'month'
    
    def timeLastWeek(self):
        """Set the timeframe. DEPRECATED Use timeLast('week') instead! """        
        self.toTime   = 'now'
        self.fromTime = 'now-1w'
        self.timeFrame = 'week'        

    def timeLastDay(self):
        """Set the timeframe. DEPRECATED Use timeLast('day') instead!"""        
        self.toTime   = 'now'
        self.fromTime = 'now-1d'
        self.timeFrame = 'day'        
        
    def timeLastHour(self):
        """Set the timeframe. DEPRECATED! Use timeLast('hour') instead!"""        
        self.toTime   = 'now'
        self.fromTime = 'now-1h'
        self.timeFrame = 'hour'        

    def timeLast(self,timeframe='day'):
        """Sets the timeframe of the presentation
        Currently valid timeframes: year,month,week,hour,day"""
        self.toTime = 'now'
        if timeframe   == 'year':
            self.fromTime = 'now-1Y'
            self._timeFrame = 'year'
            
        elif timeframe == 'month':
            self.fromTime = 'now-1m'
            self._timeFrame = 'month'

        elif timeframe == 'week':
            self.fromTime = 'now-1w'
            self._timeFrame = 'week'
            
        elif timeframe == 'day':
            self.fromTime = 'now-1d'
            self._timeFrame = 'day'
            
        elif timeframe == 'hour':
            self.fromTime = 'now-1h'
            self._timeFrame = 'hour'
            
        else:
            self.fromTime = 'now-1d'
            self._timeFrame = 'day'            
             
    def removeAllDs(self):
        """Removes all datasources from the presentation object"""
        self.datasources = []
    
    def removeDs(self,ds_id):
        """Removes the datasource specified by rrd_datasourceid"""
        ds = datasource(ds_id)
        self.datasources.remove(ds)

    
    def graphUrl(self):
        """Generates an url to a image representing the current presentation"""
        url = 'graph.py'
        index = 0
        params = ['-w'+str(self.graphWidth),'-h'+str(self.graphHeight),'-s'+self.fromTime,'-e'+self.toTime]
        try:
            params.append('-t %s' % self.title)
        except NameError:
            pass
        
        for i in self.datasources:
            color = {0:'#0000FF',1:'#00FF00',2:'#FF0000',3:'#00FFFF',4:'#FFFF00',5:'#FF00FF',6:'#000044',7:'#004400',8:'#440000'}
            rrd_variable = 'cel'+str(index)
            rrd_filename = i.fullPath()
            rrd_datasourcename = i.name
            linetype = i.linetype
            legend = i.legend
            params += ['DEF:'+rrd_variable+'='+rrd_filename+':'+rrd_datasourcename+':AVERAGE',linetype+':'+rrd_variable+color[index]+':'+''+legend+'']
            index += 1
            
        if index == 0:
            params += ["COMMENT:''"]
        
        id = self.genImage(*params)
        return 'http://isbre.itea.ntnu.no/rrd/rrdBrowser/graph?id='+id

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
    def __init__(self):
        self.presentations = []
        self.name = ''

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
#    f.unlink(filename)
    
    
