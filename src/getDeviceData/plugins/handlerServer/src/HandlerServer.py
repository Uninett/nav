"""Plugin for server registering using SNMP

part of the NAVme project 
http://www.nav.ntnu.no/

(c) Stian Søiland <stain@itea.ntnu.no> 2002
"""

__version__ = "$Id: HandlerServer.py,v 1.5 2002/07/02 09:34:05 cricket Exp $"

import UserDict
import re
from array import array
import string

import no.ntnu.nav.Database.Database as db 
import no.ntnu.nav.SimpleSnmp as snmp
from no.ntnu.nav.getDeviceData.plugins import DeviceHandler
from no.ntnu.nav.getDeviceData.plugins import DeviceData

#temp code
file = "/usr/local/nav/local/etc/conf/diskException.conf"

class OID:
  """Constants for typical used OIDs"""
  sysObjectID = "1.3.6.1.2.1.1.2"
  interfaceDescriptions = "1.3.6.1.2.1.2.2.1.2"
  interfaceTypes = "1.3.6.1.2.1.2.2.1.3" 
  interfaceLoopback = "24" # really an Integer, not an OID =)
  diskDescriptions = "1.3.6.1.2.1.25.2.3.1.3" 
  diskBlockSize ="1.3.6.1.2.1.25.2.3.1.4"
  diskFilesystems = "1.3.6.1.2.1.25.3.8.1.4"
  filesystemNFS = "1.3.6.1.2.1.25.3.9.14"
  filesystemUnknown = "1.3.6.1.2.1.25.3.9.2"

class Unit:
  """A temporary way to store unit data"""
  def __init__(self, unitID, description="", type="", size="1024"):
    self.unitID = unitID
    self.description = description
    self.type = type
    self.size = size
  def __repr__(self):
    info = (self.unitID, repr(self.type), repr(self.description))
    return "<unit id=%s type=%s description=%s>" % info

class Checking:
  """ Checking which disk we will skip and if it should 
      be recursive or not """
  def rec(self , line , splitter):
    li2 = string.expandtabs(line,1)
    #print li2
    li = (string.split(li2,splitter))
    #print li
    j = 1
    for i in li[1:]:
      j = j + 1
      i = string.strip(i)
      if (i == ''):
        continue
      else:
        #print 'fant noe'
        partition = i
        break
    moveon = None
    print j
    try:
      for i in li[j:]:
        i = string.strip(i)
        if (i == 'recursive'):
          moveon = 'recursive'
      return (partition,moveon)
    except:
      return (partition,moveon)

class Units(UserDict.UserDict):
  """And a nice dictionary creating those unit for us on-the-fly"""
  def __getitem__(self, unitID):
    try:
      unitID = int(unitID) # Converts strings to integers - nice! =)
    except:
      raise KeyError, "unit id must be a number, not %s" % `unitID`
    try:
      return self.data[unitID]
    except KeyError:
      # We need to create a new one transparently
      newunit = Unit(unitID)
      self.data[unitID] = newunit
      return newunit

class HandlerServer(DeviceHandler):
  """Plugin for handling servers by using SNMP. Currently checks SNMP 
  agent version, the disks and interfaces"""

  def canHandleDevice(self, box):
    """Report if this box is our responsibility"""
    # Lower the string before compare
    print "Skal sjekke", box
    if(box.getKat().lower() == 'srv' and box.getSnmpMajor() > 0):
      # We only care about servers with snmp enabled.
      return 1  
    else:
      return 0
  def handle(self, box, snmp, deviceDataList):
    """Process this box. Called by the server for each box.

       As specified in the interface
       no.ntnu.nav.getDeviceData.plugins.DeviceHandler:
    
       box -- getDeviceData.plugins.BoksData instance of the box to
              investigate
       snmp -- SimpleSnmp.SimpleSnmp instance a snmp connection for our
               free use
       deviceDataList -- getDeviceData.plugins.DeviceDataList instance
                         with methods to store DeviceData instances - 
                         which again contains our changes
    """

    print "Handler", box

    # Prepare a DeviceData object for us to store changes in
    deviceData = DeviceData()
    # We'll "submit" this in the end
   

    # Prepare smnp connection
    snmp.setHost(box.getIp())
    snmp.setCs_ro(box.getCommunityRo())

    # Print
    print "ip", box.getIp()
    print "comm", box.getCommunityRo()


    self.getSnmpAgent(box, snmp, deviceData)
    check_array = self.getDiskconf(box)
    keep_on = 1
    for i in check_array:
      if i[0] == '*':
        keep_on = 0
        break
    if keep_on:
      self.getDisks(box, snmp, deviceData, check_array)
    self.getInterfaces(box, snmp, deviceData)

    # We're done! Submit to the old large database
    deviceDataList.setDeviceData(deviceData)

  def getDiskconf(self,box):
    """ We open the config file and insert all the disks we don't want
        to monitor in an array """

    s = Checking()
    sep = ' '
    arr = []
    conf_file = open(file ,'r')
    lines = conf_file.readlines()
    for line in lines:
      line2 = string.expandtabs(line,1)
      #line = string.strip(line)
      #her må den fjerne whitespaces på begge sider
      if ((line[0] == '#') or (line == " ") or (line == "\n") or (line=="\t")):
        continue
      elif string.find(line,'"') != -1:
        if ((line[0] == '*') or (string.split(line2,' ')[0]==box)):
          on = s.rec(line,'"')
          arr.append((on[0],on[1]))
          continue
      elif (line[0] == '*'):
        on = s.rec(line,sep)
        arr.append((on[0],on[1]))
        continue
      elif (string.split(line2,' ')[0]==box):
        on = s.rec(line,sep)
        arr.append((on[0],on[1]))
        continue


  def getSnmpAgent(self, box, snmp, deviceData):
    """Retrieve SNMP agent version and store it in the database directly
       (should use deviceData, but it currently does not support that)
    
       box -- getDeviceData.plugins.BoksData instance of the box
              to investigate
       snmp -- SimpleSnmp.SimpleSnmp instance of prepared 
               SNMP connection to the box
       deviceData -- getDeviceData.plugins.DeviceData instance
                     for storing the results
    """
    
    # Get the descriptions
    snmp.setBaseOid(OID.sysObjectID)
    result = snmp.getAll(1) 
    if(result):
      agent = result[0][1]
      print "Oh, fant agent", agent
      sql = "UPDATE boks SET snmpagent='%s' WHERE boksid='%s'" % \
            (db.addSlashes(agent), box.getBoksid())
      print "Utfører SQL:", sql      
      db.update(sql)


  def getDisks(self, box, snmp, deviceData, check_array):
    """Retrieve disk data and prepare to store in deviceData.
    
       box -- getDeviceData.plugins.BoksData instance of the box
              to investigate
       snmp -- SimpleSnmp.SimpleSnmp instance of prepared 
               SNMP connection to the box
       deviceData -- getDeviceData.plugins.DeviceData instance
                     for storing the results
    """
    
    # And now for some magic to combine decriptions and filesystem
    disks = Units()

    # Get the descriptions
    snmp.setBaseOid(OID.diskDescriptions)
    diskDescriptions = snmp.getAll(1)
    for (diskID, description) in diskDescriptions:
      # uhm.. get diskID, this is the last number in the OID
      print "Fant disk %s med deskripsjon %s" %  (diskID, description)
      disks[diskID].description = description

    # .. and their filesystems
    snmp.setBaseOid(OID.diskFilesystems)
    diskFilesystems = snmp.getAll(1)
    for (diskID, filesystem) in diskFilesystems:
      # uhm.. get diskID, this is the last number in the OID
      print "Fant disk %s med filsystem %s" %  (diskID, filesystem)
      disks[diskID].type = filesystem

    #...and also their blocksize
    snmp.setBaseOid(OID.diskBlockSize)
    diskBlockSize = snmp.getAll(1)
    for (diskID,blocksize) in diskBlockSize:
      print "Fant disk %s med blokkstr %s" % (diskID,blocksize)
      disks[diskID].size = blocksize
    
    # some sanity checks 
    for disk in disks.values():
      if(disk.type in (OID.filesystemNFS, OID.filesystemUnknown)):
        # Remove disks with filesystem NFS or "unknown" 
        # (ie. floppy/cdrom) from our list
        del disks[disk.unitID]
        continue
      
