#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# $Id$
# Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
#
"""
The library part of the Messages subsystem.
"""

from conf import BASEPATH, DATEFORMAT, LIMIT, connection, database

import re
from mx import DateTime
from time import strftime

from nav.web import shouldShow

class Message:
    """Defines the communication format that is used between the scripts and the templates"""
    
    def __init__(self, user, emotdid, type, publish_start, publish_end, last_changed, author, title, description, detail, affected, downtime, replaces_emotd, replaces_title, maint_start, maint_end, state, equipment):
        self.emotdid = emotdid
        if last_changed and not isinstance(last_changed, str):
            last_changed = strftime("%Y-%m-%d %H:%M",last_changed.tuple())
        if publish_start and not isinstance(publish_start, str):
            publish_start = strftime("%Y-%m-%d %H:%M",publish_start.tuple())
        if publish_end and not isinstance(publish_end, str):
            publish_end = strftime("%Y-%m-%d %H:%M",publish_end.tuple())
        if maint_start and not isinstance(maint_start, str):
            maint_start = strftime("%Y-%m-%d %H:%M",maint_start.tuple())
        if maint_end and not isinstance(maint_end, str):
            maint_end = strftime("%Y-%m-%d %H:%M",maint_end.tuple())

        # if a the user is alse the author, then the edit is change, else it is followup
        self.own = False
        if user == author:
            self.own = True
        if description:
            description = textpara(description)
        if detail:
            # splitting the text into paragraphs (html)
            detail = textpara(detail)
        self.last_changed = last_changed
        self.publish_start = publish_start
        self.publish_end = publish_end
        self.maint_start = maint_start
        self.maint_end = maint_end
        self.author = author
        self.title = title
        self.description = description
        self.detail = detail
        self.affected = affected
        self.downtime = downtime

# commented out language crap
##         self.title_en = title_en
##         self.description_en = description_en
##         self.detail_en = detail_en
##         self.affected_en = affected_en
##         self.downtime_en = downtime_en
        self.replaces_emotd = replaces_emotd
        self.replaces_title = replaces_title
        self.equipment = equipment
        self.type = type
                 

class MessageListMessage:
    """ Short form of communication interface. units and maintenance info is not part of this stripped down version. Only the number of units assigned to the message."""
    def __init__(self,id,title,description,last_changed,author,type,publish_start = None, publish_end = None, affected = "", downtime = "", units = 0):
        self.id = int(id)
        self.title = title
        self.description = description
        self.last_changed = last_changed.strftime(DATEFORMAT)
        self.author = author
        self.type = type
        self.publish_start = publish_start
        self.publish_end = publish_end
        self.affected = affected
        self.downtime = downtime
        self.units = units
        self.new = 0
        if last_changed>DateTime.today():
            self.new = 1


def messagelist(user,view="active",offset=0):
    """ The actual message list database query method"""
    
    access = False
    if shouldShow(BASEPATH+'edit',user):
        access = True

    if offset:
        offset = int(offset)
        
    if access and view == "planned":
        time = "publish_start > now()"
    elif access and view == "historic":
        time = "publish_end < now()"
    else:
        time = "publish_end > now() and publish_start < now()"

    if access:
        database.execute("select emotd.emotdid, title, description, last_changed, author, type, publish_start, publish_end, affected, downtime, count(value) as units from emotd left outer join emotd_related using (emotdid) where %s group by emotd.emotdid, title, description, last_changed, author, type, publish_start, publish_end, affected, downtime order by last_changed desc, publish_end desc limit %d offset %d" %(time,LIMIT,offset*LIMIT))
    else:
        database.execute("select emotd.emotdid, title, description, last_changed, author, type, publish_start, publish_end, affected, downtime, count(value) as units from emotd left outer join emotd_related using (emotdid) where %s and type != 'internal' group by emotd.emotdid, title, description, last_changed, author, type, publish_start, publish_end, affected, downtime order by last_changed desc, publish_end desc limit %d offset %d" %(time, LIMIT, offset*LIMIT))

    messages = []
    for (id, titile, description, last_changed, author, type, publish_start, publish_end, affected, downtime, units) in database.fetchall():
        messages.append(MessageListMessage(id, titile, description, last_changed, author, type, publish_start, publish_end, affected, downtime, units))
        
    return messages
    
