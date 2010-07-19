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
# $Id$
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#
"""
A simple double ended queue
"""

class DEQueueEmptyError(LookupError):
    pass
class DEQueue:
    def __init__(self,stuff=()):
        self.rep=[None]*8
        self.hd=0
        self.size=0
        for x in stuff:
            self.put(x)
    def put(self,x):
        "Put at end of a DEQueue: q.put(x)"
        if self.size==len(self.rep):
            self.rep=self.rep[self.hd:]+  \
                self.rep[:self.hd]+  \
                [None]*len(self.rep)
            self.hd=0
        self.rep[(self.hd+self.size)%len(self.rep)]=x
        self.size=self.size+1
    def push(self,x):
        "Push at front of a DEQueue: q.push(x)"
        if self.size==len(self.rep):
            self.rep=self.rep[self.hd:]+  \
                self.rep[:self.hd]+  \
                [None]*len(self.rep)
            self.hd=0
        self.hd=self.hd-1
        if self.hd<0:
            self.hd=self.hd+len(self.rep)
        self.size=self.size+1
        self.rep[self.hd]=x
    def get(self):
        "Get item from front of a DEQueue: q.get()"
        if self.size==0:
            raise DEQueueEmptyError
        x=self.rep[self.hd]
        self.rep[self.hd]=None
        self.hd=(self.hd+1)%len(self.rep)
        self.size=self.size-1
        return x
    def pop(self):
        "Pop item from front of a DEQueue: =q.get()"
        return self.get()
    def pull(self):
        "Get item from end of a DEQueue: q.pull()"
        if self.size==0:
            raise DEQueueEmptyError
        i=(self.hd+self.size-1)%len(self.rep)
        x=self.rep[i]
        self.rep[i]=None
        self.size=self.size-1
        return x
    def copy(self):
        "Copy of a DEQueue: q.copy()"
        x=DEQueue()
        x.rep=self.rep[:]
        x.hd=self.hd
        x.size=self.size
        return x
    def __getitem__(self,i):
        "Look at i-th item: q[i]"
        if i<0: 
            i = self.size + i
        if i<0 or i>=self.size:
            raise IndexError
        return self.rep[(self.hd+i)%len(self.rep)]
    def __len__(self):
        'Return the length of queue: len(q)'
        return self.size
    def __nonzero__(self):
        'Return true if the queue is not empty: if q:'
        return self.size!=0
    def __repr__(self):
        'Return a string showing the contents of the queue: repr(q)'
        j=self.hd+self.size
        if j<=len(self.rep):
            s=self.rep[self.hd:j]
        else:
            s=self.rep[self.hd:]+  \
                self.rep[:j%len(self.rep)]
        return "DEQueue("+repr(s)+")"
    def __str__(self):
        'Return a string showing the contents of the queue: str(q)'
        return repr(self)