### Don't do this, cricket needs the full string, even if it's stupid     
##      # Remove the space and everything after it, if it exists
##      # (this is the case with windows mounts)
##      # NOTE: Assumes that paths are WITHOUT spaces
##      disk.description = disk.description.split(" ")[0]

      if(not disk.description or not disk.type):
        # These should not be empty. A empty 'filesystem' (ie. type)
        # usually indicates "Virtual memory" or something like that.

        # On the other hand if disk.description is empty, we have no
        # way to identify the disk, so we MUST avoid it, sadly
        # enough. 
        del disks[disk.unitID]
      
      # /dev and /proc and their childs are not interresting
      # Here we will sort out the partitions we don't want to monitor
      for i in check_array:
        if i[1] == 'recursive':
          if(re.match(r"^"+i[0], disk.description)):
            del disks[disk.unitID]
        else:
          if(i[0] == disk.description):
            del disks[disk.unitID]

    # Insert into database
    for disk in disks.values():
      deviceData.addBoksDisk(disk.description, disk.size) 
    
    deviceData.boksDiskUpdated()


  def getInterfaces(self, box, snmp, deviceData):
    """Retrieve interface names and prepare to store in deviceData.
    
       box -- getDeviceData.plugins.BoksData instance of the box
              to investigate
       snmp -- SimpleSnmp.SimpleSnmp instance of prepared 
               SNMP connection to the box
       deviceData -- getDeviceData.plugins.DeviceData instance
                     for storing the results
    """
    
    # And now for some magic to combine decriptions and interface type
    interfaces = Units()

    # Get the descriptions
    snmp.setBaseOid(OID.interfaceDescriptions)
    interfaceDescriptions = snmp.getAll(1)
    for (interfaceID, description) in interfaceDescriptions:
      # uhm.. get interfaceID, this is the last number in the OID
      print "Fant interface %s med deskripsjon %s" %  (interfaceID, description)
      interfaces[interfaceID].description = description

    # .. and their interfacetypes
    snmp.setBaseOid(OID.interfaceTypes)
    interfaceFilesystems = snmp.getAll(1)
    for (interfaceID, type) in interfaceFilesystems:
      # uhm.. get interfaceID, this is the last number in the OID
      print "Fant interface %s med type %s" %  (interfaceID, type)
      interfaces[interfaceID].type = type


    # some sanity checks 
    for interface in interfaces.values():
      if(interface.type == OID.interfaceLoopback):
        # We don't care about loopbacks!
        del interfaces[interface.unitID]
        continue
      
### Don't do this, cricket needs the full string, even if it's stupid     
##      # Remove the space and everything after it, if it exists
##      # (this is the case with windows interfaces)
##      interface.description = interface.description.split(" ")[0]

      if(not interface.description):
        # Ooops.. the description is EMPTY. This should not happen!
        # Maybe we got an interface type, but no name?
        # But.. we'll simply have to remove this interface then
        del interfaces[interface.unitID]

    # Insert into database
    for interface in interfaces.values():
      deviceData.addBoksInterface(interface.description) 
    
    deviceData.boksInterfaceUpdated()  
