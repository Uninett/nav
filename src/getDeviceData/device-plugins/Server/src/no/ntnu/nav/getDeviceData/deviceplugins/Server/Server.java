package no.ntnu.nav.getDeviceData.deviceplugins.Server;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.NetboxInfo.*;

/**
  * A small class to help us store 
  * disk information before submitting it
  */
class DiskMap extends HashMap {
    // positions  
    public static final int OID = 0;  
    public static final int DESCR = 1;  
    public static final int TYPE = 2;  
    public static final int BLOCKSIZE = 3;  
      
    public DiskMap() {
        super();
    }
    public String[] getDisk(String oid) {
        if (! this.containsKey(oid)) {
            String[] blank = {oid, "", "", ""};
            blank[OID] = oid;
            this.put(oid, blank);
        }
        return (String[])this.get(oid);
    }
    /** Extends the hashmap using the
      *  list, filling one of the posiutions OID, DESCR, TYPE or
      *  BLOCKSIZE
      */
    public void extendAs(List list, int pos) {
        // Use the OID (first pos in array) as key
        Iterator iter = list.iterator();
        while(iter.hasNext()) {
            String[] oid_value = (String[])iter.next();
            String[] diskinfo = this.getDisk(oid_value[0]);
            diskinfo[pos] = oid_value[1]; 
        }
    }
    public Iterator iterator() {
        Collection values = this.values();
        return values.iterator();
    }
}

