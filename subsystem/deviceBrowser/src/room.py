from mod_python import apache
from nav import tables
from nav import database
from nav import utils
from errors import *
import forgetHTML as html

def process(request):
    args = request['args']
    if not args:
        # We need a trailing /
        raise RedirectError, "http://isbre.itea.ntnu.no/stain/room/"    

    if args[0] == "":
        return showIndex()
    return getAllInRoom(args[0])
def showIndex():
    result = html.Division()
    result.append(html.Header("All rooms", level=1))
    rooms = tables.Room.getAll(orderBy='roomid')
    for room in rooms:
        link = html.Anchor(room.roomid, href=room.roomid)
        line = html.Division(link)
        line.append("%s %s" % (room.descr, room.location))
        result.append(line)
    return result

def getAllInRoom(roomid):
    room = tables.Room(roomid)
    netboxes = room.getChildren(tables.Netbox, orderBy="sysname")
    result = html.Division()
    result.append(html.Header("Netboxes in room: %s" % room.roomid))
    for netbox in netboxes:
        link = html.Anchor(netbox.sysname, href="../%s" % netbox.sysname)
        line = html.Division(link)
        result.append(line)
    return result
