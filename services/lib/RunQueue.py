#!/usr/bin/python2.2
"""
$Author: magnun $
$Id: RunQueue.py,v 1.5 2002/06/08 21:24:42 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/RunQueue.py,v $

TODO
* Fikse riktig navn på trådene
* Litt mer fornuftig logging
* Skal vi ha observer?

"""
from threading import *
import threading
import DEQueue
import sys, time, types
import traceback


class observer:
    def __init__(self):
        self.observees=[]
        self.hasFinished=threading.Event()

    def run(self):
        while(1):
            for each in self.observees:
                each.hasFinished.wait(10)
                #print each + " er ferdig"

	

class TerminateException(Exception):
    pass

class worker(threading.Thread):
    """
    The thread removes a job from the runqueue and executes it. If the
    runque is empty, the thread sleeps until it gets woken when a job is
    placed in the queue.

    """
    def __init__(self, rq):
        threading.Thread.__init__(self)
        self._runQueue=rq
        self._runCount=0
        self._running=1

    def run(self):
        while self._running:
            try:
                self._job=self._runQueue.deq()
                self.execute()
            except TerminateException:
                self._runQueue.numThreads-=1
                return
            except:
                traceback.print_exc()

    def execute(self):
        #print self.getName() + ' kjører jobb nr ' +str(self.runCount)
        self._runCount+=1
        self._job.run()
        if self._runCount > self._runQueue.getMaxRunCount():
            self._running=0
            self._runQueue.unusedThreadName.append(self.getName())
            self._runQueue.workers.remove(self)


class RunQueue:
    def __init__(self,**kwargs):
        self.maxThreads=kwargs.get('maxthreads', sys.maxint)
        self.numThreads=0
        self.numThreadsWaiting=0
        self._maxRunCount=5
        self.workers=[]
        self.unusedThreadName=[]
        self.rq=DEQueue.DEQueue()
        self.lock=RLock()
        self.awaitWork=Condition(self.lock)
        self.stop=0
        self.makeDaemon=1
        self.startObserver()

    def getMaxRunCount(self):
        return self._maxRunCount

    def startObserver(self):
        self.ob=observer()
        self.enq(self.ob)

    def enq(self,*r):
        self.lock.acquire()
        self.rq.put(*r)
        self.debug('Elementer i køen: %i'% (len(self.rq)))
        if self.numThreadsWaiting>0:
            self.numThreadsWaiting-=1
            self.debug('Har ventende tråd. Kaller self.awaitWork.notify()')
            self.awaitWork.notify()
        elif self.numThreads < self.maxThreads:
            t=worker(self)
            t.setDaemon(self.makeDaemon)
            self.numThreads+=1
            if len(self.unusedThreadName) > 0:
                t.setName(seld.unusedThreadName.pop())
            else:
                t.setName('worker'+str(self.numThreads))
            self.debug('Har lagd nytt trådobjekt, %s' % (t.getName()))
            self.workers.append(t)

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

    def debug(self, msg):
        if type(msg)==types.StringType:
            print msg

    def terminate(self):
        self.lock.acquire()
        self.stop=1
        self.awaitWork.notifyAll()
        self.numThreadsWaiting=0
        self.lock.release()
			
