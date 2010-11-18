# -*- coding: ISO8859-1 -*-
#
# Copyright 2002 Norwegian University of Science and Technology
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
# Inspired by a example in Thomas W. Christopher's excellent book
# Python Programming Patterns. 
#
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#

import operator
#one of these will be called to choose the 
# new priority when an item is reinserted.
#The first parameter will be the priority
# of the previous item, the second will be the
# priority of the new item.
minprio=min
maxprio=max
sumprio=operator.add
def oldprio(x,y): return x
def newprio(x,y): return y

# these functions determine whether the first
# or second argument should be preferred.
# one of them is passed to parameter "first"
#when the queue is created
def smallerfirst(x,y): return x<y
def largerfirst(x,y): return y<x

class prioque:
    def __init__(self,before=smallerfirst, \
            newprio=None):
        self.q=[(None,None)]
        self.before=before
        if newprio==None:
            self.newprio=self.__beforeprio
        else:
            self.newprio=newprio
        self.loc={}
    def __beforeprio(self,x,y):
        if self.before(x,y): return x
        else: return y
    def __siftHole(self,i):
        j=i+i
        n=len(self.q)
        while j<n:
            k=j+1
            if k<n and \
                self.before(self.q[k][0],self.q[j][0]):
                j=k
            self.q[i]=self.q[j]
            i=j
            j=i+i
        return i
    def __siftRootwards(self,i):
        j=i/2
        while j>0:
            if self.before(self.q[j][0],self.q[i][0]):
                break
            self.q[i],self.q[j]=self.q[j],self.q[i]
            i=j
            j=j/2
        return i
    def __setLocs(self,lo,hi):
        i=hi
        while i>=lo:
            self.loc[self.q[i][1]]=i
            i=i/2
    def __delete(self,i):
        item=self.q[i]
        del self.loc[item[1]] #record item not present
        t=self.q[-1] #item from last position
        del self.q[-1] #reduce size
        if len(self.q)==1:
            #last item removed
            self.loc.clear()
            return item
        j=self.__siftHole(i) #sift hole from i to leaf
        self.q[j]=t #fill with old last item
        self.loc[t[1]]=j #record its new loc (?)
        k=self.__siftRootwards(j) #move to new position
        self.__setLocs(min(i,k),max(i,k)) #adjust table
        return item #return item removed
        
    def put(self,prio,item): 
        '''q.put(priority,item)
        puts the item with the given priority into 
        the queue. The priorities must be comparable 
        values, e.g. cmp() is defined for the priorities.'''
        if self.loc.has_key(item):
            #if inserting again
            i=self.loc[item]
            #get old priority
            oldprio=self.q[i][0]
            #calculate new priority to use:
            newprio=self.newprio(oldprio,prio)
            if newprio==oldprio:
                return
            t=(newprio,item)
            if self.before(newprio,oldprio):
                self.q[i]=t
                j=self.__siftRootwards(i)
                self.__setLocs(j,i)
            else:
                j=self.__siftHole(i)
                self.q[j]=t
                k=self.__siftRootwards(j)
                self.__setLocs(min(i,k),j)
            return
        #if new item
        n=len(self.q)         
        self.q.append((prio,item))
        #self.loc[item]=n
        i=self.__siftRootwards(n)
        self.__setLocs(i,n)
    
    def remove(self,item):
        '''q.remove(item) removes the item.'''
        if self.loc.has_key(item):
            return self.__delete(self.loc[item])
        else: return None
    def getPair(self):
        '''q.getPair() 
        removes and returns (p,x) where x is the first 
        item in the queue and p is its priority. It 
        raises an exception if the queue is empty. '''
        if len(self.q)==1:
            raise IndexError("empty priority queue")
        item=self.__delete(1)
        return item
    def get(self):
        '''q.get() removes and returns the first 
        (highest priority) item in the queue. It 
        raises an exception if the queue is empty.'''
        return self.getPair()[1]
    def headPair(self):
        '''q.headPair() returns (p,x) where x is 
        the first item in the queue and p is its 
        priority. It does not remove x. It raises 
        a LookupError exception if the queue is empty.'''
        return self.q[1]
    def head(self):
        '''q.head() returns the first item in the 
        queue without removing it. It raises a 
        LookupError exception if the queue is empty.'''
        return self.q[1][1]
    def __len__(self):
        '''len(q) or q.__len__() returns the number 
        of items in the queue.'''
        return len(self.q)-1
    def __getitem__(self,i):
        '''q[i] or q.__getitem__(i) returns (p,x) 
        where x is the ith item in the queue and p 
        is its priority. The items are not in an 
        obvious order.'''
        return self.q[i+1]
    def __nonzero__(self):
        '''q.__nonzero__() or if q: returns true if 
        len(q)>0, false otherwise. '''
        return len(self.q)>1
