#!/usr/bin/python2.2
"""
$Author: magnun $
$Id: RunQueue.py,v 1.1 2002/06/04 09:26:44 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/RunQueue.py,v $
"""
from threading import *
import threading
import DEQueue
import sys, time
import traceback


class observer:
    def __init__(self):
        self.observees=[]
        self.hasFinished=threading.Event()

    def run(self):
        print 'starter observer'
        while(1):
            for each in self.observees:
                each.hasFinished.wait(10)
                #print each + " er ferdig"

	

class TerminateException(Exception):
    pass

def runStrategy(runnable, rq):
    runnable.starttime=time.time()
    rq.ob.observees.append(runnable)
    print 'kaller run() på objektet'
    runnable.run()
    print 'ting er ferdig :)'

def simpleRunStrategy(runnable,rq):
    runnable.run()

def execute(runQueue,runStrategy):
    while 1:
        try:
            r=runQueue.deq()
            runStrategy(r,runQueue)
        except TerminateException:
            runQueue.numThreads-=1
            return
        except:
            traceback.print_exc()

class RunQueue:
    def __init__(self,**kwargs):
        self.runStrategy=kwargs.get('runstrategy', runStrategy)
        self.maxThreads=kwargs.get('maxthreads', sys.maxint)
        self.numThreads=0
        self.numThreadsWaiting=0
        self.rq=kwargs.get('queue')
        if self.rq is None:
            self.rq=DEQueue.DEQueue()
            self.lock=RLock()
            self.awaitWork=Condition(self.lock)
            self.stop=0
            self.makeDaemon=1
            self.threadfunction=kwargs.get('threadfunction', execute)
            self.startObserver()

    def startObserver(self):
        self.ob=observer()
        print 'køer observer'
        self.enq(self.ob)

    def enq(self,*r):
        self.lock.acquire()
        self.rq.put(*r)
        if self.numThreadsWaiting>0:
            self.numThreadsWaiting-=1
            self.awaitWork.notify()
        elif self.numThreads < self.maxThreads:
            t=Thread(target=self.threadfunction, args=(self,self.runStrategy))
            t.setDaemon(self.makeDaemon)
            self.numThreads+=1
            t.start()
        self.lock.release()

    def deq(self):
        self.lock.acquire()
        while len(self.rq)==0:
            if self.stop:
                self.numThreads-=1 
                self.lock.release()
                raise TerminateException
            self.numThreadsWaiting+=1
            self.awaitWork.wait()
        if self.stop: 
            self.numThreads-=1 
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
			