public class Server implements DeviceHandler
{
    /** An inner class to seperate the actual work and keep thread safe 
      * references to the current netbox etc.
      */
    // some common constants.. 
    static final String OID_sysDescr = "1.3.6.1.2.1.1.1";
    static final String OID_sysObjectID = "1.3.6.1.2.1.1.2";
    static final String OID_interfaceDescriptions = "1.3.6.1.2.1.2.2.1.2";
    static final String OID_interfaceTypes = "1.3.6.1.2.1.2.2.1.3";
    static final String OID_interfaceLoopback = "24"; // really an Integer, not an OID =)
    static final String OID_diskDescriptions = "1.3.6.1.2.1.25.2.3.1.3";
    static final String OID_diskBlockSize ="1.3.6.1.2.1.25.2.3.1.4";
    static final String OID_diskFilesystems = "1.3.6.1.2.1.25.3.8.1.4";
    static final String OID_filesystemNFS = "1.3.6.1.2.1.25.3.9.14";
    static final String OID_filesystemUnknown = "1.3.6.1.2.1.25.3.9.2";
    static final String OID_solarisAgent = "1.3.6.1.4.1.8072.3.2.3";
    static final String OID_linuxAgent = "1.3.6.1.4.1.8072.3.2.10";
    static final String OID_other = "1.3.6.1.4.1.8072.3.2.255";
    static final String OID_bugAgent = "1.3.6.1.4.1.8072.3.2";
    static final String OID_windows = "1.3.6.1.4.1.311";
    class ServerHandler {
        Netbox nb;
        SimpleSnmp snmp;
        ConfigParser cp;
        NetboxInfoContainer info;
        public ServerHandler(Netbox nb, SimpleSnmp snmp, 
                             ConfigParser cp, DataContainers containers) {
                                       
            Log.setDefaultSubsystem("ServerPlugin " + nb.getSysname());
            Log.d("ServerHandler", "Handling the device");
            // Blapp Blapp = Blapp Blapp blapp blapp blapp blapp !!!!
            NetboxInfoContainer info = 
                (NetboxInfoContainer)containers.getContainer("NetboxInfoContainer");
            // Store stuff
            this.nb = nb;
            this.snmp = snmp;
            this.cp = cp;
            this.info = info;
            // don't need this, really
            // this.containers = containers
        }
        void getSnmp() {
            snmp.setBaseOid(OID_sysDescr);
            List result = snmp.getAll(true);
            if ( result.isEmpty() ) {
                Log.w("getSnmp", "No sysDescr found");
                return;
            }
            String descr = (String)result.get(0);
            Log.i("getSnmp", "sysDescr found: " + descr);
            info.put("snmp_agent", descr);
            String os;
            if (descr.equals(OID_solarisAgent)) {
                os = "solaris";
            } else if (descr.equals(OID_linuxAgent)) {
                os = "linux";
            } else if (descr.startsWith(OID_bugAgent)) {
                os = "unix"; // when is this?
            } else if (descr.startsWith(OID_windows)) {
                os = "windows"; // could guess version
            } else {
                os = "unknown";
            }
            Log.i("getSnmp", "os guessed: " + os);
            info.put("os_guess", os);
        }
        void getDisks() {
            DiskMap disks = new DiskMap();

            snmp.setBaseOid(OID_diskDescriptions);
            List result = snmp.getAll(true);
            disks.extendAs(result, disks.DESCR);

            snmp.setBaseOid(OID_diskFilesystems);
            result = snmp.getAll(true);
            disks.extendAs(result, disks.TYPE);

            snmp.setBaseOid(OID_diskBlockSize);
            result = snmp.getAll(true);
            disks.extendAs(result, disks.BLOCKSIZE);


            Iterator iter = disks.iterator();
            while (iter.hasNext()) {
                // ooo, how beautiful it is to not have value unpacking!
                String[] disk = (String[])iter.next();
                String id = disk[disks.OID];
                String descr = disk[disks.DESCR];
                String type = disk[disks.TYPE];
                String blocksize = disk[disks.BLOCKSIZE];

                int blocksizeInt;
                if (type.equals(OID_filesystemNFS)) 
                    continue;
                if (type.equals(OID_filesystemUnknown)) 
                    continue;
                if (type.equals("") || descr.equals("")) {
                    Log.i("getDisks", "Skipping disk " + id + " since it has no description or type");
                    continue;
                }
                try {
                    blocksizeInt = Integer.parseInt(blocksize);
                    if (blocksizeInt < 1)
                        blocksizeInt = 1024;
                } catch (NumberFormatException e) {
                    blocksizeInt = 1024;
                }
                Log.d("getDisks", "Adding " + descr + " " + type + 
                      " " + blocksizeInt);
                info.put(descr, "disk_unitid", id);
                info.put(descr, "disk_type", type);
                info.put(descr, "disk_blocksizeInt",
                         Integer.toString(blocksizeInt));
            }
        }
        void getInterfaces() {
            snmp.setBaseOid(OID_interfaceDescriptions);
            ArrayList interfaceDescriptions = snmp.getAll(true);
            snmp.setBaseOid(OID_interfaceTypes);
            ArrayList interfaceTypes = snmp.getAll(true);
            if (! (interfaceDescriptions.size() == interfaceTypes.size())) {
                Log.e("getInterfaces", 
                  "Our stupid assumption about snmp-results-sizes were wrong, please add 50 lines of java code");
                // You need to gather these in a HashMap or something
                // like that.. use the id (the first string of each
                // String-list).
                return;
            }
            Iterator descriptions = interfaceDescriptions.iterator();
            Iterator types = interfaceTypes.iterator();
            while (descriptions.hasNext()) {
                String description, type, id;
                String[] tmpArray;
                tmpArray = (String[])descriptions.next();
                id = tmpArray[0];
                description = tmpArray[1];
                tmpArray = (String[])types.next();
                if (! tmpArray[0].equals(id)) {
                    Log.e("getInterfaces", 
                       "Assumption about snmp-results failed, mismatch for id " + 
                       id + "/" + tmpArray[0]);
                    continue; // hehe
                }
                type = tmpArray[1];

                // Ok, we've got an interface, but should
                // we add it?
                if (type.equals(OID_interfaceLoopback))
                    continue;
                if (description.equals(""))
                    continue;
                if (description.startsWith("dummy"))
                    continue;
                info.put(description, "interf_unitid", id);
                info.put(description, "interf_type", type);
                Log.d("getInterfaces", "Added interface " + id + " " + description + " " + type);
            }
        }
        void sync() {
            this.info.commit();
        }
    }
    public int canHandleDevice(Netbox nb) {
        if (nb.getCat().equalsIgnoreCase("srv")  && nb.getCommunityRo() != null) {
            Log.d("ServerPlugin", "canHandleDevice", "We are ready to serve " + nb.getSysname());
            return DeviceHandler.ALWAYS_HANDLE;
        } 
        Log.d("ServerPlugin", "canHandleDevice", "We cannot serve " + nb.getSysname());
        return DeviceHandler.NEVER_HANDLE;
    }
    public void handleDevice(Netbox nb, SimpleSnmp snmp, 
                             ConfigParser cp, DataContainers containers) 
                throws TimeoutException {
        // prepare the snmp connection (why wasn't this done by the
        // caller?)
        snmp.setHost(nb.getIp());
        snmp.setCs_ro(nb.getCommunityRo());
        ServerHandler handler = new ServerHandler(nb, snmp, cp, containers);
        handler.getSnmp();
        handler.getDisks();
        handler.getInterfaces();
        handler.sync();
    }
}
    
