"""Plugin for server registering using SNMP.

This file is part of the NAV project.

Connects with SNMP to boxes in category
srv with snmpMajor > 0, records which interfaces and 
disks the server has, as well as the OS type.

These disk/interface-mappings are later used by the 
cricket-config-maker.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Stian Søiland <stain@itea.ntnu.no> 
         Magnus Nordseth <magnun@itea.ntnu.no>
"""

__version__ = "$Id: HandlerServer.py,v 1.10 2002/10/18 09:23:15 stain Exp $"

import UserDict
import re
import os
import string
import fnmatch

from no.ntnu.nav.getDeviceData.deviceplugins import DeviceHandler

from no.ntnu.nav.logger import Log

class OID:
  """Constants for typical used OIDs"""
  sysDescr = "1.3.6.1.2.1.1.1"
  sysObjectID = "1.3.6.1.2.1.1.2"
  interfaceDescriptions = "1.3.6.1.2.1.2.2.1.2"
  interfaceTypes = "1.3.6.1.2.1.2.2.1.3" 
  interfaceLoopback = "24" # really an Integer, not an OID =)
  diskDescriptions = "1.3.6.1.2.1.25.2.3.1.3" 
  diskBlockSize ="1.3.6.1.2.1.25.2.3.1.4"
  diskFilesystems = "1.3.6.1.2.1.25.3.8.1.4"
  filesystemNFS = "1.3.6.1.2.1.25.3.9.14"
  filesystemUnknown = "1.3.6.1.2.1.25.3.9.2"
  solarisAgent = "1.3.6.1.4.1.8072.3.2.3"
  linuxAgent = "1.3.6.1.4.1.8072.3.2.10"
  other = "1.3.6.1.4.1.8072.3.2.255"
  bugAgent = "1.3.6.1.4.1.8072.3.2"

class Unit:
  """A temporary way to store unit data"""
  def __init__(self, unitID, description="", type="", size=None):
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
    option = None
    #print j
    try:
      for i in li[j:]:
        i = string.strip(i)
        if (i == 'recursive'):
          option = 'recursive'
    except:
      pass
    return (partition,option)

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

