"""
$Author: magnun $
$Id: RunQueue.py,v 1.24 2003/01/03 15:47:02 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/RunQueue.py,v $

"""
from threading import *
import threading, DEQueue, sys, time, types, traceback, debug, config
import prioqueunique
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
        if self._runqueue.getMaxRunCount() != 0 and self._runcount > self._runqueue.getMaxRunCount():
            self._running=0
            self._runqueue.unusedThreadName.append(self.getName())
            self._runqueue.workers.remove(self)
            self.debug.log("%s is recycling."% self.getName())
        self.debug.log("%s finished job number %i" % (self.getName(), self._runcount),7)
        self._timeStartExecute=0


def RunQueue(*args, **kwargs):
    if _RunQueue._instance is None:
        _RunQueue._instance=_RunQueue(*args,**kwargs)
    return _RunQueue._instance

class _RunQueue:
    _instance=None
    def __init__(self,**kwargs):
        self.conf=config.serviceconf()
        self.debug=debug.debug()
        self._maxThreads=int(self.conf.get('maxthreads', sys.maxint))
        self.debug.log("Setting maxthreads=%i" % self._maxThreads)
        self._maxRunCount=int(self.conf.get('recycle interval',50))
        self.debug.log("Setting maxRunCount=%i" % self._maxRunCount)
        self._controller=kwargs.get('controller',self)
        self.numThreadsWaiting=0
        self.workers=[]
        self.unusedThreadName=[]
        self.rq=DEQueue.DEQueue()
        self.pq=prioqueunique.prioque()
        self.lock=RLock()
        self.awaitWork=Condition(self.lock)
        self.stop=0
        self.makeDaemon=1

    def getMaxRunCount(self):
        return self._maxRunCount

    def enq(self, r):
        self.lock.acquire()
        # Jobs with priority is put in a seperate queue
        if type(r) == types.TupleType:
            pri,obj=r
            self.pq.put(pri,obj)
        else:
            self.rq.put(r)

        #self.debug.log("Number of workers: %i Waiting workers: %i" % (len(self.workers),self.numThreadsWaiting))
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
        while 1:
            # wait if we have no jobs in queue
            while len(self.rq)==0 and len(self.pq)==0:
                if self.stop:
                    self.lock.release()
                    raise TerminateException
                self.numThreadsWaiting+=1
                self.awaitWork.wait()
            if self.stop: 
                self.lock.release()
                raise TerminateException

            if len(self.pq)>0:
                scheduledTime, obj = self.pq.headPair()
                scheduledTime=float(scheduledTime)
                now=time.time()
                wait=scheduledTime-now
                # If we have priority ready we
                # return it now.
                if wait <= 0:
                    r=self.pq.get()
                    self.lock.release()
                    return r
            # We have no priority jobs ready.
            # Check if we have unpriority jobs
            # to execute
            if len(self.rq) > 0:
                r=self.rq.get()
                self.lock.release()
                return r
            # Wait to execute priority job, break if new jobs arrive
            else:
                self.numThreadsWaiting+=1
                self.debug.log("Thread waits for %s secs"%wait,7)
                self.awaitWork.wait(wait)
            

    def terminate(self):
        self.lock.acquire()
        self.stop=1
        self.awaitWork.notifyAll()
        self.numThreadsWaiting=0
        self.lock.release()
	self.debug.log("Waiting for threads to terminate...")
        for i in self.workers:
            i.join()
        self.debug.log("All threads have finished")
