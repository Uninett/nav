#!/usr/bin/python2.2
"""
$Author: magnun $
$Id: RunQueue.py,v 1.18 2002/08/08 18:09:20 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/RunQueue.py,v $

"""
from threading import *
import threading, DEQueue, sys, time, types, traceback, debug

class TerminateException(Exception):
    pass

class observer:
    def __init__(self, rq):
        self._rq=rq
        self.debug=debug.debug()

    def run(self):
        while not self._rq.stop:
            for eachWorker in self._rq.workers[1:]:
                
                #if eachWorker._timeStartExecute and time.time()-eachWorker._timeStartExecute > 10:
                    #self.debug.log("%s has used more than 10 seconds running %s"% (eachWorker.getName(), eachWorker._job.getType(),2))

                    time.sleep(20)



class worker(threading.Thread):
    """
    The thread removes a job from the runqueue and executes it. If the
    runque is empty, the thread sleeps until it gets woken when a job is
    placed in the queue.

    """
    def __init__(self, rq):
        threading.Thread.__init__(self)
        self.debug=debug.debug()
        self._runqueue=rq
        self._runcount=0
        self._running=1
        self._timeCreated=time.time()
        self._timeStartExecute=0

    def run(self):
        """
        Tries to dequeue a job. Loops while
        self._running=1
        """
        while self._running:
            try:
                self._job=self._runqueue.deq()
                self.execute()
            except TerminateException:
                self._runqueue.workers.remove(self)
                return
            except:
                traceback.print_exc()

    def execute(self):
        """
        Executes the job. If maximum runcount is
        exceeded, self._running is set to zero and the
        thread will be recycled.
        """
        self._runcount+=1
        self._timeStartExecute=time.time()
        self._job.run()
        if self._runcount > self._runqueue.getMaxRunCount():
            self._running=0
            self._runqueue.unusedThreadName.append(self.getName())
            self._runqueue.workers.remove(self)
            self.debug.log("%s is recycling."% self.getName())
        self.debug.log("%s finished job number %i" % (self.getName(), self._runcount),7)
        self._timeStartExecute=0


class RunQueue:
    def __init__(self,**kwargs):
        self._maxThreads=kwargs.get('maxthreads', sys.maxint)
        self._controller=kwargs.get('controller',self)
        self.debug=debug.debug()
        self.numThreadsWaiting=0
        self._maxRunCount=50
        self.workers=[]
        self.unusedThreadName=[]
        self.rq=DEQueue.DEQueue()
        self.lock=RLock()
        self.awaitWork=Condition(self.lock)
        self.stop=0
        self.makeDaemon=1
        self._observer=observer(self)
        self.enq(self._observer)


    def getMaxRunCount(self):
        return self._maxRunCount

    def enq(self,*r):
        self.lock.acquire()
        self.rq.put(*r)
        self.debug.log("Number of workers: %i Waiting workers: %i" % (len(self.workers),self.numThreadsWaiting))
        if self.numThreadsWaiting>0:
            self.numThreadsWaiting-=1
            self.awaitWork.notify()
        elif len(self.workers) < self._maxThreads:
            t=worker(self)
            t.setDaemon(self.makeDaemon)
            if len(self.unusedThreadName) > 0:
                t.setName(self.unusedThreadName.pop())
            else:
                t.setName('worker'+str(len(self.workers)))
            self.workers.append(t)

            t.start()
        self.lock.release()

    def deq(self):
        self.lock.acquire()
        while len(self.rq)==0:
            if self.stop:
                self.lock.release()
                raise TerminateException
            self.numThreadsWaiting+=1
            self.awaitWork.wait()
        if self.stop: 
            self.lock.release()
            raise TerminateException
        r=self.rq.get()
        self.lock.release()
        return r

    def terminate(self):
        self.lock.acquire()
        self.stop=1
        self.awaitWork.notifyAll()
        self.numThreadsWaiting=0
        self.lock.release()
			