class Server(DeviceHandler):
  """Plugin for handling servers by using SNMP. Currently checks SNMP 
  agent version, the disks and interfaces"""

  def canHandleDevice(self, netbox):
    """Report if this netbox is our responsibility"""
    # Lower the string before compare
    if(netbox.getCat().lower() == 'srv' and netbox.getSnmpMajor() > 0):
      Log.d("ServerPlugin", "canHandleDevice", "We are ready to serve %s" % netbox.getSysname())
      # We only care about servers with snmp enabled.
      return DeviceHandler.ALWAYS_HANDLE  
    else:
      return DeviceHandler.NEVER_HANDLE
  def handleDevice(self, netbox, snmp, configParser, containers):
    """Process this netbox. Called by the server for each netbox.

       As specified in the interface
       no.ntnu.nav.getDeviceData.plugins.DeviceHandler:
    
       netbox -- getDeviceData.plugins.NetBox instance of the netbox to
              investigate
       snmp -- SimpleSnmp.SimpleSnmp instance a snmp connection for our
               free use
       configParser -- ConfigParser-instance with the main NAV
                       configuration file already opened
                       (used to find our base path)
       containers   -- A DataContainers instance    
    """

    self.basePath = configParser.get("NAVROOT")
    Log.setDefaultSubsystem("ServerPlugin")
    Log.d("handleDevice", "Just starting, %s" % netbox.getSysname())
    # Preparing container to store our data, we are doing this the
    # java way =)
    infoContainer = containers.getContainer("NetboxInfoContainer")
    
    # Prepare smnp connection
    snmp.setHost(netbox.getIp())
    snmp.setCs_ro(netbox.getCommunityRo())

    self.getSnmpAgent(netbox, snmp)
    self.getDisks(netbox, snmp, infoContainer)
    self.getInterfaces(netbox, snmp, infoContainer)

    # We're done! Submit to the old large database
    infoContainer.commit()

  def getDiskconf(self,netbox):
    """ We open the config file and insert all the disks we don't want
        to monitor in an array """
    sysname = netbox.getSysname()
    s = Checking()
    sep = ' '
    ignores = []
    file = os.path.join(self.basePath, 'local', 'etc', 'conf', 'diskException.conf')
    try:
      conf_file = open(file ,'r')
    except:
      Log.e("getDiskconf", "Could not open config file %s" % file)
      return [] # We failed.
    lines = conf_file.readlines()
    for line in lines:
      line2 = string.expandtabs(line,1)
      #line = string.strip(line)
      #her må den fjerne whitespaces på begge sider
      if ((line[0] == '#') or (line == " ") or (line == "\n") or (line=="\t")):
        continue
      elif string.find(line,'"') != -1:
        if (fnmatch(sysname, line2.split(' ')[0])):
          on = s.rec(line,'"')
          ignores.append((on[0],on[1]))
          continue
      elif (fnmatch(sysname, line2.split(' ')[0])):
        on = s.rec(line,sep)
        ignores.append((on[0],on[1]))
        continue
    return ignores  


  def getSnmpAgent(self, netbox, snmp):
    """Retrieve SNMP agent version and store it in the database directly
       (should use deviceData, but it currently does not support that)
    
       netbox -- getDeviceData.plugins.BoksData instance of the netbox
              to investigate
       snmp -- SimpleSnmp.SimpleSnmp instance of prepared 
               SNMP connection to the netbox
    """
    
    # Get the descriptions
    agent = netbox.getSnmpagent()
    #TEMP - this is not good but a bug in the net-snmp agent forced us
    # to set the agent like this.
    if (agent == OID.bugAgent):
      Log.d("getSnmpAgent", "Got buggy SNMP agent for %s" % netbox.getSysname())
      snmp.setBaseOid(OID.sysDescr)
      res = ""
      try:
        res = snmp.getAll(1)
        res = res[0][1]
      except:
        Log.w("getSnmpAgent", "Found no SNMP sysDescr for %s" % netbox.getSysname())
        return None # Give up

      res = res.split(" ")[0]
      if (res.lower() == "sunos"):
        agent = (OID.solarisAgent)
      elif (res.lower() == "linux"):
        agent = (OID.linuxAgent)
      else:
        agent = (OID.other)

    try:
      Log.d("getSnmpAgent", "Setting agent %s for %s" % 
                             (agent, netbox.getSysname()) )
      netbox.setSnmpagent(agent)
    except Exception, e:
      Log.e("getSnmpAgent", "Could not set SNMP agent on %s: %s" % 
            (netbox.getSysname(), e) )

  def getDisks(self, netbox, snmp, infoContainer):
    """Retrieve disk data and prepare to store in deviceData.
    
       netbox -- getDeviceData.plugins.BoksData instance of the netbox
              to investigate
       snmp -- SimpleSnmp.SimpleSnmp instance, a prepared 
               SNMP connection to the netbox
       infoContainer -- a NetboxInfoContainer to store information
                        about this netbox
    """
    # First - get the ignores and.. check if we have anything to do at all
    ignores = self.getDiskconf(netbox)
    for (path, option) in ignores:
      if path == '*':
        # No none of the disks on this machine should be checked
        return
    
    # And now for some magic to combine decriptions and filesystem
    disks = Units()
    # Note that accessing disks[diskID] will create a Unit if it
    # does not exist.

    # Get the descriptions
    snmp.setBaseOid(OID.diskDescriptions)
    diskDescriptions = snmp.getAll(1)
    for (diskID, description) in diskDescriptions:
      # uhm.. get diskID, this is the last number in the OID
      #print "Fant disk %s med deskripsjon %s" %  (diskID, description)
      disks[diskID].description = description

    # .. and their filesystems
    snmp.setBaseOid(OID.diskFilesystems)
    diskFilesystems = snmp.getAll(1)
    for (diskID, filesystem) in diskFilesystems:
      # uhm.. get diskID, this is the last number in the OID
      #print "Fant disk %s med filsystem %s" %  (diskID, filesystem)
      disks[diskID].type = filesystem

    #...and also their blocksize
    snmp.setBaseOid(OID.diskBlockSize)
    diskBlockSize = snmp.getAll(1)
    for (diskID,blocksize) in diskBlockSize:
      #print "Fant disk %s med blokkstr %s" % (diskID,blocksize)
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
        Log.d("getDisks", 
              "Skipping disk %s on %s since it has no description" % 
                  (disk, netbox.getSysname()) )
        del disks[disk.unitID]
      
      # /dev and /proc and their childs are not interesting
      # Here we will sort out the partitions we don't want to monitor
      for (path, option) in ignores:
        if option == 'recursive':
          path += '*' # Make the pattern recursive, ie. /Store/ -> /Store/*
        if(fnmatch.fnmatch(disk.description, path)):
          del disks[disk.unitID]

    # Insert the resulting disks into database
    for disk in disks.values():
      try:
        blocksize = int(disk.size)
      except:
        Log.d("getDisks", "Invalid blocksize, using default of 1024 for %s on %s" % 
                            (disk, netbox.getSysname()))
        blocksize = 1024 # Default
      

      # Insert into database.. note that disk.description is the
      # key used to match these different attributes
      infoContainer.put(disk.description, 'disk_unitid', disk.unitID)
      infoContainer.put(disk.description, 'disk_filesystem', disk.type)
      infoContainer.put(disk.description, 'disk_blocksize', blocksize)

  def getInterfaces(self, netbox, snmp, infoContainer):
    """Retrieve interface names and prepare to store in deviceData.
    
       netbox -- getDeviceData.plugins.BoksData instance of the netbox
              to investigate
       snmp -- SimpleSnmp.SimpleSnmp instance of prepared 
               SNMP connection to the netbox
       infoContainer -- a NetboxInfoContainer to store information
                        about this netbox
    """
    
    # And now for some magic to combine decriptions and interface type
    interfaces = Units()
    # Note that accessing interfaces[interfaceID] will create a Unit if it
    # does not exist.

    # Get the descriptions
    snmp.setBaseOid(OID.interfaceDescriptions)
    interfaceDescriptions = snmp.getAll(1)
    for (interfaceID, description) in interfaceDescriptions:
      interfaces[interfaceID].description = description

    # .. and their interfacetypes
    snmp.setBaseOid(OID.interfaceTypes)
    interfaceTypes = snmp.getAll(1)
    for (interfaceID, type) in interfaceTypes:
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
      infoContainer.put(interface.description, 
                        'interf_unitid', interface.unitID)
      infoContainer.put(interface.description, 
                        'interf_type', interface.unitID)
                        

    
