#!/usr/bin/python2.2
"""
$Author: magnun $
$Id: RunQueue.py,v 1.3 2002/06/05 12:18:44 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/RunQueue.py,v $

TODO
* Fikse riktig navn på trådene
* Litt mer fornuftig logging
* Skal vi ha observer?

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

class worker(threading.Thread):
    def __init__(self, rq):
        threading.Thread.__init__(self)
        self.runQueue=rq
        self.runCount=0
        self.running=1

    def run(self):
        while self.running:
            try:
                self.job=self.runQueue.deq()
                self.execute()
            except TerminateException:
                runQueue.numThreads-=1
                return
            except:
                traceback.print_exc()

    def execute(self):
        print self.getName() + ' kjører jobb nr ' +str(self.runCount)
        self.runCount+=1
        self.job.run()
        if self.runCount > self.runQueue.maxRunCount:
            self.running=0
            self.runQueue.workers.remove(self)


class RunQueue:
    def __init__(self,**kwargs):
        self.maxThreads=kwargs.get('maxthreads', sys.maxint)
        self.numThreads=0
        self.numThreadsWaiting=0
        self.maxRunCount=5
        self.workers=[]
        self.rq=DEQueue.DEQueue()
        self.lock=RLock()
        self.awaitWork=Condition(self.lock)
        self.stop=0
        self.makeDaemon=1
        self.startObserver()

    def startObserver(self):
        self.ob=observer()
        print 'køer observer'
        self.enq(self.ob)

    def enq(self,*r):
        self.lock.acquire()
        self.rq.put(*r)
        print 'Elementer i køen: '+ str(len(self.rq))
        if self.numThreadsWaiting>0:
            self.numThreadsWaiting-=1
            print 'Har ventende tråd. Kaller notify()'
            self.awaitWork.notify()
        elif self.numThreads < self.maxThreads:
            t=worker(self)
            print 'lager nytt trådobjekt'
            t.setDaemon(self.makeDaemon)
            self.numThreads+=1
            t.setName('worker'+str(self.numThreads))
            self.workers.append(t)

            t.start()
        self.lock.release()

    def deq(self):
        self.lock.acquire()
        while len(self.rq)==0:
            print 'Jobbkøen er tom. Venter...'
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
			
