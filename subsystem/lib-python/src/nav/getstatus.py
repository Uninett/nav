import mx.DateTime,nav.db.manage

def boxesDown():
    downList = []
    t = nav.db.manage.AlerthistNetbox()

    w = "eventtypeid = 'boxState' and end_time = 'infinity'"
    for alert in t.getAllIterator(where=w):
        shadow = False
        if alert.netbox.up == 's':
            shadow = True
        downList.append([alert.netbox.sysname,
                         alert.netbox.ip,
                         alert.start_time,
                         mx.DateTime.now() - alert.start_time,
                         shadow])
        
    return downList 

def boxesDownSortByNewest():
    downList = []
    t = nav.db.manage.AlerthistNetbox()

    w = "eventtypeid = 'boxState' and end_time = 'infinity'"
    for alert in t.getAllIterator(where=w):
        shadow = False
        if alert.netbox.up == 's':
            shadow = True
        downList.append([mx.DateTime.now() - alert.start_time,
                         alert.netbox.sysname,
                         alert.netbox.ip,
                         alert.start_time,
                         shadow])
    downList.sort()    
    return downList 
