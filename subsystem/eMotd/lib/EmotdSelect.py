"""
$Id$

This file id part of the NAV project

Contains functions for fetching eMOTDs and Maintenance-info

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Bjørn Ove Grøtan <bgrotan@itea.ntnu.no>
"""
###############################################################################
## Imports
from mx import DateTime
import nav.db.manage

cursor = nav.db.manage.Emotd.cursor()

###############################################################################
## Functions

def get(emotdid):
    ''' return a dict for given emotdid (int). Empty if not found '''
    res = {}
    try:
        m = nav.db.manage.Emotd(int(emotdid))
        for key in m._sqlFields:
            res[key] = getattr(m,key)
    except:
        pass
    return res
    
def sortedby(seq, keyfunc, order=None):
    '''
    Some magic to sort a list of dicts based on dict-keys' values:
    sortedby(b,lambda x: x['changed'])
    sortedby(b,lambda x: x['changed'],'desc')
    '''
    a = [(keyfunc(x),x) for x in seq]
    if order == "desc":
        a.reverse()
    else:
        a.sort()
    return [x for kfx, x in a]

def getAllActive(access=False):
    ''' returns a list of dicts with all active Emotds '''
    now = DateTime.now()
    where = ["publish_start < '%s'" % str(now)]
    where.append("publish_end > '%s'" % str(now))
    if access == False:
        where.append("type != 'internal'")
    orderby = ['last_changed']
    return  fetchAll(where=where,orderby=orderby)


def fetchAll(orderby=None,where=None,access=False):
    ''' returns a list of dicts with all registered Emotds'''
    res = []
    if where == None:
        if access == False:
            where = ["type != 'internal'"]

    motdlist = nav.db.manage.Emotd.getAllIDs(where=where,orderBy=orderby)
    motdlist.reverse()
    for entry in motdlist:
        t = {}
        m = nav.db.manage.Emotd(entry)
        t['emotdid'] = m.emotdid
        t['replaces_emotd'] = m.replaces_emotd
        t['author'] = m.author
        t['last_changed'] = str(m.last_changed)[0:10]
        t['title'] = m.title
        t['title_en'] = m.title_en
        t['description'] = m.description
        t['description_en'] = m.description_en
        t['detail'] = m.detail
        t['detail_en'] = m.detail_en
        t['affected'] = m.affected
        t['affected_en'] = m.affected_en
        t['publish_start'] = m.publish_start
        t['publish_end'] = m.publish_end
        t['downtime'] = m.downtime
        t['downtime_en'] = m.downtime_en
        t['type'] = m.type
        res.append(t)
    return res

def getMaintenance(active=True,orderby=None,where=None,access=False):
    res = []
    if where == None:
        if access == False:
            return res
    if active == True:
        where = ["state = 'active'"]
    #maintlist = nav.db.manage.Maintenance_view.Emotd.getAllIDs(where=where,orderBy=orderby)
    # temp hack, have to put maintenance_view into forgetSQL
    cursor.execute("select * from maintenance_view WHERE state = 'active'")
    rows = cursor.dictfetchall()
    #for entry in maintlist:
    for row in rows:
        #so... let's store roomid,netboxid,etc for later use also
        if row['key'] == 'service':
            row['netbox'] = nav.db.manage.Service(row['value']).netbox
        if row['key'] == 'netbox':
            row['room'] = nav.db.manage.Netbox(row['value']).room
        if row['key'] == 'room':
            row['room'] = row['value']
        res.append(row)
    return res


