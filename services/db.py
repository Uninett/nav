"""
$Author: magnun $
$Id: db.py,v 1.1 2002/06/15 21:30:47 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/db.py,v $

"""

import thread, psycopg, job, Queue

class db(threading.Thread):
    def __init__(self, dsn):
        threading.Thread.__init__(self)
        self._db = psycopg.connect(dsn)
        self._queue = Queue.Queue()

    def run(self):
        c = self._db.cursor()
        while 1:
            statement = self._queue.get()
            c.execute(statement)

    def newEvent(self, event):
        print "New event. Id: %i Status: %s Info: %s"% (event.id, event.status, event.info)

    def newVersion(self, serviceid, version):
        statement = "UPDATE service SET version = '%s' where serviceid = %i" % (version,serviceid)
        self._queue.put(statement)

    def getJobs(self):
        c = self._db.cursor()
        query = """SELECT serviceid, property, value
        FROM serviceproperty
        order by serviceid"""
        c.execute(query)
        property = {}
        for serviceid,prop,value in c.fetchall():
            if serviceid not in property:
                property[serviceid] = {}
                property[serviceid][prop] = value
                
                query = """SELECT serviceid, handler, version, ip
                FROM service NATURAL JOIN boks order by serviceid"""
                c.execute(query)
                jobs = []

                for serviceid,handler,version,ip in c.fetchall():
                    job = jobmap.get(handler,'')
                    if not job:
                        print 'no such handler:',handler
                        newJob = job(serviceid,ip,property.get(serviceid,{}),version)
                        jobs += [newJob]
                        return jobs
                    
