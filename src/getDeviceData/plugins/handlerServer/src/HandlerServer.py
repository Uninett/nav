import no.ntnu.nav.Database.Database as db 
import no.ntnu.nav.SimpleSnmp as snmp
from no.ntnu.nav.getDeviceData.plugins import DeviceHandler

class OID:
  """Constants for typical used OIDs"""
  sysObjectID = "1.3.6.1.2.1.1.2.0"
  interface = "1.3.6.1.2.1.2.2.1.2"
  interfaceTypes = "1.3.6.1.2.1.2.2.1.3" 
  interfaceLoopback = "24" # really an Integer, not an OID =)
  diskDescriptions = "1.3.6.1.2.1.25.2.3.1.3" 
  diskFilesystems = "1.3.6.1.2.1.25.3.8.1.4"
  filesystemNFS = "1.3.6.1.2.1.25.3.9.14"
  filesystemUnknown = "1.3.6.1.2.1.25.3.9.2"


class HandlerServer(DeviceHandler):
  def canHandleDevice(self, box):
    """Report if this box is our responsibility"""
    # Lower the string before compare
    print "Skal sjekke", box
    if(box.getKat().lower() == 'srv'):
      # Check the SNMP field
      resultset = db.query("SELECT snmp FROM boks WHERE boksid='%s'" %
                           boks.getBoksid())
      print resultset                     
      
    return 0  
  def handle(self, box, snmp, devicedata):
    """Process this box."""

    print "Handler", box

    # Prepare smnp connection
    snmp.setHost(box.getIp())
    snmp.setCs_ro(box.getCommunityRo())

    # Retrieve snmpagent version 
    snmp.setBaseOid(OID.sysObjectID)
    result = snmp.getAll() 
    print result  # How does this look out, really?

    agent = result[0][0] # This should be an OID
    print agent


    # Retrieve disks
    snmp.setBaseOid(OID.diskDescriptions)
    diskDescriptions = snmp.getAll()
    # .. and their filesystems
    snmp.setBaseOid(OID.diskFilesystems)
    diskFilesystems = snmp.getAll()

    for disk in diskDescriptions:
      # uhm.. get diskID, this is the last number in the OID
      diskID = disk[0]


    

    
    

    
    

    
          