def equipmentlist(emotdid):
    """ Makes a list of equipment used by maintenance/. """

    sql = "select emotdid, key, value from emotd left outer join emotd_related using (emotdid) where emotdid=%d order by publish_end desc" % int(emotdid)
    database.execute(sql)
    
    equipment = {}
    for (emotdid, key, value) in database.fetchall():
        if not equipment.has_key(emotdid):
            equipment[emotdid] = {}
        if not equipment[emotdid].has_key(key):
            equipment[emotdid][key] = []
        equipment[emotdid][key].append(value)

    for a,b in equipment.items():
        equipment[emotdid] = equipmentformat(equipment[emotdid])
        
    return equipment




def equipmentformat(eqdict):
    """ Makes a nice representation of the units in assosiated lists, ex: {netbox: [1,2,3,4], location: [10,20]. Gathers extra representational data from database."""
    
    resdict = {}
    if eqdict:
        if eqdict.has_key("location"):
            resdict["location"] = []
            for l in eqdict["location"]:
                try:
                    database.execute("select descr from location where locationid = '%s'" % l)
                    resdict["location"].append((l, "%s (%s)" % (l,database.fetchone()[0])))
                except:
                    resdict["location"].append((l,l))

        if eqdict.has_key("room"):
            resdict["room"] = []
            for l in eqdict["room"]:
                try:
                    database.execute("select descr from room where roomid = '%s'" % l)
                    resdict["room"].append((l,"%s (%s)" % (l,database.fetchone()[0])))
                except:
                    resdict["room"].append((l,l))
                    
        if eqdict.has_key("netbox"):
            resdict["netbox"] = []
            for l in eqdict["netbox"]:
                try:
                    database.execute("select sysname from netbox where netboxid = '%s'" % l)
                    resdict["netbox"].append((l,database.fetchone()[0]))
                except:
                    resdict["netbox"].append((l,l))
        if eqdict.has_key("service"):
            resdict["service"] = []
            for l in eqdict["service"]:
                try:
                    database.execute("select sysname from handler, netbox inner join service using (netboxid) where serviceid = '%s'" % l)
                    resultat = database.fetchone()
                    resdict["service"].append((l,"%s (%s)" % (resultat[0], resultat[1])))
                except:
                    resdict["service"].append((l,l))
    return resdict

def textpara(text):
    """ Formats the paragraphed text according to html syntax."""
    text = re.sub("\n+", "</p><p>", text)
    return "<p>" + text + "</p>"

#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# $Id$
# Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
#
"""
Library classes and functions for the Messages subsystem.
"""

class MaintListElement:
    def __init__(self, message, title, start, end, key):
        self.message = int(message)
        self.title = title
        self.locationid = ""
        self.locationdescr =""
        self.roomid = ""
        self.roomdescr = ""
        self.netboxid = 0
        self.sysname = ""
        self.serviceid = 0
        self.handler = ""
        self.moduleid = 0
        self.module = ""
        self.moduledescr = ""
        self.category = key
        if start:
            start = start.strftime(DATEFORMAT)
        if end:
            end = end.strftime(DATEFORMAT)
        self.start = start
        self.end = end

    def setLocation(self,locationid, descr):
        self.locationid = locationid
        self.locationdescr = descr
        
    def setRoom(self,roomid, descr):
        self.roomid = roomid
        self.roomdescr = descr

    def setNetbox(self,netboxid, sysname):
        if netboxid:
            self.netboxid = int(netboxid)
        self.sysname = sysname

    def setService(self,serviceid,handler):
        self.serviceid = int(serviceid)
        self.handler = handler

    def setModule(self,moduleid, module, descr):
        self.moduleid = int(moduleid)
        self.module = module
        self.moduledescr = descr

def getMaintTime(emotdid=None):
    """ Makes useful representation of maintenance start and maintenance end. Is it still in use?"""
    
    maintenance = None
    if emotdid:
        database.execute("select maint_start,maint_end from maintenance where emotdid=%d" % int(emotdid))
        maintenance = database.fetchone()
    if maintenance:
        start = maintenance[0]
        end = maintenance[1]
    else:
        start = DateTime.now()
        end = DateTime.now() + DateTime.RelativeDateTime(days=+7)

    (year,month,day,hour,minute) = start.tuple()[0:5]
    if not maintenance:
        minute = 0
    start = (year,month,day,hour,minute)
    
    (year,month,day,hour,minute) = end.tuple()[0:5]
    if not maintenance:
        minute = 0
    end = (year,month,day,hour,minute)
            
    return (start,end)
