#!/usr/bin/env python
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

#    rrd_fileobj = rrd_file()


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
        self.timeLastWeek()
        self.graphHeight = 195
        self.graphWidth  = 500
        self.title = ''
        self.timeFrame = 'day'
        self.timeLastDay()
        if ds != '':
            self.addDs(ds)
        

    def _updateTitle():
        for i in self.datasources:
            blapp
            

    def addDs(self,ds_id):
        """Adds a datasource to the presentation, returns the default legend"""
        ds = datasource(ds_id)
#        if not ds in self.datasources:
        self.datasources.append(ds)
        return ds.legend

    def __str__(self):
        return str(self.datasources)

    def __repr__(self):
        return str(self.datasources)

##     def fetch(self):
##         """Return the raw rrd-data as a list of dictionaries {'start':starttime in unixtime,'stop':stoptime in unixtime,'data':[data,as,list]}"""
##         returnList = []
##         for datasource in self.datasources:
##             raw = rrdtool.fetch(datasource.fullPath(),'AVERAGE','-s '+self.fromTime,'-e '+self.toTime)
##             returnDict = {}
##             returnDict['start']  = raw[0][0]
##             returnDict['stop']   = raw[0][1]
##             returnDict['deltaT'] = raw[0][2]        
            
##             row = list(raw [1]).index(datasource.name)
##             data = []
##             for i in raw[2]:
##                 if type(i[row]) == type(None):
##                     data.append(self.none)
##                 else:
##                     data.append(i[row])
##             returnDict['data'] = data
##             returnList.append(returnDict)
##         return returnList

    def fetchValid(self):
        """Return the raw rrd-data as a list of dictionaries {'start':starttime in unixtime,'stop':stoptime in unixtime,'data':[data,as,list]}"""
        returnList = []
        for datasource in self.datasources:
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
            returnList.append(returnDict)
        return returnList

##     def fetchValid(self):
##         """Returns the same data as fetch() with invalid datapoints removed"""
##         a = self.fetch()
##         for i in a:
##             i['data'] = filter(lambda x: x != self.none , i['data'])
##         return a

    
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
#            return map(lambda x,y:x/y['data'].__len__(),self.sum(),self.fetchValid())
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
        a = self.fetch()
        for i in a:
            ret = [len(i['data'])]
            ret.append(i['data'].count(self.none))
            ret.append(ret[1]/float(ret[0]))
            valid.append(ret)
        return valid
            
    def timeLastYear(self):
        tid = DateTime.now() - DateTime.RelativeDateTime(years=1) 
        toTime = int(time.time())
        fromTime   = int(tid.ticks())
        self.toTime   = str(toTime)
        self.fromTime = str(fromTime) # One year
        self.timeFrame = 'year'

    def timeLastMonth(self):
        tid = DateTime.now() - DateTime.RelativeDateTime(months=1) 
        toTime = int(time.time())
        fromTime   = int(tid.ticks())
        self.toTime   = str(toTime)
        self.fromTime = str(fromTime) # One month
        self.timeFrame = 'month'
    
    def timeLastWeek(self):
        toTime = int(time.time())
        self.toTime   = str(toTime)
        self.fromTime = str(toTime - 3600*24*7) # One week
        self.timeFrame = 'week'        

    def timeLastDay(self):
        toTime = int(time.time())
        self.toTime   = str(toTime)
        self.fromTime = str(toTime - 3600*24) # One day
        self.timeFrame = 'day'                
        
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
            #url = url + 'netboxid=%s&name=%s&' % (i.rrd_fileobj.netboxid,i.name)
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
        return 'http://isbre.itea.ntnu.no/~mjaavatt/rrdpresenter/graph?id='+id

    def genImage (self,*rrd_params):

        conf = nav.config.readConfig(configfile)
        id = str(hash(random.random()))
        imagefilename = conf['fileprefix'] + id + conf['filesuffix']
        rrd_params = (imagefilename,) + rrd_params



        try:
            size = rrdtool.graph(*rrd_params)
            print "bildet er laget"
            print size
            
        except rrdtool.error, err:
            print "RRD Error:", err

        deadline = 60*10
        for i in glob.glob('/tmp/rrd*'):

            if os.path.getmtime(i) <  (time.time() - deadline):
                try:
                    os.unlink(i)
                except:
                    pass
        return id


        

        
def graph(req,id):
    conf = nav.config.readConfig(configfile)
    filename = conf['fileprefix'] + id + conf['filesuffix']
    req.content_type  = 'image/gif'
    req.send_http_header()
    f = open(filename)
    req.write(f.read())
    f.close()
#    f.unlink(filename)
    
    
